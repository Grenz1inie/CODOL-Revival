import {beforeEach, describe, expect, it, vi} from 'vitest';
import {fireEvent, render, screen, waitFor, within} from '@testing-library/react';
import App from '../src/App';

const profile = {user_id: 'player-one', level: 42, prestige: 2, currency: 44445, premium: 99620};
const actions = ['设置最高等级', '解锁全部剧情关卡', '增加游戏币', '增加点券', '一键发放全部物品'];
let running: boolean;
let profiles: typeof profile[];
let capabilities: Record<string, {available: boolean; reason: string}>;
let items: {item_id: number; quantity: number; expires: number; name: string}[];
let posts: {path: string; data: unknown}[];
let postResponse: () => Promise<{ok: boolean; json: () => Promise<unknown>}>;
const response = (data: unknown, ok = true) => ({ok, json: async () => data});
const button = (name: string) => screen.getByRole<HTMLButtonElement>('button', {name, exact: true});

beforeEach(() => {
  running = false;
  profiles = [profile];
  capabilities = Object.fromEntries(['progression', 'currency', 'inventory'].map(key => [key, {available: true, reason: `${key} 已就绪`}]));
  items = [];
  posts = [];
  postResponse = async () => response({message: '操作已保存'});
  vi.stubGlobal('fetch', vi.fn(async (url: string, init?: RequestInit) => {
    const path = url.replace('/api/', '');
    if (init?.method === 'POST') {
      posts.push({path, data: JSON.parse(String(init.body))});
      return postResponse();
    }
    if (path === 'status') return response({profiles, game_running: running, capabilities});
    if (path === 'settings') return response({skip_tutorial: true});
    if (path.startsWith('inventory?')) return response({items});
    if (path === 'docs') return response({files: [{path: 'README.md', size: 10}, {path: 'wiki/06-onboarding-profile.md', size: 20}]});
    if (path.startsWith('docs/file?')) {
      const docPath = new URLSearchParams(path.split('?')[1]).get('path');
      return response({path: docPath, content: docPath === 'README.md' ? '# 控制器文档\n[档案说明](wiki/06-onboarding-profile.md)' : '# 档案与引导'});
    }
    throw new Error('Unexpected request: ' + path);
  }));
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
    expect(screen.getByRole('region', {name: '限时物品续期'})).toBeTruthy();
  });

  it('读取档案、余额与启动选项，空库存不显示续期表单', async () => {
    await ready();
    expect(screen.getByText('44,445')).toBeTruthy();
    expect(screen.getByText('99,620')).toBeTruthy();
    expect(screen.getByRole('switch').getAttribute('aria-checked')).toBe('true');
    for (const name of actions) expect(button(name).disabled).toBe(false);
    expect(button('启动游戏').disabled).toBe(false);
    expect(screen.getByText('当前没有限时物品。')).toBeTruthy();
    expect(screen.queryByLabelText('选择物品')).toBeNull();
  });

  it('读取中和没有档案时禁止档案写入，保留独立启动操作', async () => {
    profiles = [];
    render(<App/>);
    for (const name of actions) expect(button(name).disabled).toBe(true);
    expect(screen.getByRole<HTMLButtonElement>('switch').disabled).toBe(true);
    await screen.findByText('未运行');
    for (const name of actions) expect(button(name).disabled).toBe(true);
    expect(button('启动游戏').disabled).toBe(false);
  });

  it('游戏运行中禁用档案写入和启动，启动选项仍可修改', async () => {
    running = true;
    items = [{item_id: 7, quantity: 1, expires: 2000000000, name: '限时武器'}];
    await ready();
    fireEvent.change(await screen.findByLabelText('选择物品'), {target: {value: '7'}});
    for (const name of [...actions, '启动游戏', '续期']) expect(button(name).disabled).toBe(true);
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

  it('永久物品不参加续期，未选择禁用；到期物品和输入天数提交为数字', async () => {
    items = [
      {item_id: 7, quantity: 1, expires: 1, name: '已到期武器'},
      {item_id: 8, quantity: 1, expires: 4294967295, name: '永久武器'},
    ];
    await ready();
    const select = await screen.findByLabelText('选择物品');
    expect(within(select).queryByRole('option', {name: /永久武器/})).toBeNull();
    expect(button('续期').disabled).toBe(true);
    fireEvent.change(select, {target: {value: '7'}});
    fireEvent.change(screen.getByLabelText('增加天数'), {target: {value: '90'}});
    fireEvent.click(button('续期'));
    await screen.findByRole('status');
    expect(posts).toEqual([{path: 'profile/renew', data: {user_id: 'player-one', item_id: 7, days: 90}}]);
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
