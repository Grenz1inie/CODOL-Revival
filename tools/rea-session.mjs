import {spawn} from 'node:child_process';
import {createInterface} from 'node:readline';
import {createWriteStream, writeFileSync, mkdirSync} from 'node:fs';
import {resolve} from 'node:path';

const root = resolve(import.meta.dirname, '..');
const base = process.env.REA_HOME || resolve(process.env.LOCALAPPDATA, 'Programs/rea');
mkdirSync(resolve(root, 'runtime/logs'), {recursive:true});
mkdirSync(resolve(root, 'research/evidence'), {recursive:true});
const child = spawn(`${base}/node_modules/node/bin/node.exe`, [`${base}/node_modules/rea-agents/scripts/rea.mjs`, '--mcp'], {
  env: {...process.env, GHIDRA_INSTALL_DIR: process.env.GHIDRA_INSTALL_DIR || `${base}/engines/ghidra_12.1.4_PUBLIC`, REA_GHIDRA_STARTUP_TIMEOUT_MS: '1200000'},
  stdio: ['pipe', 'pipe', 'pipe'], windowsHide: true,
});
child.stderr.pipe(createWriteStream(resolve(root, 'runtime/logs/rea-session.log'), {flags:'a'}));
let seq=0;
const pending = new Map();
function request(method, params) {
  return new Promise((resolve, reject) => {
    const id=++seq;
    pending.set(id, {resolve,reject});
    child.stdin.write(JSON.stringify({jsonrpc:'2.0',id,method,params})+'\n');
  });
}
createInterface({input:child.stdout}).on('line', line => {
  let msg;
  try {msg=JSON.parse(line);} catch {return;}
  const p=pending.get(msg.id);
  if (p) {pending.delete(msg.id); msg.error ? p.reject(msg.error) : p.resolve(msg.result);}
});
child.on('exit', code => {console.log(JSON.stringify({event:'rea-exit',code})); process.exit(code || 0);});
await request('initialize',{protocolVersion:'2024-11-05',capabilities:{},clientInfo:{name:'codol-local-analysis',version:'1'}});
child.stdin.write(JSON.stringify({jsonrpc:'2.0',method:'notifications/initialized'})+'\n');
console.log('REA ready. Input {name,arguments,output} JSON lines; output is relative to research/evidence/.');
for await (const line of createInterface({input:process.stdin})) {
  if (!line.trim()) continue;
  try {
    const input=JSON.parse(line);
    const result=await request('tools/call',{name:input.name,arguments:input.arguments || {}});
    const output=resolve(root,'research/evidence',input.output || `${input.name}-${Date.now()}.json`);
    writeFileSync(output,JSON.stringify(result,null,2));
    console.log(JSON.stringify({name:input.name,output,isError:result.isError,preview:JSON.stringify(result.structuredContent || result.content).slice(0,1800)}));
  } catch (error) {console.log(JSON.stringify({error:String(error),details:error}));}
}
child.kill();
