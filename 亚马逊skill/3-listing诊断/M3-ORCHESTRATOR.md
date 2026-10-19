---
name: m3-listing-diagnosis-orchestrator
description: "模块 3 · Listing 诊断：抓取本品与真竞品的 listing、图片与 A+，用 工具/八维评分.py 按九项（沿用原名八维）打分，写出 模块3-Listing诊断-<ASIN>.md。"
argument-hint: "[本品ASIN]"
---

# 模块 3 · Listing 诊断（编排器）

依赖模块 1 的真竞品结果（`candidates/true_competitors.json`、`candidates/head_keyword.json`）。没有先执行模块 1 的步骤 1–6。

## 输入与变量

同模块 1：`OWN`、`SITE=US`、`DATA`、`REPORT`、`MONTH`、`PARENT`。

## 对象范围

本品 + 5 个真竞品，共 6 个。本品在第一行。内部关联参照不进入评分。

## 必读资料

- `../共享规则/取数/取数清单.json`（`object_detail`、`reviews_neg`、`listing_capture`、`image_main`、`image_aplus`）。
- `references/章节标题.json`（共 22 条）。
- `references/输出格式强制规定.md`、`格式检查清单.md`。
- `../共享规则/交叉验证规则.md` 6.3.4（交付前 grep 检查）。
- 工具脚本：`../工具/八维评分.py`。

## 步骤

### 步骤 1 · 对象详情与差评

1. 对 6 个对象：`sellersprite.asin_detail(marketplace=US, asin=…)` → `DATA/listing/detail/<ASIN>.json`。模块 1 已取过的直接复用。
2. 对 6 个对象：`sellersprite.review(marketplace=US, asin=…, starList=[1,2,3], size=100)` → `DATA/reviews/<ASIN>_neg.json`。实测只返回 20 条，样本量写进报告。

### 步骤 2 · Listing 文本

3. `amazon-review-insights/scripts/amazon_listing_capture.js`（路径相对于本文件为 `../2-竞品销售策略分析/amazon-review-insights/scripts/`）：抓取全部对象的标题、五点、描述、A+ 文本、图片数、视频数，保存为 `DATA/listing/listing_capture_all.json`。
4. 每个对象都必须有标题、五点、A+ 文本。缺失的写明原因。

### 步骤 3 · 图片与读图

5. `amazon_image_capture.js --asins <全部对象> --video --frame-interval 3 --out DATA/images/images.json --download --outdir DATA/images`（同样在 `../2-竞品销售策略分析/amazon-review-insights/scripts/`）。视频为 mp4 直链并每 3 秒抽帧，逐帧读取写入 `DATA/images/analysis/video_<ASIN>.json`，流程见 `../共享规则/图片标准.md` 第零节 0.1。
6. 用 Read 工具逐张查看主图，写入 `DATA/images/analysis/main_<ASIN>.json`。每个对象的 `items[0]` 必须带 `main_class`，取值只能是：
   - `pure_white`：纯白底、无道具。
   - `white_with_props`：白底，道具贴在产品旁边。
   - `scene_or_color`：背景是场景、色块、渐变或灰底。
7. 附图与 A+ 图逐张读，写入 `DATA/images/analysis/aplus_<ASIN>.json`。完成度必须 100%，缺一张写明缺哪张。

### 步骤 4 · 九项评分（工具计算）

8. 写 `DATA/取数配置.json`（模块 1 已写过，确保包含 `own` 与 `head_keyword`）。
9. 运行 `python 工具/八维评分.py DATA`。输入：`listing/listing_capture_all.json`、`listing/detail/<ASIN>.json`、`candidates/true_competitors.json`、`images/analysis/main_<ASIN>.json`、`取数配置.json`。输出：`listing/score_8dim.json`。
10. 脚本输出的分数不得手改。报告引用的分数必须与该文件一致。

评分档位（脚本即规则，满分合计 100）：

| 项目 | 满分 | 档位 |
|---|---|---|
| 标题 | 15 | 长度不超过 200 字符 3；不含禁用符号 `!$?_{}^¬¦~#<>*` 3；不含促销语（free shipping、100% quality、best seller、top rated、hot item、high quality）3；品牌在前 80 字符 3；头号词在前 80 字符 3 |
| 五点 | 15 | 条数 5 条得 5，4 条得 3，其余得 1；每条不超过 500 字符得 3，否则 1；含小标题（"："前置）的条数 ≥4 得 3，≥2 得 1.5，其余 0.5；头号词出现在任一条得 4，否则 1.5 |
| 主图 | 5 | `pure_white` 5；`white_with_props` 3；`scene_or_color` 0 |
| 附图与视频 | 10 | 图库张数 ≥7 得 4，=6 得 3，其余 1.5；有视频占位得 2；附图类型覆盖（卖点/信息、场景/使用、尺寸参照、对比）每类 1 分 |
| A+ | 10 | A+ 存在得 4；正文 ≥300 字符得 3，否则 1.5（若为图片型，alt ≥60 字符得 3）；A+ 图 ≥5 张得 3，1–4 张得 1.5 |
| 描述 | 10 | 无描述模块时以 A+ 正文代替。文案 ≥300 字符得 6，否则 3（图片型 ≥60 得 4，否则 2）；头号词在文案中得 2，否则 0.5；图 ≥5 张得 2，1–4 张得 1 |
| 定价 | 10 | 价格 ÷ 对象中位数：≤1.00 得 10；≤1.15 得 7；≤1.30 得 4；其余 2 |
| 评论 | 15 | 星级：≥4.5 得 7，≥4.0 得 6，≥3.5 得 4，≥3.0 得 2，其余 1；评论数：≥1000 得 8，≥100 得 6，≥50 得 4，≥10 得 2，其余 1 |
| SEO | 10 | 头号词完整短语出现在标题得 4、五点得 3、A+ 或描述得 3；都没有得 0 |

- 六个对象的 SEO 都是 0 时，报告要写明这是规则结果，不要解释为"无问题"。
- 价格中位数由脚本计算，报告中写明中位数的数值。

### 步骤 5 · 写报告

11. 章节逐条使用 `references/章节标题.json`（共 22 条）：
    - 一、竞品判定表（本品 + 5 真竞品，价格、评分、BSR、月销、上架时间）。
    - 二、九项逐家评分、评分依据、图片实测、图片核心发现、图片行动。
    - 三、Listing 核心差距：五点与违禁词扫描、定价差距、A+ 结构、图片架构升级。
    - 四、流量结构与竞品对比、类目节点异常。
    - 五、行动清单（立即执行、本周完成、持续优化）。
    - 附表：实测原始数据与取数日期。
    - KPI 行：引导块之后、第一个 H2 之前放一行 `<div class="kpi-grid">`，含 4 个 `<div class="kpi"><span class="kpi-label">标签</span><span class="kpi-value">数值</span></div>`。数值只取本模块已取到的数据，取不到写 `未取（原因：…）`，不估算。KPI 行下方一行 `来源：` 写明数据来自哪个文件或工具字段。 指标示例：本品八维总分（来自 score_8dim.json）、本品定价、评分 / 评论数、五点违禁词命中数。
12. 违禁词扫描列出每个命中的词、位置和风险等级。写明扫描了哪些文本，不要只写"无违规"。
13. 每个 H2 下：一个小结区块。H3 直接写正文，不加结论、依据、含义与置信度标签。
   对比类内容一律用表格（`<div class="tablewrap cmp-wrap">`），不写成段落，每张表下方一行 `来源：`：
   - 二、九项评分表（对象 × 九项分 × 合计）；图片实测表（对象 × 主图类型 × 张数 × 违规点）。
   - 三、Listing 差距表（维度 × 本品 × 竞品中位数或最优 × 差距）；定价差距表（对象 × 价格 × 与本品差额）；A+ 结构对比表（A+ 模块 × 本品 × 每个竞品）；图片架构升级表（图片类型 × 本品 × 竞品 × 升级动作）。
   - 四、流量结构对比表（对象 × 流量指数 × 自然占比 × 广告占比）；类目节点异常表（节点 × 对象 × 异常 × 影响）。
   - 附表：实测原始数据表（字段 × 来源 × 取数日期）。
14. 保存为 `REPORT/模块3-Listing诊断-<OWN>.md`。

## 交付前检查

按 `references/格式检查清单.md` 核对，并执行 `交叉验证规则.md` 6.3.4 的 grep 检查。

另外检查：
- 用 `convert.js` 与 `build.js` 重新生成 `report.html`，不得只改模板。
- 生成的 `report.html` 在无脚本环境下内容可见（见 `../共享规则/在线报告生成/README.md` 的"交付前检查"）。
- 目录链接（`nav.index`）指向的模块 id 与 `section id` 一致。
