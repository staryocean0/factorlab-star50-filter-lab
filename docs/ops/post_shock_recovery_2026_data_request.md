# 2026恢复状态独立验证：最小数据请求

任务：`CL-STAR-RISK-20260907 / POST-SHOCK-RECOVERY-2026`

用户已于2026-09-07明确授权2026数据用于本专题的独立研究验证。研究协议已冻结在 `docs/research/post_shock_recovery_2026/PROTOCOL.md`。

## 当前阻断

仓库现有科创50/中证1000分钟与3秒有界研究包均截止2025-12-31；当前GitHub installation中没有可访问的`unified_datahub`仓库，也没有2026分区。因此无法开始2026 held-out验证。

这不是算法、Actions额度或GitHub权限问题；缺的是**权威2026行情分区**。

## 只需要以下最小输入

时间：`2026-01-01` 至本次导出时最新的**已完整收盘交易日**，本次验证快照最多到 `2026-09-07`。

标的：
- `000688.SH` 科创50指数
- `000852.SH` 中证1000指数

频率：
- 原生/现有DataHub语义的 `1m`
- 现有指数源观测语义的 `3s`

1分钟至少保留现有研究loader所需的字段及质量语义：`symbol/timestamp/trading_day/OHLC(or close)/causal_flat_fill/source_minute_count/high_frequency_analysis_eligible`以及dataset/source/version身份字段。

3秒至少保留：`symbol/observation_datetime/trading_day/price/row_index`以及dataset/source/version身份字段。同秒多行保持源顺序，不静默去重；不插值。

同时提供新的独立2026 manifest/receipt：逐文件SHA256、行数、first/last day、时区语义、父数据版本/源版本、导出截止日。**不要修改或覆盖2021-2025已封存manifest及其hash。**

## 建议落盘位置

为了避免污染旧包，可新增：

- `data/cross_index_risk_gate_2026_v1/1m/000688.SH/2026.parquet`
- `data/cross_index_risk_gate_2026_v1/1m/000852.SH/2026.parquet`
- `data/cross_index_risk_gate_2026_3s_v1/000688.SH_2026.parquet`
- `data/cross_index_risk_gate_2026_3s_v1/000852.SH_2026.parquet`
- 对应独立manifest/receipt

如实际DataHub只提供到较早日期，也可以上传该完整区间；验证代码必须按manifest实际截止日运行并报告覆盖，不要求伪造到9月7日。

## 数据到位后云端立即执行

1. SHA/行数/时区/质量字段验收；
2. 使用冻结事件定义生成2026首跳事件；
3. 复算风险衰减和KM恢复时长；
4. **不重新拟合**，直接检验当前5分钟波动持续性这个主恢复分数；
5. 固定回放此前release规则/模型及3秒路径特征模型；
6. 单独报告科创50、中证1000，再给合并辅助视图。

验收目标是独立验证`Unsafe -> Recovering`风险衰减及是否存在可靠在线`Clean`解除，不进行交易回测或2026参数搜索。
