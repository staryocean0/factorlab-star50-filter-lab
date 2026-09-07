# 因果未来波动工具 V1：接口与复现

[结果](result.md) · [结果前合同](protocol.md) · [数据使用边界](data_usage.json)

## 研究接口

工作目录为本STAR50研究仓库；使用安装本项目依赖的Python，或设置`PYTHONPATH=src`。接口只接收一个指数的已闭合一分钟历史前缀，不接收未来标签。

```python
from star50_filter.causal_volatility import VolatilityModel, forecast_latest
from star50_filter.tail_distribution import prepare_instrument

# raw_prefix: 一个指数，timestamp/open/high/low/close/symbol，按真实闭合时间截断。
# 时间按Asia/Shanghai；输入必须满足本项目完整连续交易时钟合同。
history = prepare_instrument(raw_prefix, minutes=1)
model = VolatilityModel.load("artifacts/causal_volatility_tool_v1/models/000852.SH_15")
forecast = forecast_latest(history, model)
```

000852.SH为中证1000，000688.SH为科创50；模型后缀5/15/30为预测交易分钟数。已准备的history应含`timestamp/symbol/r/body/gap/boundary`；至少480槽位预热，不足或未来窗口跨会话会拒绝预测。接口不拉实时行情、不发订单；返回波动预测区间、未来状态及放大概率，`production_authority=false`。

[中证1000接口实例](../../../artifacts/causal_volatility_tool_v1/final/000852.SH_historical_api_example.json)与[科创50实例](../../../artifacts/causal_volatility_tool_v1/final/000688.SH_historical_api_example.json)均为2025历史时点，不是实时预测。

## 执行顺序

以下是已经执行的研究顺序。现有产物为冻结证据，不得覆盖或把重复历史当作新检验；新运行应另建有身份的隔离研究根，并先冻结数据、路径与参数。

```bash
PYTHONPATH=src python scripts/research_causal_volatility_v1.py freeze
PYTHONPATH=src python scripts/research_causal_volatility_v1.py fit
PYTHONPATH=src python scripts/research_causal_volatility_v1.py evaluate --year 2024
# 控制器核对2024回执并写review.json，不改变模型。
PYTHONPATH=src python scripts/research_causal_volatility_v1.py evaluate --year 2025
# 控制器核对2025回执并写review.json。
PYTHONPATH=src python scripts/report_causal_volatility_v1.py
PYTHONPATH=src python -m pytest -q
```

输入是既有两指数共同一分钟面`artifacts/tail_distribution_v1/panel_1m.parquet`，SHA256为`fb5d275ba4fc9cf8ca3b9b65a2a6a499d8f11529e6fba5d1221768a1b79ab23b`。2021—2022拟合、2023校准、2024/2025顺序固定审计，无2026读取。

核心代码在`src/star50_filter/causal_volatility.py`，测试在`tests/test_causal_volatility.py`。`artifacts/causal_volatility_tool_v1/`保存冻结、模型、逐年预测、review、资源记录；`final/`保存逐分钟/非重叠指标、倍率告警、所有相位敏感性、区块bootstrap、混淆矩阵及图形。

## 验证与已知事件

全部146项测试通过；模型拟合/校准不读检验标签，前缀预测容差检查、未来窗口边界与零分母测试通过。报告额外核验模型文件、拟合回执和年度审查链，并直接抽查150个未来窗口。

首次图形汇总因pandas查询在列表推导式中无法解析局部变量而中止。原产物保存在`final_pre_render_scope_fix/`；仅将报告筛选改成显式布尔索引并重跑渲染，没有重拟合或改变模型。五个科学CSV修复前后逐字节一致。最终图形已视觉检查，真实浏览器交互未验收。

下一步若要交易路由，应另冻结“哪种波动状态下滤波器相对通道确有劣势”的条件净收益与切换成本检验；当前结果不授自动切换权限，也不证明通道能接住冲击。
