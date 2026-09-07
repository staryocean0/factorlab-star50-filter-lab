# 结果前输入类型修复

首轮准备时1m标定完成，5m源OHLC为字符串，body/gap计算拒绝字符串除法。未执行尾部检验、未输出2024/2025研究结论。

原freeze、1m panel/阈值与旧实现/测试字节保留在 `artifacts/tail_distribution_v1_preflight_dtype_incident`。修复只在输入入口把四个OHLC字段显式转换为已校验的浮点数组，并在数值比较前完成转换；没有改阈值、窗口、日期或统计量。新增字符串源等价回归测试，重建后核对1m面与阈值仍相同。
