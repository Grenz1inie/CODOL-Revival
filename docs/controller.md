# 本地 Web 控制器

## 启动与使用

在项目根目录运行 `powershell -NoProfile -ExecutionPolicy Bypass -File scripts/Start-Controller.ps1`，打开 <http://127.0.0.1:8765/>。

首次构建：在 `web/` 运行 `npm ci`、`npm run build`。控制器只监听本机回环地址，复用已有 Python 环境和游戏启动脚本。

- **游戏控制**：选择已保存档案、配置下一次启动是否跳过新手引导、启动游戏。引导默认跳过；开关持久化于 `runtime/data/controller.json`。
- **开发 WIKI**：左侧按 `docs/` 的实际目录列出文件，右侧显示 Markdown 或 JSON。目录外源码及证据显示相对路径，避免误跳转为同名文档。
- **等级与货币**：退出游戏后可设置此版本最高的 3 转生 70 级、同步商城等级解锁值、分别增加游戏币和点券。游戏币购买、重登保持及点券购买已实测。
- **全部物品**：点击“一键发放全部物品”，发放完整目录的 6772 种物品，期限设为永久，201 把武器写入对应满级经验；已有数量不叠加，余额不变。游戏内装备验收状态见 [物品与武器成长](wiki/09-inventory-completion.md)。
- **限时物品续期**：选择已有的限时物品和天数，未到期从原期限延长，已过期从现在延长；永久物品无需续期。所有数据操作写前备份，游戏运行时拒绝修改，重启游戏后读取。

## 页面设计依据

这是高频本地操作控制台。采用固定导航、档案状态条、主要操作区和启动选项侧栏；Wiki 使用目录树与正文双栏。浅色/深色均基于 Radix Themes 官方组件和状态色，石墨灰背景配琥珀色强调，避免大面积游戏宣传背景影响阅读。

设计参数：`DESIGN_VARIANCE=3`、`MOTION_INTENSITY=2`、`VISUAL_DENSITY=6`。前者约束布局变化，中者限制装饰动效，后者保留桌面工具所需的信息密度。系统字体支持中文，交互提供键盘焦点；窄屏切换为纵向内容。

参考：[Carbon 色彩角色](https://www.carbondesignsystem.com/building-blocks/foundations/color/overview)、[侧栏组织](https://www.carbondesignsystem.com/building-blocks/core/components/ui-shell-left-panel/guidelines)。实际组件来自 Radix Themes，不声称采用 Carbon 组件实现。

## 代码与状态归属

| 目录 / 文件 | 责任 |
|---|---|
| `web/src/` | React 页面、主题、Wiki 阅读 |
| `src/controller.py` | 本机 HTTP API、设置、游戏启动入口、受限 docs 读取 |
| `scripts/Start-Controller.ps1` | 隐藏运行控制器并记录 PID、日志 |
| `runtime/data/` | 玩家数据与控制器设置 |
| `runtime/backups/` | 修改前备份 |
| `research/evidence/` | REA 证据和有边界的运行时提取 |

接口不允许 docs 路径越界；写入接受同源 JSON，设置对布尔值严格校验。游戏启动复用现有管理员启动流程，UAC 由用户确认。

## 测试安排

用户已确认三层边界：档案修改/备份/重载；HTTP 操作和 Wiki 路径；集中浏览器操作与真实游戏重启。每个功能先做失败测试再实现，不用未实现的字段假设生成测试期望。

已完成 HTTP、私有档案、货币及商城协议用例验证，共 44 项通过；浏览器已验证引导开关持久化、增加点券、限时物品续期与全物品发放。游戏实测 3 转生、70 级；购买 M14 EBR 后余额 44445，退出再进余额及物品保持。点券购买 380 后余额 99620，用户确认显示、扣款及入库；再次登录后确认全物品永久、武器满级、配件和皮肤可装备，点券保持。续期的期限计算及持久化已通过浏览器/API 核对，续期后尚未单独在游戏查看期限便执行了永久发放。
