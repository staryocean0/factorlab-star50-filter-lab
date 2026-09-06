# 第四轮交付后的校验状态

研究正文和99项封存文件位于代码/证据提交`2ae61ee90cc14c45cb474ec3e9f643109fbb3470`。102个新增/更新blob与本地逐一核对一致；历史三轮封存blob没有改动。此补充只记录交付后的检查状态，不改动研究结论或原manifest。

本地通过：3个新测试；原始完整持仓逐点重放；原始年度/MDD指纹；日/交易/事件/互斥格记账；分量重建；七种数学构造的原路径重建；五个年度链式回执；全部注册预算和PNG解码。冻结校验器带development-only材料返回valid=true。

本地部分checkout全套pytest为34通过、1失败，唯一失败是`tests/test_package.py::test_only_star50_and_roles`找不到GitHub原始`data/development/5m_offset_0.parquet`。研究实际使用的是此前已取得并保留原文件/导出双哈希的<=2025载体；未把它伪装成缺失的原始文件。排除该整个包测试文件的运行31项通过；这不等于完整仓库CI通过。

GitHub代码提交触发的8个工作流任务都在任何执行步骤开始前失败。第四轮[CI运行](https://github.com/staryocean0/factorlab-star50-filter-lab/actions/runs/34007578040)已重试一次，第二次同样steps=null、logs_url=null；第一次日志接口返回404 BlobNotFound。检查项确有一条注释，但当前GitHub连接不支持读取该注释端点。**无法确认具体平台原因，也不能推断是额度、账单或代码错误。**

研究已完成并保持草稿PR；远端完整CI未通过、主分支未合并。后续应查看Actions页面注释/执行环境状态，再重跑既有冻结工作流；不删除失败记录、不弱化测试、不修改历史manifest。

机器回执：[validation_receipt.json](../../artifacts/cross_scale_root_cause_ci/validation_receipt.json)。最新入口`CURRENT_RESEARCH.md`同步此状态。
