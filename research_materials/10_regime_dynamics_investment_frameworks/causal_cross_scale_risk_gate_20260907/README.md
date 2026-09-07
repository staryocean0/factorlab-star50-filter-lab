# 跨频段突发波动的事前门控：文献归档

归档日期：2026-09-07。所属项目资料库：`research_materials/`，分类为`10_regime_dynamics_investment_frameworks`。本次仅归档文献，不评定综述的策略结论，不修改策略或授予生产权限。

## 原文与元数据

- [用户提供的完整综述](从“滤波”转向“风险分桶”：跨频段突发波动的事前门控研究.md)：从桌面同名文件逐字节复制，保留原文件，未改写其中的判断或原会话引用标记。
- [来源元数据](sources.json)：14项主要文献的作者、题名、年份、DOI、下载URL、原会话引用标记及版本说明。
- [全文缺口补齐记录](missing_fulltexts.md)：此前2项主要文献及CUSUM原始论文均由用户补齐，保留历史访问失败情况。
- `download_receipt_*.json`：逐轮真实下载记录、HTTP状态、文件页数和SHA-256；后轮的existing表示本地已有，不代表最初没有联网下载。
- `validation.json`：原文一致性、引用覆盖、PDF完整性、重复副本与视觉核验记录。

原文只含`turn…view/search…`会话标记，没有导出的URL列表或完整参考文献表。以下映射是依据作者、内容、题名和出版者/机构记录重建，不声称恢复了原会话每一个链接。相同作品不同链接合并；bipower只给出方法体系，因此其唯一原始版本无法确定。没有递归下载这些论文参考文献中的全部作品。

## 14项主要文献

| 编号 | 作品 | 本地全文 | 版本/页数 |
|---|---|---|---|
| R01 | Corsi，HAR-RV多尺度波动 | [PDF](corsi_2009_har_rv.pdf) | 2009出版者版，大学公开副本；23页 |
| R02 | Kwok，A Consistent and Robust Test for Autocorrelated Jump Occurrences | [PDF](kwok_2024_autocorrelated_jump_occurrences.pdf) | 用户补齐2024出版者全文；30页，157–186 |
| R03 | Chen/Clements/Urquhart，Marked Hawkes | [PDF](chen_clements_urquhart_2024_marked_hawkes.pdf) | Reading机构库，2023在线出版版、2024卷期；32页含机构封面 |
| R04 | Chen，Jump Clustering, Information Flows, and Stock Price Efficiency | [PDF](chen_2024_jump_clustering_forecasting.pdf) | 用户补齐2024出版者全文；28页，1588–1615 |
| R05 | Christensen/Kolokolov，An unbounded intensity model for point processes | [PDF](christensen_kolokolov_2024_intensity_bursts.pdf) | 2024出版者版，Aarhus机构库；37页 |
| R06 | Mucciante/Sancetta，Order Book Dependent Hawkes | [PDF](mucciante_sancetta_order_book_hawkes.pdf) | arXiv v2，2026-05-10上传，稿面日期2023-07-20；42页 |
| R07 | Nason/von Sachs/Kroisandt，Evolutionary Wavelet Spectrum | [PDF](nason_vonsachs_kroisandt_2000_wavelet_spectrum.pdf) | 作者1999稿，期刊版2000；28页 |
| R08 | Cont/Kukanov/Stoikov，The Price Impact of Order Book Events | [PDF](cont_kukanov_stoikov_2014_order_book_impact.pdf) | arXiv v3，2011稿，期刊版2014；26页 |
| R09 | Gould/Bonart，Queue Imbalance as a One-Tick-Ahead Price Predictor | [PDF](gould_bonart_queue_imbalance.pdf) | arXiv v1，2015稿，期刊版2016；30页 |
| R10 | Lee/Mykland，Jumps in Financial Markets | [PDF](lee_mykland_2008_jump_detection.pdf) | 作者机构公开稿，期刊版2008；43页 |
| R11 | Alexiou等，Pricing Event Risk | [PDF](alexiou_et_al_2025_pricing_event_risk.pdf) | Edinburgh机构库2025出版者版；46页含机构封面 |
| R12 | Barndorff-Nielsen/Shephard，Power and Bipower Variation with Stochastic Volatility and Jumps | [PDF](barndorff_nielsen_shephard_2004_bipower.pdf) | 2004出版者版，Duke课程公开副本；38页；方法匹配，原会话具体版本不确定 |
| R13 | Christensen/Oomen/Podolskij，Fact or friction: Jumps at ultra high frequency | [PDF](christensen_oomen_podolskij_2014_fact_or_friction.pdf) | 2014-11-06作者稿，2026年arXiv归档；43页，不冒称2026新论文 |
| R14 | Adams/MacKay，Bayesian Online Changepoint Detection | [已有PDF](../volatility_three_state_router_methods_20260828/adams_mackay_2007_bayesian_online_changepoint_detection.pdf) | arXiv 2007 v1；7页，复用资料库已有全文 |

当前结果：**14/14项主要文献具备可读PDF全文，另补齐Page的CUSUM原始论文，共15项作品，无已识别全文缺口。** 最初联网下载11个PDF；本次用户另提供3个PDF并授权重命名、从桌面移入。R01和R08与既有专题副本同SHA，R14以相对链接复用。因此“本次获取文件数”不等于“新增唯一作品数”。移动前后SHA逐项一致，见`user_delivery_receipt.json`。

## 方法性提及与既有补充资料

原文还泛称CUSUM，但没有作者、年份或唯一论文身份。用户现已补齐[Page (1954) Continuous Inspection Schemes全文](page_1954_continuous_inspection_schemes.pdf)，16页，对应100–115页；保留[历史来源记录](../volatility_three_state_router_methods_20260828/page_1954_source_record.md)。它是单列的补充方法原始论文，不计入上表14项具名作品。该用户提供扫描副本只用于项目内部研究，不宣称开放获取授权。

关于bipower体系，资料库还保存[Econometrics of Testing for Jumps in Financial Economics Using Bipower Variation](../volatility_three_state_router_methods_20260828/barndorff_nielsen_shephard_2003_jump_testing_bipower_variation.pdf)的44页Oxford公开工作稿。它与R12是不同作品，不冒充同一版本，也不重复下载。

## 访问与验真边界

只使用公开出版者、作者机构及arXiv资源；未绕过付费墙、登录或验证码，未联系作者或使用用户凭据。HTTP 403只证明当前下载通道受限，不证明论文没有开放获取版本。下载后检查PDF魔数、pdfinfo解析、全部页文本可提取、首页题名/作者及页数，并渲染首页；机构封面后另核验正文题名。

下载是文献获取，不等于论文方法在中证1000/科创50上的实证成功。综述中的因果门控提案仍需独立研究验证。
