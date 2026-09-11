# 科创50 / 中证1000：因果 K 线风险属性模块

**识别行情演变中当时可知的K线风险属性及其变化，为下游状态识别、策略分桶和适用环境判断提供可按时点消费的信息。** 本仓不开发具体策略动作、方向、仓位或收益路由。

## 当前状态：D3 已执行，实际增量用途未获晋升

**D3_COMPLETED_NO_PRACTICAL_INCREMENTAL_PROMOTION**。

V19有冻结参考定义下的识别证据；D2因果E15/CLOSE回放与研究消费者交付已通过。D3现在已单独检验后续15/30/60分钟风险信息：相对上一确认状态及简单历史波动，状态/转移/恢复属性带来小幅正改善，但6项主比较均低于预注册1%相对误差改善门槛；加入已有实时连续强度后，状态额外增量更小且区间跨0。**D3_INCREMENTAL_UTILITY_NOT_SUPPORTED**，不是执行失败，不推翻V19/D2，也不宣称已经证明强预测门控。

阅读：[当前任务](CURRENT_RESEARCH.md) → [方向](docs/research/CAUSAL_KLINE_STATE_NEXT_PHASE_20260911.md) → [接续入口](CONTINUE_HERE.md) → [机器进度](research/causal_state_utility_d3/PROGRAM_STATE.json) → [D3结果](research/causal_state_utility_d3/RESULTS.md) / [判定回执](research/causal_state_utility_d3/DECISIVE_RECEIPT.json) / [复现](research/causal_state_utility_d3/REPRODUCE.md)。

下一合理方向为独立预注册连续风险属性的实际用途，不继续挤三状态accuracy；D4和V20均未启动。描述性风险区分不等于有足够增量，更不等于策略盈利。

## 保留的基线及适用边界

[V19 Validation](research/highvol_risk_episode_state_machine_v19_validation/VALIDATION_RESULTS.md)、[残差审计](research/v19_residual_failure_audit/RESULTS.md)、[D2结果](research/causal_state_delivery_d2/RESULTS.md)与原代码/surface/回执保持不变。D2原可用113928行零漂移；完整网格可用率97.9167%，日初缺参考与日末观察新鲜度限制保留。历史假设下15秒提前量不是实测延迟。

D3未来窗口不含当前bar、不跨午休/隔夜；缺窗口不补无风险。NORMAL非安全保证，UNSAFE非看空，UNAVAILABLE非NORMAL。后验只用于评价；available_at仍是历史检索时钟。

Development2021–2023；Validation2024–2026-08-21按[V2政策](docs/governance/DATA_USAGE_POLICY_V2.md)复用，非fresh OOS；实际实时证据/本次评价止于2025。无2026 3s、BlackBox或生产权限。[研究桶边界](docs/governance/BUCKET_SCOPE_REPAIR_20260909.md)不变，旧payoff/router只作历史证据。

```bash
python scripts/validate_data_usage_policy.py
python -m unittest discover -s research/causal_state_utility_d3 -p 'test_*.py' -v
```

`d3_executed=true`; `d3_practical_incremental_promotion=false`; `d4_started=false`; `v20_started=false`; `production_authority=false`。
