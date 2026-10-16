# 网页启动设置进度 — 2026-10-17

用户因电脑电量不足要求保存进度，当前暂停开发。

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

## 下次继续

1. 先查看当前 Git 状态及并行任务变化，保留其他工作；核对日志是否足够定位全量测试进度，不盲目重复全套。
2. 完成剩余 Python 集中回归、窄屏视觉检查；runtime/logs/launch-settings-desktop.jpg 的裁剪不正确，不可作为最终交付截图。
3. 更新 GitNexus / CodeGraph 索引（本次实现后尚未刷新）：gitnexus analyze . --skip-git --index-only --name CODOL-Revival；codegraph sync .。
4. 游戏实际全屏/分辨率及中文菜单，需用户方便时退出并下次启动验收。不得为验证而打断用户现有游戏。

当前控制器：http://127.0.0.1:8765/。当前实例 codol-3.19.26.22-911c42a0027c；实际游戏版本 3.19.26.22，不是工具默认工作目录名中的 3.3.3.3。
