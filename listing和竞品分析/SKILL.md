# TikTok Shop Listing 诊断 + 竞品分析（v6.2）

> 输入一个 TikTok Shop 产品链接/ID/关键词/店铺名 → 输出一份 **Listing 诊断 + 竞品分析** 报告（HTML，发布为在线 Artifact）。
> **本文件是唯一权威**，与 `skills/` 下子文件冲突时一律以本文件为准。

## 目录

| # | 章节 | 回答什么问题 |
|---|------|------------|
| 一 | [运行机制总览](#一运行机制总览) | 这个 Skill 是怎么跑起来的 |
| 二 | [取数链路（逐步）](#二取数链路逐步) | 每一步调什么 API、传什么参数、取回什么 |
| 三 | [维度字段总清单](#三维度字段总清单) | 到底取了哪些字段、口径是什么、用在哪 |
| 四 | [派生指标计算公式](#四派生指标计算公式) | 哪些数字是算出来的、怎么算 |
| 五 | [数据真实性红线](#五数据真实性红线) | 什么情况下这份报告不合格 |
| 六 | [竞品选取规范](#六竞品选取规范) | 谁算竞品、怎么选、怎么验证 |
| 七 | [报告各板块内容规范](#七报告各板块内容规范) | 每个板块必须写什么 |
| 八 | [评分规定](#八评分规定) | 分数怎么来、怎么展示 |
| 九 | [写作与排版规范](#九写作与排版规范) | 文字和样式怎么写 |
| 十 | [交付前检查清单](#十交付前检查清单) | 发布前逐条核对 |

---

## 一、运行机制总览

### 1.1 输入 → 处理 → 输出

```
输入：产品链接 / 产品ID / 关键词 / 店铺名
  ↓
阶段 A  定位分析对象 + 类目坐标      → 拿到 product_id + L1/L2/L3 category_id
  ↓
阶段 B  本品全量取数（7 个 API）      → 产出「概览」的 ①③④⑤ 段
  ↓
阶段 C  L3 类目大盘取数（榜单1-50）   → 产出「概览」的 ② 段 + TOP20标题词源 + 竞品候选池
  ↓
阶段 D  竞品选取与取数（7+3，AI看图）  → 产出「概览」⑥ 段 + Section 1 全部
  ↓
阶段 E  诊断与评分                    → 产出 Section 2 + Section 3
  ↓
输出：Markdown 报告（供确认）→ HTML → 发布为在线 Artifact，回传链接
```

### 1.2 五个阶段与报告板块的映射

| 阶段 | 主要动作 | 调用的 API | 产出报告的哪一块 |
|------|---------|-----------|----------------|
| **A 定位** | 确定 product_id、拿到 L3 类目 ID | `product_search`、`search_category_by_words` | （不直接产出，为后续提供坐标） |
| **B 本品** | 把本品的身份/销售/流量/内容/SKU/评价全部取一遍 | `product_detail_info`、`product_overview`、`product_sku`、`product_video_list`、`product_creator_analysis`、`product_review_list`、`shop_base_info` | 概览 ①诊断产品 ③店铺 ④趋势 ⑤MSKU |
| **C 大盘** | L3 榜单 1–50 名分页取全，逐条加总 | `product_rank_top_selling`(5页) | 概览 ②类目大盘 + 2.1 选词词源 |
| **D 竞品** | 7+3 选品（AI 看图定形态）→ 逐个取数 → 形态生存力验证 | 对 10 款各调 `product_detail_info`+`product_overview`+`product_video_list`，对 5 款补 `product_creator_analysis` | 概览 ⑥竞品表 + Section 1 全部 |
| **E 诊断** | 选词/标题/描述/图片/评论诊断 + 打分 + 风险 | 不新增取数，Browser pane AI 看图 | Section 2 + Section 3 |

### 1.3 触发与反问

- 给了链接 / ID / 关键词 / 店铺名 → **执行完整 5 阶段**，禁止只出 Listing 诊断而漏掉竞品分析
- 没给产品信息 → 反问要链接/ID/关键词/店铺名
- 给了非 TikTok Shop 链接 → 说明只支持 TK Shop
- 只给店铺名 → 先 `shop_search` 列出 TOP 产品让用户选
- 只给类目词 → 问是要整体格局还是具体产品
- 市场默认 **US**，竞品自动筛选，这两项不反问

### 1.4 运行前置检查

```
1. credit_usage_summary()  → 确认额度充足（整套流程约 25–35 次调用）
2. 取数日期记录下来，报告里要写明"数据取自 YYYY-MM-DD"
3. date_value 只能传已完成周期（上周 YYYY-Www / 昨天 YYYY-MM-DD / 上月 YYYY-MM）
```

### 1.5 Token 控制

- MCP 返回的原始 JSON **不写入上下文**，只提取需要的字段（标题必须完整，禁止截断）
- 阶段 A–D 用精简 Markdown 记录中间结果，**不输出 HTML**
- HTML 只在最后一步生成一次

---

## 二、取数链路（逐步）

> 每一步统一写清：**调什么 → 传什么 → 取回什么 → 干什么用**

### 阶段 A：定位分析对象 + 类目坐标

**A1. 拿到 product_id**（用户给了链接/ID 则跳过）

```
product_search({
  keywords: "<产品名或关键词>",
  filter: { region: "US" },
  orderby: [{ field: "day28_gmv", order: "desc" }],
  pagesize: 10
})
```
取回：`product.product_id / title / price_display / product_rating / sku_count`、`sales_summary.last_7d|28d|90d_gmv / units_sold`、`distribution_summary.linked_creator_count / linked_video_count`、`shop.shop_name / shop_id`

**A2. 拿到 L3 类目 ID**

```
search_category_by_words({ query: "<类目词>", top_k: 8 })   ← 参数名是 query，不是 keywords
```
取回：`category_id_level1 / level2 / level3` + `cn_full_name`
用途：L3 id 是后面所有榜单调用的坐标；**L1 id 只用于记录类目路径，不参与任何数据计算**

---

### 阶段 B：本品全量取数

**B1. 产品主档**
```
product_detail_info({ filter: { product_id } })
```
取回（**报告里最核心的一批字段**）：
`title`(完整) / `floor_price`+`ceiling_price` / `commission_rate_percent` / `product_rating` / `review_count` / `shipping_fee` / `stock_count` / `category_sales_rank`(**L3排名**) / `launch_time`(**上架时间**) / `total_gmv`+`total_units_sold`(**累计**) / `has_paid_promotion` / `linked_creator_count` / `linked_video_count` / `linked_live_count` / `cover_url` / `shop.shop_id`(**即 seller_id**) / `shop.shop_total_gmv` / `shop.shop_total_units_sold`

**B2. 流量与渠道结构**
```
product_overview({ filter: { product_id, time_range_days: 28 } })
```
取回：
- `channel_distribution.breakdown[]` → **affiliate=达人渠道 / product_card=商品卡 / shop_account** 各自 `gmv` 与 `gmv_share_percent`
- `content_distribution.breakdown[]` → video / live / product_card
- `ads_distribution.breakdown[]` → **ad_traffic 占比**（判断是自然流量还是买量驱动）
- `period_summary.linked_creator_count` → **28天活跃达人数**（注意：与 detail_info 的累计达人数不是一回事）
- `daily_trend[]` → 每日 `date / daily_gmv / daily_units_sold / cumulative_*` → 画28天趋势图

**B3. MSKU 变体**
```
product_sku({ filter: { product_id, time_range_days: 28 } })
```
取回：
- `sku_variants[]` → 每个变体的 `current_price` / `original_price` / `stock_units`
- `sku_dimensions[].distribution_summary.breakdown[]` → 每个变体的 `units_sold` / `units_sold_share_percent` / `gmv` / `gmv_share_percent` / `stock_units` / `stock_share_percent`
- `total_gmv` / `total_units_sold` / `total_stock_units`（SKU 口径合计）

> ★ SKU 口径合计常小于整品 28 天数据（部分订单未归因到具体变体），**报告中要如实注明差额来源**，不要强行对齐。

**B4. 带货视频**
```
product_video_list({
  filter: { product_id, time_range_days: 28 },     ← ★ 不传 time_range_days 会返回空
  orderby: [{ field: "play_count", order: "desc" }],
  pagesize: 5
})
```
取回：`videos[].engagement_metrics.play_count / like_count`、`product_contribution.window_gmv / window_units_sold`、**`traffic_flags.is_ad`（是否投流）**、`video_meta.duration_seconds / published_at / tiktok_url`、`creator.creator_handle`

> ★ `is_ad` 很关键：一条"有转化的达人视频"如果是投流的，说明自然内容转化其实为 0。

**B5. 达人明细**
```
product_creator_analysis({
  filter: { product_id },
  orderby: [{ field: "product_gmv", order: "desc" }],
  pagesize: 10
})
```
取回：`creator_summary.follower_tier_distribution`（粉丝层级分布）、`linked_creators.list[].creator.creator_handle / follower_count`、**`product_contribution.product_gmv / product_units_sold / product_linked_video_count`（每个达人的累计带货GMV）**

**B6. 评论**
```
product_review_list({ filter: { product_id } })
```
- 评论量 <500 时大概率返回 0 条 → 降级跑 `python scripts/tiktok_review_scraper.py {product_id}`
- 仍失败 → 只用 `detail_info` 的 `product_rating` + `review_count` 做量化对比，**不编造评论原文**

**B7. 店铺**
```
shop_base_info({ seller_id })          ← ★ 用 detail_info 里的 shop.shop_id，不是别处的 shop_id
shop_product_analysis({ seller_id })
```
取回：店铺总GMV / 总销量 / 在售商品数 / 店铺评分 / 48h发货率 / 好评率 / 24h回复率；多产品线分布

---

### 阶段 C：L3 类目大盘取数

```
for page in 1..5:
  product_rank_top_selling({
    filter: { category_id: <L3 id>, date_type: "week", date_value: "<已完成周 YYYY-Www>", region: "US" },
    orderby: [{ field: "period_gmv", order: "desc" }],
    page: page, pagesize: 10          ← pagesize 上限就是 10，必须分 5 页
  })
```
取回每条：`product_id / title(完整) / cover_url / floor_price+ceiling_price / commission_rate_percent / period_gmv / period_units_sold / total_gmv / total_units_sold / units_sold_growth_rate_percent / launch_date / shop.shop_name`

**这一次调用同时供给三件事**：
1. **L3 大盘指标**（逐条加总，公式见 §四）
2. **TOP20 完整标题** → 2.1 选词的唯一词源
3. **竞品候选池**（1–50 名的 `cover_url` 用于看图定形态）

> ★ 榜单常混入错分类目产品（车香薰榜出现过男士发胶、洗衣机清洁片），**必须识别并剔除，在报告注明实际分母**。
> ★ `market_category_analysis` **已停用**——它只支持 L1，而 L1（如 Automotive）含轮胎车灯等无关品类，用它算市占率会失真到没有决策价值。

---

### 阶段 D：竞品选取与取数

**D1. 7+3 选品**（规则详见 §六）
- 前 7 席：榜单自然排名 1–7
- 后 3 席：榜单 8–50 名中**与本品外观形态一致**的，按近7天销量取前 3

**D2. AI 看图定形态**（不可省略）
```
把候选的 cover_url 拼成一页本地 HTML → Browser pane 打开 → AI 截图识别，逐张比对外观
```
归类：圆柱坐杯架 / 挂绳挂件 / 出风口夹式 / 贴片 / 喷雾瓶 / 电子设备…
只保留与本品**外观真正一致**的。
> 形态判定由 AI 视觉完成（Claude 通过 Browser pane 截图分析主图），**不依赖标题关键词**。标题常省略形态词或使用泛称，只看标题会全判错。

**D3. 逐个取数**
```
对矩阵 10 款：product_detail_info + product_overview(28) + product_video_list(7)
对选定的 5 个对标竞品，补：product_creator_analysis (+ product_sku / product_review_list 按需)
```

**D4. 形态生存力验证**（4 项证据，详见 §六）

**D5. 僵尸链接剔除**
近 7/28/90 天销量均为 0、且达人数/视频数≈0 的 listing → **不计入竞品对比**，但在报告中说明"检索到 N 条同形态，其中 M 条为零动销僵尸链接"。

---

### 阶段 E：诊断与评分

不新增 FastMoss 取数，只做两件事：
1. **Browser pane AI 看图**：打开 `https://shop.tiktok.com/us/pdp/-/{product_id}`，AI 截图分析主图背景/角度/信息图/场景/SKU缩略图区分度（FastMoss 只给图片 URL 和数量，**不判断图片内容**）
2. **计算与判断**：TOP20 词频统计、六维度打分、风险汇总

---

## 三、维度字段总清单

> 这张表回答"到底取了哪些维度、每个字段从哪来、什么口径、用在报告哪里"。

### 3.1 产品身份维度

| 字段 | 来源 | 用在哪 |
|------|------|--------|
| 产品标题（完整不截断） | `product_detail_info.title` | 概览①、2.1 选词与标题改写 |
| 产品ID / 详情页链接 | `product_id` / 拼 `https://shop.tiktok.com/us/pdp/-/{id}` | 全篇可点击链接 |
| 店铺名 | `detail_info.shop.shop_name` | 概览①⑥、矩阵 |
| **产品形态**（挂式/杯架式/夹式…） | `cover_url` → **AI 看图判定** | **矩阵第1行**、竞品选取、形态生存力验证 |
| **驱动方式**（被动挥发/电子喷雾…） | 标题 + 主图综合判断 | **矩阵第2行** |
| 上架时间 | `detail_info.launch_time` | 矩阵、形态生存力验证证据② |
| L3 类目排名 | `detail_info.category_sales_rank` | 概览②、矩阵 |

### 3.2 销售表现维度

| 字段 | 来源 | 口径 |
|------|------|------|
| 周GMV / 周销量 | `product_rank_top_selling.period_gmv / period_units_sold` | 某个**已完成周** |
| 28天GMV / 销量 | `product_overview.period_summary.period_total_gmv / period_total_units_sold` | 近28天 |
| 累计GMV / 累计销量 | `detail_info.total_gmv / total_units_sold` | 上架至今 |
| 日销趋势 | `product_overview.daily_trend[]` | 每日 |
| 增长率 | 榜单 `units_sold_growth_rate_percent` | 周环比 |

### 3.3 流量结构维度

| 字段 | 来源 | 说明 |
|------|------|------|
| **达人渠道GMV占比** | `product_overview.channel_distribution` → `affiliate.gmv_share_percent` | 最能反映达人渠道真实贡献 |
| 商品卡GMV占比 | 同上 → `product_card.gmv_share_percent` | 占比过高=被动等客 |
| 视频 / 直播 GMV占比 | `content_distribution.breakdown[]` | video / live |
| **广告流量占比** | `ads_distribution` → `ad_traffic.gmv_share_percent` | 判断增长是买量还是自然 |

### 3.4 内容与达人维度

| 字段 | 来源 | 说明 |
|------|------|------|
| 关联达人数（累计） | `detail_info.linked_creator_count` | 矩阵 |
| **28天活跃达人数** | `product_overview.period_summary.linked_creator_count` | 与累计数区分开 |
| 关联视频数 / 直播场次 | `detail_info.linked_video_count / linked_live_count` | 矩阵 |
| **每个达人的带货GMV** | `product_creator_analysis` → `linked_creators.list[].product_contribution.product_gmv` | 算逐人占比 |
| 达人粉丝数 | `linked_creators.list[].creator.follower_count` | 看"粉丝量与转化是否脱钩" |
| 粉丝层级分布 | `creator_summary.follower_tier_distribution` | 达人结构判断 |
| 视频播放量 | `product_video_list.videos[].engagement_metrics.play_count` | 算视频均播 |
| **视频是否投流** | `videos[].traffic_flags.is_ad` | 判断自然转化真实性 |

### 3.5 商品要素维度

| 字段 | 来源 | 说明 |
|------|------|------|
| 现价 / 原价 | `product_sku.sku_variants[].current_price / original_price` | 变体级真实价格 |
| 价格区间 | `detail_info.floor_price / ceiling_price` | 产品级展示价 |
| 佣金率 | `detail_info.commission_rate_percent` | 矩阵、佣金策略 |
| 运费 | `detail_info.shipping_fee` | 算到手价 |
| 库存（总/分变体） | `detail_info.stock_count`、`sku` 的 `stock_units` | 断货风险 |
| SKU数 | `detail_info.has_sku_options` + `sku_variants` 长度 | 矩阵 |
| 各变体销量/GMV/库存占比 | `product_sku.distribution_summary.breakdown[]` | 概览⑤ MSKU表 |

### 3.6 评价维度

| 字段 | 来源 | 说明 |
|------|------|------|
| 评分 | `detail_info.product_rating` | 矩阵、2.3 |
| 评论数 | `detail_info.review_count` | 矩阵、2.3 |
| 评论原文 | `product_review_list` → 降级爬虫 | 2.3 原文样本、竞品痛点 |

### 3.7 店铺维度

店铺总GMV / 总销量 / 在售商品数 / 店铺评分 / **48h发货率** / 好评率 / 24h回复率 → `shop_base_info(seller_id)` → 概览③ + 风险评估

### 3.8 类目大盘维度（全部 L3 口径）

TOP10周GMV合计 / TOP50周GMV合计 / TOP10周销量合计 / **头部集中度** / 在榜商品数 / 主流价格带 / 本品L3排名 / 本品占TOP50份额 → 由榜单 1–50 名**逐条加总**得出（公式见 §四）→ 概览②

### 3.9 口径统一规则（全篇必须一致）

| 指标 | 统一口径 |
|------|---------|
| 周数据 | 榜单某个已完成周 |
| 28天数据 | `product_overview(time_range_days:28)` |
| 累计数据 | `detail_info.total_*` |
| **单达人GMV占比** | 该达人**累计**带货GMV ÷ 产品**累计**总GMV（本品与竞品同口径，禁止一个用周一个用累计） |
| 达人激活率 | 28天活跃达人 ÷ 达人总数 |
| 视频均播 | 指定窗口内 **Top5 视频 play_count 均值**，窗口必须在表头注明 |

> **`≈` 的使用边界**：只能用于确实取不到的字段；**矩阵核心行（形态/价格/佣金/GMV/销量/评分/评论/达人/视频/运费/排名/上架时间）一律不允许出现 `≈`**。缺数据就再调一次 API，不要估。

### 3.10 API 已知坑

| 工具 | 坑 | 处理 |
|------|----|------|
| `market_category_analysis` | 只支持 L1，基数失真 | **停用**，改 L3 榜单加总 |
| `product_video_list` | 不传 `time_range_days` 返回空 | 必传 7 或 28 |
| `product_review_list` | 评论<500 返回 0 条 | 爬虫降级 → 只用统计值 |
| `shop_base_info` | 需 `seller_id` | 用 `detail_info.shop.shop_id` |
| `search_category_by_words` | 参数是 `query` | 不是 keywords |
| `product_rank_top_selling` | `category_id` 需数字；`date_value` 只能是已完成周期；pagesize≤10 | 分 5 页取 |
| `product_detail_info` | 偶发 500 | 重试 1 次 |
| 榜单数据 | 混入错分类目产品 | 识别剔除并注明分母 |

---

## 四、派生指标计算公式

> 报告里所有"算出来的数字"，公式统一在这里，避免各处口径打架。

**类目大盘**
```
L3 TOP10 周GMV合计 = Σ period_gmv (榜单第1–10名)
L3 TOP50 周GMV合计 = Σ period_gmv (榜单第1–50名)
头部集中度        = TOP10周GMV合计 ÷ TOP50周GMV合计
本品占大盘份额     = 本品周GMV ÷ TOP50周GMV合计     （注明为 TOP50 口径）
进TOP50的GMV门槛   = 榜单第50名的 period_gmv
主流价格带        = TOP10 的 floor_price 最小值 ~ ceiling_price 最大值
```

**矩阵均值**（注意：均值是"矩阵这 10 款"的均值，不是"榜单前10名"的均值，两者产品集不同，标签必须写清楚）
```
矩阵均值 = Σ(矩阵10款的该字段) ÷ 10
```

**价格与佣金**
```
到手价          = 售价 + 运费
创作者单笔收入   = 售价 × 佣金率
28天成交均价     = 28天GMV ÷ 28天销量
```

**达人与内容**
```
达人渠道GMV占比  = channel_distribution.affiliate.gmv_share_percent   （直接取，不自己算）
达人激活率      = 28天活跃达人 ÷ 达人总数
单达人GMV占比    = 该达人累计 product_gmv ÷ 产品累计 total_gmv
TOP5达人GMV占比  = Σ(前5达人 product_gmv) ÷ 产品累计 total_gmv
视频均播        = Σ(Top5 视频 play_count) ÷ 5
```

**关键词**
```
词频覆盖 = 含该词的标题数 ÷ 有效标题数（TOP20 剔除错分类目后的实际条数）
热度分级 = ≥47% 极高 / 26–46% 高 / 16–25% 中 / 5–15% 低 / 0 类目无人使用
```

**库存**
```
预计断货天数 = 当前库存 ÷ (28天销量 ÷ 28)
库存占比    = 该变体库存 ÷ 全部变体库存合计
```

---

## 五、数据真实性红线

```
□ 类目大盘为 L3 榜单逐条加总，全篇不出现 L1 的周GMV/周销量/同比增长
□ 矩阵的每一个单元格都是本次实取；不得沿用上一版报告或历史数值
□ 易变字段（类目排名、店铺GMV、售价、库存）每次重新取数
   （实测踩过：L3排名差 700 名、店铺GMV差 130%、评论数估值差 13 倍）
□ 同形态竞品经主图 AI 视觉比对确认，未仅凭标题关键词判定
□ 榜单已剔除错分类目产品，并注明实际分母
□ 已剔除僵尸链接（近7/28/90天销量均0、无达人无视频）后再做对比
□ 关键词频次为 TOP20 标题实际统计，非估算
□ 占比口径全篇统一，本品与竞品同口径
□ "蓝海/差异化窗口"类结论已通过形态生存力 4 项证据检验
□ 竞品描述/图片类判断只基于可验证字段或 AI 看图，无臆测
□ 可量化承诺（天数/尺寸/倍数）标注"需真实测试后再上架"
□ 报告中写明数据核验说明：取数日期、数据来源、本轮修正了哪些旧值
```

---

## 六、竞品选取规范

### 6.1 TOP 10 矩阵 = 7 + 3

- **前 7 席**：L3 榜单自然排名 1–7
- **后 3 席**：榜单 **8–50 名**中**与本品外观形态一致**的，按**近7天销量**取前 3（列头标注榜单原始名次）
- 不足 3 个 → 放宽到 8–100 名 → 仍不足则**如实写明检索范围与结果，不得凑数**

**为什么**：只取前 10 名往往全是同一种主流形态，本品形态一个可比对手都没有，"选择理由"只能写成"同价位/高佣金"这类与形态无关的空话。

### 6.2 同形态判定——AI 视觉识别（不可省略）

把候选 `cover_url` 拼成一页本地 HTML → Browser pane 打开 → **AI 截图后逐张识别外观**，按形态归类，只保留与本品真正一致的。

> 实测教训：关键词搜 "cup holder" 会漏掉不写形态词的同形态产品；而销量很高的 R&W（821件/周）主图是挂绳款、JOYTUTUS（159件/周）是出风口夹式——只看标题会全判错。

### 6.3 ★ 形态生存力验证（出现"蓝海"结论前必做）

"同形态竞品少"有两种相反解释：**蓝海**（没人做）or **死海**（做的人都被淘汰了）。必须用 4 项证据判别并在报告中列表呈现。

#### 6.3.1 同形态产品逐款明细表（必须先输出）

在 4 项证据表**之前**，先输出一张「同形态产品逐款数据明细表」，逐款列出每个同形态竞品 + 本品的完整数据，字段如下：

| 列 | 来源 |
|----|------|
| 产品名+链接 | `product_detail_info` |
| 售价 | `floor_price`–`ceiling_price` |
| 周销量 | `product_rank_top_selling` 或 `product_overview` |
| 周GMV | 同上 |
| 累计GMV | `product_detail_info.total_gmv` |
| 评分/评论数 | `product_rating` / `review_count` |
| 达人数 | `linked_creator_count` |
| 视频数 | `linked_video_count` |
| L3排名 | `category_sales_rank` |
| 上架时间（含已运营时长） | `launch_time` |
| 驱动方式 | AI 看图判定 |

末行为**合计/均值行**，再加一行**本品对比行**（高亮）。此表让读者一眼看清每款同形态产品的完整画像，而非只看到一个合计数字。

#### 6.3.2 4 项证据表

| 证据 | 取数 | 判读 |
|------|------|------|
| ① 同形态是否还在卖 | 同形态竞品**逐款**周销量/周GMV/累计GMV（从 6.3.1 表引用具体数字） | 有可观动销 → 非死形态 |
| ② 新入场者能否跑起来 | 同形态竞品 `launch_time` vs `category_sales_rank`，**逐款列出上架时长与当前排名** | 近期上架且排名靠前 → 赛道扩张 |
| ③ 零动销的同形态是没人要还是没推 | 零销量产品的 `linked_creator_count` / `linked_video_count`，**与有销量产品的达人/视频数做显式对比** | 内容投入≈0 → 营销缺位而非需求缺位 |
| ④ **成功者长什么样（最关键）** | 跑出来的同形态产品的**属性/驱动方式/价格带**与本品逐项比对，**引用具体售价区间和驱动方式** | 成功者的关键特征本品**不具备** → 本品处在**未被验证的子形态**，是风险不是机会 |

> **⚠ 4 项证据中引用的数据必须与 6.3.1 明细表完全一致**，且必须拆到单个产品（"Autrex 周销 313 件/$6,776"而非只写"3 款合计 760 件"）。合计数字可以有，但单品拆解不可省。

**结论必须分层**：把"形态/位置是否成立"与"本品的具体子形态是否被验证过"分开写，禁止用前者的乐观结论掩盖后者的风险。

### 6.4 5 个对标竞品与「选择理由」写法

- **同形态 3 席优先全部入选**，再从前 7 名补 1–2 个头部标杆
- 选择理由必须按三要素模板写，**不得写成"TOP1/同价位/高佣金标杆"这类与竞品定义无关的排名描述**：

```
外观：[与本品形态的相似点]；场景：[使用场景是否一致]；属性：[核心功能/材质/规格的异同，可附价格区间]
```

- 形态有差异时**必须如实说明差异并解释为何仍纳入对比**

---

## 七、报告各板块内容规范

### 7.1 报告结构（4 板块，不多不少）

```
Header → 双评分环（X/60 + X/10）
★ 诊断对象与竞品概览
   ①诊断产品 → ②类目大盘(L3) → ③店铺级数据 → ④28天趋势 → ⑤MSKU变体表 → ⑥5个对标竞品
Section 1  TOP 10 竞品全景矩阵
   1.1 转置矩阵(7+3) → 数据核验说明 → 构成说明 → 竞争位置 → ★形态生存力验证
   1.2 达人与流量结构对比 → 达人明细(逐人占比) → 佣金策略 → 达人招募策略
Section 2  Listing 诊断与优化
   评分总览 → 2.1 标题·描述·SEO → 2.2 图片与详情页 → 2.3 合规与评论
Section 3  风险评估（≥5条）
```

**不应出现**：独立的"市场背景 / 达人与内容 / 优化行动方案 / VOC / 竞品与市场分析"板块、逐个竞品拆解卡片、对比维度说明表、评分计算公式、评分进度条、评分星级分布表。

### 7.2 概览（顺序固定：维度由大到小）

① 诊断产品：链接 / 名称 / 店铺 / 现价+原价+成交均价 / 类目 / MSKU数 / 评分+评论 / 佣金+运费 / 达人+视频+直播
② 类目大盘(L3)：8 项指标 + 一句"为什么用 L3 不用 L1" + 由集中度推出的**可执行结论**（如进 TOP50 的门槛）
③ 店铺级数据 + 异常预警
④ 28天销量趋势
⑤ MSKU 变体全行展示（每变体：现价/原价、销量、销量占比、GMV、GMV占比、库存、库存占比、状态）+ 合计行 + 库存销量错配诊断
⑥ 5 个对标竞品（简称/全名/可点击链接/店铺/价格/28天GMV/选择理由）+ 同形态检索结果说明

### 7.3 Section 1 矩阵

**转置：维度做行、竞品做列，≥16 行**，行序固定：

```
★产品形态 → ★驱动方式 → 价格 → 佣金率 → 周GMV → 周销量 → 累计GMV → 评分 → 评论数
→ 达人数 → 视频数 → 直播场次 → 运费 → 到手价 → SKU数 → ★L3类目排名 → ★上架时间
```

- 前两行必须是**产品形态**与**驱动方式**——决定"谁才是真正可比的对手"
- 列：#1–#7 自然排名 + ★同形态3席（标注榜单原名次、底色区分）+ 均值列 + 本品列（最右、高亮）
- 表下依次：**数据核验说明** → **7+3构成说明** → **竞争位置** → **★形态生存力验证**（先输出同形态逐款明细表，再输出 4 项证据表+分层结论）

**1.2 达人与流量结构**（两张表，字段不重复）：

| 表 | 字段 |
|---|---|
| 表一：同形态同口径对比（28天实取） | `产品 \| 达人总数 \| 28天活跃达人 \| 达人渠道GMV占比 \| 商品卡占比 \| 广告占比 \| 28天GMV \| 流量结构判断` |
| 表二：本品达人明细 | `达人 \| 粉丝 \| 视频数 \| 带货GMV \| 销量 \| ★占产品总GMV% \| 效果` + **合计行** |

- 占比必须**拆到每个达人**（才能看出"粉丝量与转化是否脱钩"）
- 后接**佣金策略建议**（新旧对比+依据）、**达人招募策略建议**
- ★ 佣金/达人招募类建议**全篇只在这里出现一次**，Section 2.3 不得重复

### 7.4 Section 2 Listing 诊断

#### 评分总览（Section 2 开头）
固定 **3 列**：`维度 | 得分(X/10) | 核心问题`，末尾总计行 `X/60`；**不展示公式、不展示进度条**；表上方一句话说明评分依据（定性描述四个参考面，不出现权重数字）。

#### 2.1 标题、描述与SEO（★ 描述归这里，不放 2.2）

> 描述与标题同属文案/搜索索引范畴，用的是同一套 TOP20 高频词分析，放一起才能一次讲完"文案缺什么词、怎么补"。

**A. 选词法（必须在表上方写明方法）**
1. 取 **L3 榜单 TOP 20** 完整标题——**不是 TOP 10**（10 条样本单条权重 10%，一条异常就带偏；实测扩到 20 条后多暴露出 2 个高频缺口）
2. 剔除错分类目产品，注明实际分母
3. 合并同义/单复数/连字符/拼写变体
4. 统计每个词**出现在几条标题中**（同一标题内多次只记 1 次）
5. 热度分级见 §四
6. 剔除品牌名与无检索价值的连接词
7. 输出表：`关键词 | TOP20覆盖(X/19) | 热度分级 | 本品是否覆盖 | 同形态3款覆盖 | 诊断结论`

**B. 两条必须守住的判断**
- **形态词单独判定**：与本品形态不符的形态词（本品杯架式而 hanging 频次再高）→ 标注"禁止补，属误导性描述"
- **0 频次词定性**：TOP20 中无人使用的词 → 定性为**转化背书词而非搜索流量词**，保留但不应期待带来搜索流量

**C. 标题改写规则**
核心词前置 / **字符 ≤200** / 避免堆砌重复 / 属性明确；新旧并排，每条改动对应具体频次依据；★**必须实际数出优化后字符数并核对**；低频人群词可后移而非直接删。

**D. 商品描述区诊断（≥6 项检查；只对比"纯文本/结构化"视为不合格）**
```
① 描述格式与长度
② 是否承接了 TOP20 高频词（描述同样进搜索索引）
③ 本形态特有疑问是否回答（小众形态必须讲清安装/适配）
④ 是否有可量化承诺（时长、容量对比）
⑤ 是否针对同形态对手的固有弱点做防守
⑥ 是否规避了竞品评论暴露的痛点
```
优化建议为**逐段新旧对比表**（段落 | 优化前 | 优化后 | 依据），依据列必须**同时写自身诊断结论与具体取数**；竞品描述全文无法取得 → 只用可验证字段判断并注明，**不得臆测**；含可量化承诺须附"需实测后再上架"提醒。

#### 2.2 图片与详情页（图片专项）

逐项对照 **TK Shop 官方规则**打勾判定，不自创维度：

| # | 规则 | 判定方式 |
|---|------|---------|
| 1 | 主图1张+副图≤8张，建议 5–9 张 | 数数量 |
| 2 | 主图白底/浅色、无水印、无促销文字 | AI 看图 |
| 3 | ≥1 张多角度实拍 | AI 看图 |
| 4 | ≥1 张真实使用场景 | AI 看图 |
| 5 | ≥1 张卖点信息图 | AI 看图 |
| 6 | 建议含尺寸参照/对比图 | AI 看图 |
| 7 | 多SKU缩略图需可视觉区分 | 比对 |
| 8 | 建议 15–60 秒视频，前3秒出卖点 | 查视频 |

**图片优化表固定 5 列**，逐张不留空：`序号 | 图片类型 | 当前（优化前） | 建议（优化后） | 内容说明`

#### 2.3 合规与评论
```
评论数+评分（数字引用，不展示星级分布表）
→ 评论原文样本（好评/差评各1-2条）
→ 竞品痛点差异化分析表（竞品痛点 | 评论原文 | 本品是否天然规避）
→ 核心优化建议（仅本节独有：合规/发货率/库存/描述补充；
   标题图片类已在2.1/2.2，佣金达人类已在Section 1，此处不得重复）
```

### 7.5 Section 3 风险评估
高/中/低风险卡片 + 应对措施，**≥5 条**；基于前文已诊断问题汇总，不引入新数据；重复的行动细节用"详见 Section X"引用。

---

## 八、评分规定

**Listing 诊断评分：六维度 × 10 分 = 满分 60**
标题与SEO / 图片与详情页 / 合规与评论 / 定价与佣金 / MSKU变体 / 达人与内容

**单维度内部算法（仅用于推导数字，禁止写进报告）**：
`审计得分×25% + 竞品对比分×25% + 大盘对标分×25% + 评论验证分×25%`

| 维度 | 审计得分看什么 | 竞品对比分 | 大盘对标分 | 评论验证分 |
|------|--------------|-----------|-----------|-----------|
| 标题与SEO | 是否符合 TK 官方标题规则 + 关键词覆盖率 | vs 同形态3款覆盖率 | vs L3 TOP20 热词覆盖率 | 评论用词 vs 标题词匹配度 |
| 图片与详情页 | 对照 TK 官方 8 条规则的通过率 | vs 同形态图片规范达标率 | vs TOP10 图片数量/达标率 | "与图片不符"类反馈 |
| 合规与评论 | 评论量/评分健康度 + 差评占比 | vs 矩阵评分/评论排名 | vs 矩阵均值 | 评论情感与差评关键词 |
| 定价与佣金 | 佣金率/到手价是否在合理区间 | vs 矩阵佣金/到手价排名 | vs 矩阵均值 | "性价比/太贵"类感知 |
| MSKU变体 | 库存平衡度 + 价格阶梯合理性 | vs 竞品 SKU 数/阶梯 | vs 矩阵 SKU 数均值 | 变体偏好反馈 |
| 达人与内容 | 达人数/激活率/渠道占比健康度 | vs 同形态达人渠道占比 | vs 矩阵达人数/视频数均值 | "看了达人视频才买"类路径 |

**展示规则（硬性）**
- 只出现最终数字，格式统一 `分数/总分`（`5.5/10`、`27.0/60`）
- **禁止**出现权重、公式、加权分列、进度条
- 评分总览固定 3 列，「核心问题」列即为扣分理由

**竞争力评分（满分10）**：销售额规模20% / 达人生态20% / 价格竞争力15% / 评论口碑15% / 内容爆款力15% / 增长动能15%

**评级**：50–60 优秀 / 36–49 中等 / 20–35 需改进 / 0–19 严重不足

---

## 九、写作与排版规范

| 规范 | 要求 |
|------|------|
| **禁用泛化代号** | 不得出现 `本品`、`竞品A/B/C`——一律用具体简称（`HOOGALIFE杯架款`、`Aer 3-Pack`）；简称需能区分同店铺不同产品 |
| **数据唯一出处** | 同一张数据表不得出现两次；后续引用写 `同 Section X，不重复展示` |
| **小节总结** | 只在有前文未提及的新结论时才写 |
| **新旧对比** | 所有修改建议必须"优化前 / 优化后 / 变更依据"并排 |
| **中文术语** | GMV→销售额、Creator→达人、Product Card→商品卡（首次可括注英文） |
| **禁止空值** | 不得出现 `—` 或空白；实在取不到才用 `≈` 并说明 |
| **可点击链接** | `<a class="prod-link" href="https://shop.tiktok.com/us/pdp/-/{id}" target="_blank" rel="noopener">` |
| **字体权重** | body 500 / h1 800–900 / `.sec-t` 700 / `.sub-h` 700 / `th` 700 / `.ic-v` 700 / `strong` 800 |
| **CSS** | 从 [skills/12-统一报告格式.md](skills/12-统一报告格式.md) 加载，不重写 |
| **交付形式** | 生成 HTML 后**发布为在线 Artifact** 并回传链接；更新时复用同一 URL |

---

## 十、交付前检查清单

**结构**
```
□ 4 板块齐全：概览 / S1矩阵 / S2 Listing诊断 / S3风险
□ 概览按 ①产品→②L3大盘→③店铺→④趋势→⑤MSKU→⑥竞品 顺序
□ 无泛化代号；无"不应出现"的板块（见 §7.1）
□ 全部产品ID可点击
```

**数据**（逐条对照 §五 红线）
```
□ 大盘为 L3 口径，无 L1 数据
□ 矩阵单元格全部实取，核心行无 ≈
□ 同形态经 AI 看图确认；已剔除僵尸链接与错分类目
□ 关键词为 TOP20 实际统计，分母已注明
□ 占比口径全篇统一
□ 报告内有数据核验说明（取数日期/来源/修正项）
```

**内容**
```
□ 矩阵 ≥16 行，前两行为形态/驱动方式，含累计GMV/L3排名/上架时间
□ 有形态生存力验证：先输出同形态逐款明细表（售价/周销量/周GMV/累计GMV/评分评论/达人视频/排名/上架时间/驱动方式 + 本品对比行），再输出 4 项证据（引用单品数据而非只写合计）+ 分层结论
□ 达人明细逐人列占比 + 合计行
□ 2.1 含选词方法说明 + 形态词禁补判断 + 0频次词定性 + 标题字符数核对 + 描述6项检查与逐段对比
□ 2.2 逐项对照 TK 官方 8 条规则 + 5列图片优化表不留空
□ 2.3 仅保留本节独有建议，无佣金/达人/标题/图片类重复
□ 评分只出 X/10 与 X/60，无公式无进度条
□ 风险 ≥5 条
□ 可量化承诺均标注需实测
```

---

## 附录：子 Skill 文件映射

| 文件 | 阶段 | 对应板块 |
|------|------|---------|
| `01-数据采集.md` | B | 概览 |
| `02-增强竞品矩阵.md` + `09-竞品深度分析.md` | C/D | Section 1 |
| `07-达人内容诊断.md` | D | Section 1.2 |
| `03-标题描述诊断.md` + `05-SEO关键词诊断.md` | E | Section 2.1 |
| `04-图片视频诊断.md` + `04B-商品详情页诊断.md` | E | Section 2.2 |
| `08-合规评论诊断.md` + `08B-VOC消费者洞察.md` | E | Section 2.3 |
| `06-定价佣金诊断.md` | D/E | 并入矩阵，不单独成节 |
| `10-市场定位与差异化.md` | E | Section 3 |
| `11-综合评分.md` | E | 评分总览 |
| `12-统一报告格式.md` | 出报告 | CSS/HTML 模板 |
| `13-评论爬虫.md` | B | 评论降级方案 |

> 子文件已全部更新至 v6.2，每个子文件均含「固定输出格式」章节，明确了每张表的列定义、行要求与模板文本，确保换不同产品也能跑出相同格式的报告。**与本文件冲突时一律以本文件为准**。
