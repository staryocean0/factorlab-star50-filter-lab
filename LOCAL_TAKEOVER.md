# 本地接续入口：因果 K 线风险属性交付

当前任务、状态和待执行命令以 [CURRENT_RESEARCH.md](CURRENT_RESEARCH.md)、[CONTINUE_HERE.md](CONTINUE_HERE.md) 及 [下一阶段权威叙事](docs/research/CAUSAL_KLINE_STATE_NEXT_PHASE_20260911.md) 为准。

V19 已阶段性收口且保持冻结；当前走 causal state delivery V1，不重开旧滤波/payoff研究。本次仅更新研究仓权威入口并增加状态接口原型/合成测试，不声称本地 FactorLab/DataHub 已回迁、复核或接入成功。

本地回迁时先核对提交和 `research/causal_state_delivery_v1/EXECUTION_RECEIPT.json` 的代码身份与测试范围，再运行接续入口给出的命令。完整因果事件回放、close事件、恢复概率接入、消费者验收与风险分桶效用仍为待完成项；不接生产 registry。

原2026-09-06本地接管记录及源码hash缺口原样保存在 [历史快照](https://github.com/staryocean0/factorlab-star50-filter-lab/blob/766dd6f5293a1fa8588edabe368088f63981fa1a/LOCAL_TAKEOVER.md)。该记录中的旧“当前任务”、旧数据角色与“CONTINUE_HERE不得更新”不覆盖现行入口及 DATA_USAGE_POLICY_V2；历史源码事件不因新阶段而消失。

`production_authority=false`。
