# 接续入口：D5本仓消费链已通过，外部研究接入待真实回执

当前状态D5_BOUNDED_RESEARCH_CONSUMER_ACCEPTED_EXTERNAL_INTEGRATION_PENDING。不要重做D5，不重拟合V19或把D4旧“D5未启动”当作当前状态。
先读AGENTS.md、CURRENT_RESEARCH.md、docs/research/CAUSAL_KLINE_STATE_NEXT_PHASE_20260911.md，再读research/state_degree_consumer_d5/的PROGRAM_STATE.json、RESULTS.md、EXECUTION_RECEIPT.json、PROTOCOL.md、SOURCE_IDENTITY.json和INDEPENDENT_VERIFICATION.json。

## 已完成

232704条双时钟事件与116352条E15增强完整接入；零源字段/增强数值差异；930816次as-of边界检查与独立选择器一致；20个历史前缀、40项单元测试和两个样例命令通过。完全在本会话执行，无新行情、拟合或Actions。

```bash
python scripts/validate_data_usage_policy.py
python -m unittest discover -s research/state_degree_consumer_d5 -p 'test_*.py' -v
```

样例查询、零/2秒合成延迟、独立账本验收的完整可运行命令见research/state_degree_consumer_d5/REPRODUCE.md。仅需要原D2/D4封存ZIP，不需新数据；完整D5证据包提供输入副本。不要为了浏览结果重跑统计模型。

## 下一实际动作

任务CL-D5-RESEARCH-CONSUMER-20260912见research/state_degree_consumer_d5/LOCAL_HANDOFF.md：由真实本地研究进程验收，回传环境、提交/输入身份、命令、退出码与比对结果。无本地执行通道时只保留待回执，不声称已经派发或执行。不接生产registry。

E15增强不可填到CLOSE；缺D4数据只可标STATE_ONLY；UNAVAILABLE/NO_CURRENT_SNAPSHOT不是NORMAL。源发布和消费者收到分开，过期不回退，迟到不回填。CSV按Asia/Shanghai解释；不交付训练分位门控；旧观察及原概率目标不隐藏或改名。

D3未晋升、D4有限分目标支持、V19/D2冻结基线不改。D5不是新统计效用证据或经济验收。不自动启动D6/V20，原封存代码和治理不变，无2026/BlackBox/PnL/生产权限。production_authority=false。
