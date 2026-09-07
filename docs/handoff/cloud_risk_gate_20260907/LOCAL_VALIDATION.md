# 本地交付核验

本轮只执行资料/数据导出及包验证，不启动新的金融研究或交易账户。

- STAR50本地全套测试151项通过（含新增5项有界读取/时区/同秒/哈希测试）。DataHub离线出口范围测试5项通过。
- DataHub3秒父物理SHA与manifest/source_receipt一致；18个标的/年共14,771,920行，全部字段行集合的count/sumhash/xorhash与父源有界筛选一致。是指纹级复核，不声称源文件字节级独立重放。
- 原DataHub线上consumer合同hash保持不变，未写共享serving registry。新权限仅为用户明确授权的离线导出；无2026行新增输出，无ETF/期权原始行情新增。
- 旧全部成果/模型不重跑、不重新拟合；同频尾部、波动预测、分辨率、波形/连败/三方案等当前相关的本地持久化结果与原字节一并保留。
- 文献15项全文齐备，包含用户补齐的Page、Kwok、Chen。文献与原始Markdown按本地归档字节复制，不修正文中的原会话引用标记，不把综述推断当已验证结论。
- 新增便携读取器不依赖DataHub服务、桌面路径或凭据；原历史runner和文献归档工具中的本地路径仍只供本地复现，不冒充全部历史任务可在云端离线重算。
- 当前交接文档本地相对链接已检查，新增文本做常见凭据模式扫描无命中；这不是完整安全审计。PDF/Parquet/NPZ设为Git二进制，不更改原文件内容。历史导出SVG/Markdown自带空白保留，以维护原证据hash；新代码与交接文本单独检查。
- DataHub新增独立脚本的符号尚未索引；GitNexus精确target为not_found。全仓detect_changes还包含大量用户既有变更，不被当成本任务调用图证明。本任务未修改既有DataHub函数/类，也未提交或推送DataHub其他变更。
- 两次前置导出修复留档：SQL建视图参数API错误（无数据行输出）；验重初用timestamp遗漏row_index，后按原writer真实主键修正并保留346条同秒额外源序列。没有删除或修价来通过。

完整包SHA、文件复用/增量清单在`package_manifest.json`。按其中固定manifest验证，再将相同commit推送到原私有仓库，默认main仅允许fast-forward；不force push、不执行GitHub Actions。云端尚未进行科学复验。
