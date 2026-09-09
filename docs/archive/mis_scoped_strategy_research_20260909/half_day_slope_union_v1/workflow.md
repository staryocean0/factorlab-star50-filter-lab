# 科创50半日低通斜率并集：原型工作流

先读[白皮书](whitepaper.md)、[机器合同](contract.json)及[线程接管记录](handoff.md)。该版本仍属于原科创50半日低通策略，在Layer 3为外部策略研究原型。参数未按收益择优。

从本仓库根目录运行（本机可使用FactorLab `.venv/bin/python`，其中已经具备numpy、pandas、scipy、pyarrow、pytest）：

```bash
python -m pytest -q tests/test_slope_union.py
python scripts/run_half_day_slope_union_v1.py --output artifacts/half_day_slope_union_v1
python scripts/run_half_day_slope_union_v1.py --output artifacts/half_day_slope_union_v1_replay
```

执行器只生成固定种子的合成序列，不读行情；已有输出目录会报错，禁止覆盖旧收据。比较两目录的thresholds.csv、synthetic_signals.parquet、receipt.json应字节相同。收据绑定源码/白皮书/合同/测试和运行版本。10万次已知σ高斯五维联合抽样只检验推导基准，不能解释为真实交易错误率。

调用实现：

```python
from star50_filter.slope_union import SlopeUnionConfig, build_signals
cfg = SlopeUnionConfig()  # 120min, 240收益波动窗，1..5min并集
signals = build_signals(native_bars, cfg)
```

native_bars含timestamp（带时区）、trading_minute（连续交易分钟序号）、close。API输出 `target_at_close` 是t收盘决策，`prior_target`仅为上个决策目标。最早执行在下一可交易开盘；缺bar拒绝输入，不自动压缩缺口，调用方须验证DataHub日历和源序号。完整重放从同一初始点开始，不能每年/每块重新初始化后伪称连续策略。上游历史获取时间不替代真实bar闭合时钟。

每个窗口返回 `slope_h`、`entry_threshold_h`、`exit_threshold_h`。四种 `*_mask` 的bit 0..4记录各窗口过门；ready=false时无新信号，输出保留原因。读取最后一根目标不能当成已成交。

下一轮优化前在新实验身份下冻结候选预算、比较对象、发展年份和费用/账户口径。按本主题已授权2021—2025逐年读取和审阅，2026不参与候选排名；样本不足就报告，不补造2009—2020科创50。初期分别研究整体α、曲线p和入出场非对称，不同时暴力搜索所有参数。真实载体必须接Layer 4和完整账户审计，原型验证不作策略经济晋升。
