import {useEffect, useRef, useState} from 'react';
import {Theme, Button, Switch, TextField, Select} from '@radix-ui/themes';
import {BookOpen, SlidersHorizontal, CaretRight, Folder, FileText, ArrowClockwise, Play, Stop, Star, Coins, Sun, Moon, Package, Flag, ArrowUpRight, ShieldCheck, HardDrives} from '@phosphor-icons/react';
import Markdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import {savedLanguage, translate, type Language} from './i18n';

type LaunchSettings = {player_name: string; fov: number; max_fps: number; display_mode: string; resolution: string};
type Settings = {skip_tutorial: boolean; launch?: LaunchSettings};
type Profile = {user_id: string; level?: number; prestige?: number; currency?: number; premium?: number};
type Installation = {state:string; path:string; version:string|null; reason:string; instance_id?:string};
type Version = {game_id:string; version:string; label:string; supported:boolean};
type Status = {installation: Installation; profiles: Profile[]; game_running: boolean; capabilities: Record<string, {available: boolean; reason: string; max_level?:number; max_prestige?:number; currency_label?:string; premium_label?:string}>};
type Doc = {path: string; size: number};
type ServerStatus = {running: boolean; pid: number | null; ready: boolean; ports: {name: string; protocol: string; port: number; listening: boolean; conflict: boolean}[]; match?: {phase:string; error:string; result?:{event:string; paid?:Record<string,number>; error?:string}}};
async function api<T>(path: string, data?: unknown): Promise<T> {
  const response = await fetch('/api/' + path, data === undefined ? undefined : {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(data)});
  const result = await response.json();
  if (!response.ok) throw Object.assign(new Error(result.error || '请求失败'), {detail: result.detail});
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

function LaunchOptions({value, disabled, onSave, t}: {value: LaunchSettings; disabled: boolean; onSave:(value:LaunchSettings)=>Promise<void>; t:(text:string)=>string}) {
  const [name, setName] = useState(value.player_name);
  const [fov, setFov] = useState(String(value.fov));
  const [fps, setFps] = useState(String(value.max_fps));
  const [displayMode, setDisplayMode] = useState(value.display_mode);
  const [resolution, setResolution] = useState(value.resolution);
  return <form onSubmit={event=>{event.preventDefault();void onSave({player_name:name, fov:Number(fov), max_fps:Number(fps), display_mode:displayMode, resolution});}}>
    <div className="launch-options">
      <div><label className="field-label" htmlFor="launch-name">{t('玩家名')}</label><TextField.Root id="launch-name" required minLength={3} maxLength={15} value={name} disabled={disabled} onChange={e=>setName(e.target.value)}/></div>
      <div><label className="field-label" htmlFor="launch-display-mode">{t('显示模式')}</label><Select.Root value={displayMode} disabled={disabled} onValueChange={setDisplayMode}><Select.Trigger id="launch-display-mode"/><Select.Content><Select.Item value="windowed">{t('窗口化')}</Select.Item><Select.Item value="fullscreen">{t('全屏')}</Select.Item></Select.Content></Select.Root></div>
      <div><label className="field-label" htmlFor="launch-resolution">{t('分辨率')}</label><Select.Root value={resolution} disabled={disabled} onValueChange={setResolution}><Select.Trigger id="launch-resolution"/><Select.Content>{['1280x720','1366x768','1600x900','1920x1080','2560x1440','3840x2160'].map(size=><Select.Item key={size} value={size}>{size.replace('x',' × ')}</Select.Item>)}</Select.Content></Select.Root></div>
      <div><label className="field-label" htmlFor="launch-fov">FOV</label><TextField.Root id="launch-fov" type="number" required min={60} max={120} step={1} value={fov} disabled={disabled} onChange={e=>setFov(e.target.value)}/></div>
      <div><label className="field-label" htmlFor="launch-fps">{t('帧率上限')}</label><TextField.Root id="launch-fps" type="number" required min={0} max={400} step={1} value={fps} disabled={disabled} onChange={e=>setFps(e.target.value)}/></div>
    </div>
    <p className="helper">{t('玩家名 3–15 位；FOV 60–120；帧率 0–400，0 表示不限。退出游戏后保存，下次启动生效。')}</p>
    <Button type="submit" variant="soft" disabled={disabled}>{t('保存启动选项')}</Button>
  </form>;
}

export default function App() {
  const [language, setLanguage] = useState<Language>(savedLanguage);
  const t = (text: string) => translate(text, language);
  useEffect(() => {
    document.documentElement.lang = language;
    document.title = language === 'en' ? 'CODOL · Local controller' : 'CODOL · 本地控制器';
    try { localStorage.setItem('codol-language', language); } catch { /* The switch still works when storage is unavailable. */ }
  }, [language]);
  const [page, setPage] = useState(new URLSearchParams(location.search).has('doc') ? 'wiki' : 'control');
  const [dark, setDark] = useState(matchMedia('(prefers-color-scheme: dark)').matches);
  const [settings, setSettings] = useState<Settings>();
  const [status, setStatus] = useState<Status>();
  const [versions, setVersions] = useState<Version[]>([]);
  const [statusError, setStatusError] = useState('');
  const [server, setServer] = useState<ServerStatus>();
  const [serverError, setServerError] = useState('');
  const [serverLoading, setServerLoading] = useState(true);
  const [gameAction, setGameAction] = useState('');
  const refreshRequest = useRef<Promise<void> | null>(null);
  const refreshTimer = useRef<ReturnType<typeof setTimeout> | undefined>(undefined);
  const actionPending = useRef(false);
  const mounted = useRef(false);
  const [files, setFiles] = useState<Doc[]>([]);
  const [doc, setDoc] = useState({path:'', content:''});
  const [account, setAccount] = useState('');
  const [amount, setAmount] = useState('100000');
  const [premiumAmount, setPremiumAmount] = useState('100000');
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');
  const [errorDetail, setErrorDetail] = useState('');
  async function refreshServer() {
    setServerLoading(true);
    try { setServer(await api<ServerStatus>('server/status')); setServerError(''); }
    catch(e) { setServer(undefined); setServerError(e instanceof Error ? e.message : String(e)); }
    finally { setServerLoading(false); }
  }
  function scheduleRefresh() {
    clearTimeout(refreshTimer.current);
    if (mounted.current && !document.hidden && !actionPending.current) {
      refreshTimer.current = setTimeout(()=>{void refresh();},10000);
    }
  }
  function refresh(): Promise<void> {
    if (refreshRequest.current) return refreshRequest.current;
    clearTimeout(refreshTimer.current);
    refreshRequest.current = Promise.all([
      refreshServer(),
      Promise.all([api<Settings>('settings'), api<Status>('status')]).then(([s,state])=>{
        setSettings(s); setStatus(state); setStatusError('');
        setAccount(current => state.profiles.some(p=>p.user_id===current) ? current : state.profiles[0]?.user_id || '');
      }).catch(e=>{setStatus(undefined); setStatusError(e instanceof Error ? e.message : String(e));}),
    ]).then(()=>{}).finally(()=>{refreshRequest.current=null; scheduleRefresh();});
    return refreshRequest.current;
  }
  async function openDoc(path:string) {
    try { setDoc(await api('docs/file?path=' + encodeURIComponent(path))); setError(''); window.scrollTo(0, 0); }
    catch(e) { setError(String(e instanceof Error ? e.message : e)); }
  }
  useEffect(()=>{
    mounted.current = true;
    void refresh();
    api<{versions:Version[]}>('versions').then(r=>setVersions(r.versions)).catch(e=>setError(e.message));
    function visibilityChanged() {
      clearTimeout(refreshTimer.current);
      if (!document.hidden && !actionPending.current) void refresh();
    }
    document.addEventListener('visibilitychange', visibilityChanged);
    api<{files:Doc[]}>('docs').then(r=>{setFiles(r.files); const first=r.files.find(f=>f.path===new URLSearchParams(location.search).get('doc')) || r.files.find(f=>f.path==='README.md') || r.files[0]; if(first) void openDoc(first.path);}).catch(e=>setError(e.message));
    return ()=>{mounted.current=false; clearTimeout(refreshTimer.current); document.removeEventListener('visibilitychange',visibilityChanged);};
  },[]);
  async function act(path:string, data:unknown, success:string) {
    if (actionPending.current) return;
    actionPending.current = true;
    clearTimeout(refreshTimer.current);
    setBusy(true); setError(''); setErrorDetail(''); setMessage('');
    if (path === 'installation/choose') setGameAction('choose');
    if (path.startsWith('game/')) setGameAction(path.split('/')[1]);
    try {
      // Drain an older read before mutation so it cannot overwrite the resulting status.
      await refreshRequest.current;
      const result = await api<{message?:string; cancelled?:boolean; installation?:Installation}>(path,data);
      if (!result.cancelled && (!result.installation || result.installation.state==='matched')) setMessage(result.message || success);
    }
    catch(e) {
      setError(e instanceof Error ? e.message : String(e));
      if (e instanceof Error && 'detail' in e) setErrorDetail(String(e.detail || ''));
    }
    finally {await refresh(); actionPending.current=false; setBusy(false); setGameAction(''); scheduleRefresh();}
  }
  function localDoc(href:string) {
    const resolved = new URL(href, 'http://docs/docs/' + doc.path);
    if (resolved.origin !== 'http://docs' || !resolved.pathname.startsWith('/docs/')) return undefined;
    const path = decodeURIComponent(resolved.pathname.slice(6));
    return files.some(file=>file.path===path) ? path : undefined;
  }
  const profile = status?.profiles.find(p=>p.user_id===account);
  const capability = (name:string)=>status?.capabilities[name];
  const matched = status?.installation.state === 'matched';
  const editable = matched && !!account && !busy && !!status && !status.game_running;
  return <Theme appearance={dark?'dark':'light'} accentColor="blue" grayColor="slate" radius="medium" scaling="100%">
    <div className="shell">
      <header className="navigation">
        <div className="brand"><strong className="brand-wordmark">CODOL</strong><small>{t('本地控制器')}<span aria-hidden="true"> / LOCAL</span></small></div>
        <nav aria-label={t('主导航')}><button className={page==='control'?'active':''} aria-current={page==='control'?'page':undefined} onClick={()=>setPage('control')}><SlidersHorizontal size={20}/>{t('游戏控制')}</button><button className={page==='wiki'?'active':''} aria-current={page==='wiki'?'page':undefined} onClick={()=>setPage('wiki')}><BookOpen size={20}/>{t('开发 WIKI')}</button></nav>
        <div className="header-tools">
          <span className="local-address mono">127.0.0.1</span>
          <Button variant="ghost" disabled={busy} onClick={()=>refresh().then(()=>setMessage('状态已更新')).catch(e=>setError(e.message))}><ArrowClockwise/>{t('刷新状态')}</Button>
          <Button variant="ghost" onClick={()=>setDark(!dark)}>{dark?<Sun size={18}/>:<Moon size={18}/>} {t(dark?'切换浅色':'切换深色')}</Button>
          <Button className="language-toggle" variant="soft" onClick={()=>setLanguage(language==='zh-CN'?'en':'zh-CN')} lang={language==='zh-CN'?'en':'zh-CN'}>{language==='zh-CN'?'English':'中文'}</Button>
        </div>
      </header>
      <main>
        {error && <div className="notice error" role="alert">{t(error)}{errorDetail && <pre className="error-detail">{errorDetail}</pre>}</div>}
        {statusError && <div className="notice error" role="alert">{t('游戏状态读取失败')} · {t(statusError)}</div>}
        {message && <div className="notice" role="status">{t(message)}</div>}
        {page==='control' ? <div className="workspace">
          <div className="page-heading">
            <div><p className="eyebrow"><span className="mono">LOCAL SESSION</span><span>{t('本地游戏')}</span></p><h1>{t('玩家与启动设置')}</h1><p>{t('管理当前档案，设置下一次游戏启动。')}</p></div>
            <div className="game-actions">
              <Button aria-label={t('停止游戏')} className="stop-button" variant="soft" size="3" disabled={busy || !status || (!status.game_running && !server?.running)} onClick={()=>act('game/stop',{},'游戏与服务器已停止。')}><Stop weight="fill"/>{t(gameAction==='stop'?'停止中…':'停止游戏')}</Button>
              <Button aria-label={t('启动游戏')} className="launch-button" size="3" disabled={busy || !matched || !capability('launch')?.available || status?.game_running} onClick={()=>act('game/launch',{},'游戏与服务器已启动。')}><Play weight="fill"/><span>{t(gameAction==='launch'?'启动中…':'启动游戏')}</span><ArrowUpRight className="launch-arrow"/></Button>
            </div>
          </div>
          <section className="panel installation-panel" aria-labelledby="installation-title">
            <div className="installation-heading"><div><h2 id="installation-title">{t('游戏目录')}</h2><p className="installation-path mono">{status?.installation.path || t('尚未选择目录')}</p></div>
              <Button variant="soft" disabled={busy || !status || status.game_running || server?.running} onClick={()=>act('installation/choose',{},'游戏目录已匹配')}><Folder/>{t(gameAction==='choose'?'选择与识别中…':'选择游戏目录')}</Button></div>
            <div className={'installation-result ' + (matched?'matched':'')}><span className="state-dot"/>{status?.installation.version && <strong className="mono">{status.installation.version}</strong>}<span>{t(status?.installation.reason || '读取中')}</span></div>
            <details className="version-list"><summary>{t('版本列表')} <span className="mono">{versions.length}</span></summary>
              <table><thead><tr><th>{t('版本号')}</th><th>{t('适配状态')}</th></tr></thead><tbody>{versions.map(version=><tr key={version.game_id+version.version}><td className="mono">{version.version}</td><td>{t(version.supported?'已接入':'尚未接入')}</td></tr>)}</tbody></table>
            </details>
          </section>
          <section className="panel startup-panel" aria-labelledby="startup-title">
            <div className="section-title"><SlidersHorizontal size={20}/><h2 id="startup-title">{t('启动选项')}</h2><span className="section-code">{t('下次启动生效')}</span></div>
            {capability('launch_settings')?.available && settings?.launch ? <LaunchOptions key={status?.installation.instance_id} value={settings.launch} disabled={busy || !matched || !!status?.game_running} onSave={launch=>act('settings',{launch},'启动选项已保存')} t={t}/> : <>
              <div className="switch-row"><label htmlFor="skip">{t('跳过新手引导')}</label><Switch id="skip" checked={settings?.skip_tutorial ?? true} disabled={busy || !settings || !matched || !capability('skip_tutorial')?.available} onCheckedChange={value=>act('settings',{skip_tutorial:value},'启动选项已保存')}/></div>
              <p className="helper">{t('默认开启。训练服务尚未恢复；更改在下一次启动生效。')}</p>
            </>}
          </section>
          <section className="profile-strip" aria-label={t('玩家概况')}>
            <div><label className="label" htmlFor="account">{t('当前档案')}</label><Select.Root value={account} onValueChange={setAccount}><Select.Trigger id="account" placeholder={t('尚无档案')}/><Select.Content>{status?.profiles.map(p=><Select.Item key={p.user_id} value={p.user_id}>{p.user_id}</Select.Item>)}</Select.Content></Select.Root></div>
            <div><span className="label">{t('等级')}</span><strong>{profile?.level ?? t('待读取')}</strong></div>
            <div><span className="label">{t('转生')}</span><strong>{profile?.prestige === undefined ? t('待读取') : language==='en' ? profile.prestige : `${profile.prestige} 转`}</strong></div>
            <div><span className="label">{t('游戏状态')}</span><strong className={'game-state ' + (status?.game_running?'running':'')}><span className="state-dot"/>{t(status ? (status.game_running?'运行中':'未运行') : '读取中')}</strong></div>
          </section>
          {status?.game_running && <p className="edit-hint">{t('游戏运行中，档案修改已锁定。退出后自动更新状态。')}</p>}
          <div className="control-grid">
            <div className="primary-column">
              <section className="wallet-panel" aria-labelledby="wallet-title">
                <h2 id="wallet-title" className="sr-only">{t('游戏币与商城')}</h2>
                <div className="wallet-grid">
                  <section className="wallet panel" aria-labelledby="currency-title">
                    <div className="balance-label"><Coins size={19}/><h3 id="currency-title">{t('游戏币')}</h3><span className="mono">{capability('currency')?.currency_label || 'CP'}</span></div>
                    <strong className="balance">{profile?.currency?.toLocaleString(language) ?? t('待读取')}</strong>
                    <label htmlFor="amount" className="field-label">{t('增加数量')}</label>
                    <div className="input-action"><TextField.Root id="amount" type="number" min="1" max="2147483647" value={amount} onChange={e=>setAmount(e.target.value)}/><Button variant="soft" disabled={!editable || !capability('currency')?.available} onClick={()=>act('profile/currency',{user_id:account,amount:Number(amount)},'游戏币已更新')}>{t('增加游戏币')}</Button></div>
                  </section>
                  <section className="wallet panel" aria-labelledby="premium-title">
                    <div className="balance-label"><Coins size={19}/><h3 id="premium-title">{t('点券')}</h3><span className="mono">{capability('currency')?.premium_label || 'CC'}</span></div>
                    <strong className="balance">{profile?.premium?.toLocaleString(language) ?? t('待读取')}</strong>
                    <label htmlFor="premium-amount" className="field-label">{t('增加点券数量')}</label>
                    <div className="input-action"><TextField.Root id="premium-amount" type="number" min="1" max="2147483647" value={premiumAmount} onChange={e=>setPremiumAmount(e.target.value)}/><Button variant="soft" disabled={!editable || !capability('currency')?.available} onClick={()=>act('profile/premium',{user_id:account,amount:Number(premiumAmount)},'点券已更新')}>{t('增加点券')}</Button></div>
                  </section>
                </div>
                <p className="helper">{t(status?.game_running ? '请先退出游戏，再修改余额。' : capability('currency')?.reason || '正在确认货币协议')}</p>
              </section>
              <section className="quick-grid" aria-labelledby="quick-title">
                <h2 id="quick-title" className="group-heading">{t('快捷操作')}<span className="mono" aria-hidden="true">QUICK ACTIONS</span></h2>
                <section className="panel quick-panel" aria-labelledby="progression-title">
                  <span className="action-icon"><Star size={22}/></span>
                  <div className="quick-copy"><h3 id="progression-title">{t('等级与转生')}</h3><p className="helper">{t(capability('progression')?.reason || '正在确认客户端字段')}</p></div>
                  <Button variant="soft" disabled={!editable || !capability('progression')?.available} onClick={()=>act('profile/progression',{user_id:account,prestige:capability('progression')?.max_prestige,level:capability('progression')?.max_level},'等级设置已保存，请重新启动游戏')}>{t('设置最高等级')}</Button>
                </section>
                <section className="panel quick-panel" aria-labelledby="story-title">
                  <span className="action-icon"><Flag size={22}/></span>
                  <div className="quick-copy"><h3 id="story-title">{t('剧情关卡')}</h3><p className="helper">{t('解除剧情前置条件，保留等级、货币和库存。地图启动与可玩性仍在恢复中；请退出游戏后操作。')}</p></div>
                  <Button variant="soft" disabled={!editable || !capability('story')?.available} onClick={()=>act('profile/story',{user_id:account},'剧情关卡解锁数据已保存，请重新启动游戏')}>{t('解锁全部剧情关卡')}</Button>
                </section>
                <section className="panel quick-panel" aria-labelledby="inventory-title">
                  <span className="action-icon"><Package size={22}/></span>
                  <div className="quick-copy"><h3 id="inventory-title">{t('商城内容')}</h3><p className="helper">{t(capability('inventory')?.reason || '正在确认物品数据')}</p></div>
                  <Button variant="soft" disabled={!editable || !capability('inventory')?.available} onClick={()=>act('profile/unlock',{user_id:account},'全部物品已保存，请重启游戏读取')}>{t('一键发放全部物品')}</Button>
                </section>
              </section>
            </div>
            <aside className="secondary-column">
              <section className="panel server-panel" aria-labelledby="server-title" aria-busy={serverLoading}>
                <div className="section-title"><HardDrives size={20}/><h2 id="server-title">{t('模拟服务器')}</h2><span className="section-code mono">{server?.pid ? `PID ${server.pid}` : 'PID —'}</span></div>
                <div className={'server-state ' + (server?.ready?'ready':'')}><span className="state-dot"/>{t(serverLoading && !server && !serverError ? '读取中' : serverError ? '状态读取失败' : server?.ports.some(p=>p.conflict) ? '端口被占用' : server?.ready ? '运行中' : server?.running ? '部分未监听' : '已停止')}<span className="section-code">{t('自动刷新 · 10 秒间隔')}</span></div>
                <div className="server-ports">{(server?.ports || [{name:'auth',protocol:'TCP',port:443},{name:'lobby',protocol:'TCP',port:3074},{name:'stun',protocol:'UDP',port:3074},{name:'match',protocol:'UDP',port:28970}]).map(port=><div key={port.name}>
                  <span>{t(port.name==='auth'?'认证':port.name==='lobby'?'大厅':port.name==='match'?'对局':port.name==='web'?'资源':'STUN')} <small className="mono">{port.protocol} {port.port}</small></span>
                  <span className={'port-state ' + ('listening' in port && port.listening ? 'listening':'')}>{t(!server ? '—' : 'conflict' in port && port.conflict ? '端口被占用' : 'listening' in port && port.listening ? '监听中':'未监听')}</span>
                </div>)}</div>
                <p className="helper">{t('随游戏自动启停。监听状态仅用于调试，不代表对局可玩。')}</p>
                {server?.match && <div className="helper">
                  <p>Seatown · {t('团队竞技')} · <span>{t(({waiting:'等待大厅 Ready', running:'对局服务已启动', finished:'本次对局已结束，重启游戏可再开一局', error:'对局启动或运行失败'} as Record<string,string>)[server.match.phase] || server.match.phase)}</span></p>
                  <p>{t('PLAY → Join Room → Ready；当前仅 Seatown，无 AI。')}</p>
                  {server.match.error && <p className="server-error">{server.match.error}</p>}
                  {server.match.result?.event === 'match_pay' && <p>{server.match.result.paid && Object.keys(server.match.result.paid).length ? `GP +${server.match.result.paid['1'] || 0} · CP +${server.match.result.paid['2'] || 0} · ${t('总经验')} ${server.match.result.paid.xp}` : t('本局不足一分钟，无结算奖励')}</p>}
                  {server.match.result?.event === 'match_pay_failed' && <p className="server-error">{t('结算失败')}：{server.match.result.error}</p>}
                </div>}
                {serverError && <p className="helper server-error">{t(serverError)}</p>}
              </section>
            </aside>
          </div>
          <footer className="usage"><ShieldCheck size={18}/><p>{t('先退出游戏，再修改数据，随后重新启动读取。写入前保留原档案备份。')}</p><button className="text-link" onClick={()=>{setPage('wiki');void openDoc('wiki/06-onboarding-profile.md');}}>{t('查看档案与引导说明')}<CaretRight/></button></footer>
        </div> : <div className="wiki-layout"><aside className="wiki-tree"><div className="tree-title">docs <span>{files.length} {t('个文件')}</span></div><FileTree files={files} active={doc.path} onSelect={openDoc}/></aside><article className="document"><div className="document-path"><FileText/>{doc.path || t('选择文档')}</div><p className="helper">{t('文档按原文显示。')}</p>{doc.path.endsWith('.md') ? <Markdown remarkPlugins={[remarkGfm]} components={{a:({href='',children})=>{
          if (/^https?:\/\//.test(href)) return <a href={href} target="_blank" rel="noreferrer">{children}</a>;
          const path = localDoc(href);
          return path ? <a href={'/?doc='+encodeURIComponent(path)} onClick={e=>{e.preventDefault();void openDoc(path);}}>{children}</a> : <span title={t('docs 以外的本地引用：')+href}>{children} <code className="helper">{href}</code></span>;
        }, img:({alt})=><span className="helper">[{t('图片：')}{alt || t('本地证据附件')}]</span>}}>{doc.content}</Markdown> : <pre className="raw-doc">{doc.content}</pre>}</article></div>}
      </main>
    </div>
  </Theme>;
}
