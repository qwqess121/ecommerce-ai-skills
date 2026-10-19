---
name: m1-product-development-orchestrator
description: "模块 1 · 产品开发：取数、用工具判定真竞品与类目 Top15、头号词与差评分类，写出 模块1-产品开发-<ASIN>.md（章节依据参考标题 Xk3D，格式依据输出格式强制规定）。"
argument-hint: "[本品ASIN]"
---

# 模块 1 · 产品开发（编排器）

由 Claude 按步骤调用 MCP 工具、保存原始结果、运行工具脚本、再写 Markdown。

## 输入与变量

| 变量 | 含义 | 来源 |
|---|---|---|
| `OWN` | 本品 ASIN | 用户给出 |
| `SITE` | 站点，固定 `US` | — |
| `DATA` | 数据目录，放在 skill 之外 | 用户指定，如 `D:\数据\<OWN>` |
| `REPORT` | 报告目录，放模块 md | 用户指定，如 `D:\报告\<OWN>` |
| `MONTH` | 最近一个完整月，格式 `YYYYMM` | 当前日期推算 |
| `YOY` | 上一年同月 | 由 `MONTH` 推算 |
| `NODE` | 本品精确节点 `nodeIdPath` | 步骤 1 的 `asin_detail` |
| `PARENT` | 父体 ASIN | 步骤 1 的 `asin_detail.parent` |
| `PRICE` | 本品现价 | 步骤 1 的 `asin_detail.price` |

## 必读资料（skill 内）

- `../共享规则/取数/取数清单.json`：任务、参数、保存路径。
- `../共享规则/取数/取数手册.md`：参数形态、分页与限制。
- `../共享规则/取数/差评分类规则.md`：差评四类口径。
- `../共享规则/取数/竞品门槛词表.json`：形态族词表（脚本使用）。
- `../共享规则/竞品判定标准.md`：判定原则。
- `references/章节标题.json`：章节标题（共 31 条）。
- `references/输出格式强制规定.md`、`格式检查清单.md`：格式。
- 工具脚本：`../工具/竞品门槛.py`、`选类目Top15.py`、`推荐头号词.py`、`差评分类.py`。

## 参数形态（已实测）

- 平铺参数：`sellersprite.asin_detail`、`sellersprite.asin_sales_trend`、`sellersprite.review`、`sellersprite.keepa_info`。
- `request` 包裹：`sellersprite.product_research`、`market_*`、`traffic_keyword`、`traffic_extend`、`aba_research_monthly`、`google_trend`、`keyword_research`。
- `sif.*` 工具按取数清单的参数名传入，已实测 `ops_get_listing_traffic_overview`、`ops_get_asin_traffic_trend`、`ads_get_asin_ad_structure` 可用。

## 步骤

### 步骤 1 · 本品基准

1. `sellersprite.asin_detail(marketplace=US, asin=OWN)` → `DATA/listing/asin_detail.json`。读出 `PRICE`、`PARENT`、`NODE`。

### 步骤 2 · 判定配置

2. 写 `DATA/取数配置.json`：
   ```json
   {"own": "<OWN>",
    "gate": {"price_band": [0.6, 1.4], "max_n": 5, "backup_n": 5,
             "exclude_brands": ["<本公司其他品牌>"],
             "internal_brands": ["<同卖家主体的其他品牌>"]}}
   ```
   `price_band` 是本品售价的倍数区间，默认 `[0.6, 1.4]`（±40%），真竞品不足时才按步骤 5 放宽。真竞品判定 = 节点相同 + 形态族相同（`roll_on` 等）+ 使用场景族相同（`pheromone` 等，见 `竞品门槛词表.json` 的 `scenario_families`）+ 价格带内 + 同品牌只留一个代表。

### 步骤 3 · 候选池与真竞品（工具判定）

3. 按价格带逐页取候选池：`sellersprite.product_research`，`request={"marketplace":"US","nodeIdPath":NODE,"month":MONTH,"minPrice":PRICE×0.6,"maxPrice":PRICE×1.4,"matchType":1,"page":N,"size":50,"order":{"field":"total_units","desc":true},"returnFields":"asin,brand,title,price,units,ratings,rating,nodeLabelPath"}`。第 1 页起，每页保存为 `DATA/candidates/pool_band_p{N}.json`。
4. 每取一页后运行：`python 工具/竞品门槛.py DATA`。
   - 退出码 0：判定完成。若存在 `candidates/pool_stop.json`，说明触发了提前停止，停止取数。
   - 退出码 1，提示"候选池不完整"：继续取下一页，再运行一次。
   - 页数取完仍未达到条件：脚本会如实写出 `shortfall`，不得用其他形态凑数。
5. 价格带二次放宽：若真竞品不足 5 个，依次把 `gate.price_band` 改为 `[0.4, 1.6]`、`[0.2, 1.8]`，只放宽价格，每次重跑步骤 3 与 4（池子需按新区间重新分页取回）。放宽后纳入的竞品，在判定表里标注"价格带放宽至 X 倍纳入"。
6. 结果：`DATA/candidates/true_competitors.json`（真竞品、备选、缺额）、`gate.json`（门槛参数，可审计）、`internal_related.json`（内部关联）。

### 步骤 4 · 类目 Top15（工具判定）

7. `sellersprite.product_research`，`request={"marketplace":"US","nodeIdPath":NODE,"nodeIdPathEqual":true,"month":MONTH,"page":N,"size":50,"order":{"field":"total_units","desc":true},"returnFields":"asin,brand,price,units,ratings,rating,nodeLabelPath"}`，取前 2 页，保存为 `DATA/candidates/node_top15_p{N}.json`。
8. `python 工具/选类目Top15.py DATA`，结果 `DATA/candidates/top15.json`（按品牌去重，剔除本品与内部品牌，不足 15 个写明缺额）。

### 步骤 5 · 市场数据（与步骤 3–4 并行）

9. `sellersprite.market_research(request={"marketplace":"US","nodeIdPath":NODE,"month":M,"topNum":10})`，M 取 `MONTH` 前推的 6 个完整月，保存为 `DATA/market/market_research_{M}.json`。
10. 同上参数取 `YOY` → `DATA/market/market_research_{YOY}.json`。
11. `sellersprite.market_price_distribution`、`sellersprite.market_product_concentration`、`sellersprite.market_ratings_count_distribution`，参数同上，`month=MONTH`。
12. `sellersprite.keepa_info(marketplace=US, asin=OWN, dailyLatest=true)` → `DATA/market/keepa_<OWN>.json`，用于 BS100 门槛。

### 步骤 6 · 头号词（工具判定）

13. `sellersprite.traffic_keyword(request={"asin":OWN,"marketplace":"US","size":100})`，不带 month → `DATA/keywords/<OWN>.json`。
14. `python 工具/推荐头号词.py DATA`，结果写入 `DATA/取数配置.json` 的 `head_keyword` 与 `candidates/head_keyword.json`。
    - 规则：本品有自然排名、不含品牌名的词中，流量占比最高者；并列时取月搜索量最高者。
    - 复核：结果若是泛品类词（如 `car accessories`），不能直接使用。需人工判断，选用本品的核心产品词，并在报告中写明理由与依据数字。
15. 以 `HEAD` 调用头号词的市场数据：
    - `sellersprite.aba_research_monthly(request={"marketplace":"US","date":MONTH,"includeKeywords":HEAD,"size":10,"order":{"field":"searches","desc":true}})`
    - `sellersprite.google_trend(request={"marketplace":"US","keyword":HEAD,"monthly":true,"googleProp":"web"})`
    - `sellersprite.keyword_research(request={"marketplace":"US","keywords":HEAD,"month":MONTH,"size":10,"order":{"field":"searches","desc":true}})`
    - `sif.market_get_keyword_demand(keywords=[HEAD], country=US)`
    - `sif.market_get_keyword_competition(keyword=HEAD, asin=OWN, country=US)`
    - `sif.market_get_keyword_history(keywords=[HEAD], country=US, granularity=month)`
16. `sellersprite.traffic_extend(request={"asinList":[OWN],"marketplace":"US","queryType":2,"size":10,"order":{"field":"trafficPercentage","desc":true}})` → `DATA/ads/traffic_extend_<OWN>.json`。

### 步骤 7 · 对象评论（差评差集）

17. 本品与 5 个真竞品：`sellersprite.review(marketplace=US, asin=…, starList=[1,2,3], size=100)` → `DATA/reviews/<ASIN>_neg.json`，并取 `starList=[4,5]` → `_pos.json`。
    - 实测：`size=100` 只返回 20 条，且返回的 `total` 可能小于 100。样本量必须写进报告。
18. 差评分类：
    - `python 工具/差评分类.py template DATA <ASIN>`：生成骨架。
    - 人工阅读每条摘录，按 `差评分类规则.md` 填写 `categories`（留香不足、渗漏、QC、其他；"其他"不得与其他类同时出现）。
    - `python 工具/差评分类.py import DATA <结果.json>`：导入分类结果。
    - `python 工具/差评分类.py stat DATA`：退出码 0 才算通过。报告中的差评数字以 `summary` 为准。

### 步骤 8 · 领星效率（可选）

19. 领星 MCP：`help` → `search` 找到查询工具 → `action` 调用，取本品 `MONTH` 整月的花费、广告销售额、ACOS、TACOS、ROAS、CPC、CVR。保存为 `DATA/ads/lingxing_<OWN>_<MONTH>.json`。取不到写"未取（原因：…）"，不得估算。

### 步骤 8b · 已验证的补充取数（卖家精灵与 sif，不得用"未取"代替）

以下数据源都已实测可用。缺数据时先按本节调用，仍取不到才写"未取（原因：…）"。

21. 竞争参照节点（EDP）：`sellersprite.market_research(request={"marketplace":"US","nodeIdPath":"3760911:11056591:11056931:11057071","month":M,"topNum":10})`，取 M 与 YOY 两个月，用于第一节 1.2。
22. BS100：`sellersprite.keepa_info(marketplace=US, asin=OWN, dailyLatest=true)` 返回 `subSalesRank`，按 `nodeId` 统计 `rank ≤ 100` 的采样点（子类目 Cologne 11057051 与父节点 Women's 11056931 分别统计）。结果是采样点占比，不写成"天数"。
23. 广告结构（sif）：`ads_get_asin_ad_structure(asin, country=US)`（活动数、广告类型）；`ads_get_asin_campaign_contribution_overview(asin, country=US)`（曝光份额，按活动）；`ads_get_asin_ad_traffic_trend(asin, country=US)`（周曝光，按 SP/SB/SBV）；`ads_get_asin_ad_feature_profile(asin, country=US)`（投放特征）。**sif 只返回曝光份额，不返回花费与 ACOS。**
24. 花费与 ACOS：sellersprite、sif 都不返回。领星按店铺查：`LingXing action → ad_auth_shops` 取店铺 profile_id，再 `ad_campaign_report(report_date, profile_ids, asin)`。店铺没有该 ASIN 的广告记录时写"未取（原因：…）"。需要花费与 ACOS 时，让用户从卖家后台导出该月广告报表。
25. 关键词需求（卖家精灵 ABA，比 keyword_research 更稳）：`aba_research_monthly(request={"marketplace":"US","date":MONTH,"includeKeywords":"<词>","size":10,"order":{"field":"searches","desc":true}})`。**实测 `keyword_research` 对多词短语经常返回空，不作为唯一来源。**
26. sif 关键词需求：`market_get_keyword_demand(keywords=[词], country=US)`，`market_get_keyword_competition(keyword, asin, country=US)`，`market_get_keyword_history(keywords=[词], country=US, granularity=month)`。
27. 真竞品流量词：对 5 个真竞品逐个 `traffic_keyword(request={"asin":ASIN,"marketplace":"US","size":20})`，取 `trafficPercentage`、`searches`、`supplyDemandRatio`。
28. 流量结构：`traffic_listing_stat(marketplace=US, asin=OWN, month=MONTH)` 返回免费与付费关联数（不是花费）；`keyword_order(request={"asins":[OWN],"date":MONTH,"marketplace":"US","reverseType":"M","size":20,"order":{"field":"searchRank","desc":true}})` 返回关键词级点击与转化占比及转化类型（E/S/L/I/U）。
29. 好评：`sellersprite.review(marketplace=US, asin=…, starList=[4,5], size=100)`，每个对象一次；报告中写全量数字，主题为抽样归纳。
30. 扩展方向与 Top15 外的 ASIN：`sellersprite.asin_sales_trend(marketplace=US, asin=…)` 返回 `salesTrendPoints`（父体与子体月销），用于候选方向 B1–B3 的需求数字；`asin_detail` 返回节点与价格。
31. 本品属性：`sif.market_get_asin_profile(asins=[OWN], country=US)`（参数名是 `asins` 数组，不是 `asin`）。

### 步骤 9 · 写报告

20. 章节逐条使用 `参考标题_Xk3D.json` 的 `modules.1`。
    - KPI 行：引导块之后、第一个 H2 之前放一行 `<div class="kpi-grid">`，含 4 个 `<div class="kpi"><span class="kpi-label">标签</span><span class="kpi-value">数值</span></div>`。数值只取本模块已取到的数据，取不到写 `未取（原因：…）`，不估算。KPI 行下方一行 `来源：` 写明数据来自哪个文件或工具字段。 指标示例：本品定价、头号词月搜索量、类目 Top 15 中位价、真竞品数量。
21. 每个 H2 下：至少一个 `**小结** —— …` 区块。H3/H4 下直接写正文，不加 `结论`、`依据`、`含义与置信度` 标签；数字来源用表格下方的 `来源：` 行说明。
22. 对比类内容一律用表格（`<div class="tablewrap cmp-wrap">`），不写成段落：七、1.3 垂直 vs 扩展详细矩阵（1.3.1 垂直 A1/A2/A3，1.3.2 扩展 B1/B2/B3）、1.4 BS100 可行性对标（垂直 vs 扩展并排）、1.5 三个月执行计划（月份为行，垂直 A1/A2/A3 与扩展 B1–B3 为列）。每张表下方一行 `来源：`。
22. 每张表下方写 `<p class="src">来源：<工具名> <字段></p>`。
23. 数字必须能追溯到上述文件。派生数字（均值、占比、差额）写明公式。
24. 候选方向必须由本品真实优势推导，每个候选写出依托的优势来源，并给出一个需求数字和一个竞争数字。
25. 保存为 `REPORT/模块1-产品开发-<OWN>.md`。

## 口径

- 真竞品不足、价格带放宽、样本量少（评论只取到 20 条）、工具不覆盖（竞品广告花费）、头号词人工改选：每一项都要写进报告。
- 同一事实的不同口径并列写，不互相换算。

## 交付前检查

按 `references/格式检查清单.md` 核对，并按 `../共享规则/交叉验证规则.md` 的 6.3.4 执行 grep 检查。

另外检查：
- 用 `convert.js` 与 `build.js` 重新生成 `report.html`，不得只改模板。
- 生成的 `report.html` 在无脚本环境下内容可见（见 `../共享规则/在线报告生成/README.md` 的"交付前检查"）。
- 目录链接（`nav.index`）指向的模块 id 与 `section id` 一致。
