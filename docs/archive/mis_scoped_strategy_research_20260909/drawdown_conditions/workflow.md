# 本轮执行与复核

结论见 [report.md](report.md)。工作主图5m+0；基线保持P12/order1/k1。两个诊断反事实不获策略升级权限。

安装项目依赖后运行：

```bash
python scripts/validate_theme_package.py
python -m pytest -q
python scripts/validate_drawdown_study.py
```

最后一步只从封存账本/回执复核哈希、边界和会计恒等式，不重跑策略，不依赖实验是否有赢家。完整原数据位于仓库；接管时通过只读Actions导出2020—2025载体，原数据与导出文件的SHA256对照保存在input_material_receipt.json。导出run33980179951及固定代码提交980015146a44363fe25ad836b0b85890c6f837fa证明来源。

全新复现实验应在单独输出工作副本进行；保留本轮封存产物，不覆盖已有receipt：

```bash
python scripts/reproduce_historical_baseline.py --data-dir data/development
python scripts/run_drawdown_study.py --data-dir data/development describe
python scripts/run_drawdown_study.py --data-dir data/development year --year 2021
```

随后必须由主研究者检查一个年度的结果、具体事件和图，手工填写该年的analysis_ledger.json，才可运行对应seal命令并打开下一年。这里**不提供自动串行跑完五年并生成科学结论的脚本**。本轮已存在的sealed_receipt会阻止覆盖。所有年份使用同一冻结规则；年度仅为审阅边界，不是运行时因子。

原切片Skill中的2009—2020/Koopman/FactorLab外部脚本属于其他项目，未复制来伪造合规。本轮依据用户及本仓库明确的2021—2025边界，完成五个已消费年度的固定诊断实验；不是原十二年隔离重建、不是盲测，也未宣称通过原SSA/A0—A7实盘账户流程。缺失的真实可得性与执行映射明确阻断升级。

以下命令只汇总已封存结果：

```bash
python scripts/finalize_drawdown_evidence.py
python -m pip install 'matplotlib>=3.10,<4'
python scripts/build_drawdown_figures.py
```

PNG用于本地视觉检查，SVG为仓库图件。overview中的日MDD不可替代五年指标中的bar级MDD。年度matched_constant仓位不同，不能把它们拼接后冒称全期固定83.11%对照；全期对照见2025 cumulative表。

计算为约6万根bar、两个固定条件的轻量诊断。保留矢量化一次性特征，不属于反复大规模训练负载；未引入GPU端口或神经模型。
