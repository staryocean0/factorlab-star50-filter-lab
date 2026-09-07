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

---

## CL-STAR-RISK-20260907 / FIRST-SHOCK-V1（云端执行追加，2026-09-07）

- 用户本轮授权：继续检验共同波动环境之外的跨尺度异常能否提前区分普通时段首冲击；不恢复交易或账户。
- 代码分支：`research/first-shock-gate-20260907`，基线`8a07c422593c66e3d5669ebfd5b83586e1609411`。新增入口：`docs/research/first_shock_gate_v1/README.md`。本地应绑定本分支实际提交，核对源SHA；不要把后续main变化当作本轮输入。
- 云端已执行：46项新增工程测试；原始合并尺度正／负合成控制；保留原失败结论后的分尺度诊断（3种子×2场景）；随机告警反例；逐案例汇总一致性与恢复后七份JSON字节一致性检查。全部为合成／工程证据，不是两指数市场验证；不是仓库全量pytest或全包验收。
- 新发现：先平均高频尺度会丢失某些尺度重分配；分尺度合成正对照改善Clean桶内风险，但告警段精确率下降。随机20%时点告警也能得到94.93%的合成首事件召回，因此不单用召回晋级。数值和限制见新增报告及`artifacts/engineering_summary.json`。
- 当前阻断：本会话直接下载已授权私有行情遇到DNS／连接失败，pyarrow安装也失败；未获得可执行的完整行情挂载。不是仓库缺数据。没有运行市场实证，没有开启2026，没有自动派发本地模型，没有启动Actions。

### 本地最小执行请求

1. 先复用已有适用验收回执；必要时在保留的基线版本校验旧交接包。不要修改旧freeze／manifest的hash来让新增文档通过历史校验。新增工件独立验收。
2. 在本研究分支或精确回迁后的文件树运行新增测试；确认依赖与源SHA。市场入口已实现，但尚未接受真实DataHub数据适配验收。
3. 只读现有`data/cross_index_risk_gate_v1`中两指数2021—2025原生1分钟及质量字段，使用仓库有界loader。无需新导出2026、ETF、期权或全部父源；无需订单簿数据。
4. 执行：

```bash
D=docs/research/first_shock_gate_v1
python -m pytest -q "$D/tests"
python "$D/code/run_split_market.py" --repo-root . --out artifacts/first_shock_v1_market_local_01
```

5. 回传：实际commit、命令／退出码、`market_run_receipt.json`、8份年度／模型summary、唯一事件表、最小失败或适配说明；必要时给少量指定事件的核验切片。大型行情、逐分钟预测和模型文件留本地。
6. 验收：同日／同会话／共同质量支持，保留缺失／修复导致的Unknown；标签起于未来，首项／后续分离，告警至少早于冲击分钟起点1分钟；2021—2022拟合、2023校准、2024与2025固定评价，全部consumed development。冻结阈值与评价期相同覆盖曲线必须分别报告。不能仅因合成结果或包校验通过宣称有效。

### 尚未完成与复核口径

- 本地市场执行：待用户安排，本会话没有自动执行通道。
- 云端市场复核：尚未发生；收到实际回执后才能记录复核范围，不能把本地反馈称为云端全量重放。
- 完整3秒／15秒市场实验、单指数质量支持敏感性、完整季节匹配随机参照与非重叠相位尚未运行。秒级辅助函数测试通过不等于其真实市场效果通过。
- 主分支、旧策略和生产注册表不改；新研究先留独立分支，发布提交使用`[skip ci]`。

---

## CL-STAR-RISK-20260907 / FIRST-SHOCK-V1 / ACTIONS-RESULT（最新，2026-09-07）

**本节更新前述待执行状态；历史记录保留，不再要求本地完成同一轮首次实证。**

- 最新用户指令：仓库已改public；直接访问再失败，允许Actions。GitHub接口确认public，会话终端文本／行情下载仍DNS失败。已据明确授权在独立执行分支使用Actions。
- 实际执行：运行34091320590，工作流提交`ed6ad5e86fdd76a891aedabd3ebdf3752c4d3e45`，冻结研究代码`b725544ff8fef9688877c6c7e1fd4d19081ea75c`。10个2021—2025分钟分区，2指数各290880行，46项新增测试通过，8份年度／候选结果全部产出；所有步骤成功。没有修改main或旧研究代码，没有读取2026或执行交易。
- 报告入口：`docs/research/first_shock_actions_v1/RESULTS.md`；结构化结果`results.json`；执行和产物定位`evidence_index.json`。结果归档到原研究分支，执行分支不合并main。
- 云端已复核范围：在本会话下载30,003字节小型artifact，核对artifact SHA、24个输出文件SHA、32个事件表汇总单元及严格提前量。不是本会话原始行情全量重放，不是用户本地科学验收。
- 科学结论：合并与分尺度候选的全部8个年度／候选Clean风险差异区间均包含0；分尺度科创502025风险点估计反而升高。有限事件样本不支持稳定增量风险门控，不晋级；完整秒级和随机参照仍未执行。
- 本地现在只需回迁归档并进行自己的必要验收，不默认重跑已经有适用证据的整轮计算。小型artifact 10006954915于2026-09-21到期；完整预测／模型artifact 10006956259于2026-09-14到期。大型原始行情仍留本地；不要求新导出全量父源。
- 存储边界：用户公开设置只改变仓库可见性，不扩大数据时间／用途／生产权；旧private-only文档和manifest保持历史原样。本次新增结果独立版本化，不通过篡改旧hash制造验收。

---

## CL-STAR-RISK-20260907 / FIRST-SHOCK-SECONDS-V2 / REVIEWED（最新，2026-09-07）

**秒级V2已执行并完成限定范围复核，不再停留在public访问或等待本地首次运行。**

完整交接见[本轮执行闭合与回迁](first_shock_seconds_v2_closeout_20260907.md)，报告见[秒级实证与独立输出复核](../research/first_shock_seconds_v2/RESULTS_REVIEWED.md)。主Actions34094586286、独立账本修正34094969260均成功；冻结模型不重调。20个2021—2025分区，秒级10265397行、分钟581760行；71项主测试及2项账本修正测试通过。

当前会话取回全部三份ZIP，核验63份清单文件；从导出特征／估计器重放349200行决定、936行事件表、356完整路径及全部相位和六组区块区间。不是重新训练或原始Parquet的全量再计算。2021无满足规则的秒级特征决定点；科创50实际2022训练58个重叠正窗口，中证1000三种支持均只有14个、未过冻结门槛，未拟合。科创50B2-B1差异区间仍含零，不晋级，不据此否定所有跨尺度方法。

本地只需按新review/evidence_index.json归档三份ZIP并做自己的必要验收，不重复启动已有证据的整轮计算。完整重放artifact10008242216于2026-09-14到期；主小证据10008240326及账本10008304105于2026-09-21到期。未修改main、旧freeze、2026输入或生产；下一轮采样支持／端点语义与标签问题单独登记。

---

## CL-STAR-RISK-20260907 / POST-SHOCK-RECOVERY-2026（本地已反馈，等待云端复核）

- 任务：按 `docs/ops/post_shock_recovery_2026_data_request.md` 导出科创50/中证1000 的 2026 年 1 分钟与 3 秒，并推到本主题仓 `research/post-shock-recovery-2026-validation`。
- 代码分支/提交：本反馈写入同一分支；推送后的 commit 以 git log 为准，基线请求提交为 `ba549e1e6b`。
- 执行地点：本地 DataHub 父层切片，不是 Actions，不是云端重算。
- 命令与退出码：`python3 scripts/export_post_shock_recovery_2026.py` 退出码 0。随后对父层做独立 DuckDB 对照，1m close/质量字段与 3s price 的 parent-child mismatch 均为 0。
- 实际数据范围：`2026-01-05` 至 `2026-08-21`，两指数各 154 个完整交易日。请求上界是最新完整交易日、最多 `2026-09-07`；同语义父层只到 `2026-08-21`。未拼接 TDX 重建的 `2026-08-24/25`，未伪造 8 月 22 日之后的行情。
- 身份摘要：
  - 1m 父层 `factorlab_unified_index_kline_v3_20260824` / `1m_official.parquet` SHA256 `aeacff04b268c166faac333ec7ab9d840abcd347d82cb3bcee0218d058fc7423`，dataset `bars_cn_index_1m_raw_canonical_market_index_baidu_3s_20000714_20260821_factorlab_unified_missing_day_repaired_v8_20260824`。
  - 3s 父层 `market_index_baidu_3s_20000714_20260821_cffex_underlyings_alias_repaired_v4_20260823` SHA256 `a2abc93ef0975490aae73c606ca8157a15c44cd182626c7537a9a62494310540`。
- 产物（独立新包，未改 2021-2025 封存 manifest）：
  - `data/cross_index_risk_gate_2026_v1/1m/000688.SH/2026.parquet` 36960 行，SHA256 `b7e7e9a9e85b738d661583dcd3d7dab158562fddac4355362cc37597db21eca4`
  - `data/cross_index_risk_gate_2026_v1/1m/000852.SH/2026.parquet` 36960 行，SHA256 `60b2054d2055bef8010a9948a0589bc1c4b0bb18dd6f373a9366f97e689fdf87`
  - `data/cross_index_risk_gate_2026_3s_v1/000688.SH_2026.parquet` 730261 行，SHA256 `2b791b8e977a77a97b30854e441ef88fca8be43f96ffff0d97e825bb3e74bc96`，同秒额外源顺序行 14
  - `data/cross_index_risk_gate_2026_3s_v1/000852.SH_2026.parquet` 730395 行，SHA256 `59c960a7d8d585b5d312d9952dd4f54e3f9e16807f5e43fc15c2fa0f45a5caca`，同秒额外源顺序行 46
  - 汇总 receipt：`docs/ops/evidence/post_shock_recovery_2026_export_v1/receipt.json`
- 时区：源字符串 Z 仍是上海墙钟，按前 19 字符 localize Asia/Shanghai。
- 未执行：2026 首跳事件、风险衰减、KM、恢复分数、release/3s 模型回放、交易回测、参数搜索。旧 `load_market_data` 仍拒绝 2026，以免污染 2021-2025 loader。
- 云端复核：**尚未发生**。本地切片与 hash 对照不是云端独立全量复验。
- 云端下一步：按 receipt 验收 SHA/行数/时区/质量字段后，用冻结定义跑 2026 held-out 验证；覆盖只报到 `2026-08-21`。
