# Amazon Skill 工具库

> AB America Corp / HOOGALIFE — Amazon US 运营工具包
> 46个 Skill，按6大模块分类，供 Claude Code 自动执行
> 2026-09-16 重构：原60个skill精简为46个，删除2个重复/被覆盖的skill，把14个同构的框架型skill合并成3个带模式切换的skill（详见各模块SKILL.md的重构说明）

---

## 数据来源

| MCP 工具 | 覆盖领域 | 核心接口 |
|---------|---------|---------|
| SIF (sif-mcp) | 流量分析 + 广告分析 + 市场分析 | `ops_get_listing_*`, `ads_get_asin_*`, `market_*` |
| 卖家精灵 (237a35ba) | 产品/市场/关键词/竞品研究 | `asin_detail`, `keyword_research`, `market_research` |
| LingXing 领星 | ERP 真实数据（成本/利润/库存/广告花费），276个业务工具，help→search→action调用 | `query_order_profit_list_gross_profit`（真实毛利）等 |
| Brightdata | 网页抓取/竞品 Listing 全文 | `competitive-intel`, `scrape` |
| Canva (2dc429e6) | 设计素材生成 | `generate-design`, `edit-design` |

**⚠️ 关键教训（2026-09-16实测）**：卖家精灵`market_research`给出的类目平均利润估算（52%）跟领星ERP真实数据（11%，其中一款低至3.48%）能差5倍以上。任何利润/毛利率结论，优先用领星真实数据，类目估算值只能标注为参考，不能作为Go/No-Go判断依据。

---

## 模块总览

### 1-产品开发（9个 skill）

新品决策链（niche-finder→product-research→trending-products→lyt-product-selection→lyt-product-validation）+ 存量产品运营工具（financials/strategy-advisor/deal-finder/inventory-dashboard），详见模块内SKILL.md的"线A/线B"说明。

| Skill | 用途 | 搭配 MCP |
|-------|------|---------|
| amazon-niche-finder | 细分市场发现 | 卖家精灵 `market_research` |
| amazon-product-research | 产品深度调研 | 卖家精灵 `asin_detail` + `product_research` |
| amazon-trending-products | 趋势品发现 | 卖家精灵 `market_product_demand_trend` |
| lyt-product-selection | 从0选品/自有资产核查 | 卖家精灵全套 |
| lyt-product-validation | 产品7维验证 | SIF `market_evaluate_niche` |
| amazon-product-financials | 销量估算+FBA成本+真实利润（合并自3个skill） | 领星ERP真实毛利 + 卖家精灵 |
| amazon-product-strategy-advisor | 品牌/捆绑/变体/解锁/合规/采购6模式（合并自6个skill） | 卖家精灵 + Brightdata + 领星 |
| amazon-deal-finder | 促销机会发现 | 领星ERP + 卖家精灵 |
| fba-inventory-risk-dashboard | 库存风险看板（全自动） | SP-API |

### 2-竞品销售策略分析（10个 skill）

竞品识别→监控→关键词→价格→评论 全方位情报

| Skill | 用途 | 搭配 MCP |
|-------|------|---------|
| amazon-competitor-analysis | 8维度竞品评分 | SIF `market_discover_competitors` + 卖家精灵 `asin_competitor` |
| amazon-competitor-monitoring | 持续竞品监控 | Brightdata `competitive-intel` |
| amazon-keyword-research | 长尾词挖掘 | 卖家精灵 `keyword_miner` + `keyword_research` |
| amazon-keyword-tracker | 排名追踪 | SIF `ops_get_listing_keyword_distribution` |
| amazon-rank-tracker | BSR 追踪 | 卖家精灵 `asin_sales_trend` |
| amazon-review-analyzer | 评论分析 | 卖家精灵 `review` |
| amazon-brand-analytics | 品牌分析 | 卖家精灵 `aba_research_*` |
| amazon-seller-analytics | 卖家画像 | 卖家精灵 `market_seller_concentration` |
| amazon-price-tracker | 价格追踪 | Brightdata 抓取 |
| amazon-repricing-strategy | 定价策略 | 领星 ERP + 卖家精灵 |

### 3-Listing诊断（7个 skill）

审计→优化→关键词→图片→A+ 全流程

| Skill | 用途 | 搭配 MCP |
|-------|------|---------|
| amazon-listing-optimization | Listing 审计+改写双模式 | SIF `ops_get_listing_*` |
| sys-amazon-listing-audit | [已安装] Listing 质量审计 | SIF 流量数据 |
| amazon-backend-keywords | 后台搜索词优化 | 卖家精灵 `keyword_research` |
| amazon-search-optimization | 搜索排名优化 | SIF `market_get_keyword_demand` |
| amazon-listing-images | 主图优化指南 | Canva 设计生成 |
| amazon-a-plus-content | A+页面制作 | Canva + Brightdata 抓竞品 A+ |
| sys-amazon-title-image-compliance | [已安装] 标题图片合规 | — |

### 4-广告策略分析（11个 skill）

PPC结构→出价→否词→DSP→分时 全覆盖

| Skill | 用途 | 搭配 MCP |
|-------|------|---------|
| amazon-ppc-campaign | 4-campaign漏斗结构 | SIF `ads_get_asin_ad_structure` 全链路 |
| amazon-advertising-strategy | 广告整体策略 | SIF 广告分析全套 |
| amazon-dayparting-strategy | 分时出价策略 | SIF `ads_get_campaign_traffic_trend` |
| amazon-negative-keywords | 否定关键词管理 | SIF `ads_get_ad_group_keyword_breakdown` |
| amazon-display-ads | 展示广告 | SIF + 卖家精灵 |
| sys-amazon-ads | [已安装] 广告基础管理 | SIF |
| sys-amazon-ads-optimization | [已安装] 广告优化 | SIF |
| sys-amazon-ads-marketplace | [已安装] 市场广告 | SIF |
| sys-amazon-dsp | [已安装] DSP 广告 | SIF |
| sys-search-term-harvest-dashboard | [已安装] 搜索词收割 | SIF |
| sys-wasted-ad-spend-dashboard | [已安装] 浪费广告看板 | SIF |

### 5-内容生产工具（7个 skill）

文案→图片→视频→店铺设计

| Skill | 用途 | 搭配 MCP |
|-------|------|---------|
| product-description-generator | 产品文案生成 | — |
| amazon-storefront-design | 品牌旗舰店设计 | Canva |
| amazon-product-photography | 产品拍摄指南 | Canva |
| lyt-detail-page | 详情页策划 | Canva |
| lyt-image-patterns | 图片套路分析 | Brightdata 抓竞品图 |
| lyt-image-prompt | AI 图片提示词 | Canva `generate-design` |
| lyt-video-script | 视频脚本生成 | — |

### 6-站外营销自动化（2个 skill）

促销→Vine→Subscribe&Save→季节规划→Buy Box

| Skill | 用途 | 搭配 MCP |
|-------|------|---------|
| amazon-lifecycle-marketing | 品牌促销/Vine/优惠券/评论/季节性/S&S 6模式（合并自6个skill） | 卖家精灵 + 领星ERP + sys-amazon-ads |
| amazon-buy-box | Buy Box 策略 | 卖家精灵 + 领星ERP |

---

## 使用方式

告诉 Claude 读取对应目录的 SKILL.md 即可启动工作流：

```
请读取 C:\Users\Administrator\Desktop\skill\亚马逊skill\2-竞品销售策略分析\amazon-competitor-analysis\SKILL.md，
然后帮我分析这个竞品 ASIN: B0XXXXXXX
```

或者直接说自然语言，Claude 会根据已安装的 system skill 自动路由。合并后的skill（`amazon-product-financials`、`amazon-product-strategy-advisor`、`amazon-lifecycle-marketing`）需要先说明或描述场景以确定模式。

---

## Skill 来源

| 来源 | 数量 | 说明 |
|------|------|------|
| [nexscope-ai/Amazon-Skills](https://github.com/nexscope-ai/Amazon-Skills) | 原52 | MIT 开源，Claude Code 原生格式，重构后部分合并 |
| 已安装 System Skills | 8 | 通过 `npx skills add` 安装的全局 skill |
| 自建合并skill | 3 | `amazon-product-financials`、`amazon-product-strategy-advisor`、`amazon-lifecycle-marketing` |

---

*最后更新: 2026-09-16（结构重构）*
