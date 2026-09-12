# 云端—本地沟通记录

## CL-STAR-RISK-20260907

- 授权：用户要求恢复原科创50云仓库，用于科创50/中证1000底层K线与突发波动研究；随后明确授权DataHub将两指数3秒离线导出扩展至2025年底。
- 本地核心：FactorLab主仓保存资料库与研究记录，STAR50本地仓保存专题代码/成果，DataHub保存权威数据父层。其他主题仓库不修改。
- 当前入口：[完整交接说明](../handoff/cloud_risk_gate_20260907/HANDOFF.md)。
- 本地已执行：资料归档，父源与导出完整性检查，公开/用户提供PDF身份核验，研究包验证与测试；具体结果看包manifest与handoff receipts。
- 云端已复核：**尚未发生**。包上传与本地测试不代表云端复验。
- 云端下一步：先验证包与阅读研究协议/文献，不自动执行历史账户或训练，不打开2026。新研究协议、运行证据与成果写入新版本并回传commit及清单。
- 缺数据流程：只列目标问题所需最小字段、标的、时间范围、消费者语义及输出验收；不默认搬全部本地数据，不将缺订单簿数据误说成已具备OFI或撤单强度。
- 执行位置：云端会话能直接执行则自己执行；确缺输入/能力时写本表请求本地；Actions不是默认计算场所。未经用户授权，不联系第三方、不改生产。
- 回迁：本地fetch指定commit，逐文件hash、时间/单位/权限、测试和科学结论复核后才接受；大型父数据仍留本地，禁止静默覆盖固定历史证据。

## CL-HIGHVOL-ROUTER-EXEC-20260909

- 背景：HighVol Router V1 已在指数身份 `000852.SH` 上完成 Development 104 笔与 reusable Validation 129 笔，Validation pooled net@1bp/leg `+0.546255 bp/trade`、one-way BE `1.273128 bp`；随后固定 stability audit 显示1.5bp/leg即转负、day-block bootstrap跨0、去最强3个正收益日后转负。`production_authority=false`，BlackBox查询数0。
- 云端已核查：当前STAR50仓 `data/market` 与 cross-index 包均为指数点位，不是tradable fills；handoff数据合同明确无新增ETF/期权/期货原始行情。`factorlab-trend-reversion-regime-lab`复用的仍是000688/000852指数1m/5m。`factorlab-overnight-open-lab`的ETF包仅为ASHS/ASHR/FXI/MCHI/SPY日线辅助变量，不是中证1000国内执行载体。现有云端证据不足以估计真实点差/滑点/成交价。
- 执行成本硬约束：若真实载体收益与指数路径近似，当前指数gross只容许平均总单边成本约`1.273128 bp/leg`；相对原抽象1bp/leg假设，仅剩`0.273128 bp/leg`余量，即额外round-trip损耗约`0.546255 bp/trade`即可吃掉pooled edge。这不是对真实载体成本的估计，只是待验收的break-even预算。
- 本地/DataHub最小请求：寻找**可实际交易的中证1000跟踪载体**，优先能覆盖2021-01-01至2026-08-21的国内ETF；若不存在完整覆盖，返回候选清单、上市日和实际可用区间，不静默拼接。IM股指期货可作为2022上市后的独立次级执行车道，但不得伪造2021覆盖。
- 载体选择必须与Router收益无关：先按产品身份、覆盖完整性、数据质量及Development期可观察流动性指标冻结primary carrier，再打开其Validation执行结果；不得按Router PnL挑ETF/合约。
- 最小行情字段：本地交易所墙钟timestamp/交易日、bid1/ask1及对应size（若权威源可得）、逐笔/快照last或首笔成交价、成交量/成交额、交易状态/停牌/异常标记；如只有OHLC而无L1，必须标记为insufficient_for_spread_slippage，不冒充真实fill。
- ETF附加字段：复权/拆分/分红或明确不复权原价规则、最小价位、最小交易单位、申赎/交易状态；提供可审计的佣金/经手费等费用假设来源。若使用期货：合约代码、到期日、乘数、tick、保证金仅作容量信息、交易手续费、主力/合约选择规则和日内bid/ask；3分钟持有不得用事后连续合约价替代可交易合约。
- 时间语义：Router信号继续来自已冻结指数，entry=`next minute open`、exit=`open exactly 3 minutes later`。载体执行需要定义为相应时间点**首个因果可见、可成交的quote/trade**，并同时报告index-to-carrier tracking return与marketable-fill return；不得用分钟OHLC最优价。
- 数据角色：Development载体数据仅用于选择/校验执行映射和冻结费用/撮合语义；Validation载体数据只在执行映射冻结后原样评估；2026只到2026-08-21。post-2026-08-21继续属于BlackBox，禁止为本请求读取。
- 回传验收：manifest须列每个文件SHA256、symbol、venue、frequency、first/last day、行数、字段schema、source identity、consumer authorization；同时给coverage/gap报告。优先回传小型有界执行包，不搬无关全市场数据。
- 云端收到数据后的固定输出：每笔index gross、carrier mid/last tracking gross、marketable fill gross、费用、all-in net；按Development/Validation分别报告trade count、mean/median、BE、cost decomposition、unfillable/missing比例、年度切片和day-block bootstrap。此步骤不得改变Router V1 selector、hold、route或日期。

## CL-STAR50-TRUE-RECEPTION-RAW-20260912

- 任务：按云端要求检索 `000688.SH` / `000852.SH` 带真实本地接收时间的原始行情；只做只读查找、最小导出与打包，不跑 V19/D2–D5、不改 DataHub/FactorLab 科学代码。
- 本地结论：`NO_TRUE_RECEPTION_TIMESTAMP_AVAILABLE`。DataHub `recording_datasets`/`recording_runtime`/`subscriptions` 均为 0 行，`lake/recording` 与 `ticks.parquet` 不存在。未伪造 `received_at`。
- 交付包（无行情行）：[docs/ops/receipts/star50_true_reception_raw_20260912/](receipts/star50_true_reception_raw_20260912/)
- ZIP：`docs/ops/receipts/star50_true_reception_raw_20260912/STAR50_TRUE_RECEPTION_RAW_20260912.zip`
- ZIP SHA256：`63badecf70405452674831f41a6aef0de174ca8d10b113fc32c91a8e1ca24cf0`
- ZIP 大小：5446 bytes
- 云端待复核：本包只证明本地没有逐笔 reception clock；不是风险状态或 consumer 结论。

## CL-STAR50-DATAHUB-RAW-CALLBACK-SAMPLE-20260912

- 任务：云端要求本地提取 parser 之前的真实 raw payload，供 DataHub adapter / prospective recorder 使用；不跑 V19/D2–D5、不装 recorder、不改 DataHub、不做延迟分析。
- 本地结论：`CALLBACK_RAW_NOT_PERSISTED`。实际交付级别为 `NORMALIZED_SOURCE_ROWS`（`market_index_transactions` lake 行）。2025 vendor ZIP/CSV 原字节入库后已删除，当前百度账号无 `/A股数据_分笔成交_指数/`。未伪造 `received_at`。
- vendor/source：`baidu_netdisk_market_index_transaction_3s`；原字段 `时间,价位,成交额`；成员 `000688.csv` / `000852.csv`。
- 日期与行数：`2025-06-11`；`000688.SH` 4746 行；`000852.SH` 4746 行。
- 交付包：[docs/ops/receipts/star50_datahub_raw_callback_sample_20260912/](receipts/star50_datahub_raw_callback_sample_20260912/)
- ZIP：`docs/ops/receipts/star50_datahub_raw_callback_sample_20260912/STAR50_DATAHUB_RAW_CALLBACK_SAMPLE_20260912.zip`
- ZIP SHA256：`866824b8966b237ed8463afd6280186301db95c450876112da77787d5d50fa0d`
- ZIP 大小：328518 bytes
- 云端待复核：本包只提供接口格式与 parser 源码副本；不是研究样本、风险状态或 consumer 结论。
