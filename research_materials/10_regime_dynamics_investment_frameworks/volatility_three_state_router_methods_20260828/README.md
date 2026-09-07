# 三态波动率择时路由方法包

本目录为 `CSI1000_VOL3_FILTER_CHANNEL_DIVERSIFIER_V1` 保存原始文献与项目关系评估。
文献只提供机制候选，不构成中证1000策略证据。

## 文件

| 文件 | 方法 | 归档状态 |
|---|---|---|
| `page_1954_source_record.md` | CUSUM | 出版者书目记录；全文非开放，未绕过权限 |
| `adams_mackay_2007_bayesian_online_changepoint_detection.pdf` | BOCPD | arXiv 开放原文，7页，首页可视核验 |
| `hamilton_1989_regime_switching.pdf` | Markov switching | 项目已有可信副本的同哈希复用，28页 |
| `barndorff_nielsen_shephard_2003_jump_testing_bipower_variation.pdf` | 跳跃/连续波动分解 | Oxford 作者机构仓库公开稿，44页 |
| `method_assessment.md` | 四方法与项目框架 | 控制器分析，无实证授权 |

## 原始来源

- Page (1954): https://doi.org/10.1093/biomet/41.1-2.100
- Adams and MacKay (2007): https://arxiv.org/abs/0710.3742
- Hamilton (1989): https://doi.org/10.2307/1912559
- Barndorff-Nielsen and Shephard (2003 working paper):
  https://ora.ox.ac.uk/objects/uuid:69814686-bf28-49b0-981a-7a08317396b8

PDF 和记录的实际 SHA-256 由框架构建器写入
`docs/ops/evidence/market_state_volatility_three_state_router_framework_v1_20260828/source_closure.json`。
