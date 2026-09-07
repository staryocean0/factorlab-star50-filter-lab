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
- 原 local replay request：`docs/ops/session_aware_information_set_bounds_v0617_LOCAL_REPLAY_REQUEST.md`；其中两个 prior identity gates 继续具有约束力。
- 云端进一步做 prior-identity preflight 后，**没有在当前仓库/可追溯 merge lineage/takeover receipts/communication records/handoff DataHub archive 中找到**：
  1. 349,923-row authoritative DataHub source 的事前 SHA-256 receipt；
  2. v0.6.15 实际 frozen published-leg universe + strict-pair / qualification overlays 的事前 SHA-256/manifest。
- handoff `DATA.md` 中另有 000688.SH 1m 截止2025的 317,280-row 云消费面；它不是 v0.6.17 要求的 349,923-row authoritative source，禁止替代。
- 云端 blocker receipt：`docs/research/session_aware_information_set_bounds_v0617/identity_preflight_blocker_receipt.json`，首次记录 commit `6992290aee43b0af1600061a205f70201daa4c8e`。
- **当前本地请求已收窄为 IDENTITY ONLY**：先在本地 DataHub / 历史实验 evidence store 恢复上述两个“本请求之前已存在”的 receipt/manifest，只回传路径、receipt 自身身份、expected hash、创建/commit provenance 和最小非结果元数据；不得执行 v0.6.17 scientific runner，不得查看 v0.6.17 bounds 结果。
- 若本地也找不到其中任一 prior receipt，按原 frozen request fail closed；不得现场对候选文件新算 hash 后同时当 expected/actual。若两者都能恢复，则先回云端做 identity adjudication，只有通过后才恢复 exact DataHub replay。
- local replay return branch 当前仍未出现；real authoritative replay 仍为 `NOT_EXECUTED`。
- `morphology_replication_not_yet_accepted`、direction、third-wave、returns、OOS、trading、production 全部继续冻结。
