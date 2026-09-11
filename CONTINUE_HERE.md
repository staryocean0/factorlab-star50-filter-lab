# 接续入口：D2 已通过，D3 待预注册

当前交付状态：**D2_CAUSAL_REPLAY_SUPPORTED_D3_NOT_EXECUTED**。
历史基线：V19_VALIDATED_RESIDUAL_PATH_CLOSED_NO_V20。不要重新设计或重跑V19，不要再把D2当作未执行。

先读 `AGENTS.md`、`CURRENT_RESEARCH.md`、`docs/research/CAUSAL_KLINE_STATE_NEXT_PHASE_20260911.md`，然后：

1. `research/causal_state_delivery_d2/PROGRAM_STATE.json`
2. `research/causal_state_delivery_d2/RESULTS.md`
3. `research/causal_state_delivery_d2/EXECUTION_RECEIPT.json`
4. `research/causal_state_delivery_d2/PROTOCOL.md` 与 `FROZEN_INPUTS.json`
5. `research/causal_state_delivery_d2/LOCAL_VERIFICATION_SUMMARY.json`
6. V2数据治理、研究桶边界、available_at字段澄清和原始V19/V18/V17/V16证据。

D1文件仍在 `research/causal_state_delivery_v1/`，其旧PROGRAM_STATE是D1封存状态，不是当前断点。

## 已执行

独立原始价格回放 run34620317766，artifact10271634055，ZIP SHA256 cf1c89e1412fd70f27992d9077af10dd7887a6843072e03ef808902bf5a84096。113,928个原可用E-15行全部保留、状态与概率等零漂移；232,704个双时钟事件；20个固定市场未来扰动检查通过。D1原20项、D2新38项测试及数据治理校验通过。

当前会话又独立核验全部JSONL事件和哈希链。原始Parquet回放执行地点是Actions，不是本地FactorLab/DataHub；源码和数据身份见回执/产物manifest。

## 可运行的无行情检查

```bash
python scripts/validate_data_usage_policy.py
python -m unittest discover -s research/causal_state_delivery_d2 -p 'test_*.py' -v
```

已取得原D2 artifact并解压后，可用标准库独立复核：

```bash
python research/causal_state_delivery_d2/verify_ledger.py /path/to/extracted/d2/artifact --out verification.json
```

不要为浏览结果重新触发raw replay。完整重放需严格满足FROZEN_INPUTS和原始artifact身份，不以重跑生成新统计Validation证据。

## 下一项直接执行：D3协议先行

先冻结非PnL的风险分桶效用问题、评价对象、因果时钟、未来窗口、基准、覆盖要求、最小实际效应和按日/依赖块的不确定性；再在Development/可复用Validation上评价。D3当前没有结果或已冻结协议，不把本页方向写成已完成预注册。

用途是区分后续波动、再冲击、持续与恢复等风险环境，不是提高自身标签一致率，不是看多看空、开平仓、仓位或收益router。

必须明确日初排除、午休/日终、观察新鲜度和未来窗口不可用的口径。D2完整网格状态覆盖97.9167%；2,424个日初bar不可用。2,424个15:00 bar的E-15观察旧于120秒，其他时点30条旧于15秒；不能事后删除这些行再称完整覆盖。概率原始horizon标签和日内bar年龄不等于任意墙钟目标。

数学决策已委托执行者，不再逐项索要批准。按AGENTS的执行位置顺序工作，确需Actions时说明真实理由；不自动执行本地或生产任务。

## 边界

保持V16—V19及D1封存对象不变，不开残差优化V20。Validation可复用但非fresh OOS；不拟合当前受测候选。不合成2026 3s，不查截止日后保护数据或BlackBox。不把工程回放通过称为市场增量效用或策略经济验收。

NORMAL不是交易许可，UNAVAILABLE不是NORMAL，临时快照不能跨close继续冒充当前状态。production_authority=false。
