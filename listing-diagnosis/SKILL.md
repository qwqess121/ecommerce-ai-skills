---
name: listing-diagnosis
display_name: "亚马逊 & TikTok Listing 诊断分析"
display_name_en: "Amazon & TikTok Listing Diagnosis"
description: "跨平台Listing诊断——122个亚马逊父ASIN + 64个TikTok商品，8维度评分+修改建议+竞品对标(含月销量/销售额)+广告策略+违规词检测，输出带超链接的Excel报告。"
category: e-commerce
version: 3.1.0
author: AB America Corp
visibility: "public"
---

# 亚马逊 & TikTok Listing 诊断分析 v3.1

## 核心定位

**内容级诊断** — 不只是打分，而是给出可直接使用的修改建议：
- 原标题 → 修改标题（可直接复制粘贴）
- 五点描述 → 具体建议（覆盖RUFUS三问）
- 主副图 → 基于**实际采集图片数**的针对性建议
- A+详情 → 基于**实际采集A+模块**的修改建议
- 违规词 → 替换词（标题+五点+描述全文扫描）
- 竞品对标 → 含**月销量/月销售额**数据
- 广告策略 → **多维度详细策略**（竞价建议、流量分析、优化方向）
- 所有ASIN/商品ID → **可点击超链接**

---

## 触发场景

- "诊断我的 Listing" / "Listing 周报" / "出一份诊断报告"
- "检查违规词" / "竞品对标分析"
- 每周五定时执行（配合 `/schedule` 或 `/loop`）

## 环境依赖

```bash
python -m pip install openpyxl requests
```

---

## 覆盖范围

| 平台 | 店铺数 | 诊断对象 | 品类数 |
|------|--------|---------|--------|
| Amazon | 15个店铺 (US+CA) | 122个父ASIN | 24个L3品类 |
| TikTok | 2个店铺 | 64个商品 | 7个L3品类 |

---

## 数据源 & MCP 工具链

| MCP 工具 | 用途 | 调用方式 |
|---|---|---|
| **领星 MCP** (`LingXing-MCP`) | 亚马逊全部在售Listing | `action(erp_listing, {status:"1", offset:0, length:50, pvi_ids:""})` 分页 |
| **卖酷 MCP** (`237a35ba`) | ASIN详情 + L3品类竞品 | `asin_detail(asin)` / `product_research(nodeIdPaths, month)` |
| **FastMoss MCP** | TikTok商品+达人+竞品 | `shop_product_analysis` / `product_detail_info` / `product_rank_top_selling` |
| **Sif MCP** (`sif-mcp`) | 广告结构+流量分析 | `ads_get_asin_ad_structure` / `ops_get_listing_traffic_overview` |
| **HTTP采集** | AMZ图片+A+ / TK图片+描述 | `scrape_amz_images.py` / `scrape_tk_details.py` |

---

## 完整工作流（6个Phase）

### Phase 0：加载配置 & 拉取商品清单

读取 `<skill>/templates/report-config.json` 获取店铺映射、L3品类节点、自有品牌列表。

**Step 0.1 — 亚马逊在售商品（领星 MCP）：**
```
1. help → search("erp_listing") → 获取工具签名
2. action(erp_listing, {status:"1", offset:0, length:50, pvi_ids:""})
   注意：pvi_ids 必填传空字符串；status 字符串 "1"
3. 分页遍历 offset += 50 直到空
4. 保留 status_text == "在售"
5. 按 parent_asin + marketplace 去重 → 父ASIN列表
6. 保留全部子ASIN → 附表
7. 用 small_rank 自动匹配 L3 品类节点
```

**Step 0.2 — TikTok在售商品（FastMoss MCP）：**
```
1. 遍历 config.tiktok_shops 的 seller_id
2. shop_product_analysis(seller_id, sort_by="revenue", time_range_days=28)
3. 记录 product_id, title, price, sales, gmv, category
```

**输出：** `output/phase0_data.json`, `output/tiktok_data.json`

---

### Phase 1：Listing内容采集

**1.1 亚马逊ASIN详情（卖酷 MCP）：**
```
对每个父ASIN（分批，每批约50个）：
  asin_detail(asin, marketplace_id) →
  保存: title, features(五点原文), price, bsr, rating, ratings, lqs, brand, badge
```
输出：`output/asin_detail_us1.json`, `output/asin_detail_us2.json`, `output/asin_detail_ca.json`

**1.2 亚马逊图片+A+采集（HTTP抓取）：**
```bash
python -I scripts/scrape_amz_images.py
```
- 对122个ASIN抓取Amazon页面
- 提取: `colorImages` JSON中的图片URL列表、`aplus_feature_div` A+内容结构
- 输出: `output/amz_scrape_images.json`（平均6.1张图、120个有A+、56个有视频）

**1.3 TikTok商品详情（FastMoss MCP）：**
```
对每个TK商品:
  product_detail_info(product_id) → title, description, images, price
  product_creator_analysis(product_id) → creator_count, tier_distribution
```
输出：`output/tk_product_details.json`

**1.4 TikTok图片+描述采集（HTTP抓取）：**
```bash
python -I scripts/scrape_tk_details.py
```
- 对64个商品抓取 shop.tiktok.com 页面
- 提取: `product_info` 中图片URL列表、`rich_text` 描述内容、`og:description`
- 注意: 不能使用 `Accept-Encoding: gzip, deflate, br` 头（Python requests不支持brotli解压）
- 输出: `output/tk_scrape_details.json`（平均7.5张图、平均1793字符描述）

**1.5 竞品数据采集（卖酷 product_research）：**
```
对每个L3品类:
  product_research(nodeIdPaths=L3路径, variation="Y", month="YYYYMM",
                   order={field:"total_units", desc:true}, size:10)
  → 不使用 returnFields，获取完整字段包括 units(月销量) 和 revenue(月销售额)
  → 标注自有品牌 is_own_brand
```
输出：`output/competitor_products.json`（API字段: `units`=月销量, `revenue`=月销售额, `bsr`=BSR, `fulfillment`=配送方式）

**1.6 TikTok竞品（FastMoss product_rank_top_selling）：**
```
对每个TK L3品类:
  product_rank_top_selling(category_path=[L1,L2,L3], country="US", date_type="weekly")
  → 取Top10
```

---

### Phase 2：广告分析（Sif MCP，仅亚马逊US）

**对每个US父ASIN（约92个）：**
```
1. ads_get_asin_ad_structure(asin, marketplace="us")
   → campaign数、类型分布(SP/SB/SBV)
2. ops_get_listing_traffic_overview(asin, marketplace="us")
   → 自然流量%、广告流量%、总流量评分
```

**详细策略生成规则（在Phase 3中执行）：**

| 条件 | 策略内容 |
|------|---------|
| 无广告 | 建议开启SP自动+手动精准，含基于价格的竞价建议 |
| 仅SP | 建议增加SB品牌广告+SBV视频广告 |
| 有SP+SB无SBV | 建议增加SBV视频广告 |
| 自然流量<20% | 警告广告依赖度过高+优化Listing关键词建议 |
| 流量评分极低 | 建议多渠道引流：站外Deal+社媒+Vine |

竞价建议公式: `$max(0.3, price×0.05) - $max(0.5, price×0.08)`

输出：`output/ads_analysis.json`（含 `strategy_detail` 字段）

---

### Phase 3：诊断评分 & 建议生成

```bash
python -I scripts/phase3_scoring_v3.py
```

**数据源整合：**
- 加载 `amz_scrape_images.json` → 实际图片数、A+模块信息
- 加载 `tk_scrape_details.json` → 实际TK图片数、描述内容长度
- 加载 `ads_analysis.json` → 生成详细广告策略

#### 亚马逊评分规则（满分100）

| 维度 | 扣分规则 |
|------|---------|
| 标题 | 超200字符扣5, 无品牌扣3, 含违规词按严重性扣分 |
| 五点描述 | 少于5条扣分, 过短(<10字符)扣分, 缺RUFUS三问扣分 |
| 图片 | 采集<7张扣4, <5张扣8, 0张扣10（使用实际采集数据） |
| A+ | 无A+扣5, 模块<3个扣3 |
| 违规词 | 高危扣5/词, 中危扣3/词, 低危扣1/词 |
| 错词 | 每个扣1分 |

**无asin_detail时的处理：**
- 不显示"ASIN详情暂不可查"等泛文本
- 使用采集数据（图片数、A+模块）生成品类针对性建议
- 五点建议使用品类名提示覆盖RUFUS三问

#### TikTok评分规则（满分100）

| 维度 | 扣分规则 |
|------|---------|
| 标题 | 超128字符扣5, 过短<30扣5, 含违规词扣分 |
| 图片 | 采集<5张扣4, <3张扣8（使用实际采集数据） |
| 描述 | 采集<200字符扣5, <500字符扣2 |
| 违规词 | 扫描标题+采集描述全文 |

**TikTok图片建议（基于实际数量）：**
- ≥8张: "图片X张(充足)，确保包含: 主图+信息图+场景图+成分/材质+包装"
- 5-7张: "图片X张(达标)，建议补充至8+张: 增加使用场景图、对比图、尺寸参考图"
- <5张: "图片仅X张(不足)，建议补充至8+张: 主图+功效信息图+场景图+成分图+对比图+包装图"

输出：`output/phase3_diagnosis_v3.json`

---

### Phase 4：子ASIN运营扫描（零额外API调用）

从领星已拉取数据中提取子ASIN运营指标：
- 价格异常: 与同父ASIN偏差>30%标黄, >50%标红
- FBA库存: 0=断货(红), <10=低库存(黄)
- Buy Box: 是否持有
- 变体状态: 是否下架/抑制

输出：`output/phase3_child_scan.json`

---

### Phase 5：Excel报告生成

```bash
python -I scripts/phase5_report_v3.py
```

#### 8个Sheet

| # | Sheet名 | 行数 | 关键特性 |
|---|---------|------|---------|
| 1 | **诊断摘要** | ~27 | AMZ+TK等级分布、违规词统计、竞品覆盖率、数据覆盖率 |
| 2 | **亚马逊Listing诊断** | 122 | ASIN带超链接、修改标题、五点建议、图片建议（含实际张数）、A+建议、综合评分 |
| 3 | **TikTok Listing诊断** | 64 | 产品ID带超链接、修改标题、描述建议（含实际字数）、图片建议（含实际张数）、综合评分 |
| 4 | **亚马逊竞品分析** | ~147 | ASIN带超链接、**月销量**、**月销售额**、BSR、评分、评论数、LQS、自有品牌标记(绿底) |
| 5 | **TikTok竞品分析** | ~83 | 商品ID带超链接、周GMV、累计GMV、达人数、增长率 |
| 6 | **违规词&错词汇总** | ~173 | ASIN/商品ID、违规词、类别、严重程度、出现位置、上下文、替换建议 |
| 7 | **广告分析&策略建议** | 92 | ASIN带超链接、Campaign结构(SP/SB/SBV)、流量占比、**详细策略建议**(含竞价) |
| 8 | **数据覆盖率** | ~13 | 各数据源覆盖统计、状态标色(OK绿/P黄/!红) |

#### 超链接规则

| 位置 | 链接格式 |
|------|---------|
| AMZ ASIN列 | `https://www.amazon.com/dp/{asin}` (US) 或 `amazon.ca` (CA) |
| TK 产品ID列 | `https://www.tiktok.com/shop/pdp/{product_id}` |
| 竞品ASIN列 | `https://www.amazon.com/dp/{asin}` |
| 广告ASIN列 | `https://www.amazon.{domain}/dp/{asin}` |

输出：`output/Listing诊断报告v3.1_YYYYMMDD_HHMM.xlsx`

---

## 快速运行指南

### 全量运行（约45-50分钟）

按顺序执行Phase 0-5，MCP数据采集 → HTTP抓取 → 评分 → 报告：

```
1. 执行 Phase 0: 领星拉取AMZ商品 + FastMoss拉取TK商品
2. 执行 Phase 1.1-1.3: 卖酷asin_detail + FastMoss TK详情
3. 执行 Phase 1.5-1.6: 卖酷竞品 + FastMoss TK竞品
4. 执行 Phase 2: Sif广告分析
5. 运行 python -I scripts/scrape_amz_images.py   (AMZ图片+A+采集, ~10min)
6. 运行 python -I scripts/scrape_tk_details.py    (TK图片+描述采集, ~2min)
7. 运行 python -I scripts/phase3_scoring_v3.py    (诊断评分+策略生成)
8. 运行 python -I scripts/phase5_report_v3.py     (Excel报告生成)
```

### 仅重新生成报告（已有数据时，约1分钟）

如果 `output/` 下的数据文件都是最新的，只需：
```bash
python -I scripts/phase3_scoring_v3.py
python -I scripts/phase5_report_v3.py
```

### 仅更新评分+报告（不重新采集）

```bash
python -I scripts/phase3_scoring_v3.py    # 重新评分（读取所有output/*.json）
python -I scripts/phase5_report_v3.py     # 重新生成Excel
```

---

## 脚本说明

| 脚本 | 功能 | 输入 | 输出 |
|------|------|------|------|
| `scrape_amz_images.py` | 抓取Amazon页面提取图片列表+A+结构 | phase0_data.json | amz_scrape_images.json |
| `scrape_tk_details.py` | 抓取TikTok页面提取图片+描述 | tiktok_data.json | tk_scrape_details.json |
| `phase3_scoring_v3.py` | 8维度评分+建议生成+广告策略 | 所有output/*.json + references/*.json | phase3_diagnosis_v3.json |
| `phase5_report_v3.py` | 生成8-Sheet Excel报告 | 所有output/*.json | Listing诊断报告v3.1_*.xlsx |

**所有脚本的 BASE 路径：** 脚本内硬编码 `output` 目录路径，运行前确认路径正确。

---

## L3 品类节点参考

### 亚马逊（24个L3品类）

| 品类 | nodeIdPaths | 适用品牌 |
|---|---|---|
| Automotive Air Fresheners | `15684181:15857501:15735121` | CLASSY, Airpurelle |
| Automobile Aroma Diffusers | `15684181:15857501:38276428011` | HoogaLife, CLASSY |
| Women's Eau de Parfum | `3760911:11056591:11056931:11057071` | Pureamor, PUREU, Purefittech |
| Women's Cologne | `3760911:11056591:11056931:11057051` | Pureamor, PUREU |
| Women's Fragrance Sets | `3760911:11056591:11056931:11057111` | Pureamor, PUREU, CLASSY |
| Men's Cologne | `3760911:11056591:11056811:11056851` | PUREU, Pureamor |
| Women's Body Sprays Fragrance | `3760911:11056591:11056931:11057011` | Pureamor, PUREU |
| Women's Eau de Toilette | `3760911:11056591:11056931:11057091` | Pureamor |
| LED Bulbs | `228013:322525011:2314207011` | HoogaLife |
| Medical Hair & Beard Covers | `16310091:8404647011` | Abamerica, Burst Bird |
| Medical Stethoscope Accessories | `16310091:17277660011` | Abamerica |
| Stethoscopes | `16310091:17277659011` | Abamerica |
| Medical Uniforms & Scrubs | `7141123011:7586144011:1265851011:1268047011` | Abamerica |
| Women's Tote Handbags | `7141123011:7147440011:15743631:16977746011` | HoogaLife, Abamerica |
| Travel Tote Bags | `7141123011:7147440011:15743631:15743241` | HoogaLife, Abamerica |
| Men's Food Service Uniforms | `7141123011:7147441011:7581682011:6575930011` | Abamerica |
| Insect & Pest Repellent Pouches | `2972638011:553844:3737951:220628941011` | Pesova |
| Ultrasonic Pest Repellers | `2972638011:553844:3737951:23539054011` | Pesova |
| Essential Oil Singles | `3760901:3760941:18502612011` | PUREU, Purefittech |
| Essential Oil Sets | `3760901:3760941:18502613011` | Abamerica |
| Women's Fashion Headbands | `3760911:11058051` | Abamerica |
| Reed Diffuser Oils | `1055398:3734261:3734281:16400691` | Purefittech, CLASSY |
| Flameless Candles | `228013:495224:3734261:14087331` | HoogaLife |
| Nameplates & Desk Tapes | `1064954:12900881` | C CLASSY PERSONALIZED JEWELRY |

### TikTok（7个L3品类）

| 品类 | category_path | l3_id |
|---|---|---|
| Women's Perfume | `[14, 856208, 855952]` | 855952 |
| Unisex Perfume | `[14, 856208, 855824]` | 855824 |
| Men's Perfume | `[14, 856208, 855696]` | 855696 |
| Perfume Sets | `[14, 856208, 856080]` | 856080 |
| Perfume (Generic) | `[14, 856208, 601583]` | 601583 |
| Car Air Freshener | `[23, 930184, 842256]` | 842256 |
| Pest & Weed Control | `[10, 852232, 600466]` | 600466 |

---

## 违规词库 & 错词库

- `references/amazon-prohibited-words.json` — 7类含 replacement_suggestions
- `references/tiktok-prohibited-words.json` — 7类中英双语含替代建议
- `references/common-typos.json` — 214通用+38电商+12单位错误

**检测逻辑：** `word.lower() in text.lower()` 子串匹配，TikTok扫描标题+采集描述全文

---

## 配置文件

`<skill>/templates/report-config.json` — 店铺映射、L3品类节点、自动映射规则(63条)、自有品牌列表。

---

## output/ 数据文件说明

| 文件 | 来源 | 用途 |
|------|------|------|
| `phase0_data.json` | 领星MCP | AMZ父ASIN+子ASIN清单、店铺映射 |
| `tiktok_data.json` | FastMoss MCP | TK商品清单、店铺信息 |
| `asin_detail_us1/us2/ca.json` | 卖酷MCP | ASIN详情(标题/五点/价格/BSR) |
| `amz_scrape_images.json` | scrape_amz_images.py | AMZ图片URL列表+A+模块结构 |
| `tk_product_details.json` | FastMoss MCP | TK商品详情+达人数据 |
| `tk_scrape_details.json` | scrape_tk_details.py | TK图片URL列表+描述文本 |
| `competitor_products.json` | 卖酷MCP | 竞品数据(含units/revenue) |
| `phase2_tiktok_scores.json` | FastMoss MCP | TK品类竞品Top10 |
| `ads_analysis.json` | Sif MCP + phase3 | 广告结构+详细策略 |
| `phase3_diagnosis_v3.json` | phase3_scoring_v3.py | 最终诊断评分结果 |

---

## 与其他 Skill 的协作

| Skill | 协作方式 |
|---|---|
| `amazon-listing-optimization` | 标题优化方法论 |
| `sys-amazon-listing-audit` | RUFUS 评分、banned claims |
| `tiktok-shop-listing-optimization` | TK标题/描述优化方法论 |
| `tiktok-shop-compliance` | TK合规检查 |
