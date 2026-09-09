# V2运行与查看工作流

当前优先读[结果](result.md)、[原始方法](whitepaper.md)和[选择规则修订](selection_amendment.md)。当前参数以 `artifacts/half_day_slope_union_v2/2023/review.json` 的selected_config为准，2024和2025的review只延续该身份。

实现：`src/star50_filter/slope_union_v2.py`；`Policy`封装六个参数，`features`构建固定120分钟低通/斜率/过去波动，`targets`生成收盘目标，`account`执行年度隔离的指数方向模拟。完整账户与历史目标仅用于研究。

```bash
python -m pytest -q
python scripts/research_slope_union_v2.py freeze
python scripts/research_slope_union_v2.py blind --year 2021
```

主控实际阅读blind的metrics/trades，写 `2021/blind_review.json`，再单独执行：

```bash
python scripts/research_slope_union_v2.py family --year 2021
python scripts/research_slope_union_v2.py rank --year 2021
```

主控审阅结果，写selected_config与evidence_hashes的年度review；2022和2023分别按这一流程推进，不能用shell循环生成年度解读。2023冻结最终参数后，2024/2025只运行blind并分别审阅，不运行family或rank。

已有freeze和年度输出不可覆盖。以上命令是过程说明；本次已完成的工件无需重复生成。要全量重放应使用独立checkout与空输出目录，并逐个年度核验；原封存代码/合同仍保持原字节。开发后的选择修订作为独立附录，不覆盖旧100笔规则的ranking文件。

最终报告命令 `python scripts/report_slope_union_v2.py` 会独立检查冻结目标与原始V1、生成完整账户快照、现金份额对账，并渲染HTML/PNG；它同样拒绝覆盖已有final目录。重复查看直接打开HTML，后续统计优先只读取冻结快照/逐笔/日账。

[完整报告](../../../artifacts/half_day_slope_union_v2/final/report.html)包含0/2/4/7bp成本表、年度均值、夏普、收益、MDD及2021—2025的一分钟交易图。可按日期、交易编号定位，滚轮缩放；开仓/平仓连接到上层原始K线。图中买卖方向包含空头开平仓，不能误读为纯做多。

本机Python可用 `/home/starryocean/桌面/量化/baylum terminal 0.4.1/factor_lab/.venv/bin/python`。资源wrapper为FactorLab `scripts/run_research_job.py`，本次三年telemetry在 `artifacts/half_day_slope_union_v2/resource_2021` 等目录。依赖FactorLab数据时钟配对模块，未独立安装者需保留相邻工作区路径。
