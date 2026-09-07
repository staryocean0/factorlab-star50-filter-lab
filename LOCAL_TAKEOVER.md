# 科创50本地接续入口（2026-09-06）

最新进展：[第五轮结果](docs/research/streak_mechanism_v1/report.md)已完成并独立通过本轮来源/数值校验。连败不异常，后验频段规律主要关联每笔收益；无新策略。以下为第一阶段历史接管说明，旧第四轮哈希缺口仍保留。

当前本地控制者为Codex。第一阶段只完成原包增量回迁、进度梳理与重复核验，没有启动新研究或修改远端。

完整交接报告：[FactorLab第一阶段报告](</home/starryocean/桌面/量化/baylum terminal 0.4.1/factor_lab/docs/user/star50_local_takeover_v1_report.md>)。

云端来源：`research/drawdown-conditions-20260905@4f9f01c69353e8e9ea15db341e39c967e5873359`，原包/main为`bdbcf7dc2f613100ea7ceeb6968ab7fc2b5c9df9`。本地分支为`local/takeover-20260906`，研究已推进至第四轮。最初`/tmp/factorlab-star50-filter-lab`原样保留；此处是独立持久副本，不依赖原目录的Git对象。

接续顺序：本页 → `CURRENT_RESEARCH.md` → `docs/research/cross_scale_root_cause/report.md` → 第四轮白皮书/协议 → 本次来源缺口。`CONTINUE_HERE.md`是第二轮封存依赖，内容较旧，不修改。

本地完整pytest为54通过；前三轮封存验证通过。第四轮99个封存文件、5年度链、58,176根原策略路径和两组80项统计关系可复核，原持仓与损益零差异。但第四轮严格验证器失败：协议绑定的`filters.py`与`backtest.py`哈希不等于已提交字节，且对应旧字节不在已取得的Git历史中。不得把独立数值复现冒充来源闭合，也不得覆盖旧manifest。后续缺口：`bd://fl-mmbk4`（在FactorLab根运行bd）。

原研究结果维持研究材料身份。2020预热；2021—2025已消费；2026不得参与新属性发现或选参。原包虽含2026存档，但本地重复行情核验使用`artifacts/drawdown_material/`中截至2025的14份载体。`available_at`仍是用户澄清的历史可获取时间，不是盘中延迟。固定5分钟满仓原策略，不能用降仓替代回撤根因；无生产授权。

环境无需重新安装；从此目录执行：

```bash
'/home/starryocean/桌面/量化/baylum terminal 0.4.1/factor_lab/.venv/bin/python' -m pytest -q
```

第四轮原验证器当前会忠实报告源码哈希失败。完整日志、源码事件及独立数值审计见[本地证据目录](</home/starryocean/桌面/量化/baylum terminal 0.4.1/factor_lab/docs/ops/evidence/star50_local_takeover_v1_20260906>)。不要重跑旧年度seal、覆盖旧研究产物，或自动触发新的研究/云端执行。
