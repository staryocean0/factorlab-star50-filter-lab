# D4复核与复现

优先核对结果，不为查看报告重跑统计。源仓保留PROTOCOL.md，冻结commit ef865110aee6c1c3b300d27c38a578c2b8882a67；本轮先冻结再评分的回执在643671b7ca6bf0e7a0c3a975a383c8029a8ee92d。旧D3 runner只读依赖，Git blob ea9f77bedd0b952385917015ef080800bfa596ba。

完整D4会话证据包包含results_d4/、执行代码、旧D3输入包与SHA清单。不是Actions统计artifact。旧D3包里inputs/包含D2原ZIP与5m CSV转运ZIP。解包到独立工作区，勿覆盖原冻结结果。运行环境Python3.13.5、numpy2.3.5、pandas2.2.3；依赖版本不同的复现不能冒称字节完全一致。

```bash
python -m unittest discover -s research/continuous_risk_utility_d4 -p 'test_*.py' -v
python research/continuous_risk_utility_d4/verify_d4.py --transport /path/to/d3_input_transport_34623937960.zip --out results_d4
python research/continuous_risk_utility_d4/check_prefix.py --transport /path/to/d3_input_transport_34623937960.zip --out prefix_recheck.json
python scripts/validate_data_usage_policy.py
```

完整重算必须使用新输出目录，不覆盖冻结models。固定输入：--d3-bundle为旧D3_risk_bucket_utility_evidence.zip，--transport为上面无损CSV包，--ledger为d2_causal_state_replay_34620317766.zip，--out为新目录；依次运行run_d4.py --phase fit和--phase evaluate。复验不是新OOS，不重新选择参数。本轮正式模型SHA256为30edb34a68bd7b6010f57128177d5500558b7af1803cc8b279abeb9df80ddd18，完整SUMMARY SHA256为3ff0333f4faea571c58d328d7f056f05afa5dc5ee60a6d6bdb74c1a26ff1c345。

causal_attributes.csv.gz与ATTRIBUTE_METADATA.json属于研究消费者数据面；validation_predictions_*是独立评价面，不能混入在线输入。分位配置不是在2021年已知的配置；完整仓库、外部消费者、实时feed、策略收益和生产权限均未验收。
