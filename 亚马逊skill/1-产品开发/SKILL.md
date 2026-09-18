# 模块一：产品开发

> 本文件是给人看的目录说明，不是可调用的 skill。每个子目录下的 SKILL.md 才是实际工作流。
> 2026-09-16 重构：16个skill合并精简为9个，删除重复项，把同构的框架型skill合并成带模式切换的单一skill。

## 这个模块解决什么问题，分两条线

**产品开发这个词经常被混用，模块内部实际是两条不同的链条，别搞混：**

### 线A：新品决策链——"要不要做一个还没做过的产品"
从市场信号出发，判断值不值得投入开发资源，最后给Go/No-Go结论。
`amazon-niche-finder` → `amazon-product-research` → `amazon-trending-products`（时机校验）→ `lyt-product-selection`（能力边界+候选方向）→ `lyt-product-validation`（7维验证+最终结论）

### 线B：存量产品运营——"已经在卖的产品怎么优化"
财务测算和策略决策工具，作用对象是已上架产品。
`amazon-product-financials`（销量→成本→真实利润）、`amazon-product-strategy-advisor`（品牌/捆绑/变体/解锁/合规/采购6模式）、`amazon-deal-finder`（促销）、`fba-inventory-risk-dashboard`（库存）

**跑之前先问自己："这个产品我们做过没有？"** 做过 → 线B。没做过 → 线A。别用线B的财务工具去回答"要不要做"这种问题——那是选品判断，不是财务诊断。

---

## 详细清单

### amazon-niche-finder — 细分市场发现
线A第一步。从大类目挖子类目和长尾细分，验证需求、看竞争密度和价格缺口。
**MCP**：卖家精灵`market_research`/`market_product_demand_trend`/`market_brand_concentration`；SIF`market_evaluate_niche`
**输出**：Top5利基机会评分卡 + 跨类目利基地图

### amazon-product-research — 产品深度调研
线A第二步。把方向落地成具体产品候选，拆成本算利润率。
**MCP**：卖家精灵`product_research`/`asin_detail`；SIF`market_evaluate_niche`/`market_get_keyword_demand`
**输出**：综合机会评分（8因子） + Go/No-Go建议

### amazon-trending-products — 趋势产品发现
线A时机校验。区分正在上升的趋势、已经过气的红海、短期风潮，避免压货压在退潮期。
**MCP**：卖家精灵`market_product_demand_trend`/`google_trend`/`bsr_prediction`

### lyt-product-selection — 从0选品/候选池构建
线A第三步。**已有店铺时先做自有资产核查**（用`asin_detail`/`review`/`traffic_keyword`查自己现有ASIN），把能延伸出什么作为候选方向第一来源，再对比市场缺口，构建≥3个候选方向。

### lyt-product-validation — 已有产品验证
线A终点。对具体候选做需求/供给/竞争/利润/履约/合规/验证成本7维验证，给能测/暂缓/不建议做的结论。**利润维度必须用真实COGS（供应商报价或领星ERP），不能用类目估算值**。

### amazon-product-financials — 产品财务测算（原sales-estimator+fba-calculator+profit-analyzer合并）
线B核心工具。销量估算→FBA成本拆解→真实利润分析三步一条流水线。
**硬性规则**：真实COGS必须来自领星ERP `query_order_profit_list_gross_profit`；领星未连通时不得用卖家精灵的类目profit字段冒充真实利润结论（实测两者能差5倍：类目估算52% vs 真实11%）。
**MCP**：领星ERP（真实毛利/ROI/退货）+ 卖家精灵`asin_detail`/`asin_sales_trend`（销量与尺寸）

### amazon-product-strategy-advisor — 产品策略顾问（原6个skill合并）
线B专项决策工具，按模式覆盖：①自有品牌打法 ②产品捆绑 ③变体策略 ④类目解锁 ⑤产品合规 ⑥批发采购。共用"收集信息→追问→研究→建议"框架，各模式对应不同MCP工具，详见该skill内的模式对照表。

### amazon-deal-finder — 促销策略规划
线B专项。评估Lightning Deal/Coupon等促销资格和ROI，排全年促销日历。
**MCP**：领星ERP（库存/利润）；卖家精灵`asin_coupon_trend`

### fba-inventory-risk-dashboard — FBA库存风险仪表盘
线B全自动工具。给Selling Partner账号，直接查真实库存数据，找断货风险SKU，渲染交互式仪表盘。**注意**：需要独立的SP-API集成授权，跟领星ERP是两个不同的授权体系。

---

## 内部串联逻辑（举例）

已经在卖车载香水，想知道下一步开发什么新形态：
1. `lyt-product-selection` 自有资产核查 → 找候选方向
2. `amazon-product-research` + `amazon-trending-products` 验证候选方向的市场数据和时机
3. `lyt-product-validation` 7维验证给Go/No-Go（利润维度要真实供应商报价，不能用估算）
4. 验证通过后转产品开发实际执行；已上架的老产品定期用`amazon-product-financials`复查真实利润是否在下滑

## MCP 集成程度总表

| 类型 | Skill | 能否直接跑 |
|---|---|---|
| 全自动 | `fba-inventory-risk-dashboard` | ✅ 给账号直接出仪表盘 |
| 数据自动拉取 | `amazon-niche-finder`、`amazon-product-research`、`amazon-trending-products` | ✅ 给类目/关键词/ASIN即可 |
| 半自动，强依赖真实成本 | `amazon-product-financials`、`amazon-deal-finder` | ⚠️ 领星连通才能出可信结论 |
| 需人工问答 | `amazon-product-strategy-advisor` | ❌ 核心仍需你回答问题 |
| 结构化验证流程 | `lyt-product-selection`、`lyt-product-validation` | ⚠️ 有店铺时能自动核查资产，候选方向和验证结论仍需你确认关键信息 |

## 默认锚点（自有资产核查的起点）

`lyt-product-selection` 的自有资产核查默认先查：HoogaLife（车载香薰扩散器）、C Classy（悬挂式车载香薰）、AirPurelle（杯架插棒式车载香薰）。品类无关时按用户实际提供的品牌核查。

## 评判标准速查表

| 检查项 | 数据来源 | 判定阈值 |
|---|---|---|
| 类目机会评分 | SIF `market_evaluate_niche` | 需求/竞争/利润/规模/增长5维加权，单项显著低于均值需标注风险 |
| 品牌集中度 | 卖家精灵 `market_brand_concentration` | Top3份额>50%判定高度集中，新品切入需差异化 |
| 产品评分健康度 | 卖家精灵 `asin_detail` | 低于类目平均评分判定需优先修复 |
| 单件真实净利润率 | 领星ERP `query_order_profit_list_gross_profit` | 环比骤降（如降50%以上）判P1紧急排查，不看类目估算值 |
| 库存风险 | `fba-inventory-risk-dashboard` | 有效DOS（含在途）<14天判CRITICAL |
| 候选方向与自有能力复用度 | `lyt-product-selection` 自有资产核查 | 需要全新供应链的方向即使市场数据好看也要标注"风险更高" |
