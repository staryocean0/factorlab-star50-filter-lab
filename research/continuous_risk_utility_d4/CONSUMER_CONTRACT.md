# D4 研究消费者契约：状态、程度、适用性三轴

本契约是后续有界接入的冻结起点，不是已经验收了外部消费者或生产服务。V19三状态不变；D3未通过的结论不变。

## 输入输出

主输入为D2 E15快照：symbol、bar_end、decision_time、published_at、valid_until、observation_time、state/state_basis、availability_reason，以及shock_intensity和vol_ratio。D4补充同一已确认历史口径下的lag_intensity、lag_ratio及二者更新差delta_intensity/delta_ratio。所有CSV时钟按Asia/Shanghai解释；不得默认UTC。原D2完整事件身份和timing_basis仍由封存账本提供，D4 CSV不是替代生产消息总线。

连续I/V信息集对15/30/60分钟log未来RMS、30分钟尾部预测的有限增量有本轮可复用Validation支持；15/60分钟尾部未晋升。delta字段和3×3分位键只作描述，尚无独立增量效用验收。统计ridge输出不是可以直接交易或已校准的新概率服务。

## 必须拒绝的误用

不得用未来标签、当前未收盘final close、事后episode终点或收益方向作为消费者属性。不得把UNAVAILABLE当NORMAL，或把缺失恢复概率补0/1。不得用CLOSE覆盖E15历史快照；消费时须满足published_at<=as_of<valid_until。不将E15跨收盘、午休或隔夜无限沿用。

3×3边界仅由Development各指数20%/80%分位固定。它是研究编码，不能声称2021–2023当时已经具备全期拟合的边界。研究复用和真实上线的配置可得时间须分别登记。高分位不是trade_allowed=false、看空、止损或降仓指令；本次未证明这种离散门控有效。

## 下一项接入验收的冻结范围

仅在当前仓建立无交易动作的样例消费者，以D2 E15/CLOSE为时钟，接入状态和D4裸值，按已发布时间做as-of join。逐行验证不回填、过期失效、缺失显式传递、状态语义不漂移、列白名单、时区和版本正确。输出仅为研究用属性视图和不适用原因，不能写其他仓或live registry。

样例消费者可在已有2021–2025有界封存记录上验收，不需要新raw3s、2026或BlackBox，也不重新拟合模型或选择阈值。日初2424条缺参考和日末观察新鲜度限制原样传递；不制造实测延迟。外部策略仓如何行动、费用/盈亏和生产上线必须独立验收。

真实样例消费者接入尚未执行；d5_started=false。该工作完成后再考虑是否有必要继续统计模型研究，不为版本号立新题。
production_authority=false。
