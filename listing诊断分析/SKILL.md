---
name: listing-diagnosis
display_name: "亚马逊 & TikTok Listing 诊断分析"
display_name_en: "Amazon & TikTok Listing Diagnosis"
description: "跨平台Listing诊断——122个亚马逊父ASIN(1000条子ASIN) + 64个TikTok商品，8维度评分+修改建议+竞品对标(三级降级获取真竞品)+广告策略+违规词检测，输出10个Sheet的Excel报告。"
category: e-commerce
version: 3.5.1
author: AB America Corp
visibility: "public"
---

# 亚马逊 & TikTok Listing 诊断分析 v3.5.1

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
| Amazon | 17个店铺 (US 10 + CA 7) | 122个父ASIN / 1000条子ASIN | 24个L3品类 |
| TikTok | 2个店铺 (pureamor + pureamor_california) | 64个商品 | 4个L3品类 (实际在售) |

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

**1.5 竞品数据采集 — 真竞品精准匹配（2026-10-12 验证通过）：**

核心原则：**产品形态必须一致**。同L3品类≠同产品形态（例：Nameplates品类含办公桌名牌和tumbler name tag，只有后者是我们的真竞品）。

每个品类采集：
- **同外观真竞品 Top5**：产品形态、外观、场景完全一致的直接竞品，排除自有品牌/店铺
- **品类排名 Top15**：该细分品类销量/GMV前15，含自有品牌（标记`is_own_brand`/`Y`）

**亚马逊真竞品获取 — 三级降级策略（按优先级依次尝试）：**

```
Level 1: asin_competitor API（最佳质量，~25%覆盖率）
   asin_competitor(marketplace="US", asin=我方代表ASIN, size=15)
   → 返回与该ASIN最相似的竞品列表
   → 排除自有品牌后取Top5
   → 覆盖率低（大部分ASIN返回空数组），成功时数据质量最高

Level 2: 浏览器"Customers who viewed"抓取（推荐降级方案）
   当 asin_competitor 返回空时：
   1. navigate("https://www.amazon.com/dp/{我方ASIN}")
   2. javascript_tool 提取 carousel 中的 /dp/ASIN 链接：
      const items = document.querySelectorAll('[class*="a-carousel"] .a-link-normal[href*="/dp/"]');
      const asins = new Set(); const results = [];
      items.forEach(el => {
        const match = el.href.match(/\/dp\/([A-Z0-9]{10})/);
        if (match && !asins.has(match[1])) {
          asins.add(match[1]); const img = el.querySelector('img');
          results.push({asin: match[1], title: img ? img.alt.substring(0,80) : ''});
        }
      });
      JSON.stringify(results.slice(0, 15));
   3. 用 asin_detail 补全每个竞品的 brand/price/rating/ratings/imageUrl/fulfillment/lqs
   4. 排除自有品牌后取Top5

Level 3: Amazon搜索抓取（形态关键词搜索）
   当产品页面不存在或carousel无数据时：
   1. navigate("https://www.amazon.com/s?k={产品形态关键词}")
      关键词必须精准描述产品形态（如"tumbler name tag"而非"nameplate"）
   2. javascript_tool 提取搜索结果 [data-asin]：
      const cards = document.querySelectorAll('[data-asin]');
      const results = [];
      cards.forEach(card => {
        const asin = card.getAttribute('data-asin');
        if (!asin || asin.length !== 10) return;
        const titleEl = card.querySelector('h2 a span, h2 span');
        results.push({asin, title: titleEl ? titleEl.textContent.trim().substring(0,100) : ''});
      });
   3. 用 asin_detail 补全详情，排除自有品牌后取Top5
```

**品类排名 Top15（所有品类统一，使用 competitor_lookup）：**
```
competitor_lookup(marketplace="US", nodeIdPath=L3路径, month="YYYYMM",
                  variation="Y", size=15, order={field:"total_units", desc:true})
→ 含自有品牌，标记 is_own_brand
```

**验证步骤（每次更新竞品后必须执行）：**
```
1. 用 asin_detail 获取每个竞品的标题，确认产品形态与我方产品一致
2. 如有疑问，浏览器打开竞品页面查看图片确认外观
3. 确保所有竞品都有 title/brand/imageUrl 字段（无title的用asin_detail补全）
```

**已验证的品类特殊规则（2026-10-12）：**
| 品类 | 我方产品形态 | 竞品匹配要求 |
|---|---|---|
| LED Bulbs | 火焰灯泡 | 必须是flame/flickering light bulb，排除普通A19/BR30 |
| Stethoscopes | 听诊器套 | 必须是stethoscope cover/sleeve，排除真听诊器 |
| Medical Stethoscope Accessories | 听诊器套 | 同上 |
| Women's Tote Handbags | 护士包 | 必须是nurse bag/medical bag，排除时尚手提包 |
| Nameplates & Desk Tapes | Tumbler name tag | 必须是tumbler/Stanley name tag，排除办公桌名牌 |
| Automotive Air Fresheners | 挂式瓶香薰 | 排除skull/electronic/vent wrap等非挂瓶形态 |

输出：`output/competitor_products_v2.json`，每品类含 `true_competitors`(已验证) + `category_ranking`(完整排名)

**1.6 TikTok竞品（FastMoss product_rank_top_selling）：**
```
对每个TK L3品类:
  product_rank_top_selling(category_path=[L1,L2,L3], country="US", date_type="weekly")
  → 取Top10
```

**1.7 报告中自己产品按产品形态分组显示（v3.5.1新增）：**

TikTok的L3品类较粗（如Women's Perfume含55个产品），同一品类下产品的外观和使用场景差异大。报告的竞品分析Sheet中，自己的产品按**产品形态**分组显示：

```
产品形态分类规则（classify_tk_product_form）：
  keychain  — 标题含 keychain/keyring/key chain
  roll_on   — 标题含 roll-on/roll on/rollon
  oil       — 标题含 perfume oil
  mini_sample — 标题含 2ml（非keychain）
  travel_spray — 标题含 travel size/12ml/0.4oz/20ml/0.67oz
  full_spray — 标题含 30ml/1oz/50ml
  set       — 标题含 set/trio/pack/giftbox/bundle
  spray     — 默认（无特殊标识的喷雾）
```

报告显示结构：
```
■ Women's Perfume（品类标题）
  ★ 钥匙扣香水 (Keychain) (10)    ← 按形态分组的自己产品
    1. 产品A ...
    2. 产品B ...
  ★ 滚珠香水 (Roll-On) (8)
    1. 产品C ...
  ★ 旅行装喷雾 (Travel Spray) (5)
    ...
  ▸ 同外观真竞品 Top5              ← 品类级真竞品（当前共享）
  ▸ 品类排名 Top15                  ← 不变
```

亚马逊L3品类已足够细分（如Women's Eau de Parfum、Fragrance Sets分别独立），同品类产品形态基本一致，暂不需要子分组。

---

### Phase 2：广告分析（Sif MCP，仅亚马逊US）

**Sif MCP 连接重试策略：**
```
尝试调用 Sif MCP 工具前，先检查连接状态。
如果连接失败（CONNECT_TIMEOUT 等错误），执行以下重试流程：
1. 等待 10 秒，第1次重试
2. 等待 20 秒，第2次重试  
3. 等待 30 秒，第3次重试
共3次重试，每次间隔递增。3次全部失败后：
- 在报告中标注"Sif数据未采集"
- 广告分析Sheet保留已有数据或标记为待补充
- 不阻断其他Phase的执行
```

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

#### 10个Sheet

| # | Sheet名 | 行数 | 关键特性 |
|---|---------|------|---------|
| 1 | **诊断摘要** | ~27 | AMZ+TK等级分布、违规词统计、竞品覆盖率、数据覆盖率 |
| 2 | **亚马逊Listing诊断** | 122 | ASIN带超链接、修改标题、五点建议、图片建议（含实际张数）、A+建议、综合评分 |
| 3 | **TikTok Listing诊断** | 64 | 产品ID带超链接、修改标题、描述建议（含实际字数）、图片建议（含实际张数）、综合评分 |
| 4 | **竞品-同外观Top5** | ~69 | 排除自有品牌，每品类取Top5竞品，含月销量/月销售额/BSR/LQS |
| 5 | **竞品-同场景品类前20** | ~119 | 含所有品牌（自有品牌标"Y"绿底），每品类Top20 |
| 6 | **TikTok竞品分析** | ~83 | 商品ID带超链接、周GMV、累计GMV、达人数、增长率 |
| 7 | **子ASIN运营附表** | ~1000 | 子ASIN价格/FBA库存/配送方式，价格异常(偏差>30%黄/>50%红)，库存预警(断货红/低库存黄) |
| 8 | **违规词&错词汇总** | ~173 | ASIN/商品ID、违规词、类别、严重程度、出现位置、上下文、替换建议 |
| 9 | **广告分析&策略建议** | 92 | ASIN带超链接、Campaign结构(SP/SB/SBV)、流量占比、**详细策略建议**(含竞价) |
| 10 | **数据覆盖率** | ~14 | 各数据源覆盖统计、状态标色(OK绿/P黄/!红) |

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

### 一键运行（推荐）

```bash
python -I scripts/run_all.py
```

自动执行：数据文件检查 → Phase 3 评分 → Phase 5 报告生成 → 清理旧报告。

```bash
python -I scripts/run_all.py --data-check-only   # 仅检查数据文件
python -I scripts/run_all.py --skip-scoring       # 跳过评分，直接生成报告
```

### 全量运行（约45-50分钟）

按顺序执行Phase 0-5，MCP数据采集 → HTTP抓取 → 一键生成：

```
1. 执行 Phase 0: 领星拉取AMZ商品 + FastMoss拉取TK商品
2. 执行 Phase 1.1-1.3: 卖酷asin_detail + FastMoss TK详情
3. 执行 Phase 1.5-1.6: 卖酷竞品(每品类Top20) + FastMoss TK竞品
4. 执行 Phase 2: Sif广告分析（失败自动重试3次）
5. 运行 python -I scripts/scrape_amz_images.py   (AMZ图片+A+采集, ~10min)
6. 运行 python -I scripts/scrape_tk_details.py    (TK图片+描述采集, ~2min)
7. 运行 python -I scripts/run_all.py              (一键评分+报告生成)
```

### 仅重新生成报告（已有数据时，约1分钟）

```bash
python -I scripts/run_all.py
```

---

## 脚本说明

| 脚本 | 功能 | 输入 | 输出 |
|------|------|------|------|
| `scrape_amz_images.py` | 抓取Amazon页面提取图片列表+A+结构 | phase0_data.json | amz_scrape_images.json |
| `scrape_tk_details.py` | 抓取TikTok页面提取图片+描述 | tiktok_data.json | tk_scrape_details.json |
| `phase3_scoring_v3.py` | 8维度评分+建议生成+广告策略 | 所有output/*.json + references/*.json | phase3_diagnosis_v3.json |
| `phase5_report_v3.py` | 生成10-Sheet Excel报告 | 所有output/*.json | Listing诊断报告v3.1_*.xlsx |
| `run_all.py` | 一键运行：数据检查→评分→报告→清理 | 所有output/*.json | 最终Excel报告 |

**所有脚本的 BASE 路径：** 脚本内硬编码 `output` 目录路径，运行前确认路径正确。

---

## 当前商品库存快照（2026-10-12 验证）

### 亚马逊：17个店铺 / 122个父ASIN / 1000条子ASIN

| 店铺 | 国家 | 父ASIN | 品牌 | 负责人 |
|------|------|--------|------|--------|
| Classy AP-HL-25-2 | US | 36 | CLASSY, Airpurelle, Pureamor, C CLASSY, Generic | AMZ-L3-Chong, Richer, Alvin, Luo, Stella |
| Abamerica-Tony-19-3 | US | 19 | Abamerica, HoogaLife | AMZ-L2-Abbott |
| Abamerica-Tony-19-3 | CA | 11 | Abamerica, HoogaLife | AMZ-L2-Abbott |
| PureU-Lori-25-6 | US | 10 | PUREU | AMZ-L2-Alvin Yue, AMZ-L2-Luo |
| Pureamor-Yu-25-4 | US | 10 | Pureamor, LUXEA | AMZ-L2-Alvin Yue |
| Hoogalife-Tao-19-1 | US | 7 | HoogaLife | AMZ-L2-Abbott, AMZ-L3-Richer |
| Pureamor-Yu-25-4 | CA | 6 | Pureamor | AMZ-L2-Alvin Yue |
| PureFitTech-Mei-25-7 | US | 5 | Purefittech | AMZ-L2-Luo, DesL2-AMZL3-Stella |
| Classy AP-HL-25-2 | CA | 5 | CLASSY, Pureamor | AMZ-L3-Chong |
| Caliwest PU-Zhang-26-5 | US | 3 | PUREU | AMZ-L3-Richer |
| PureU-Lori-25-6 | CA | 3 | PUREU | AMZ-L2-Alvin Yue, AMZ-L2-Luo |
| PureFitTech-Mei-25-7 | CA | 2 | Purefittech | AMZ-L2-Luo |
| Burst Bird-MJ-20-9 | US | 1 | Burst Bird | — |
| Burst Bird-MJ-20-9 | CA | 1 | PUREFITINSOLES | — |
| Pesova-Du-25-8 | US | 1 | Pesova | AMZ-L3-Chong |
| Hoogalife-Tao-19-1 | CA | 1 | HoogaLife | AMZ-L2-Abbott |
| Caliwest PU-Zhang-26-5 | CA | 1 | PUREU | AMZ-L3-Richer |

### TikTok：2个店铺 / 64个活跃商品

| 店铺 | 商品数 | 主要品类 | 品类分布 |
|------|--------|---------|---------|
| pureamor（主店） | 58 | Women's Perfume (51), Unisex Perfume (6), Perfume Sets (1) | 香水为主 |
| pureamor_california（副店） | 6 | Women's Perfume (4), Unisex Perfume (1), Pest Control (1) | 香水+驱虫 |

> **未匹配L3品类的2个ASIN**：B0H7RQ4ND6（心形项链）、B0H7GN79QX（天使翼钥匙扣），均为Generic品牌首饰，不影响主体分析。

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

## 全量流程验证记录（2026-10-12）

6阶段全部跑通，4个MCP数据源连接正常，本地脚本无报错。

| Phase | 测试内容 | 状态 | 结果详情 |
|-------|---------|------|---------|
| **0** 商品拉取 | 领星 erp_listing 分页 + FastMoss shop_product | ✅ | 领星930条/50每页/19页，数据结构 `data.data.data.list`；FastMoss主店47商品/28d GMV $25,974 |
| **1.1** ASIN详情 | 卖酷 asin_detail | ✅ | 测试B0H2DPL94Y：标题/价格$16.99/BSR 21000/评分4.2/LQS 93/变体数完整返回 |
| **1.3** TK详情 | FastMoss product_detail_info | ✅ | 测试钥匙扣香水：$11.05/4.5★/1945评论/722达人/总GMV $106K |
| **1.6** TK竞品 | FastMoss product_rank_top_selling | ✅ | Women's Perfume周榜Top3返回，QAWAFI $544K/周居首 |
| **2** 广告分析 | Sif ads_get_asin_ad_structure | ✅ | B0H2DPL94Y：4活动(SP×3+SB×1)，数据更新至10/11 |
| **2** 流量分析 | Sif ops_get_listing_traffic_overview | ✅ | 广告40.1%/自然59.9%，SB占广告流量97.5%，总分1673 |
| **3** 诊断评分 | phase3_scoring_v3.py | ✅ | AMZ 122个/avg 88.5/A89·B33；TK 64个/avg 88.1/A47·B16·C1；违规词AMZ95+TK78；广告策略92条 |
| **4** 子ASIN扫描 | 领星已有数据本地计算 | ✅ | 1000条子ASIN价格异常/FBA库存/Buy Box全部计算，零额外API |
| **5** 报告生成 | phase5_report_v3.py | ✅ | 10 Sheet / 300KB：摘要34行·AMZ诊断122·TK诊断64·AMZ竞品578·TK竞品235·子ASIN 1000·违规词173·广告92·覆盖率17·验证31 |

**MCP连接稳定性：**
- 领星：偶发 `mcp-remote: fetch failed`，重试1次即恢复
- 卖酷：稳定
- FastMoss：偶发 `Server unavailable`，重试2-3次恢复；注意 seller_id 必须使用 `7496269973698153227`
- Sif：稳定，数据延迟1天（T-1）

---

## 与其他 Skill 的协作

| Skill | 协作方式 |
|---|---|
| `amazon-listing-optimization` | 标题优化方法论 |
| `sys-amazon-listing-audit` | RUFUS 评分、banned claims |
| `tiktok-shop-listing-optimization` | TK标题/描述优化方法论 |
| `tiktok-shop-compliance` | TK合规检查 |
