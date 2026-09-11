# 科创50 / 中证1000：因果 K 线风险属性模块

**识别行情演变中当时可知的K线风险属性变化，为下游状态识别、策略分桶和适用环境判断提供可按时点消费的信息。** 本仓不开发买卖、方向、仓位或收益路由，不以事后解释或准确率小数点为终点。

## 当前阶段：D2 已通过，D3 尚未执行

V19基线及残差审计保持冻结。交付路线为：契约 → 因果双时钟事件回放/消费者验收 → 非PnL风险分桶效用评价；不是新模型V20。

D2完成独立原始价格回放：113,928个原可用E-15行全部保留、状态与概率零漂移；生成232,704个E-15/CLOSE事件，固定市场未来扰动20/20通过。D1原20项和D2新38项测试通过。

开始阅读：[当前任务](CURRENT_RESEARCH.md) → [方向](docs/research/CAUSAL_KLINE_STATE_NEXT_PHASE_20260911.md) → [接续入口](CONTINUE_HERE.md) → [当前机器进度](research/causal_state_delivery_d2/PROGRAM_STATE.json) → [D2结果](research/causal_state_delivery_d2/RESULTS.md) / [回执](research/causal_state_delivery_d2/EXECUTION_RECEIPT.json)。

完整网格状态覆盖97.9167%，不把日初不可用补NORMAL。日末15:00 bar的E-15观察有已披露新鲜度限制；15秒提前量是历史实时可得假设，不是实测延迟。工程回放通过不证明分桶增量效用或生产就绪。

下一步D3先预注册后续波动、再次冲击、持续/恢复的风险效用评价，再与匹配的简单已知基准比较；当前没有D3结果。

## 冻结基线与范围

V18：E-15 switch-on；V19：UNSAFE/RECOVERING连续性与收盘确认退出；V16/V17：冻结多horizon恢复对象。[V19 Validation](research/highvol_risk_episode_state_machine_v19_validation/VALIDATION_RESULTS.md)和[残差审计](research/v19_residual_failure_audit/RESULTS.md)保持原样。D1封存切片在research/causal_state_delivery_v1/。

NORMAL不保证交易安全，UNSAFE不代表看空，UNAVAILABLE不是NORMAL。后验标签只能评价，不能进入消费者输入。available_at仍是历史检索时钟。

Range/UpTrend/DownTrend属于two-wave仓，具体策略经济验收属于对应策略仓；旧payoff/router仅历史证据。[研究桶边界](docs/governance/BUCKET_SCOPE_REPAIR_20260909.md)不变。

Development为2021–2023；Validation为2024–2026-08-21的可复用池，不是fresh OOS。实际3s验证覆盖仍止于2025；V16 final-5m覆盖不替代2026 realtime authority。遵守[V2数据政策](docs/governance/DATA_USAGE_POLICY_V2.md)，不查询BlackBox，不改生产权限。

```bash
python scripts/validate_data_usage_policy.py
python -m unittest discover -s research/causal_state_delivery_d2 -p 'test_*.py' -v
```

`D2_CAUSAL_REPLAY_SUPPORTED_D3_NOT_EXECUTED`；`production_authority=false`。
