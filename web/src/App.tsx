import {useEffect, useState} from 'react';
import {Theme, Button, Switch, TextField, Select} from '@radix-ui/themes';
import {BookOpen, SlidersHorizontal, CaretRight, Folder, FileText, ArrowClockwise, Play, Stop, Star, Coins, Sun, Moon, Package, Flag, ArrowUpRight, ShieldCheck} from '@phosphor-icons/react';
import Markdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

type Settings = {skip_tutorial: boolean};
type Profile = {user_id: string; level?: number; prestige?: number; currency?: number; premium?: number};
type Status = {profiles: Profile[]; game_running: boolean; capabilities: Record<string, {available: boolean; reason: string}>};
type Doc = {path: string; size: number};
async function api<T>(path: string, data?: unknown): Promise<T> {
  const response = await fetch('/api/' + path, data === undefined ? undefined : {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(data)});
  const result = await response.json();
  if (!response.ok) throw new Error(result.error || '请求失败');
  return result;
}

function FileTree({files, active, onSelect, prefix = ''}: {files: Doc[]; active:string; onSelect:(p:string)=>void; prefix?:string}) {
  const names = [...new Set(files.map(f => f.path.slice(prefix.length).split('/')[0]))];
  return <ul className="file-tree">{names.map(name => {
    const path = prefix + name;
    const children = files.filter(f => f.path.startsWith(path + '/'));
    return <li key={path}>{children.length ? <details open><summary><Folder size={17}/>{name}</summary><FileTree files={children} active={active} onSelect={onSelect} prefix={path + '/'}/></details> : <button className={path === active ? 'selected' : ''} onClick={()=>onSelect(path)}><FileText size={16}/><span>{name}</span></button>}</li>;
  })}</ul>;
}

export default function App() {
  const [page, setPage] = useState(new URLSearchParams(location.search).has('doc') ? 'wiki' : 'control');
  const [dark, setDark] = useState(matchMedia('(prefers-color-scheme: dark)').matches);
  const [settings, setSettings] = useState<Settings>();
  const [status, setStatus] = useState<Status>();
  const [files, setFiles] = useState<Doc[]>([]);
  const [doc, setDoc] = useState({path:'', content:''});
  const [account, setAccount] = useState('');
  const [amount, setAmount] = useState('100000');
  const [premiumAmount, setPremiumAmount] = useState('100000');
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');
  async function refresh() {
    const [s, state] = await Promise.all([api<Settings>('settings'), api<Status>('status')]);
    setSettings(s); setStatus(state);
    setAccount(current => current || state.profiles[0]?.user_id || '');
  }
  async function openDoc(path:string) {
    try { setDoc(await api('docs/file?path=' + encodeURIComponent(path))); setError(''); window.scrollTo(0, 0); }
    catch(e) { setError(String(e instanceof Error ? e.message : e)); }
  }
  useEffect(()=>{ refresh().catch(e=>setError(e.message)); api<{files:Doc[]}>('docs').then(r=>{setFiles(r.files); const first=r.files.find(f=>f.path===new URLSearchParams(location.search).get('doc')) || r.files.find(f=>f.path==='README.md') || r.files[0]; if(first) void openDoc(first.path);}).catch(e=>setError(e.message)); },[]);
  async function act(path:string, data:unknown, success:string) {
    setBusy(true); setError(''); setMessage('');
    try {const result = await api<{message?:string}>(path,data); setMessage(result.message || success); await refresh();}
    catch(e) {setError(e instanceof Error ? e.message : String(e));}
    finally {setBusy(false);}
  }
  function localDoc(href:string) {
    const resolved = new URL(href, 'http://docs/docs/' + doc.path);
    if (resolved.origin !== 'http://docs' || !resolved.pathname.startsWith('/docs/')) return undefined;
    const path = decodeURIComponent(resolved.pathname.slice(6));
    return files.some(file=>file.path===path) ? path : undefined;
  }
  const profile = status?.profiles.find(p=>p.user_id===account);
  const capability = (name:string)=>status?.capabilities[name];
  const editable = !!account && !busy && !status?.game_running;
  return <Theme appearance={dark?'dark':'light'} accentColor="blue" grayColor="slate" radius="medium" scaling="100%">
    <div className="shell">
      <header className="navigation">
        <div className="brand"><strong className="brand-wordmark">CODOL</strong><small>本地控制器<span aria-hidden="true"> / LOCAL</span></small></div>
        <nav aria-label="主导航"><button className={page==='control'?'active':''} aria-current={page==='control'?'page':undefined} onClick={()=>setPage('control')}><SlidersHorizontal size={20}/>游戏控制</button><button className={page==='wiki'?'active':''} aria-current={page==='wiki'?'page':undefined} onClick={()=>setPage('wiki')}><BookOpen size={20}/>开发 WIKI</button></nav>
        <div className="header-tools">
          <span className="local-address mono">127.0.0.1</span>
          <Button variant="ghost" disabled={busy} onClick={()=>refresh().then(()=>setMessage('状态已更新')).catch(e=>setError(e.message))}><ArrowClockwise/>刷新状态</Button>
          <Button variant="ghost" onClick={()=>setDark(!dark)}>{dark?<Sun size={18}/>:<Moon size={18}/>}切换{dark?'浅色':'深色'}</Button>
        </div>
      </header>
      <main>
        {error && <div className="notice error" role="alert">{error}</div>}
        {message && <div className="notice" role="status">{message}</div>}
        {page==='control' ? <div className="workspace">
          <div className="page-heading">
            <div><p className="eyebrow"><span className="mono">LOCAL SESSION</span><span>本地游戏</span></p><h1>玩家与启动设置</h1><p>管理当前档案，设置下一次游戏启动。</p></div>
            <div className="game-actions">
              <Button className="stop-button" variant="soft" size="3" disabled={busy || !status?.game_running} onClick={()=>act('game/stop',{},'游戏已停止。')}><Stop weight="fill"/>停止游戏</Button>
              <Button className="launch-button" size="3" disabled={busy || status?.game_running} onClick={()=>act('game/launch',{},'游戏启动命令已执行')}><Play weight="fill"/><span>启动游戏</span><ArrowUpRight className="launch-arrow"/></Button>
            </div>
          </div>
          <section className="profile-strip" aria-label="玩家概况">
            <div><label className="label" htmlFor="account">当前档案</label><Select.Root value={account} onValueChange={setAccount}><Select.Trigger id="account" placeholder="尚无档案"/><Select.Content>{status?.profiles.map(p=><Select.Item key={p.user_id} value={p.user_id}>{p.user_id}</Select.Item>)}</Select.Content></Select.Root></div>
            <div><span className="label">等级</span><strong>{profile?.level ?? '待读取'}</strong></div>
            <div><span className="label">转生</span><strong>{profile?.prestige === undefined ? '待读取' : `${profile.prestige} 转`}</strong></div>
            <div><span className="label">游戏状态</span><strong className={'game-state ' + (status?.game_running?'running':'')}><span className="state-dot"/>{status ? (status.game_running?'运行中':'未运行') : '读取中'}</strong></div>
          </section>
          {status?.game_running && <p className="edit-hint">游戏运行中，档案修改已锁定。退出游戏后刷新状态即可操作。</p>}
          <div className="control-grid">
            <div className="primary-column">
              <section className="wallet-panel" aria-labelledby="wallet-title">
                <h2 id="wallet-title" className="sr-only">游戏币与商城</h2>
                <div className="wallet-grid">
                  <section className="wallet panel" aria-labelledby="currency-title">
                    <div className="balance-label"><Coins size={19}/><h3 id="currency-title">游戏币</h3><span className="mono">CP</span></div>
                    <strong className="balance">{profile?.currency?.toLocaleString() ?? '待读取'}</strong>
                    <label htmlFor="amount" className="field-label">增加数量</label>
                    <div className="input-action"><TextField.Root id="amount" type="number" min="1" max="2147483647" value={amount} onChange={e=>setAmount(e.target.value)}/><Button variant="soft" disabled={!editable || !capability('currency')?.available} onClick={()=>act('profile/currency',{user_id:account,amount:Number(amount)},'游戏币已更新')}>增加游戏币</Button></div>
                  </section>
                  <section className="wallet panel" aria-labelledby="premium-title">
                    <div className="balance-label"><Coins size={19}/><h3 id="premium-title">点券</h3><span className="mono">CC</span></div>
                    <strong className="balance">{profile?.premium?.toLocaleString() ?? '待读取'}</strong>
                    <label htmlFor="premium-amount" className="field-label">增加点券数量</label>
                    <div className="input-action"><TextField.Root id="premium-amount" type="number" min="1" max="2147483647" value={premiumAmount} onChange={e=>setPremiumAmount(e.target.value)}/><Button variant="soft" disabled={!editable || !capability('currency')?.available} onClick={()=>act('profile/premium',{user_id:account,amount:Number(premiumAmount)},'点券已更新')}>增加点券</Button></div>
                  </section>
                </div>
                <p className="helper">{status?.game_running ? '请先退出游戏，再修改余额。' : capability('currency')?.reason || '正在确认货币协议'}</p>
              </section>
              <section className="quick-grid" aria-labelledby="quick-title">
                <h2 id="quick-title" className="group-heading">快捷操作<span className="mono" aria-hidden="true">QUICK ACTIONS</span></h2>
                <section className="panel quick-panel" aria-labelledby="progression-title">
                  <span className="action-icon"><Star size={22}/></span>
                  <div className="quick-copy"><h3 id="progression-title">等级与转生</h3><p className="helper">{capability('progression')?.reason || '正在确认客户端字段'}</p></div>
                  <Button variant="soft" disabled={!editable || !capability('progression')?.available} onClick={()=>act('profile/progression',{user_id:account,prestige:3,level:70},'等级设置已保存，请重新启动游戏')}>设置最高等级</Button>
                </section>
                <section className="panel quick-panel" aria-labelledby="story-title">
                  <span className="action-icon"><Flag size={22}/></span>
                  <div className="quick-copy"><h3 id="story-title">剧情关卡</h3><p className="helper">解除剧情前置条件，保留等级、货币和库存。地图启动与可玩性仍在恢复中；请退出游戏后操作。</p></div>
                  <Button variant="soft" disabled={!editable} onClick={()=>act('profile/story',{user_id:account},'剧情关卡解锁数据已保存，请重新启动游戏')}>解锁全部剧情关卡</Button>
                </section>
                <section className="panel quick-panel" aria-labelledby="inventory-title">
                  <span className="action-icon"><Package size={22}/></span>
                  <div className="quick-copy"><h3 id="inventory-title">商城内容</h3><p className="helper">{capability('inventory')?.reason || '正在确认物品数据'}</p></div>
                  <Button variant="soft" disabled={!editable || !capability('inventory')?.available} onClick={()=>act('profile/unlock',{user_id:account},'全部物品已保存，请重启游戏读取')}>一键发放全部物品</Button>
                </section>
              </section>
            </div>
            <aside className="secondary-column">
              <section className="panel startup-panel" aria-labelledby="startup-title">
                <div className="section-title"><SlidersHorizontal size={20}/><h2 id="startup-title">启动选项</h2><span className="section-code">下次启动生效</span></div>
                <div className="switch-row"><label htmlFor="skip">跳过新手引导</label><Switch id="skip" checked={settings?.skip_tutorial ?? true} disabled={busy || !settings} onCheckedChange={value=>act('settings',{skip_tutorial:value},'启动选项已保存')}/></div>
                <p className="helper">默认开启。训练服务尚未恢复；更改在下一次启动生效。</p>
              </section>
            </aside>
          </div>
          <footer className="usage"><ShieldCheck size={18}/><p>先退出游戏，再修改数据，随后重新启动读取。写入前保留原档案备份。</p><button className="text-link" onClick={()=>{setPage('wiki');void openDoc('wiki/06-onboarding-profile.md');}}>查看档案与引导说明<CaretRight/></button></footer>
        </div> : <div className="wiki-layout"><aside className="wiki-tree"><div className="tree-title">docs <span>{files.length} 个文件</span></div><FileTree files={files} active={doc.path} onSelect={openDoc}/></aside><article className="document"><div className="document-path"><FileText/>{doc.path || '选择文档'}</div>{doc.path.endsWith('.md') ? <Markdown remarkPlugins={[remarkGfm]} components={{a:({href='',children})=>{
          if (/^https?:\/\//.test(href)) return <a href={href} target="_blank" rel="noreferrer">{children}</a>;
          const path = localDoc(href);
          return path ? <a href={'/?doc='+encodeURIComponent(path)} onClick={e=>{e.preventDefault();void openDoc(path);}}>{children}</a> : <span title={'docs 以外的本地引用：'+href}>{children} <code className="helper">{href}</code></span>;
        }, img:({alt})=><span className="helper">[图片：{alt || '本地证据附件'}]</span>}}>{doc.content}</Markdown> : <pre className="raw-doc">{doc.content}</pre>}</article></div>}
      </main>
    </div>
  </Theme>;
}
