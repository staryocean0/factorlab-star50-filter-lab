# D5 执行与复核

依赖仅 Python 标准库（建议3.11及以上，系统须提供 Asia/Shanghai 时区数据库）。不需 numpy/pandas/Parquet、网络、凭据或原始行情。以下从仓库根目录执行；把 INPUT_DIR 设置为含两个原封存 ZIP 的目录。完整 D5 证据包 inputs/ 也保留这两个 ZIP。

```bash
export INPUT_DIR=/path/to/evidence/inputs
export D2="$INPUT_DIR/d2_causal_state_replay_34620317766.zip"
export D4="$INPUT_DIR/D4_continuous_risk_utility_evidence.zip"
python -m unittest discover -s research/state_degree_consumer_d5 -p 'test_*.py' -v
python scripts/validate_data_usage_policy.py
```

查看既有结果不需重放。独立检查已经解压的 results/：

```bash
python research/state_degree_consumer_d5/verify_acceptance.py --d2-zip "$D2" --d4-zip "$D4" --out /path/to/evidence/results --report /tmp/d5_verification.json
```

真实可执行样例（没有交易动作）：

```bash
python research/state_degree_consumer_d5/example_consumer.py --d2-zip "$D2" --d4-zip "$D4" --symbol 000688.SH --as-of 2024-01-02T10:00:00+08:00
python research/state_degree_consumer_d5/example_consumer.py --d2-zip "$D2" --d4-zip "$D4" --symbol 000688.SH --as-of 2024-01-02T10:00:00+08:00 --receipt-delay-seconds 2
```

结果分别为 AVAILABLE/CLOSE 与 NO_CURRENT_SNAPSHOT/LATEST_EVENT_EXPIRED。延迟参数是合成检查，不是行情延迟估计。样例只消费指定当日已发布且已收到的封存快照，不初始化或运行价格引擎。

只有要独立复现工程导出时才运行，输出目录必须尚不存在：

```bash
python research/state_degree_consumer_d5/run_acceptance.py --d2-zip "$D2" --d4-zip "$D4" --out /tmp/d5_new_replay
```

全部结果需连同 INPUT_VERIFICATION、OUTPUT_MANIFEST、INDEPENDENT_VERIFICATION、测试/执行日志与代码身份复核。输入 ZIP 的精确 SHA256 在协议及 runner 中固定。重复运行不构成新统计 Validation，不重跑旧模型。未运行完整仓库 suite 或实际外部接入，production_authority=false。
