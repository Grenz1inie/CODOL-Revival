# CODOL 3.19 移动输入阶段结论（2026-10-17晚）

Case: codol319-move-input（protocol-reverse, offline, auth granted）。
接手自 codol319-handoff-20261017-2056；运行现场未动。

## Evidence

- `E1` `work/codol319-map-live-20261017/session.pcapng`（最终文件，tshark 21:12:43
  定稿）：322,664包/1764.6s；客户端→服务器289,472包，289,460个move包全部
  op0增量、0解码错误、0 moveNoDelta；首move帧676；每包2条usercmd（重复+新增），
  server_time自1000、每条5-6ms。
- `E2` 真实输入窗口：帧3446-3472用户按住LEFT(cls=8)约1.3s，buttons位0x8000000
  保持，早期开火位0按下192条；预测尾迹全程等于出生点[-1601.8,1176.2,-24]。
- `E3` 截图 `map-visible.png`：无菜单遮挡，HUD/小地图在，无武器（弹药0、按1提示）。
- `E4` fixtures `move319-{head,moving,tail}.json`（Python已验证解析器
  client_message319 全链基线解码）+ golden `move319-trajectory.json`。

## Finding

- `F1` Rust usercmd解码逐字段复现参考（E4→tests/client_move.rs，134包全对）。
- `F2` 客户端自身预测冻结（E2+E3）：按住移动键预测origin纹丝不动。原因未定位；
  候选：无武器状态/pmove门控/ps标志。需新REA（CL_Frame/pmove门控）或实机
  服务器推动origin对照。此为本阶段最重要的开放问题。
- `F3` 移动窗口含可靠命令18-21（`n 85`等），语义未知；session严格编号门控
  会拒绝跳号（符合设计）。
- `F4` 服务端移动闭环已实现并全绿：无碰撞积分器+C1 wish缩放+16单位reconcile+
  short差分角度累计；快照4状态与Python编码器逐字节一致（E4→tests/movement.rs）。
- `F5` reconcile在冻结客户端下会把服务器拉回出生点（74/74采纳）——容差设计
  使然；实机闭环时客户端应回显服务器新origin，反馈闭合，待验证。

## Path（复现）

```
python -B work/codol319-move-input/move_reference319.py   # 重建fixtures+golden
powershell -NoProfile -File scripts/Invoke-MatchCargo.ps1 test --offline \
  --manifest-path "$PWD/games/codol/versions/v3_19_26_22/server/native/match-server/Cargo.toml" \
  --target-dir "$PWD/runtime/builds/codol/v3_19_26_22/rust-match" --test client_move --test movement
```

下一步：实机联调（用户已同意随时开游戏）——重点观察服务器推动origin后客户端
画面是否跟随（F2/F5）；随后碰撞/跳跃或武器阶段按用户优先级。
