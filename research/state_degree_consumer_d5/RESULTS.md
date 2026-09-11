# D5 结果：有界“状态 + 程度 + 适用性”研究消费者通过

## 判定与范围

**D5_BOUNDED_RESEARCH_CONSUMER_ACCEPTED_EXTERNAL_INTEGRATION_PENDING。**
本仓样例消费者已经实现并实际验收，不再是只有契约。它把 D2 双时钟事件与 D4 E15 裸值按来源、时点和版本接起来，并按实际收到消息的时点限制读取。这不是新统计 Validation、模型提升或外部系统上线。

协议在执行前提交：e0eb6d0006c326430aa6429ce52a24df60d65e3f；source main 为 11ade25e0ea7a25321955015e327854915cc211a。D4 原消费者契约不改，D3 未晋升和 D4 分目标支持不改，V19 不重拟合。

## 实际结果

| 项目 | 结果 |
|---|---:|
| D2 E15/CLOSE 事件完整接入 | 232,704 |
| D4 E15 一对一匹配 | 116,352 |
| 原可用 E15 / CLOSE | 各 113,928 |
| 原不可用 E15 / CLOSE | 各 2,424，全部保留 |
| D2 状态、转移、时钟、裸值、概率及缺失传递差异 | 0 |
| D4 增强数值最大绝对差 | 0.0 |
| 独立 as-of 边界查询检查 | 930,816，零差异 |
| 固定历史前缀检查 | 20/20 通过 |
| 合成接口测试 | 40/40 通过，含九种状态组合 |
| E15 / CLOSE 冻结恢复曲线 | 12,660 / 12,662 |
| 治理校验 / 编译 / 两个真实记录样例命令 | 通过 |

930,816 是每个事件在发布前1微秒、发布时、过期前1微秒和过期时的四次工程检查，不是930,816个独立市场样本。独立选择器不导入消费者或回放 runner；从原 D2 记录重新选择应可见事件，并检查完整导出白名单、同名值、D4 裸值和来源摘要。

## 消费者真正怎样使用

E15：状态、状态转移、临时/退出待确认性质以 D2 为准。D4 同键同时间同裸值核对后补充 lag_intensity、lag_ratio、delta_intensity、delta_ratio；差分仍仅为描述，不晋升为预测门控。
CLOSE：使用 D2 收盘确认事件及其确认裸值、原冻结恢复信息；不沿用 E15 的增强字段，不把 D4 的 E15 用途结论跨时钟推广。CLOSE 的 lag/delta 为 null，原因 NOT_DEFINED_FOR_CLOSE，不是假零。

不输出 D4 的 numeric_bucket。其分位配置需要训练期拟合，且分位门控效用未单独通过；本次只接裸值，不制造训练期已经部署分位表的叙事。V16 恢复概率保留原 probability_target_clock，不冒称新 D4 概率服务。

四种读取状态明确分开：AVAILABLE、STATE_ONLY（有 D2 状态但 D4 增强缺失）、UNAVAILABLE（当前源记录不可用）、NO_CURRENT_SNAPSHOT（尚未收到、已过期或休市）。后两者不是 NORMAL；最新记录不可用或过期时不回退到更旧的“可用”状态。

源端 published_at 和消费者 received_at 分开。消费需满足 max(published_at, received_at) <= as_of < valid_until；本历史包默认收到时间等于发布时间只是理想假设。对象和历史记录不可变，重复消息幂等，冲突重复拒绝，迟到增强不可回填。

样例实际查询固定的 2024-01-02 10:00:00+08:00：零延迟得到 CLOSE；人为加入2秒接收延迟后返回 NO_CURRENT_SNAPSHOT / LATEST_EVENT_EXPIRED。这2秒是合成情景，不是测得的 feed 延迟。原始输出保留在 EXAMPLE_ZERO_DELAY.json 与 EXAMPLE_DELAYED_CLOSE.json。

## 原有边界没有被隐藏

每种时钟的完整网格可用率仍为97.9167%；日初2,424条无同日参考记录不补正常。E15观察旧于120秒的2,424条、旧于15秒的2,454条均保留，最大165秒。没有加新鲜度阈值或删除日末样本来改善覆盖。

午休期间不输出当前状态；午后13:00到首个E15之前，可以按原D2规则读取上午最后确认上下文，明确保留上午观察时刻，不冒充午后新观察。日终确认记录在15:00瞬间可读，之后不跨夜沿用。这里保留的是原D2样例失效语义，不是对交易所接收系统的认证。

20个固定锚点是每指数每年度首/末交易日10:00的E15。只加载已发布前缀、加载全量后再查历史、改变其后的合成CLOSE，三种结果一致。它检验消费者不回写，不是再次重算 raw3s，也不是所有部署情况下的普遍因果证明。

## 执行与中断记录

全部 D5 计算在当前会话，Python 3.13.5，标准库实现。没有 GitHub Actions、外部 FactorLab/DataHub 执行、新行情查询或依赖拟合。只读取两份已封存包的必要消费者字段，其余成员仅校验哈希，预测/未来标签不进入消费者。

第一次全量导出遭会话工具120秒执行上限中断，未形成完整验收结果。之后只把 gzip 输出压缩级别由9改为1并增加进度记录，采用同一输入、同一接口与门槛完成执行和独立验证；未择优或改数据。中断日志和 ATTEMPTS.json 保留，部分未封存压缩文件不当作科学结果发布。

已发布的五个 Python 文件 Git blob 与实际执行字节一致，见 SOURCE_IDENTITY.json。成功摘要 SHA256：b621e95393ca4207dcfbad44451bbe6acec0a7cc54dfd4cfda1cfefe3f201cb9；输出 manifest SHA256：d052d10b15f10d1e051ec81381065bd2368ace9da2c93f09c152a00e15d192a7。

## 下一阶段不是继续造模型

当前“状态+程度+适用性”的本仓样例消费链已经打通。接下来进入有界外部研究消费者回迁/接入验收，按 LOCAL_HANDOFF.md 由真实本地回执确认；本会话没有外部执行通道，不声称已派发、已回迁或已接生产。

完整仓库测试、长期持久化、实盘消息认证/接收日志、重连修订、外部策略适用性及经济收益均未通过本次验收。D5 的字节/时钟一致性不提高 D3/D4 的预测证据等级。没有必要仅为版本号启动D6或V20。

v19_frozen=true；d3_decision_unchanged=true；d4_scope_unchanged=true；d5_completed=true；external_consumer_accepted=false；d6_started=false；v20_started=false；blackbox_queried=false；pnl_computed=false；production_authority=false。
