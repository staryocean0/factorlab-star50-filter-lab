# 接续入口：D3 已完成，无实际增量晋升

当前状态：**D3_COMPLETED_NO_PRACTICAL_INCREMENTAL_PROMOTION**。
正式判定：**D3_INCREMENTAL_UTILITY_NOT_SUPPORTED**。
V19冻结识别基线与D2工程回放通过的结论保留，不重跑旧版本，不把D3当作待执行。

先读AGENTS.md、CURRENT_RESEARCH.md、docs/research/CAUSAL_KLINE_STATE_NEXT_PHASE_20260911.md，然后：

1. research/causal_state_utility_d3/PROGRAM_STATE.json
2. research/causal_state_utility_d3/RESULTS.md
3. research/causal_state_utility_d3/DECISIVE_RECEIPT.json 与 EXECUTION_RECEIPT.json
4. research/causal_state_utility_d3/PROTOCOL.md、FIT_FREEZE_RECEIPT.json、REPRODUCE.md
5. D2 RESULTS.md/EXECUTION_RECEIPT.json，以及原V19/V18/V17/V16证据。
6. V2数据政策、研究桶边界、available_at澄清及BlackBox ledger。

## 不能弄错的结论

相对历史波动/上一确认状态基准，6项主比较均有小幅正增量与正的调整区间，但都低于事前1%相对改善门槛。基准已含同一E15实时连续强度时，状态字段额外改善更小、区间跨0。保留全部12项结果，不通过降低门槛、选窗口或换比较器改成PASS。

D3失败不是V19识别/交付失败，也不是状态毫无描述用途。状态自身标签一致性、未来风险区分、增量预测效用、策略收益必须分开。15m去重未来冲击捕获134/527，不能与V19现有episode重叠捕获互换。

## 已执行检查与复现

本会话24项单元测试、治理与编译通过；独立复核96030条未来结果/预测损失；20个新增历史特征前缀检查通过。Actions只转运旧5m输入，不承担D3统计。

```bash
python scripts/validate_data_usage_policy.py
python -m unittest discover -s research/causal_state_utility_d3 -p 'test_*.py' -v
```

完整结果包的输入、系数、逐行预测、块统计和原始日志按REPRODUCE.md复核。不要为阅读结果重新触发Actions。需要复现使用新输出目录，不覆盖冻结模型，也不把复现叫新独立Validation。完整仓库测试与生产尚未验收。

## 下一项方向：先注册新的连续属性问题

独立预注册现有连续冲击强度/波动比率对下游风险环境的用途，明确同信息基准、未来窗口、效应和覆盖边界；不是继续提高三状态accuracy。D3中B3对B1描述性改善仅作假说来源，不是已支持的晋升。

**D4未启动。** 不直接改V19阈值/时点/恢复表，不修改D3协议或用已评分结果拟合当前受测候选。数学决策已委托，无需逐项审批；数据/研究桶/生产权限不会扩大。

原D1/D2 PROGRAM_STATE均为各自封存阶段记录，当前状态以D3为准。历史available_at非盘中延迟；不可用不补NORMAL；无2026 3s、保护期数据、BlackBox、PnL或生产权限。Validation按V2可复用但非fresh OOS。
