# 更长历史盘口的阻断归属

2026-09-06主控只读诊断。结论：**更长期权原始归档存在，当前深历史物化/登记/供应链未闭合，主要处理方是DataHub；不是FactorLab改一个日期即可解决。**

FactorLab既有接口确实钉死了最近一年L5版本，但已另外调用DataHub深历史专用CLI和精确resolver、查询live注册表并核对物理路径。没有找到其他已获准的ETF期权深历史版本。较长的上交所期权日线产品不能替代买一卖一。

| 层 | 当前证据 |
|---|---|
| 最近一年供应 | ETF与期权都存在固定READY及研究grant；截至2025有82个日期分区，范围2025-09-01..12-31，尚未在本次核验逐标的报价完整性 |
| 原始更长历史 | `raw-prefetch-v10`现有475日目录，其中435日在2024-03-13..2025-12-31；有更早远端来源和完成前缀记录，未重验全部raw payload SHA |
| 已退休原件 | 27份回执记录day acceptance后退休原件，引用的27个旧workset输出路径当前均不存在；需追查去向，不能据此断言永久丢失 |
| 深历史正式产物 | 文档给出的lake根为空、workset根不存在，冷盘及bind mount存在 |
| 注册与供应 | 深历史legacy/v2版本与供应decision均为0；专用coverage返回`exact ETF option depth serving pointer is not ready`，resolver为`no active product-scoped serving decision` |
| 执行状态 | backfill及prefetched-materialization两个服务not-found，审计watcher仍等待；文档旧“执行中”不能作当前证明 |

现货ETF的早期盘口还需另审：既有基金源说明早期只含少量大盘ETF，不能从期权长历史推导588000/588080现货BBO同样齐全。目标应分别提供真实覆盖，期权上市前不能补造。

没有更改DataHub数据、供应授权或服务。按DataHub本仓要求刷新了GitNexus代码索引缓存，使用`--skip-agents-md`保留其指令文档；诊断依据仍是当前代码、只读数据库、文件和服务状态。

转交提示词：[FactorLab用户入口](</home/starryocean/桌面/量化/baylum terminal 0.4.1/factor_lab/docs/user/star50_datahub_history_repair_prompt.md>)。
完整机器证据：[diagnosis.json](../../../artifacts/conditional_bucket_v1_datahub_diagnosis/diagnosis.json)。

研究目标已保存为[owner_contract.json](owner_contract.json)：先有效条件分桶与交易否决，再微量调参，仓位最后；两个强目标是最大回撤和平均单笔净质量。已物化8个因果候选测量、58,176根观察、3,483个原始入场事件，全部事件测量可用且通过前缀不变测试。它们尚未被证明是有效因子或准入否决，未计算新策略收益。费率方向与载体映射问题仍待用户澄清，不能用默认选项当成已确认。
