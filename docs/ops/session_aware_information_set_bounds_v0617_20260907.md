# CL-STAR-RISK-20260907 / v0.6.17 implementation freeze

日期：2026-09-07。

本提交冻结 results-blind session-aware information-set bounds v0.6.17 的云端执行面，并用本提交触发仓库现有 CI。CI 结果必须从 GitHub Actions 实际 run 读取，不能由本文件预先宣称通过。

## 冻结对象

- `docs/research/session_aware_information_set_bounds_v0617/FROZEN_PROTOCOL.md`
- `src/star50_filter/session_aware_information_bounds.py`
- `scripts/run_session_aware_information_bounds_v0617.py`
- `tests/test_session_aware_information_bounds.py`

## 不变量

- 集中度沿用既有 `wave_shape.py` 的 log-price `motion_concentration` 定义。
- FactorLab 不复刻 DataHub bucket SQL，不用 adjacent native close / fixed-five 猜 support。
- support-gap / session-edge leg 保留并使用 universal `[1,n]` interval，不删除。
- authoritative source 固定为 DataHub 349,923-row surface，并要求 frozen SHA-256；350,561-row FactorLab `1m_official` 明确拒绝。
- frozen legs 必须通过已有 receipt/manifest SHA-256 绑定；本地不得重新筛 universe/overlays。
- observed support rows 必须逐行回连 accepted authoritative source 并核对 OHLC。
- results-blind：不读取 return/P&L/MDD/OOS/trading outcome。
- `morphology_replication_not_yet_accepted`、direction、third-wave、returns、OOS、trading 均保持冻结。

## 当前阶段

本提交之后先读取 CI。只有 CI 真实 PASS 才进入本地 authoritative replay 准备。真实 349,923-row DataHub source 不在 GitHub Actions runner 上，因此 CI 只验实现/合成拓扑不变量；不得把 CI PASS 写成 real replay PASS。

正式本地 replay 入口固定为：

```bash
python scripts/run_session_aware_information_bounds_v0617.py \
  --authoritative-source <exact-datahub-1m-file> \
  --expected-source-sha256 <frozen-datahub-source-sha256> \
  --legs <frozen-v0615-leg-universe> \
  --expected-legs-sha256 <frozen-v0615-legs-sha256> \
  --support <datahub-actual-support-topology> \
  --source-key timestamp \
  --out <new-v0617-output-dir>
```

若 authoritative source 的 `timestamp` 合法重复，必须改用 DataHub 的稳定 row key；禁止为了通过 gate 而去重。
