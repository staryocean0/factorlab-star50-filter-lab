# 科创50 / 中证1000：因果 K 线风险属性模块

使命：识别行情演变中当时可知的K线风险属性和变化，为下游环境分桶与策略适用性研究提供信息。本仓不开发交易动作、方向、仓位或收益路由。

## 当前：D4完成，连续程度信息获得分目标支持

**D4_COMPLETED_CONTINUOUS_ATTRIBUTES_PARTIALLY_SUPPORTED**。
V19识别基线与D2因果交付保持冻结；D3三状态属性未达到实际增量门槛的结论不改。D4转向连续冲击强度/波动比率：对简单历史基准和同复杂度旧数值基准，15/30/60m log未来RMS、30m未来尾部通过联合门槛；15/60m尾部不晋升。这是既有2024–2025可复用Validation的注册后续评价，不是fresh OOS或强交易预警证明。

阅读：[当前任务](CURRENT_RESEARCH.md) → [方向](docs/research/CAUSAL_KLINE_STATE_NEXT_PHASE_20260911.md) → [接续入口](CONTINUE_HERE.md) → [D4进度](research/continuous_risk_utility_d4/PROGRAM_STATE.json) → [结果](research/continuous_risk_utility_d4/RESULTS.md) / [回执](research/continuous_risk_utility_d4/EXECUTION_RECEIPT.json) / [消费者契约](research/continuous_risk_utility_d4/CONSUMER_CONTRACT.md)。

目标交付为状态上下文+连续程度+时间/缺失约束，不将高分位直接映射为买卖许可。delta及3×3分位键只作描述，未单独证明效用。下一步是本仓有界研究消费者接入验收，尚未执行；不急开新预测器或V20。

## 冻结证据与边界

[D3原结论](research/causal_state_utility_d3/RESULTS.md)、[D2工程证据](research/causal_state_delivery_d2/RESULTS.md)、[V19 Validation](research/highvol_risk_episode_state_machine_v19_validation/VALIDATION_RESULTS.md)、[残差审计](research/v19_residual_failure_audit/RESULTS.md)及原代码/surface/receipt不变。

D4全部会话计算：23测试、20市场前缀检查、113928可用属性和96030未来记录独立核验通过，无Actions。日初缺参考/日末旧观察仍保留；CSV为Asia/Shanghai墙钟；理想15秒不是实测feed延迟。NORMAL非安全保证，UNSAFE非看空，UNAVAILABLE非NORMAL。

[V2数据政策](docs/governance/DATA_USAGE_POLICY_V2.md)与[研究桶边界](docs/governance/BUCKET_SCOPE_REPAIR_20260909.md)不变。Development2021–2023，本轮Validation2024–2025，不称fresh OOS；无新raw3s、2026、保护期或BlackBox。V16 final-5m到2026-08-21不创建2026 realtime证据。父结构分类和具体策略经济验收仍属其他仓。

```bash
python scripts/validate_data_usage_policy.py
python -m unittest discover -s research/continuous_risk_utility_d4 -p 'test_*.py' -v
```

`v19_frozen=true`; `d3_decision_unchanged=true`; `d5_started=false`; `v20_started=false`; `production_authority=false`。
