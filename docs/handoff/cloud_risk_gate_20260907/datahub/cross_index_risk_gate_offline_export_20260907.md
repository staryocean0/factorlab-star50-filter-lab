# 科创50/中证1000：用户授权的固定3秒历史离线导出

关联FactorLab任务：`fl-w1nrl`。用户在2026-09-07明确授权将两指数3秒研究范围扩展至2025年底。级别A：既有产品、既有字段与时间语义，仅增加有界离线导出合同；不是新增线上供应或生产grant。

父版本固定为`market_index_baidu_3s_20000714_20260821_cffex_underlyings_alias_repaired_v4_20260823`，物理SHA为`a2abc93ef0975490aae73c606ca8157a15c44cd182626c7537a9a62494310540`。只选择000852.SH从2014-10-17、000688.SH从2020-07-23至2025-12-31；保留全部源字段、原始价额和source receipt键，按标的/年分区。不是收益率运算、K线重采样、秒标签重建或填补。

价格单位是指数点；amount为源区间成交额，volume保持null，不能解释为成交股数或方向。观察字符串的Z沿用旧源上海墙钟语义，消费时按交易日/时间解释，不将其误转晚8小时。有效采样间隔以真实观测为准；3s是产品名，不保证每个3秒格点有数据。源端gap不填补。

## 源可行性与权限

父manifest/source_receipt的目标hash一致，物理文件哈希已核对。父coverage中两目标指数无source-member缺日，独立全量质量记录invalid/duplicate=0。旧消费者止于2020的限制不改写、不继承；新权限仅来自本次显式用户授权与本独立合同。导出在本地DataHub运行，生成固定manifest、coverage、gap、质量与primary acceptance回执；通过后才由FactorLab复制到私有仓库。不会改共享数据库或线上默认指针。

## 必查表面

| 表面 | 状态与理由 |
|---|---|
| scope_and_consumer | changed：新增独立offline consumer JSON，二指数、截至2025 |
| instrument_identity_and_lifecycle | not_applicable：复用官方index catalog，按发布日期限定；不新增证券 |
| calendar_session_and_market_rules | not_applicable：不生成bar或交易语义，原记录保留 |
| source_contract_and_raw_receipts | not_applicable：既有exact Baidu源与完整物理hash，保留receipt列 |
| dataset_schema_and_physical_key | not_applicable：原schema及(symbol,observation_datetime,row_index)键不变；同秒不同源顺序行保留，不擅自去重 |
| dataset_transform_and_parent_lineage | changed：纯行筛选与年分区，manifest绑定父源SHA |
| quality_coverage_and_gap_ledger | changed：逐标的年行数/日数、空值/重复/非法值、源成员缺日回执 |
| immutable_storage_manifest_and_retention | changed：独立新export目录，存在则拒绝，不覆盖父版本 |
| refresh_resume_and_reconciliation_workflow | not_applicable：一次性导出，不下载、不更新父产品，不创建周期任务 |
| query_cli_api_and_export | changed：新增专用离线CLI；线上API完全不改 |
| dataset_product_lifecycle_and_consumer_contract | changed：独立offline合同；其余产品生命周期不变 |
| serving_decision_and_fail_closed_negative_canary | changed：仅离线acceptance，非online grant；错symbol/越2025/错hash/旧目录拒绝 |
| observability_performance_and_resource_budget | changed：保存总行数、大小、时间；CPU/I/O，DuckDB最多4线程/2GB内存 |
| documentation_indexes_tests_and_rollback | changed：本spec/新测试/receipt；撤销仅停止使用新export，父文件/旧合同不变 |

## 执行与接受

`PYTHONPATH=src .venv/bin/python scripts/export_cross_index_risk_gate_20260907.py`

`PYTHONPATH=src .venv/bin/python -m pytest -q tests/unit/test_cross_index_risk_gate_export_20260907.py`

新文件不修改任何既有函数/类，既有符号调用图影响为零；不修改或提交其他在途改动。导出不做研究预测、策略评分或回测。验收只证明导出完整性和授权范围，不能授模型/策略有效性或fresh OOS。输出中的`online_serving_granted=false/production_granted=false`必须保留。

执行前置修复记录：首次SQL建视图参数接口不支持，尚未导出行；第二次在2022科创50发现39条同秒额外记录。复查父writer后，真实主键包含row_index；同秒不同价额是保留的源序列，不是身份重复。改为按父主键验重并额外报告same_timestamp_extra_rows，不删行、不改价。两次未完成目录单独保留，最终接受只绑定完成版本。GitNexus对新增脚本精确符号返回not_found；未修改任何已有符号。
