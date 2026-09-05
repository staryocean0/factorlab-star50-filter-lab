# 数据和执行验收操作说明

当前入口为根目录`CURRENT_RESEARCH.md`，研究合同为`preregistration.json`，解释见`whitepaper.md`，结果见`report.md`。旧`CONTINUE_HERE.md`也被第二轮哈希封存，保持不变。这是前两轮的基础设施后续，不是新策略分支。原始导出以及前两轮封存的代码、图和账户不能覆盖。

## 已消费订单的单年审阅

```bash
python scripts/audit_market_admission.py --year 2021
```

这条命令只读取指定年份封存订单、时间网格和边界元数据，不加载价格、收益或重算信号。主审阅者检查该年`first_counterexample.svg`、`requests.csv.gz`、`summary.json`，手写`analysis.json`，再运行：

```bash
python scripts/audit_market_admission.py --seal 2021
```

之后才可打开下一自然年；禁止用循环代替人工逐年审阅。现有五份回执已经封存，重跑会拒绝覆盖。只需验证：

```bash
python scripts/audit_market_admission.py --validate
python -m pytest -q tests/test_market_admission.py
python scripts/validate_drawdown_study.py
python scripts/finalize_execution_audit.py --validate-only
```

库存验证从封存初始状态逐个重放请求，核对买卖、锁定、跨年连续性及文件哈希。`market-admission.yml`在GitHub执行这些检查。

## 数据到货后的验收

先按`data_request.json`索取已有授权数据中的原始证据，不购买、不发信、不把当前下载时间写成历史接收时间。尚未获得实际外部数据，也没有可用的专用上游API或凭据。

交付目录使用`manifest.json`，至少包括以下字段：

| 字段 | 内容 |
|---|---|
| schema | `star50_external_market_bundle@1` |
| files | 相对路径到SHA256的映射；原始证据和规范化文件分别保存 |
| revision_policy | `append_only_first_and_corrections` |
| clock_basis | `source_sent_at`或`received_at`，不能混称 |
| bar_versions_file | 哈希绑定的JSONL规范化文件 |
| generator_evidence_file | 源端生成代码/版本/获取说明 |
| clock_semantics_file | 时区、首发/发送/接收/入库/修订的语义说明 |
| coverage_file | 按证券、日期、字段记录实际覆盖与缺失；附完整预热bar菜单 |

每行bar版本至少包含`symbol`、`bar_end`、`version_id`、布尔`is_first`、`source_kind=observed`、`price_view=raw`、正数`close`、所选时钟以及`evidence_ref`/`evidence_sha256`。时间均为真实含时区的时刻；旧载体墙钟Z不自动套用此合同。此规范化文件只是信号值版本证据，完整OHLCV仍按取数清单交付。新数据必须进入独立目录，不改旧文件。

```bash
python scripts/audit_market_admission.py --inspect-bundle /absolute/path/to/delivered_bundle
```

格式通过后仍须审阅生成代码、原始载体、时钟和修订真实性；程序始终不自动授予盘中策略准入。将`coverage_file`的完整bar菜单交给`asof_prefix`才能检查决策时的递归前缀，不能仅验当前一行。

下一阶段还需验证真实ETF数据/盘口和历史费用、库存资金约束。`visible_quote`只选订单到达前最新收到的原始报价，遇停牌/过期/无量不会退回较早的好报价；它不假定限价单已成交，不处理排队冲击。报价最大年龄、下单时延和成交模式应在正式重放前预注册，此处没有按收益校准。

实盘没有准入，2026没有选参权限。若未来考虑期权或借券，先补齐相应资料并重建完整政策账户，再遵循切片Skill；本轮产品列表不是候选排名。
