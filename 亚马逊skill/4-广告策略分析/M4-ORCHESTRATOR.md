---
name: m4-ad-strategy-orchestrator
description: "模块 4 · 广告策略分析：取广告结构、关联流量与关键词数据，领星取本品整月效率，写出 模块4-广告策略-<ASIN>.md（否词三层、执行清单）。"
argument-hint: "[本品ASIN]"
---

# 模块 4 · 广告策略分析（编排器）

可执行流程：取数、计算派生值、写 Markdown。

## 输入

同模块 1。另需 `DATA/candidates/true_competitors.json`。

## 数据范围与口径

- 对象：本品、5 个真竞品。广告结构对比可加入内部关联参照，标注"内部关联"，不进入均值。
- 竞品的广告花费、ACOS 不在任何 MCP 工具覆盖内，只能写"工具不覆盖"。
- 本品的花费与 ACOS 来自领星，只能取到本品整月汇总，没有分活动、分广告组的拆解。

## 步骤

### 步骤 1 · 广告结构

对本品与每个真竞品：
1. `sif.ads_get_asin_ad_structure(asin, country=US, granularity=month)` → `DATA/ads/structure_<ASIN>.json`。只返回活动数量，不返回花费与点击。

### 步骤 2 · 本品关键词与关联流量

2. `sellersprite.traffic_keyword(asin=OWN, marketplace=US, size=100)` → `DATA/keywords/<OWN>.json`（不带 month）。
3. `sellersprite.traffic_extend(asinList=[OWN], marketplace=US, queryType=2, size=10)` → `DATA/ads/traffic_extend_<OWN>.json`。
4. `sellersprite.keyword_research(keywords=HEAD, month=MONTH, size=10)` → `DATA/keywords/keyword_research_headword_<MONTH>.json`。仅作市场估算，不是本店铺的花费。
5. 头号词竞争：`sif.market_get_keyword_competition(keyword=HEAD, asin=OWN, country=US)` → `DATA/keywords/headword_competition.json`。

### 步骤 3 · 本品效率（领星）

6. 领星 MCP：`help` 找到查询工具，`search` 确认参数，`action` 调用，取本品 `MONTH` 整月：花费、广告销售额、ACOS、TACOS、ROAS、CPC、CVR、广告订单、广告点击、广告展示。保存为 `DATA/ads/lingxing_<OWN>_<MONTH>.json`。
7. 领星取不到时，写明"未取（原因：…）"，不得估算。

### 步骤 4 · 流量占比

8. `sif.ops_get_listing_traffic_overview` 对本品与竞品（参数见模块 2 步骤 2）。用于广告流量占比。

### 步骤 5 · 派生值

9. 计算并写明公式：ACOS = 花费 ÷ 广告销售额；TACOS = 花费 ÷ 总销售额；广告订单占比 = 广告订单 ÷ 总订单；SP 占比；否词流量占比；竞品中位数。
10. 派生值保留到小数点后一位（比率）或整数（件数、金额）。

### 步骤 6 · 写报告

11. 章节使用 `references/章节标题.json`（共 23 条标题）。H1 固定为 `模块四·广告策略分析 —— <本品名>`。
12. 结构：
   - 核心发现（3 条，每条一段，数字指向下表）。
   - 一、为什么落后：1.1 竞品广告结构对标；1.2 竞品对标详情（广告组拆解仅在可取时写，否则"未取"）；1.3 关联流量与关键词竞争；1.4 广告效率诊断（领星整月）。
   - 二、怎么改：关键词估算；竞品广告结构对本品的含义；否定关键词三层（Tier1 流量高购买率低，Tier2 点击无转化，Tier3 品牌词策略）；词级流量结构。
   - 三、立即行动：红线（不建议做的动作）；立即执行、本周完成、持续优化（表格）。
   - KPI 行：引导块之后、第一个 H2 之前放一行 `<div class="kpi-grid">`，含 4 个 `<div class="kpi"><span class="kpi-label">标签</span><span class="kpi-value">数值</span></div>`。数值只取本模块已取到的数据，取不到写 `未取（原因：…）`，不估算。KPI 行下方一行 `来源：` 写明数据来自哪个文件或工具字段。 指标示例：广告流量占比（近 30 天）、整月花费、ACOS、TACOS（花费与 ACOS 目前多为未取）。
13. 否定关键词每一层写阈值、依据字段、列出具体词。不得凭印象列词。
14. 每个 H2 下一个小结区块；H3 直接写正文，不加结论、依据、含义与置信度标签；表格下方来源行。
   对比类内容一律用表格，不写成段落，每张表下方一行 `来源：`：
   - 核心发现：3 条，每条一段正文，不用表。
   - 一、1.1 竞品广告结构对标表（对象 × SP / SB / SBV 数量 × 合计 × 广告流量占比）；1.2 竞品对标详情表（对象 × 可取字段 × 未取原因）；1.3 关联流量与关键词竞争表（关键词 × 本品流量占比 × 竞品占比 × 竞争者数）；1.4 广告效率表（指标 × 本品整月数值 × 口径 × 未取原因）。
   - 二、关键词估算表（关键词 × 搜索量 × 口径）；竞品广告结构对本品的含义表（维度 × 竞品做法 × 本品现状 × 含义）；否定关键词三层表（层 × 阈值 × 依据字段 × 具体词）；词级流量结构表（词 × 流量占比 × 排名）。
   - 三、红线表（不做的动作 × 原因）；立即执行、本周完成、持续优化表。
15. 保存为 `REPORT/模块4-广告策略-<OWN>.md`。

## 口径

- 同一事实的不同口径并列写：领星的 ACOS（本品整月）与卖家精灵的关键词估算（市场口径）不得相减。
- 竞品数字一律"工具不覆盖"，不写估算值。

## 交付前检查

按 `references/格式检查清单.md` 核对；无占位符、无过程用语；ASIN 为 Amazon 链接。

另外检查：
- 用 `convert.js` 与 `build.js` 重新生成 `report.html`，不得只改模板。
- 生成的 `report.html` 在无脚本环境下内容可见（见 `../共享规则/在线报告生成/README.md` 的"交付前检查"）。
- 目录链接（`nav.index`）指向的模块 id 与 `section id` 一致。
