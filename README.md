# 科创50 / 中证1000：因果 K 线风险属性模块

本仓的目的：**识别行情演变中当时可知的 K 线风险属性变化，为下游状态识别、策略分桶和适用环境判断提供可按时点消费的信息。** 不以事后解释或准确率小数点为终点，也不在本仓开发买卖、方向、仓位或收益路由。

## 当前阶段

V19 风险状态基线及残差审计已经阶段性收口，保持冻结；不启动为了修补边界残差的 V20。

现在进入 **causal state delivery V1**：契约 → 因果事件回放 → 消费者接入 → 非 PnL 的风险分桶效用评价。交付版本不是新模型版本。

开始阅读：

- [当前任务与证据](CURRENT_RESEARCH.md)
- [下一阶段权威叙事](docs/research/CAUSAL_KLINE_STATE_NEXT_PHASE_20260911.md)
- [继续执行入口](CONTINUE_HERE.md)
- [机器可读进度](research/causal_state_delivery_v1/PROGRAM_STATE.json)
- [接口契约](research/causal_state_delivery_v1/CONTRACT.md)

首个 E-15 状态适配切片及合成测试已实现；收盘事件、恢复概率接入、真实序列回放与实际分桶效用尚待验收。不得称为完整生产服务。

## 已冻结的基线

V18：E-15 switch-on；V19：UNSAFE / RECOVERING 连续性与收盘确认退出；V16/V17：多 horizon 恢复对象。

[原始 V19 Validation](research/highvol_risk_episode_state_machine_v19_validation/VALIDATION_RESULTS.md) 与 [残差审计](research/v19_residual_failure_audit/RESULTS.md) 保留不变。标签复现好不等于新风险全部提前可知，更不等于盈利得到证明。

## 不可混淆的边界

NORMAL 不代表交易安全保证；UNSAFE 不代表看空；不可用不是 NORMAL。后验标签只能评价，不能进入消费者输入。历史 available_at 不是盘中可得性时钟。

Range/UpTrend/DownTrend 父结构属于 two-wave 仓；具体交易策略及经济验收属于对应策略仓。旧 payoff/router 材料只是历史证据，参见 [研究桶边界](docs/governance/BUCKET_SCOPE_REPAIR_20260909.md)。

Development 为 2021–2023；Validation 为 2024–2026-08-21 的可复用池，不是 fresh OOS。实时 3s 的现有验证覆盖限于 2024–2025；V16 final-5m 覆盖不能替代 2026 realtime authority。适用 [V2 数据政策](docs/governance/DATA_USAGE_POLICY_V2.md)，不查询 BlackBox，不更改生产权限。

```bash
python scripts/validate_data_usage_policy.py
python -m unittest discover -s research/causal_state_delivery_v1 -p 'test_*.py' -v
```

`production_authority=false`。研究识别支持、工程交付通过和下游经济有效是三个不同结论。
