# POST-SHOCK-RECOVERY-2026 云端复核回执

日期：2026-09-07

状态：**云端已完成2026 held-out验证及限定范围复核。**

- 用户授权：2026历史数据仅用于本专题独立研究验证；不含交易、生产或注册表权限。
- 数据包提交：`1e49e7b2cbab590981c86c36e31ef5e272f4e76f`。
- 实际支持：2026-01-05 至 2026-08-21，两指数各154个完整交易日。
- 输入：两指数1m各36,960行；3s为STAR50 730,261行、CSI1000 730,395行。
- 云端执行：GitHub Actions run `34113054287`，结论success；执行分支 `research/post-shock-recovery-2026-actions-20260907`。
- 证据artifact：`10015140042`，SHA256 `f31e3019fa7cfad7858529d16bd927b8a16374dd22b4c0d5e46d1836e55b8981`。
- 云端复核：下载artifact并核对9个输出清单文件的SHA和大小，0 mismatch。当前会话未重新读取全部Parquet训练；原始Parquet读取、输入SHA/行数/日期检查由成功的隔离Actions完成。
- 2026冻结事件数：STAR50 8，CSI1000 6，共14个，样本有限。
- 科学结论：首跳后的`Unsafe -> Recovering`风险持续现象在2026方向上复现；此前冻结的R1/R2/R3、固定时间解除、release logistic、3s path models均未达到高置信度在线`Clean`标准。
- 主状态分数：继续保留当前trailing-5m RMS / pre-shock sigma作为透明主测量；冻结ridge只作比较，不因2026结果重拟合或换主模型。
- `Clean`：仍未验证为在线状态转换，不晋级。
- 完整报告：`docs/research/post_shock_recovery_2026/RESULTS.md`。

后续纪律：不使用本次2026结果继续调阈值/特征/事件定义。若要再次验证`Clean`，需要2026-08-21之后的真正新增同语义事件，或 materially different information；否则停止在同一批数据上搜索。
