// Sequential REA MCP client. All retained output stays in this analysis directory.
import {spawn} from 'node:child_process';
import {createInterface} from 'node:readline';
import {createWriteStream, mkdirSync, writeFileSync} from 'node:fs';
import {resolve, relative, isAbsolute} from 'node:path';

const root = resolve(import.meta.dirname, '..');
const base = process.env.REA_HOME || resolve(process.env.LOCALAPPDATA, 'Programs/rea');
mkdirSync(resolve(root, 'evidence/fresh'), {recursive: true});
const child = spawn(resolve(base, 'node_modules/node/bin/node.exe'),
  [resolve(base, 'node_modules/rea-agents/scripts/rea.mjs'), '--mcp'], {
    env: {...process.env,
      GHIDRA_INSTALL_DIR: process.env.GHIDRA_INSTALL_DIR || resolve(base, 'engines/ghidra_12.1.4_PUBLIC'),
      JAVA_HOME: process.env.JAVA_HOME || 'A:/Coding/Java/jdk-21.0.11.10-hotspot',
      REA_GHIDRA_STARTUP_TIMEOUT_MS: '1200000'},
    stdio: ['pipe', 'pipe', 'pipe'], windowsHide: true,
  });
child.stderr.pipe(createWriteStream(resolve(root, 'evidence/fresh/rea-session.log'), {flags: 'a'}));
const pending = new Map();
let sequence = 0;
function request(method, params) {
  return new Promise((resolve, reject) => {
    const id = ++sequence;
    pending.set(id, {resolve, reject});
    child.stdin.write(JSON.stringify({jsonrpc: '2.0', id, method, params}) + '\n');
  });
}
createInterface({input: child.stdout}).on('line', line => {
  let msg;
  try { msg = JSON.parse(line); } catch { return; }
  const entry = pending.get(msg.id);
  if (entry) {
    pending.delete(msg.id);
    msg.error ? entry.reject(msg.error) : entry.resolve(msg.result);
  }
});
child.on('exit', code => {
  for (const entry of pending.values()) entry.reject(new Error(`REA exited: ${code}`));
  console.log(JSON.stringify({event: 'rea-exit', code}));
});
await request('initialize', {protocolVersion: '2024-11-05', capabilities: {},
  clientInfo: {name: 'codol-recovered-code', version: '1'}});
child.stdin.write(JSON.stringify({jsonrpc: '2.0', method: 'notifications/initialized'}) + '\n');
console.log(JSON.stringify({event: 'ready', pid: child.pid, root}));
// Input: {name, arguments, output}; output is relative to evidence/fresh.
for await (const line of createInterface({input: process.stdin})) {
  if (!line.trim()) continue;
  if (line.trim() === 'quit') break; // Call close_binary before quitting.
  try {
    const command = JSON.parse(line);
    const directory = resolve(root, 'evidence/fresh');
    const output = resolve(directory, command.output || `${command.name}-${Date.now()}.json`);
    const rel = relative(directory, output);
    if (rel.startsWith('..') || isAbsolute(rel)) throw new Error('Output must stay in evidence/fresh');
    const startedAt = new Date().toISOString();
    console.log(JSON.stringify({event: 'started', name: command.name, startedAt}));
    const result = await request('tools/call', {name: command.name, arguments: command.arguments || {}});
    writeFileSync(output, JSON.stringify(result, null, 2) + '\n');
    const data = result.structuredContent || result.content?.find(c => c.type === 'text')?.text;
    const timing = {name: command.name, arguments: command.arguments || {}, startedAt,
      completedAt: new Date().toISOString(), output, isError: !!result.isError};
    writeFileSync(output + '.timing.json', JSON.stringify(timing, null, 2) + '\n');
    console.log(JSON.stringify({...timing, preview: JSON.stringify(data).slice(0, 650)}));
  } catch (error) { console.log(JSON.stringify({error: String(error), details: error})); }
}
child.stdin.end();
