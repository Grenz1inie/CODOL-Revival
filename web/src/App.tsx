import {useEffect, useState} from 'react';
import {Theme, Button, Switch, TextField, Select} from '@radix-ui/themes';
import {BookOpen, SlidersHorizontal, CaretRight, Folder, FileText, ArrowClockwise, Play, Star, Coins, Sun, Moon} from '@phosphor-icons/react';
import Markdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

type Settings = {skip_tutorial: boolean};
type Profile = {user_id: string; level?: number; prestige?: number; currency?: number; premium?: number};
type Status = {profiles: Profile[]; game_running: boolean; capabilities: Record<string, {available: boolean; reason: string}>};
type InventoryItem = {item_id:number; quantity:number; expires:number; name?:string};
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
  const [inventory, setInventory] = useState<InventoryItem[]>([]);
  const [renewItem, setRenewItem] = useState('');
  const [renewDays, setRenewDays] = useState('30');
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');
  async function refresh() {
    const [s, state] = await Promise.all([api<Settings>('settings'), api<Status>('status')]);
    setSettings(s); setStatus(state);
    setAccount(current => current || state.profiles[0]?.user_id || '');
    const uid = account || state.profiles[0]?.user_id;
    if(uid) setInventory((await api<{items:InventoryItem[]}>('inventory?user_id=' + uid)).items);
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
  useEffect(()=>{ setRenewItem(''); setInventory([]); if(account) api<{items:InventoryItem[]}>('inventory?user_id=' + account).then(r=>setInventory(r.items)).catch(e=>setError(e.message)); },[account]);
  const timedItems = inventory.filter(item=>item.expires !== 4294967295);
  const profile = status?.profiles.find(p=>p.user_id===account);
  const capability = (name:string)=>status?.capabilities[name];
  const editable = !!account && !busy && !status?.game_running;
  return <Theme appearance={dark?'dark':'light'} accentColor="amber" grayColor="gray" radius="small" scaling="100%">
    <div className="shell">
      <aside className="navigation">
        <div className="brand"><span className="brand-mark">CO</span><div><strong>CODOL</strong><small>本地控制器</small></div></div>
        <nav aria-label="主导航"><button className={page==='control'?'active':''} onClick={()=>setPage('control')}><SlidersHorizontal size={20}/>游戏控制</button><button className={page==='wiki'?'active':''} onClick={()=>setPage('wiki')}><BookOpen size={20}/>开发 WIKI</button></nav>
        <div className="nav-bottom"><span className="mono">127.0.0.1</span><span>本地档案与服务</span><button onClick={()=>setDark(!dark)}>{dark?<Sun size={18}/>:<Moon size={18}/>}切换{dark?'浅色':'深色'}</button></div>
      </aside>
      <main>
        <header className="topbar"><span>CODOL / {page==='control'?'游戏控制':'开发 WIKI'}</span><Button variant="ghost" disabled={busy} onClick={()=>refresh().then(()=>setMessage('状态已更新')).catch(e=>setError(e.message))}><ArrowClockwise/>刷新状态</Button></header>
        {error && <div className="notice error" role="alert">{error}</div>}
        {message && <div className="notice" role="status">{message}</div>}
        {page==='control' ? <div className="workspace">
          <div className="page-heading"><div><p className="eyebrow">本地游戏</p><h1>玩家与启动设置</h1><p>管理当前档案，设置下一次游戏启动。</p></div><Button size="3" disabled={busy || status?.game_running} onClick={()=>act('game/launch',{},'游戏启动命令已执行')}><Play weight="fill"/>启动游戏</Button></div>
          <section className="profile-strip"><div><span className="label">当前档案</span><Select.Root value={account || undefined} onValueChange={setAccount}><Select.Trigger placeholder="尚无档案"/><Select.Content>{status?.profiles.map(p=><Select.Item key={p.user_id} value={p.user_id}>{p.user_id}</Select.Item>)}</Select.Content></Select.Root></div><div><span className="label">等级</span><strong>{profile?.level ?? '待读取'}</strong></div><div><span className="label">转生</span><strong>{profile?.prestige === undefined ? '待读取' : `${profile.prestige} 转`}</strong></div><div><span className="label">游戏状态</span><strong>{status ? (status.game_running?'运行中':'未运行') : '读取中'}</strong></div></section>
          <div className="control-grid"><div className="primary-column">
            <section className="panel"><div className="section-title"><Star size={22}/><h2>等级与转生</h2></div><p>按此版本等级表，设置最高等级和转生次数。</p><div className="form-row"><span>目标等级</span><strong>3 转生 · 70 级</strong></div><Button disabled={!editable || !capability('progression')?.available} onClick={()=>act('profile/progression',{user_id:account,prestige:3,level:70},'等级设置已保存，请重新启动游戏')} >设置最高等级</Button><p className="helper">{capability('progression')?.reason || '正在确认客户端字段'}</p></section>
            <section className="panel"><h2>剧情关卡</h2><p>解除当前地图表中剧情关卡的前置条件。地图启动与可玩性仍在恢复中。</p><Button disabled={!editable} onClick={()=>act('profile/story',{user_id:account},'剧情关卡解锁数据已保存，请重新启动游戏')}>解锁全部剧情关卡</Button><p className="helper">只修改剧情前置条件，保留等级、货币和库存。请退出游戏后操作。</p></section>
            <section className="panel"><div className="section-title"><Coins size={22}/><h2>游戏币与商城</h2></div><p>本地余额：<strong>{profile?.currency?.toLocaleString() ?? '待读取'}</strong>。向当前账号增加游戏币。</p><label htmlFor="amount" className="field-label">增加数量</label><div className="input-action"><TextField.Root id="amount" type="number" min="1" max="2147483647" value={amount} onChange={e=>setAmount(e.target.value)}/><Button disabled={!editable || !capability('currency')?.available} onClick={()=>act('profile/currency',{user_id:account,amount:Number(amount)},'游戏币已更新')}>增加游戏币</Button></div><p className="helper">{status?.game_running ? '请先退出游戏，再修改余额。' : capability('currency')?.reason || '正在确认货币协议'}</p><div className="subsection"><h3>点券</h3><p>本地余额：<strong>{profile?.premium?.toLocaleString() ?? '待读取'}</strong></p><label htmlFor="premium-amount" className="field-label">增加点券数量</label><div className="input-action"><TextField.Root id="premium-amount" type="number" min="1" max="2147483647" value={premiumAmount} onChange={e=>setPremiumAmount(e.target.value)}/><Button disabled={!editable || !capability('currency')?.available} onClick={()=>act('profile/premium',{user_id:account,amount:Number(premiumAmount)},'点券已更新')}>增加点券</Button></div></div><div className="subsection"><h3>商城内容</h3><Button variant="soft" disabled={!editable || !capability('inventory')?.available} onClick={()=>act('profile/unlock',{user_id:account},'全部物品已保存，请重启游戏读取')}>一键发放全部物品</Button><p className="helper">{capability('inventory')?.reason || '正在确认物品数据'}</p></div><div className="subsection"><h3>限时物品续期</h3><p className="helper">从当前到期日续期；已过期的物品从现在起计算。永久物品无需续期。</p>{timedItems.length ? <><label htmlFor="renew-item" className="field-label">选择物品</label><select id="renew-item" value={renewItem} onChange={e=>setRenewItem(e.target.value)}><option value="">请选择</option>{timedItems.map(item=><option key={item.item_id} value={item.item_id}>{item.name || `物品 ${item.item_id}`} · {new Date(item.expires*1000).toLocaleDateString()} 到期</option>)}</select><label htmlFor="renew-days" className="field-label">增加天数</label><div className="input-action"><TextField.Root id="renew-days" type="number" min="1" max="36500" value={renewDays} onChange={e=>setRenewDays(e.target.value)}/><Button disabled={!editable || !renewItem} onClick={()=>act('profile/renew',{user_id:account,item_id:Number(renewItem),days:Number(renewDays)},'续期已保存')}>续期</Button></div></> : <p>当前没有限时物品。</p>}</div></section>
          </div><aside className="secondary-column"><section className="panel"><h2>启动选项</h2><div className="switch-row"><label htmlFor="skip">跳过新手引导</label><Switch id="skip" checked={settings?.skip_tutorial ?? true} disabled={busy || !settings} onCheckedChange={value=>act('settings',{skip_tutorial:value},'启动选项已保存')}/></div><p className="helper">默认开启。训练服务尚未恢复；更改在下一次启动生效。</p></section><section className="usage"><h3>修改档案</h3><p>先退出游戏，再修改数据，随后重新启动读取。写入前保留原档案备份。</p><button className="text-link" onClick={()=>{setPage('wiki');void openDoc('wiki/06-onboarding-profile.md');}}>查看档案与引导说明<CaretRight/></button></section></aside></div>
        </div> : <div className="wiki-layout"><aside className="wiki-tree"><div className="tree-title">docs <span>{files.length} 个文件</span></div><FileTree files={files} active={doc.path} onSelect={openDoc}/></aside><article className="document"><div className="document-path"><FileText/>{doc.path || '选择文档'}</div>{doc.path.endsWith('.md') ? <Markdown remarkPlugins={[remarkGfm]} components={{a:({href='',children})=>{
          if (/^https?:\/\//.test(href)) return <a href={href} target="_blank" rel="noreferrer">{children}</a>;
          const path = localDoc(href);
          return path ? <a href={'/?doc='+encodeURIComponent(path)} onClick={e=>{e.preventDefault();void openDoc(path);}}>{children}</a> : <span title={'docs 以外的本地引用：'+href}>{children} <code className="helper">{href}</code></span>;
        }, img:({alt})=><span className="helper">[图片：{alt || '本地证据附件'}]</span>}}>{doc.content}</Markdown> : <pre className="raw-doc">{doc.content}</pre>}</article></div>}
      </main>
    </div>
  </Theme>;
}
