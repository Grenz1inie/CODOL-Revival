import {afterEach, beforeEach, describe, expect, it, vi} from 'vitest';
import {act, fireEvent, render, screen, waitFor, within} from '@testing-library/react';
import App from '../src/App';

const profile = {user_id: 'player-one', level: 42, prestige: 2, currency: 44445, premium: 99620};
const actions = ['设置最高等级', '解锁全部剧情关卡', '增加游戏币', '增加点券', '一键发放全部物品'];
let installation: {state: string; path: string; version: string | null; reason: string; instance_id?: string};
const matched = {state:'matched', path:'E:/Games/CODOL', version:'3.3.3.3', reason:'已匹配', instance_id:'codol-main'};
let running: boolean;
let launchSettings: {player_name: string; fov: number; max_fps: number; display_mode: string; resolution: string} | undefined;
let serverState: {running: boolean; pid: number | null; ready: boolean; ports: {name: string; protocol: string; port: number; listening: boolean; conflict: boolean}[]; match?: {phase:string; error:string; result?:{event:string; paid?:Record<string,number>}}};
let serverError: boolean;
let statusError: boolean;
let serverResponse: () => Promise<ReturnType<typeof response>>;
let profiles: typeof profile[];
let capabilities: Record<string, {available: boolean; reason: string; max_level?:number; max_prestige?:number; currency_label?:string; premium_label?:string}>;
let posts: {path: string; data: unknown}[];
let postResponse: () => Promise<{ok: boolean; json: () => Promise<unknown>}>;
const response = (data: unknown, ok = true) => ({ok, json: async () => data});
const button = (name: string) => screen.getByRole<HTMLButtonElement>('button', {name, exact: true});

beforeEach(() => {
  localStorage.clear();
  statusError = false;
  vi.spyOn(document, 'hidden', 'get').mockReturnValue(false);
  serverResponse = async () => response(serverError ? {error:'服务器状态读取失败'} : serverState, !serverError);
  serverError = false;
  serverState = {running: false, pid: null, ready: false, ports: [
    {name: 'auth', protocol: 'TCP', port: 443, listening: false, conflict: false},
    {name: 'lobby', protocol: 'TCP', port: 3074, listening: false, conflict: false},
    {name: 'stun', protocol: 'UDP', port: 3074, listening: false, conflict: false},
    {name: 'match', protocol: 'UDP', port: 28970, listening: false, conflict: false},
  ]};
  installation = {...matched};
  running = false;
  launchSettings = undefined;
  profiles = [profile];
  capabilities = Object.fromEntries(['progression', 'currency', 'inventory', 'story', 'launch', 'skip_tutorial'].map(key => [key, {available: true, reason: `${key} 已就绪`, max_level:70, max_prestige:3}]));
  posts = [];
  postResponse = async () => response({message: '操作已保存'});
  vi.stubGlobal('fetch', vi.fn(async (url: string, init?: RequestInit) => {
    const path = url.replace('/api/', '');
    if (init?.method === 'POST') {
      posts.push({path, data: JSON.parse(String(init.body))});
      return postResponse();
    }
    if (path === 'status') return response(statusError ? {error:'读取失败'} : {profiles, game_running: running, capabilities, installation}, !statusError);
    if (path === 'server/status') return serverResponse();
    if (path === 'versions') return response({versions:[{game_id:'codol', version:'3.3.3.3', label:'体验服 3.3.3.3', supported:true}, {game_id:'codol', version:'2.6.9.7', label:'2.6.9.7', supported:false}]});
    if (path === 'settings') return response({skip_tutorial: true, launch: launchSettings});
    if (path.startsWith('inventory?')) return response({items: []});
    if (path === 'docs') return response({files: [{path: 'README.md', size: 10}, {path: 'wiki/06-onboarding-profile.md', size: 20}]});
    if (path.startsWith('docs/file?')) {
      const docPath = new URLSearchParams(path.split('?')[1]).get('path');
      return response({path: docPath, content: docPath === 'README.md' ? '# 控制器文档\n[档案说明](wiki/06-onboarding-profile.md)' : '# 档案与引导'});
    }
    throw new Error('Unexpected request: ' + path);
  }));
});

describe('服务器控制与语言切换', () => {
  it('服务器只读显示 PID 与四个监听状态，区分对局和STUN', async () => {
    serverState = {...serverState,running:true,pid:123,ready:true,ports:serverState.ports.map(p=>({...p,listening:true}))};
    await ready();
    const panel = screen.getByRole('region',{name:'模拟服务器'});
    expect(within(panel).getByText('PID 123')).toBeTruthy();
    expect(within(panel).getAllByText('监听中')).toHaveLength(4);
    expect(within(panel).getByText('对局')).toBeTruthy();
    expect(within(panel).getByText('UDP 28970')).toBeTruthy();
    expect(within(panel).queryByRole('button')).toBeNull();
  });

  it('端口冲突和读取失败仍可见，读取失败不显示上次的正常状态', async () => {
    serverState.ports[0].conflict = true;
    await ready();
    expect(screen.getAllByText('端口被占用')).toHaveLength(2);
    serverError = true;
    fireEvent.click(button('刷新状态'));
    expect(await screen.findByText('状态读取失败')).toBeTruthy();
    expect(button('增加游戏币').disabled).toBe(false);
  });

  it('游戏启动失败仍立即刷新，允许停止残留服务器', async () => {
    await ready();
    postResponse = async () => {
      serverState = {...serverState,running:true,pid:123};
      return response({error:'游戏与服务器操作失败',detail:'Server cleanup failed'},false);
    };
    fireEvent.click(button('启动游戏'));
    expect((await screen.findByRole('alert')).textContent).toContain('Server cleanup failed');
    await waitFor(()=>expect(button('停止游戏').disabled).toBe(false));
    expect(screen.getByText('部分未监听')).toBeTruthy();
  });

  it('默认中文，英文覆盖控制台与文档导航，切回时保留输入', async () => {
    await ready();
    fireEvent.change(screen.getByLabelText('增加数量'), {target:{value:'321'}});
    fireEvent.click(button('English'));
    expect(document.documentElement.lang).toBe('en');
    expect(localStorage.getItem('codol-language')).toBe('en');
    expect(screen.getByRole('heading', {name:'Player & launch settings'})).toBeTruthy();
    expect(screen.getByRole('region', {name:'Local server'})).toBeTruthy();
    expect(screen.queryByRole('button',{name:'Start server'})).toBeNull();
    expect(button('Stop game').disabled).toBe(true);
    expect(screen.getByRole<HTMLInputElement>('spinbutton', {name:'Amount to add'}).value).toBe('321');
    fireEvent.click(button('Developer WIKI'));
    expect(await screen.findByText('2 files')).toBeTruthy();
    expect(screen.getByText('Documents are shown in their original language.')).toBeTruthy();
    fireEvent.click(button('中文'));
    fireEvent.click(button('游戏控制'));
    expect(document.documentElement.lang).toBe('zh-CN');
    expect(screen.getByRole<HTMLInputElement>('spinbutton', {name:'增加数量'}).value).toBe('321');
  });

  it('恢复已保存的英文选择，并翻译操作结果与错误', async () => {
    localStorage.setItem('codol-language', 'en');
    postResponse = async () => response({error:'请先退出游戏'}, false);
    render(<App/>);
    await screen.findByText('player-one');
    fireEvent.click(button('Add credits'));
    expect((await screen.findByRole('alert')).textContent).toBe('Please exit the game first.');
    postResponse = async () => response({message:'玩家数据已保存；重新启动游戏后生效。'});
    await waitFor(() => expect(button('Add credits').disabled).toBe(false));
    fireEvent.click(button('Add credits'));
    expect((await screen.findByRole('status')).textContent).toBe('Player data saved. Restart the game to apply.');
    expect(posts[0]).toEqual({path:'profile/currency',data:{user_id:'player-one',amount:100000}});
  });

  it('无效的语言偏好回退到中文', async () => {
    localStorage.setItem('codol-language','fr');
    await ready();
    expect(button('English')).toBeTruthy();
    expect(document.documentElement.lang).toBe('zh-CN');
  });
});

async function ready() {
  render(<App/>);
  await screen.findByText('player-one');
  await screen.findByRole('switch', {name: '跳过新手引导'});
}

describe('控制器原有操作契约', () => {
  it('横向指挥台将导航和工具集中到顶栏，余额分区可独立定位', async () => {
    await ready();
    const header = within(screen.getByRole('banner'));
    expect(header.getByRole('navigation', {name: '主导航'})).toBeTruthy();
    expect(header.getByRole('button', {name: '刷新状态'})).toBeTruthy();
    expect(header.getByRole('button', {name: '切换浅色'})).toBeTruthy();
    expect(header.getByText('CODOL')).toBeTruthy();
    expect(header.queryByText('CO', {exact: true})).toBeNull();
    expect(within(screen.getByRole('region', {name: '游戏币', exact: true})).getByLabelText('增加数量')).toBeTruthy();
    expect(within(screen.getByRole('region', {name: '点券', exact: true})).getByLabelText('增加点券数量')).toBeTruthy();
    fireEvent.click(header.getByRole('button', {name: '开发 WIKI'}));
    await screen.findByRole('heading', {name: '控制器文档'});
    expect(within(screen.getByRole('banner')).getByRole('button', {name: '刷新状态'})).toBeTruthy();
  });

  it('紧凑操作区提供可访问的档案选择、分区名称和当前导航状态', async () => {
    await ready();
    expect(screen.getByRole('combobox', {name: '当前档案'})).toBeTruthy();
    expect(button('游戏控制').getAttribute('aria-current')).toBe('page');
    const wallet = screen.getByRole('region', {name: '游戏币与商城'});
    expect(within(wallet).getByLabelText('增加数量')).toBeTruthy();
    expect(within(wallet).getByLabelText('增加点券数量')).toBeTruthy();
    const quickActions = screen.getByRole('region', {name: '快捷操作'});
    expect(within(quickActions).getByRole('button', {name: '一键发放全部物品'})).toBeTruthy();
    expect(screen.queryByRole('region', {name: '限时物品续期'})).toBeNull();
  });

  it('读取档案、余额与启动选项，未运行时禁用停止游戏', async () => {
    await ready();
    expect(screen.getByText('44,445')).toBeTruthy();
    expect(screen.getByText('99,620')).toBeTruthy();
    expect(screen.getByRole('switch').getAttribute('aria-checked')).toBe('true');
    for (const name of actions) expect(button(name).disabled).toBe(false);
    expect(button('启动游戏').disabled).toBe(false);
    expect(button('停止游戏').disabled).toBe(true);
    expect(screen.queryByLabelText('选择物品')).toBeNull();
  });

  it('读取中和没有档案时禁止档案写入，保留独立启动操作', async () => {
    profiles = [];
    render(<App/>);
    expect(button('停止游戏').disabled).toBe(true);
    for (const name of actions) expect(button(name).disabled).toBe(true);
    expect(screen.getByRole<HTMLButtonElement>('switch').disabled).toBe(true);
    await screen.findByText('未运行');
    for (const name of actions) expect(button(name).disabled).toBe(true);
    expect(button('启动游戏').disabled).toBe(false);
    expect(button('停止游戏').disabled).toBe(true);
  });

  it('游戏运行中禁用档案写入和启动，启动选项仍可修改', async () => {
    running = true;
    await ready();
    for (const name of [...actions, '启动游戏']) expect(button(name).disabled).toBe(true);
    expect(button('停止游戏').disabled).toBe(false);
    expect(screen.getByRole<HTMLButtonElement>('switch').disabled).toBe(false);
  });

  it('按能力分别禁用等级、货币、物品；剧情操作不受这些能力限制', async () => {
    for (const key of ['progression', 'currency', 'inventory']) capabilities[key].available = false;
    await ready();
    for (const name of actions.filter(name => name !== '解锁全部剧情关卡')) expect(button(name).disabled).toBe(true);
    expect(button('解锁全部剧情关卡').disabled).toBe(false);
    expect(screen.getByText('progression 已就绪')).toBeTruthy();
  });

  it('3.19 使用本版本币种和转生上限并开放五项档案操作', async () => {
    installation = {...matched,version:'3.19.26.22'};
    capabilities.currency = {available:true,reason:'本地余额',currency_label:'GP',premium_label:'CP'};
    capabilities.progression = {available:true,reason:'70级、4转',max_level:70,max_prestige:4};
    await ready();
    expect(within(screen.getByRole('region',{name:'游戏币',exact:true})).getByText('GP')).toBeTruthy();
    expect(within(screen.getByRole('region',{name:'点券',exact:true})).getByText('CP')).toBeTruthy();
    for (const name of actions) expect(button(name).disabled).toBe(false);
    fireEvent.click(button('设置最高等级'));
    await waitFor(()=>expect(posts).toEqual([{path:'profile/progression',data:{user_id:'player-one',level:70,prestige:4}}]));
  });

  it.each([
    ['设置最高等级', 'profile/progression', {user_id: 'player-one', prestige: 3, level: 70}],
    ['解锁全部剧情关卡', 'profile/story', {user_id: 'player-one'}],
    ['增加游戏币', 'profile/currency', {user_id: 'player-one', amount: 100000}],
    ['增加点券', 'profile/premium', {user_id: 'player-one', amount: 100000}],
    ['一键发放全部物品', 'profile/unlock', {user_id: 'player-one'}],
    ['启动游戏', 'game/launch', {}],
  ])('%s 保留原有请求参数并反馈结果', async (name, path, data) => {
    await ready();
    fireEvent.click(button(name));
    await screen.findByRole('status');
    expect(posts).toEqual([{path, data}]);
    expect(screen.getByRole('status').textContent).toBe('操作已保存');
  });

  it('处理请求时锁住操作；失败后展示服务端错误并恢复操作', async () => {
    let finish!: (value: ReturnType<typeof response>) => void;
    postResponse = () => new Promise(resolve => {finish = resolve;});
    await ready();
    fireEvent.click(button('增加游戏币'));
    for (const name of [...actions, '启动游戏', '刷新状态']) expect(button(name).disabled).toBe(true);
    expect(screen.getByRole<HTMLButtonElement>('switch').disabled).toBe(true);
    await waitFor(()=>expect(posts).toHaveLength(1));
    finish(response({error: '请先退出游戏'}, false));
    expect((await screen.findByRole('alert')).textContent).toBe('请先退出游戏');
    await waitFor(() => expect(button('增加游戏币').disabled).toBe(false));
    expect(screen.queryByRole('status')).toBeNull();
  });

  it('停止游戏期间锁定操作，成功后刷新状态并恢复档案修改', async () => {
    running = true;
    let finish!: (value: ReturnType<typeof response>) => void;
    postResponse = () => new Promise(resolve => {finish = resolve;});
    await ready();
    fireEvent.click(button('停止游戏'));
    for (const name of [...actions, '启动游戏', '停止游戏', '刷新状态']) expect(button(name).disabled).toBe(true);
    expect(screen.getByRole<HTMLButtonElement>('switch').disabled).toBe(true);
    running = false;
    await waitFor(()=>expect(posts).toHaveLength(1));
    finish(response({message: '游戏已停止。'}));
    await screen.findByRole('status');
    await screen.findByText('未运行');
    await waitFor(() => expect(button('增加游戏币').disabled).toBe(false));
    expect(posts).toEqual([{path: 'game/stop', data: {}}]);
    expect(button('停止游戏').disabled).toBe(true);
    expect(button('启动游戏').disabled).toBe(false);
  });

  it('停止失败显示错误，游戏运行时仍锁定档案并允许重试停止', async () => {
    running = true;
    postResponse = async () => response({error: '停止未完成，游戏仍在运行。'}, false);
    await ready();
    fireEvent.click(button('停止游戏'));
    expect((await screen.findByRole('alert')).textContent).toBe('停止未完成，游戏仍在运行。');
    await waitFor(() => expect(button('停止游戏').disabled).toBe(false));
    for (const name of [...actions, '启动游戏']) expect(button(name).disabled).toBe(true);
    expect(screen.queryByRole('status')).toBeNull();
  });

  it('启动选项保留布尔请求', async () => {
    await ready();
    fireEvent.click(screen.getByRole('switch'));
    await screen.findByRole('status');
    expect(posts).toEqual([{path: 'settings', data: {skip_tutorial: false}}]);
  });

  it('启动选项位于游戏目录之后、玩家概况之前', async () => {
    await ready();
    const installationPanel = screen.getByRole('region', {name:'游戏目录'});
    const launchPanel = screen.getByRole('region', {name:'启动选项'});
    const overview = screen.getByRole('region', {name:'玩家概况'});
    expect(installationPanel.compareDocumentPosition(launchPanel) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
    expect(launchPanel.compareDocumentPosition(overview) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
  });

  it('保留主题切换、WIKI 导航和文档内链接', async () => {
    await ready();
    fireEvent.click(button('切换浅色'));
    expect(button('切换深色')).toBeTruthy();
    fireEvent.click(button('开发 WIKI'));
    await screen.findByRole('heading', {name: '控制器文档'});
    fireEvent.click(screen.getByRole('link', {name: '档案说明'}));
    await screen.findByRole('heading', {name: '档案与引导'});
    fireEvent.click(button('游戏控制'));
    expect(screen.getByRole('heading', {name: '玩家与启动设置'})).toBeTruthy();
  });

  it('支持文档深链接', async () => {
    history.replaceState({}, '', '/?doc=wiki%2F06-onboarding-profile.md');
    render(<App/>);
    await screen.findByRole('heading', {name: '档案与引导'});
    expect(screen.queryByRole('heading', {name: '玩家与启动设置'})).toBeNull();
  });
});


afterEach(() => {vi.useRealTimers(); vi.restoreAllMocks();});

describe('低频自动刷新', () => {
  const reads = () => vi.mocked(fetch).mock.calls.filter(call=>call[0]==='/api/status').length;
  it('完成后等待十秒；更新游戏按钮，隐藏暂停，返回立即刷新，卸载清理', async () => {
    vi.useFakeTimers();
    let view!: ReturnType<typeof render>;
    await act(async()=>{view=render(<App/>);});
    expect(reads()).toBe(1);
    await act(()=>vi.advanceTimersByTimeAsync(9999));
    expect(reads()).toBe(1);
    running = true;
    await act(()=>vi.advanceTimersByTimeAsync(1));
    expect(reads()).toBe(2);
    expect(button('启动游戏').disabled).toBe(true);
    expect(button('停止游戏').disabled).toBe(false);
    vi.spyOn(document,'hidden','get').mockReturnValue(true);
    fireEvent(document,new Event('visibilitychange'));
    await act(()=>vi.advanceTimersByTimeAsync(30000));
    expect(reads()).toBe(2);
    running = false;
    vi.spyOn(document,'hidden','get').mockReturnValue(false);
    await act(async()=>{fireEvent(document,new Event('visibilitychange'));});
    expect(reads()).toBe(3);
    expect(button('启动游戏').disabled).toBe(false);
    view.unmount();
    await act(()=>vi.advanceTimersByTimeAsync(30000));
    expect(reads()).toBe(3);
  });

  it('慢请求不重叠，游戏操作期间不轮询，操作完成立即刷新', async () => {
    vi.useFakeTimers();
    let finishRead!: (r: ReturnType<typeof response>)=>void;
    serverResponse = ()=>new Promise(resolve=>{finishRead=resolve;});
    await act(async()=>{render(<App/>);});
    await act(()=>vi.advanceTimersByTimeAsync(30000));
    expect(reads()).toBe(1);
    await act(async()=>{finishRead(response(serverState));});
    serverResponse = async()=>response(serverState);
    let finishAction!: (r: ReturnType<typeof response>)=>void;
    postResponse = ()=>new Promise(resolve=>{finishAction=resolve;});
    await act(async()=>{fireEvent.click(button('启动游戏'));});
    await act(()=>vi.advanceTimersByTimeAsync(30000));
    expect(reads()).toBe(1);
    expect(button('启动游戏').disabled).toBe(true);
    running = true;
    await act(async()=>{finishAction(response({message:'游戏与服务器已启动。'}));});
    expect(reads()).toBe(2);
    expect(button('停止游戏').disabled).toBe(false);
    await act(()=>vi.advanceTimersByTimeAsync(9999));
    expect(reads()).toBe(2);
  });

  it('游戏状态读取失败禁用修改和启停，下次自动刷新恢复', async () => {
    vi.useFakeTimers();
    await act(async()=>{render(<App/>);});
    statusError = true;
    await act(()=>vi.advanceTimersByTimeAsync(10000));
    expect(button('启动游戏').disabled).toBe(true);
    expect(button('停止游戏').disabled).toBe(true);
    expect(button('增加游戏币').disabled).toBe(true);
    statusError = false;
    await act(()=>vi.advanceTimersByTimeAsync(10000));
    expect(button('启动游戏').disabled).toBe(false);
  });
});


describe('游戏目录与版本匹配', () => {
  it('3.19 对局状态区分等待、失败及结算，并正确标记资源服务', async () => {
    installation = {...matched, version:'3.19.26.22'};
    serverState.match = {phase:'waiting', error:''};
    serverState.ports = [{name:'web', protocol:'TCP', port:8319, listening:true, conflict:false}];
    await ready();
    expect(screen.getByText('等待大厅 Ready')).toBeTruthy();
    expect(screen.getByText('资源')).toBeTruthy();
    serverState.match = {phase:'error', error:'UDP 28970 已被占用'};
    fireEvent.click(button('刷新状态'));
    expect(await screen.findByText('UDP 28970 已被占用')).toBeTruthy();
    serverState.match = {phase:'finished', error:'', result:{event:'match_pay', paid:{'1':200,'2':10,xp:1400}}};
    fireEvent.click(button('刷新状态'));
    expect(await screen.findByText(/GP \+200.*CP \+10.*1400/)).toBeTruthy();
  });
  it('3.19 启动参数可保存，刷新不覆盖未保存输入，运行时禁用修改', async () => {
    installation = {...matched, version:'3.19.26.22'};
    capabilities.launch_settings = {available:true, reason:''};
    capabilities.skip_tutorial.available = false;
    launchSettings = {player_name:'Player319', fov:90, max_fps:0, display_mode:'windowed', resolution:'1280x720'};
    render(<App/>);
    await screen.findByLabelText('玩家名');
    expect((screen.getByLabelText('玩家名') as HTMLInputElement).value).toBe('Player319');
    fireEvent.change(screen.getByLabelText('玩家名'), {target:{value:'NewName'}});
    fireEvent.change(screen.getByLabelText('FOV'), {target:{value:'110'}});
    fireEvent.keyDown(screen.getByRole('combobox', {name:'显示模式'}), {key:'Enter'});
    fireEvent.click(await screen.findByRole('option', {name:'全屏', exact:true}));
    fireEvent.keyDown(screen.getByRole('combobox', {name:'分辨率'}), {key:'Enter'});
    fireEvent.click(await screen.findByRole('option', {name:'1920 × 1080', exact:true}));
    fireEvent.click(button('刷新状态'));
    await screen.findByText('状态已更新');
    expect((screen.getByLabelText('玩家名') as HTMLInputElement).value).toBe('NewName');
    expect(screen.getByRole('combobox', {name:'显示模式'}).textContent).toBe('全屏');
    expect(screen.getByRole('combobox', {name:'分辨率'}).textContent).toBe('1920 × 1080');
    fireEvent.click(button('保存启动选项'));
    await waitFor(()=>expect(posts).toContainEqual({path:'settings',data:{launch:{player_name:'NewName',fov:110,max_fps:0,
      display_mode:'fullscreen',resolution:'1920x1080'}}}));
    await waitFor(()=>expect(button('保存启动选项').disabled).toBe(false));
    running = true;
    fireEvent.click(button('刷新状态'));
    await waitFor(()=>expect(button('保存启动选项').disabled).toBe(true));
    expect(screen.getByRole<HTMLButtonElement>('combobox', {name:'显示模式'}).disabled).toBe(true);
    expect(screen.getByRole<HTMLButtonElement>('combobox', {name:'分辨率'}).disabled).toBe(true);
  });

  it('切换安装实例后读取该实例的启动设置', async () => {
    installation = {...matched, version:'3.19.26.22'};
    capabilities.launch_settings = {available:true, reason:''};
    launchSettings = {player_name:'First', fov:90, max_fps:0, display_mode:'windowed', resolution:'1280x720'};
    render(<App/>);
    await screen.findByLabelText('玩家名');
    fireEvent.change(screen.getByLabelText('玩家名'), {target:{value:'Unsaved'}});
    installation = {...installation, instance_id:'second'};
    launchSettings = {player_name:'Second', fov:100, max_fps:60, display_mode:'fullscreen', resolution:'2560x1440'};
    fireEvent.click(button('刷新状态'));
    await waitFor(()=>expect((screen.getByLabelText('玩家名') as HTMLInputElement).value).toBe('Second'));
    expect(screen.getByRole('combobox', {name:'显示模式'}).textContent).toBe('全屏');
    expect(screen.getByRole('combobox', {name:'分辨率'}).textContent).toBe('2560 × 1440');
    expect(posts).toEqual([]);
  });
  it('未选择或未支持版本时锁定所有游戏和档案操作，保留版本列表', async () => {
    installation = {state:'unselected', path:'', version:null, reason:'请先选择游戏目录'};
    await ready();
    expect(screen.getByText('请先选择游戏目录')).toBeTruthy();
    for (const name of [...actions, '启动游戏']) expect(button(name).disabled).toBe(true);
    expect(screen.getByRole<HTMLButtonElement>('switch', {name:'跳过新手引导'}).disabled).toBe(true);
    expect(button('选择游戏目录').disabled).toBe(false);
    fireEvent.click(screen.getByText('版本列表'));
    expect(screen.getByText('2.6.9.7')).toBeTruthy();
    expect(screen.getByText('尚未接入')).toBeTruthy();
  });

  it('选择成功后显示版本并启用操作，取消保留当前选择', async () => {
    installation = {state:'unselected', path:'', version:null, reason:'请先选择游戏目录'};
    await ready();
    postResponse = async () => { installation = {...matched}; return response({cancelled:false, installation}); };
    fireEvent.click(button('选择游戏目录'));
    await waitFor(()=>expect(button('启动游戏').disabled).toBe(false));
    expect(posts[0]).toEqual({path:'installation/choose', data:{}});
    expect(screen.getByText(matched.path)).toBeTruthy();
    postResponse = async () => response({cancelled:true, installation});
    fireEvent.click(button('选择游戏目录'));
    await waitFor(()=>expect(button('选择游戏目录').disabled).toBe(false));
    expect(button('启动游戏').disabled).toBe(false);
    expect(screen.queryByText('游戏目录已匹配')).toBeNull();
  });

  it('重新识别失败会锁定旧按钮，运行中不能切换目录但能停止', async () => {
    await ready();
    postResponse = async () => { installation = {...matched, state:'fingerprint_mismatch', reason:'主程序指纹与已适配客户端不一致'}; return response({installation}); };
    fireEvent.click(button('选择游戏目录'));
    expect(await screen.findByText('主程序指纹与已适配客户端不一致')).toBeTruthy();
    expect(button('增加游戏币').disabled).toBe(true);
    running = true;
    fireEvent.click(button('刷新状态'));
    await waitFor(()=>expect(button('选择游戏目录').disabled).toBe(true));
    expect(button('停止游戏').disabled).toBe(false);
  });
});
