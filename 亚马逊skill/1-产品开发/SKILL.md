# 模块一：产品开发

> 本文件是给人看的目录说明，不是可调用的 skill。每个子目录下的 SKILL.md 才是实际工作流。
> 2026-09-20 二次重构：不再区分"新品决策"和"存量产品运营"两条线——不管产品是新是老，都用同一个决策流程（竞品匹配→真实数据对比→评分→统一决策），入口是新增的 `amazon-product-decision`。评分规则和竞品匹配标准统一放在 `../_references/竞品匹配与评分规则.md`。

## 这个模块解决什么问题

**一句话：这个产品（不管做没做过）值不值得投入资源。** 用 `amazon-product-decision` 作为唯一入口，它会根据情况调用下面这些子工具，但最终只给一个决策，不再分裂成"选品判断"和"财务诊断"两套互不相干的结论。

## 统一流程（新品和存量产品走同一套步骤）

`amazon-product-decision` 编排以下子工具：
1. 方向发现（新品候选时）：`amazon-niche-finder` → `amazon-product-research` → `amazon-trending-products`
2. 竞品匹配与筛选：按`竞品匹配与评分规则.md`的属性/外观/场景三条标准，过滤出真正可比的竞品
3. 自身数据获取：`amazon-product-financials`（真实销量/成本/利润，存量产品用领星真实数据，新品用供应商真实报价）
4. 能力边界判断（有店铺时）：`lyt-product-selection`（自有资产核查）
5. 打分：机会评分/财务健康分 + 行业对标百分位，公式见评分规则文件
6. 专项决策（需要时）：`lyt-product-validation`（7维深度验证）、`amazon-product-strategy-advisor`（品牌/捆绑/变体等专项）、`amazon-deal-finder`（促销专项）
7. 库存监控（独立于决策流程）：`fba-inventory-risk-dashboard`

---

## 详细清单

### amazon-product-decision — 统一决策引擎（新增，模块一唯一入口）
不分新品/存量，统一走"竞品匹配→真实数据对比→评分→决策"。编排下面所有子工具，最终只给一个Go/Hold/Pause/Stop结论。**任何产品开发相关的请求都应该先进这个skill，而不是直接跳到某个子工具**。

### amazon-niche-finder — 细分市场发现
被`amazon-product-decision`调用的方向发现子工具。从大类目挖子类目和长尾细分，验证需求、看竞争密度和价格缺口。
**MCP**：卖家精灵`market_research`/`market_product_demand_trend`/`market_brand_concentration`；SIF`market_evaluate_niche`
**输出**：Top5利基机会评分卡 + 跨类目利基地图

### amazon-product-research — 产品深度调研
被`amazon-product-decision`调用的子工具，把方向落地成具体产品候选。
**MCP**：卖家精灵`product_research`/`asin_detail`；SIF`market_evaluate_niche`/`market_get_keyword_demand`

### amazon-trending-products — 趋势产品发现
被`amazon-product-decision`调用的时机校验子工具。区分正在上升的趋势、已经过气的红海、短期风潮。
**MCP**：卖家精灵`market_product_demand_trend`/`google_trend`/`bsr_prediction`

### lyt-product-selection — 从0选品/候选池构建
被`amazon-product-decision`调用的能力边界判断子工具。**已有店铺时先做自有资产核查**（用`asin_detail`/`review`/`traffic_keyword`查自己现有ASIN），构建≥3个候选方向。

### lyt-product-validation — 7维深度验证
需要比标准流程更深入的验证时，被`amazon-product-decision`调用。需求/供给/竞争/利润/履约/合规/验证成本7维，**利润维度必须用真实COGS，不能用类目估算值**。

### amazon-product-financials — 产品财务测算（原sales-estimator+fba-calculator+profit-analyzer合并）
被`amazon-product-decision`调用的自身数据获取工具。销量估算→FBA成本拆解→真实利润分析三步一条流水线。
**硬性规则**：真实COGS必须来自领星ERP `query_order_profit_list_gross_profit`；领星未连通时不得用卖家精灵的类目profit字段冒充真实利润结论（实测两者能差5倍：类目估算52% vs 真实11%）。
**MCP**：领星ERP（真实毛利/ROI/退货）+ 卖家精灵`asin_detail`/`asin_sales_trend`（销量与尺寸）

### amazon-product-strategy-advisor — 产品策略顾问（原6个skill合并）
`amazon-product-decision`判断需要专项处理时调用，按模式覆盖：①自有品牌打法 ②产品捆绑 ③变体策略 ④类目解锁 ⑤产品合规 ⑥批发采购。

### amazon-deal-finder — 促销策略规划
专项工具，评估Lightning Deal/Coupon等促销资格和ROI，排全年促销日历。
**MCP**：领星ERP（库存/利润）；卖家精灵`asin_coupon_trend`

### fba-inventory-risk-dashboard — FBA库存风险仪表盘
独立于决策流程的全自动监控工具。给Selling Partner账号，直接查真实库存数据，找断货风险SKU。**注意**：需要独立的SP-API集成授权，跟领星ERP是两个不同的授权体系。

---

## 内部串联逻辑（举例）

已经在卖车载香水，想知道下一步开发什么新形态，或者要不要继续投入现有产品：
1. 调用`amazon-product-decision`，它会先问清楚对象是新品候选还是存量产品
2. 有店铺时先用`lyt-product-selection`做自有资产核查
3. 按`竞品匹配与评分规则.md`筛出真正可比的竞品（同类目节点+同形态+同场景）
4. 拉自身真实数据（存量用`amazon-product-financials`接领星；新品用供应商真实报价）
5. 打分：机会评分或财务健康分 + 行业对标百分位
6. 按统一决策表给出Go/Hold/Pause/Stop，需要更深验证时调用`lyt-product-validation`

## MCP 集成程度总表

| 类型 | Skill | 能否直接跑 |
|---|---|---|
| 全自动 | `fba-inventory-risk-dashboard` | ✅ 给账号直接出仪表盘 |
| 数据自动拉取 | `amazon-niche-finder`、`amazon-product-research`、`amazon-trending-products` | ✅ 给类目/关键词/ASIN即可 |
| 半自动，强依赖真实成本 | `amazon-product-financials`、`amazon-deal-finder`、`amazon-product-decision` | ⚠️ 领星连通+竞品数据齐全才能出可信结论 |
| 需人工问答 | `amazon-product-strategy-advisor` | ❌ 核心仍需你回答问题 |
| 结构化验证流程 | `lyt-product-selection`、`lyt-product-validation` | ⚠️ 有店铺时能自动核查资产，候选方向和验证结论仍需你确认关键信息 |

## 默认锚点（自有资产核查的起点）

`lyt-product-selection` 的自有资产核查默认先查：HoogaLife（车载香薰扩散器）、C Classy（悬挂式车载香薰）、AirPurelle（杯架插棒式车载香薰）。品类无关时按用户实际提供的品牌核查。

## 评分规则

完整的机会评分、财务健康分、行业对标百分位、行动优先级公式，统一放在 `../_references/竞品匹配与评分规则.md`，本模块不重复定义，避免两处口径不一致。

| 检查项 | 数据来源 | 判定方式 |
|---|---|---|
| 品牌集中度 | 卖家精灵 `market_brand_concentration` | Top3份额>50%判定高度集中，新品切入需差异化 |
| 产品评分健康度 | 卖家精灵 `asin_detail` | 用行业对标百分位排名，不是简单"高于/低于均值" |
| 单件真实净利润率 | 领星ERP `query_order_profit_list_gross_profit` | 财务健康分公式，趋势分骤降触发Stop |
| 库存风险 | `fba-inventory-risk-dashboard` | 有效DOS（含在途）<14天判CRITICAL |
| 候选方向与自有能力复用度 | `lyt-product-selection` 自有资产核查 | 需要全新供应链的方向即使市场数据好看也要标注"风险更高" |
