# 网页启动设置进度 — 2026-10-17

用户因电脑电量不足暂停后，已于2026-10-17继续并完成本次功能及限定范围验证；游戏画面效果保留给下次启动人工验收。

## 已保存

- 本地提交 `ecbd6f9 feat(controller): add display launch settings`：启动选项移至游戏目录下方；3.19 增加全屏/窗口化和六档分辨率，实际加载器通过 CODOL319_EXTRA_ARGS 接收设置，保留 3291=0。
- 本地提交 `de9e42c feat(controller): add game language selection`：增加简体中文/英文，独立于网页语言；中文恢复原游戏的 localization.txt、ff_init_common_gfx_V109.ifs 到隔离副本并移除 --english-resources，英文恢复包内资源并启用该参数。
- 旧配置按窗口化 1280x720、英文兼容读取；游戏运行中前后端禁止保存；原游戏、存档和 .original 备份保留。
- 只提交本任务文件。其他任务并行修改及提交（包括 3350ce3）保留，未推送。

## 验证结果

- 严格按定向失败测试→实现→通过推进。
- 设置兼容/命令构建、HTTP 校验与实例隔离、语言资源往返与进度保留、所选资源缺失先报错、实际加载器 Popen 参数等定向 Python 测试通过。
- 前端集中回归 36/36 通过；生产构建通过；463 个文档链接检查无缺失。
- git diff --check 通过，做过本次范围代码检查。
- 控制器已重载。真实网页的启动设置前移、中英文字段、游戏运行中锁定已验证。API 返回 display_mode=windowed、resolution=1280x720、game_language=en；未改真实设置。
- 游戏 PID 76284、supervisor PID 28260 及三个服务身份在控制器重载前后未变，未重启游戏。
- 全量 Python 回归在运行中收到暂停要求，已终止本次测试 Python PID 42464；不能宣称全套通过。日志：runtime/logs/launch-settings-tests.log。
- 窄屏 DOM 的字段保持单列且未越界；窄屏截图超时，尚未完成视觉验收。已恢复浏览器原尺寸与英文网页。

## 恢复后的验证结果

- 两次功能提交的启动设置源码与前端未被后续提交改动；保留了其他任务的并行改动。
- 补跑集中回归，日志 `runtime/logs/launch-settings-regression.log`：HTTP启动设置用例通过；两项已有3.3初始快照断言失败；随后在 `NativeInventory319Tests.test_client_consumes_complete_registry_with_inherited_owner_and_wallet` 中以 `0xC0000005` 退出，日志停在Unicorn寄存器写入。未再重复全套，也未扩展修复范围。
- 尚未执行到的本次模块另行集中验证：`test_launch319`、`test_preparation319`、`test_settings319` 共19项通过，见 `runtime/logs/launch-settings-focused.log`。前端源码未变，沿用已通过的36项测试和构建结果。
- 控制器重新启动；当前游戏未运行，网页新设置可编辑。桌面中文效果已检查并重新保存完整截图 `runtime/logs/launch-settings-desktop.jpg`，替换了之前的错误裁剪。
- 窄屏视口585 CSS像素、页面宽562像素；六个字段为单列，边界34～528像素。窄屏截图接口超时，未声称完成截图验收；已恢复网页原语言及浏览器尺寸。
- GitNexus与CodeGraph已同步，并复核设置到准备/启动的消费者。
- 未修改真实启动设置，未启动游戏。

## 留给人工验收

在网页选择所需显示模式、分辨率和游戏语言并保存，下次启动后确认实际全屏/窗口画面和中文菜单。自动化已验证资源切换及加载器参数，不能代替游戏画面验收。

当前控制器：http://127.0.0.1:8765/。当前实例 codol-3.19.26.22-911c42a0027c；实际游戏版本 3.19.26.22，不是工具默认工作目录名中的 3.3.3.3。
