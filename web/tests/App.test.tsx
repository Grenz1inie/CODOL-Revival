import {beforeEach, describe, expect, it, vi} from 'vitest';
import {fireEvent, render, screen, waitFor, within} from '@testing-library/react';
import App from '../src/App';

const profile = {user_id: 'player-one', level: 42, prestige: 2, currency: 44445, premium: 99620};
const actions = ['设置最高等级', '解锁全部剧情关卡', '增加游戏币', '增加点券', '一键发放全部物品'];
let running: boolean;
let serverState: {running: boolean; pid: number | null; ready: boolean; ports: {name: string; protocol: string; port: number; listening: boolean; conflict: boolean}[]};
let serverError: boolean;
let profiles: typeof profile[];
let capabilities: Record<string, {available: boolean; reason: string}>;
let posts: {path: string; data: unknown}[];
let postResponse: () => Promise<{ok: boolean; json: () => Promise<unknown>}>;
const response = (data: unknown, ok = true) => ({ok, json: async () => data});
const button = (name: string) => screen.getByRole<HTMLButtonElement>('button', {name, exact: true});

beforeEach(() => {
  localStorage.clear();
  serverError = false;
  serverState = {running: false, pid: null, ready: false, ports: [
    {name: 'auth', protocol: 'TCP', port: 443, listening: false, conflict: false},
    {name: 'lobby', protocol: 'TCP', port: 3074, listening: false, conflict: false},
    {name: 'stun', protocol: 'UDP', port: 3074, listening: false, conflict: false},
  ]};
  running = false;
  profiles = [profile];
  capabilities = Object.fromEntries(['progression', 'currency', 'inventory'].map(key => [key, {available: true, reason: `${key} 已就绪`}]));
  posts = [];
  postResponse = async () => response({message: '操作已保存'});
  vi.stubGlobal('fetch', vi.fn(async (url: string, init?: RequestInit) => {
    const path = url.replace('/api/', '');
    if (init?.method === 'POST') {
      posts.push({path, data: JSON.parse(String(init.body))});
      return postResponse();
    }
    if (path === 'status') return response({profiles, game_running: running, capabilities});
    if (path === 'server/status') return response(serverError ? {error: '服务器操作失败'} : serverState, !serverError);
    if (path === 'settings') return response({skip_tutorial: true});
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
  it('读取中锁定启停，无档案也可启动；显示三个监听状态', async () => {
    profiles = [];
    render(<App/>);
    expect(button('启动服务器').disabled).toBe(true);
    expect(button('停止服务器').disabled).toBe(true);
    const panel = await screen.findByRole('region', {name: '模拟服务器'});
    await waitFor(() => expect(button('启动服务器').disabled).toBe(false));
    expect(within(panel).getAllByText('未监听')).toHaveLength(3);
    expect(button('停止服务器').disabled).toBe(true);
  });

  it('启动和停止发送空参数，等待期间锁定操作，完成后更新状态', async () => {
    let finish!: (value: ReturnType<typeof response>) => void;
    postResponse = () => new Promise(resolve => {finish = resolve;});
    await ready();
    fireEvent.click(button('启动服务器'));
    expect(button('启动服务器').disabled).toBe(true);
    expect(button('启动游戏').disabled).toBe(true);
    serverState = {...serverState, running: true, pid: 123, ready: true, ports: serverState.ports.map(p=>({...p, listening:true}))};
    finish(response(serverState));
    await waitFor(() => expect(button('停止服务器').disabled).toBe(false));
    expect(screen.getByText('PID 123')).toBeTruthy();
    fireEvent.click(button('停止服务器'));
    serverState = {...serverState, running: false, pid: null, ready: false, ports: serverState.ports.map(p=>({...p, listening:false}))};
    finish(response(serverState));
    await waitFor(() => expect(button('启动服务器').disabled).toBe(false));
    expect(posts).toEqual([{path:'server/start',data:{}},{path:'server/stop',data:{}}]);
  });

  it('游戏运行时禁止停止服务器，端口占用不算就绪', async () => {
    running = true;
    serverState = {...serverState, running:true, pid:123};
    serverState.ports[0].conflict = true;
    await ready();
    expect(button('停止服务器').disabled).toBe(true);
    expect(button('启动服务器').disabled).toBe(true);
    expect(screen.getAllByText('端口被占用')).toHaveLength(2);
    expect(screen.getByText('请先停止游戏，再停止服务器。')).toBeTruthy();
  });

  it('读取服务器失败不影响档案，禁止操作且可刷新恢复', async () => {
    serverError = true;
    await ready();
    expect(await screen.findByText('状态读取失败')).toBeTruthy();
    expect(button('启动服务器').disabled).toBe(true);
    expect(button('增加游戏币').disabled).toBe(false);
    serverError = false;
    fireEvent.click(button('刷新状态'));
    await waitFor(() => expect(button('启动服务器').disabled).toBe(false));
  });

  it('启动失败重新读取进程状态，显示错误并允许停止部分启动的服务', async () => {
    await ready();
    postResponse = async () => {
      serverState = {...serverState,running:true,pid:123};
      return response({error:'服务器操作失败',detail:'Required port unavailable'}, false);
    };
    fireEvent.click(button('启动服务器'));
    expect((await screen.findByRole('alert')).textContent).toContain('Required port unavailable');
    await waitFor(() => expect(button('停止服务器').disabled).toBe(false));
    expect(screen.getByText('部分未监听')).toBeTruthy();
    expect(button('启动服务器').disabled).toBe(true);
  });

  it('默认中文，英文覆盖控制台与文档导航，切回时保留输入', async () => {
    await ready();
    fireEvent.change(screen.getByLabelText('增加数量'), {target:{value:'321'}});
    fireEvent.click(button('English'));
    expect(document.documentElement.lang).toBe('en');
    expect(localStorage.getItem('codol-language')).toBe('en');
    expect(screen.getByRole('heading', {name:'Player & launch settings'})).toBeTruthy();
    expect(screen.getByRole('region', {name:'Local server'})).toBeTruthy();
    expect(button('Start server').disabled).toBe(false);
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
    for (const cap of Object.values(capabilities)) cap.available = false;
    await ready();
    for (const name of actions.filter(name => name !== '解锁全部剧情关卡')) expect(button(name).disabled).toBe(true);
    expect(button('解锁全部剧情关卡').disabled).toBe(false);
    expect(screen.getByText('progression 已就绪')).toBeTruthy();
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
