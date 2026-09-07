# 第五轮本地工作流

本轮已执行完毕。日常复核使用`validate`，不要重跑`freeze/prepare/year/seal/analyze`覆盖封存目录。

Python解释器：`/home/starryocean/桌面/量化/baylum terminal 0.4.1/factor_lab/.venv/bin/python`；工作目录为本主题仓库。依赖继承已核验本机环境，不再安装或触发GitHub Actions。

```bash
python -m pytest -q
python scripts/run_streak_mechanism_v1.py validate
python scripts/seal_streak_mechanism_v1.py --verify
```

首次执行顺序为：合成测试 → `freeze`冻结来源/输入/方法 → `prepare`物化五偏移固定账户 → 每次单独`year --year YYYY` → 主控阅读该年表图和反例 → 主控写review → `seal --year YYYY --review /absolute/path/review.json` → 下一年度。五年全部封存后才`analyze`与`validate`。年度解释不由脚本批量生成。

`prepare/analyze/validate`已用FactorLab `run_research_job.py --profile cpu-light --workers auto`运行。实际机械耗时约10.36/6.26/12.41秒，单worker，最高观测RSS约0.51GiB。没有神经训练或需要常驻GPU的重复大矩阵任务。

`render_streak_mechanism_v1.py`仅从已有结果生成汇总图与条件分母/例子，不改变假说或产生新的统计检验。`seal_streak_mechanism_v1.py`绑定本轮文件清单并禁止重复覆盖；后续只使用`--verify`。

两个源码哈希缺口仍仅属于第四轮的历史绑定；第五轮明确从Git原包实际源码重建自己的证据链。不要修改旧manifest以伪造历史通过，也不要把本轮当成新的样本外验证。
