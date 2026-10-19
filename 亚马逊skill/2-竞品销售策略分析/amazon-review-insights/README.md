# amazon-review-insights · 使用与复现说明

本 skill 抓取 Amazon 商品页的「评论洞察层」三类数据（**无需登录**）：

| 数据 | 字段 | 说明 |
|---|---|---|
| AI Review Insights（评论洞察标签） | `insights[]` | 维度名 + 评论条数，如 `Scent(490)` / `Longevity(134)` |
| Customers say（AI 评论总结） | `customersSay` | 一段结构化自然语言总结 |
| 🔴 Customers ask Alexa（A+ 自建问答） | `alexaQuestions[]` | 卖家 A+ 内容里的 `?` 问句；**本库「Alexa 提问」的真实来源** |

> ⚠️ **口径**：`alexaQuestions` 来自 **A+ 内容模块**（`.aplus-module-csa-wrapper`），**不是** Q&A 页按投票排序的问答（那个需登录，见 `amazon_qa_scraper.js`）。两者禁混算。

## 一、环境准备（换机器必做）

本机（Windows，托管 Node 22）已装好。别人第一次用需：

```bash
# 1) 用 Node 18+（脚本用 lookbehind regex，需现代 Node）
# 2) 在本目录装依赖
npm install            # 装 playwright（package.json 已声明）
# 3) 装浏览器内核（二选一）
npx playwright install chromium        # 推荐：自带 chromium，无需本机 Chrome
# 或者本机已有 Chrome 也行，脚本会优先用 channel:'chrome'
```

不装浏览器会报 `Executable doesn't exist`；装完 `npx playwright install chromium` 即可。

## 二、运行

```bash
# 抓多个 ASIN，写 JSON
node scripts/amazon_review_insights.js --asins B0CW9231N3,B0DRTK9BJ8 --out data.json

# 从文件读 ASIN（文件里含 B0XXXXXXXX 即自动提取）
node scripts/amazon_review_insights.js --file asins.txt --out data.json

# 复现校验：对照 baseline.example.json，打印 PASS/FAIL
node scripts/amazon_review_insights.js --asins B0CW9231N3,B0DRTK9BJ8,B0FS1NL9GJ --baseline baseline.example.json

# 看渲染过程（排错时）
node scripts/amazon_review_insights.js --asins B0CW9231N3 --headed

# 强制用自带 chromium（无本机 Chrome 时；注意：无登录态，Q&A 仍抓不到）
node scripts/amazon_review_insights.js --asins B0CW9231N3 --use-bundled
```

## 三、为什么别人能跑出同样结果（关键设计）

1. **启动回退**：优先 `channel:'chrome'`（渲染最贴近真实买家），失败自动回退 `playwright` 自带 chromium → 任何机器都能起浏览器。
2. **选择器不写死**：洞察区块用「多 id 兜底 + 整页文本正则」；Alexa 用「4 个 A+ 容器 id + `.aplus-module-csa-wrapper` 类」双路扫描 → Amazon 改版不至于静默空结果。
3. **基线自检**：`--baseline` 模式跑完逐项比对（期望 Alexa 数 / 是否有洞察），输出 `PASS x / FAIL y`，一眼看出是否复现成功。
4. **反爬提示**：脚本探测页面是否触发 bot check（`botCheck` 字段 + 终端 `⚠反爬`），命中时结果不可信，需换 IP 或带登录态。

## 四、已知基线（2026-09-24 · 11 家）

| ASIN | 定位 | Alexa 问数 | 是否有洞察 |
|---|---|---|---|
| `B0CW9231N3` | 本品 | **7** | ✅ |
| `B0DRTK9BJ8` | AROIC | **4** | ✅ |
| 其余 9 家 | — | 0（A+ 未添加该模块，非抓取失败） | ✅ |

> 复现失败最常见原因：① 卖家改了 A+ 模块 → 更新 baseline；② 命中反爬 → 换网络/带登录态；③ 浏览器没装 → `npx playwright install chromium`。

## 五、输出字段

每项：`asin / ok / status / rating / ratingsCount / customersSay / insights[]({dim,count}) / alexaQuestions[] / qa{present,textLen,text,link} / botCheck / fetchedAt`

## 六、口径纪律（写进报告前必读）

1. 洞察标签数字是「提及该维度的评论条数」，**不是比率**，禁换算百分比。
2. Customers say 是 Amazon AI 生成，须标「AI 生成、非逐条统计」。
3. Alexa 提问 = A+ 自建模块（`口径 A`），≠ Q&A 页按投票排序（`口径 B`），≠ Rufus 生成。
4. **「搜不到关键词」≠「页面没有」**：判「没有」前必须遍历候选容器（`.aplus-module-csa-wrapper` / `#aplus`）。血债见 SKILL.md。
