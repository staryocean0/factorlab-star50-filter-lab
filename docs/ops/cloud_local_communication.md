# 云端—本地沟通记录

## CL-STAR-RISK-20260907

- 授权：用户要求恢复原科创50云仓库，用于科创50/中证1000底层K线与突发波动研究；随后明确授权DataHub将两指数3秒离线导出扩展至2025年底。
- 本地核心：FactorLab主仓保存资料库与研究记录，STAR50本地仓保存专题代码/成果，DataHub保存权威数据父层。其他主题仓库不修改。
- 当前入口：[完整交接说明](../handoff/cloud_risk_gate_20260907/HANDOFF.md)。
- 本地已执行：资料归档，父源与导出完整性检查，公开/用户提供PDF身份核验，研究包验证与测试；具体结果看包manifest与handoff receipts。
- 原交接时云端复核状态：尚未发生；该句仅记录最初交接时点，不再代表2026-09-07后续状态。
- 云端下一步原则：先验证包与阅读研究协议/文献，不自动执行历史账户或训练，不打开2026。新研究协议、运行证据与成果写入新版本并回传commit及清单。
- 缺数据流程：只列目标问题所需最小字段、标的、时间范围、消费者语义及输出验收；不默认搬全部本地数据，不将缺订单簿数据误说成已具备OFI或撤单强度。
- 执行位置：云端会话能直接执行则自己执行；确缺输入/能力时写本表请求本地；Actions不是默认计算场所。未经用户授权，不联系第三方、不改生产。
- 回迁：本地fetch指定commit，逐文件hash、时间/单位/权限、测试和科学结论复核后才接受；大型父数据仍留本地，禁止静默覆盖固定历史证据。

### 2026-09-07 / session-aware information-set bounds v0.6.17

- 云端已完成 archived DataHub contract/provenance intake 裁决并解除 provenance blocker；5m offset0 的 lineage metadata caveat 与 349,923-row DataHub authority / 350,561-row FactorLab surface 差异继续显式保留。
- 新 results-blind 执行分支：`research/session-aware-information-set-bounds-v0617-20260907`。
- tested scientific implementation commit：`b6930dcd16bb47664b1edcbc13e2bdabf779cf4a`。
- GitHub Actions `34111701647` / job `101709204616`：完整 CI PASS；pytest `159 passed, 1 skipped`。唯一 skip 是 GitHub runner 未挂载 canonical local L3 三源码；该历史 exact-prefix 测试在本地源码存在时仍必须执行，未放宽科学断言。
- implementation acceptance receipt：`docs/research/session_aware_information_set_bounds_v0617/implementation_acceptance_receipt.json`。
- **当前本地请求已发出**：执行 exact DataHub 349,923-row authoritative replay，详见 `docs/ops/session_aware_information_set_bounds_v0617_LOCAL_REPLAY_REQUEST.md`。
- local replay 必须 fail closed：prior authoritative source expected SHA-256 与 prior v0.6.15 leg-universe expected SHA-256 都必须是本请求之前已存在的 frozen receipts；不允许现场算 hash 后自证，也不允许用 350,561-row FactorLab `1m_official` 替代。
- 本地回传建议分支：`local/session-aware-information-set-bounds-v0617-replay-20260907`；只回传 bounds/summary/receipts/deterministic boundary samples，不上传大型父数据，不看 returns/P&L/OOS。
- real authoritative replay 在收到并云端复核本地 commit 前仍为 `NOT_EXECUTED`。`morphology_replication_not_yet_accepted`、direction、third-wave、returns、OOS、trading、production 全部继续冻结。
