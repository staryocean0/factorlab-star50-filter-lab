# 接续入口：因果 K 线风险属性交付 V1

## 当前不是重开 V19，而是完成交付与实用性验收

当前阶段：`CAUSAL_KLINE_STATE_DELIVERY_V1_CONTRACT_TESTED_REPLAY_PENDING`。
V19 的历史科学断点 `V19_VALIDATED_RESIDUAL_PATH_CLOSED_NO_V20` 保留。

先读：

1. `AGENTS.md` 与 `CURRENT_RESEARCH.md`。
2. `docs/research/CAUSAL_KLINE_STATE_NEXT_PHASE_20260911.md`。
3. `research/causal_state_delivery_v1/PROGRAM_STATE.json`、`CONTRACT.md`、`EXECUTION_RECEIPT.json`。
4. `docs/governance/DATA_USAGE_POLICY_V2.md`、`data_usage_declaration.json`、`blackbox_query_ledger.json`。
5. `docs/governance/BUCKET_SCOPE_REPAIR_20260909.md`、`available_at_owner_clarification_20260906.json`。
6. 原始 V19 Validation、V19 residual audit 与 V16/V17/V18 冻结对象。

## 已实现且已执行

`research/causal_state_delivery_v1/adapter.py` 是状态层 E-15 适配原型：严格输入、因果时钟、临时/上一已确认状态区分、退出待确认、缺失原因、不可变输出及描述性 bucket_key。

20 项合成测试通过。这个结果不是行情回放、完整源端算法等价性、接收延迟、实用风险区分或策略收益证明。原型尚不生成 close 事件或恢复概率。

```bash
python scripts/validate_data_usage_policy.py
python -m unittest discover -s research/causal_state_delivery_v1 -p 'test_*.py' -v
```

## 直接继续的下一任务：D2

实现冻结 V9/V19 状态到 E-15/close 双时钟事件流的因果回放，接入冻结 V16/V17 概率与原有 gating，再做消费者 as-of 接入验收。

先绑定输入 manifest、代码/配置身份和协议；不要重跑旧科学版本以重获 PASS。对已验可用行检查逐行基线一致性，报告全部偏差/不可用与边界情况；不能改变 cohort、阈值或时点来修复工程测试。

确保：未来输入改变不改已发布前缀；当前 final_state 不能进入 E-15；收盘确认不能回写 E-15；迟到/缺失不冒充 NORMAL；开市/午休/日终与同秒重复记录语义有定义；发布后才可消费，过期快照不无限沿用。

数学与统计判定已委托执行者，不再逐项询问是否可设计协议/验收。按 AGENTS 的实际执行位置优先级工作，不默认派发 Actions，不创建生产任务。

## 随后 D3：风险分桶的实际信息价值

单独预注册后续波动、冲击再发生、风险持续/恢复的 endpoint、未来窗口、基准、最小实际效应与不确定性方法，再执行评价。不能只用自身状态标签的一致性证明“有用”。不做方向/PnL/开平仓/仓位/router。

已有 Validation 可复用诊断并启发后续 Development，但不是 fresh OOS，不能直接拟合当前受测候选。无新独立 holdout 不等于禁止合理工程交付或有用途的新 Development 问题。

## 不得越过的边界

不覆盖 V11–V19 冻结代码、surface、报告或 receipt；不为提高残差 accuracy 启动 V20；不把 E-6/E-3 事后替换 E-15；不合成 2026 3s，不读取保护期数据或查询 BlackBox。

V19 realtime 验证覆盖 2024–2025；V16 final-5m 到 2026-08-21，两者不能混同。NORMAL 不是“允许交易”，UNSAFE 不是“看空”，UNAVAILABLE 不是 NORMAL。

`production_authority=false`。详细实际进度与未完成项见 PROGRAM_STATE.json，不能把路线图当完成回执。
