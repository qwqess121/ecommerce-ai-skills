---
name: amazon-lifecycle-marketing
description: "Amazon产品生命周期营销顾问，按模式覆盖品牌定制促销/Vine计划/优惠券策略/评论策略/季节性规划/Subscribe&Save六个主题。合并自amazon-brand-tailored-promotions/amazon-vine-program/amazon-coupon-strategy/amazon-review-strategy/amazon-seasonal-planning/amazon-subscribe-save六个skill，因为它们共用同一套'收集信息→追问→研究→建议'框架。Buy Box策略不在此skill内，见独立的amazon-buy-box（内容更详细，涉及不同的资格评估逻辑）。"
metadata: {"nexscope":{"emoji":"🔄","category":"amazon"}}
---

# Amazon Lifecycle Marketing 🔄

产品上架后的持续运营营销，6个主题的统一入口，合并原6个独立skill。

## 模式选择

```text
你想咨询哪个方向？
1. 品牌定制促销（brand-tailored-promotions）
2. Vine早期评论者计划（vine-program）
3. 优惠券策略（coupon-strategy）
4. 评论获取策略（review-strategy）
5. 季节性销售日历与备货（seasonal-planning）
6. Subscribe & Save订阅优化（subscribe-save）
```

## 通用工作流（4步框架）

1. 收集信息——产品、平台、当前状况、目标
2. 追问补全——多选格式一次性追问
3. 研究分析——按模式调用对应MCP工具（见下表）
4. 交付建议——发现摘要 + 数据基准 + 优先行动项 + 具体下一步

## 各模式的研究内容与MCP工具、评判标准

| 模式 | 研究内容 | MCP工具 | 评判标准 |
|---|---|---|---|
| 1 定制促销 | 复购率、客户分层、受众画像 | 领星ERP`finance_page_list_msku`（复购相关）；sys-amazon-ads`ask_report_analyst`；卖家精灵`asin_sales_trend` | 复购率高于类目均值的客户群优先做定向促销 |
| 2 Vine | 当前评论数据、产品阶段 | 卖家精灵`review`、`asin_detail`、`asin_sales_trend` | 评论数<30条的新品优先注册；评分已<4.0的老品不建议（会进一步拉低均分） |
| 3 优惠券 | 竞品优惠券历史、当前售价 | 卖家精灵`asin_coupon_trend`、`asin_detail`；领星ERP`query_order_profit_list_gross_profit`（真实利润率，算折扣后安全线） | 折扣后净利率不得低于领星真实数据算出的安全线（建议≥5%，具体以实际财务模型为准，不用类目估算） |
| 4 评论策略 | 评论分布、订单量 | 卖家精灵`review`、`asin_sales_trend`；领星ERP（真实订单量算评论率） | 评论率低于类目平均需加强；某投诉主题占比>30%判定结构性问题，转`amazon-product-financials`/模块一处理，不能只靠营销手段掩盖 |
| 5 季节性规划 | 季节性趋势、历史销量、库存 | 卖家精灵`google_trend`、`asin_sales_trend`、`market_research`；领星ERP`analytics_vc_inventory_list`等库存报表 | 备货窗口设在需求峰值前6-8周；备货量=日均销量×备货天数+安全库存 |
| 6 S&S | 订阅订单、复购周期 | 领星ERP真实订单数据；卖家精灵`asin_detail` | 复购周期<90天的消耗品类适合上S&S；一次性使用型不建议 |

## 输出格式

```markdown
## {模式名称}建议：{产品}

### 发现摘要
### 数据基准（标注真实数据 vs 估算）
### 优先行动项
### 具体下一步
```

## 与其他skill的关系

- Buy Box相关问题 → 转 `amazon-buy-box`（独立skill，不在本合并范围内）
- 涉及产品本身结构性问题（不是营销能解决的） → 转模块一 `amazon-product-financials` 或产品验证流程
