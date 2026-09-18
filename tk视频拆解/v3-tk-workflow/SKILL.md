---
name: v3-tk-workflow
description: "V3 TK电商爆款视频拆解全流程: FastMoss-MCP为主数据源，5路并行采集商业数据+脚本+买家评论+趋势，视频画面本地采集，6步深度拆解。默认竞品对比模式，报告为4区块结构+转置大盘矩阵表。先出MD对数据，再填充 .claude/skills/v3-report-template/ 下的HTML模板发布Artifact，最后过交付前自检清单。"
triggers:
  - "v3拆解"
  - "拆解视频"
  - "爆款拆解"
  - "V3 breakdown"
  - "找爆款"
  - "发现爆款"
  - "拆解最爆"
  - "对比拆解"
  - "竞品对比"
---

# V3 TK电商爆款视频拆解工作流

## ★ 执行总纲（每次拆解都按这9步走，不要跳步）

```
① 入口反问      信息不全先问清（我方/竞品？只拆一条还是做对比？）
② 选品          近7天 + 5个硬门槛，不足10条按 7→14→28 天降级，报告中注明实际窗口
③ 采集          每条视频5个FastMoss工具 + 达人账号 + 广告数据（分批并行）
④ 逐条拆解      10条竞品 + 我方，Step 1→5，10条格式必须完全一致
⑤ 算聚合        竞品均值 / 竞品最优 / 我方差距（真算，不许沿用旧报告数字）
⑥ 出MD          按 MD结构A，先把数据和结论对准，交给用户确认
⑦ 填模板        读 .claude/skills/v3-report-template/template-same-product.html（见下方「模板填充规范」），把 {{PLACEHOLDER}} 替换为实际数据，区块02末尾加话题标签卡片
⑧ 自检          对照文末「交付前自检清单」逐条核对
⑨ 发布          Artifact，给用户链接
```

**四条铁律**（违反任何一条都算不合格）：

1. **不从零写HTML/CSS** —— 必须基于模板文件，否则每次样式都漂移
2. **不跨区块重复论证** —— 同一个结论只能出现在一个区块（见「区块职责边界」）
3. **不编造数据** —— 拿不到就标「—」，人工评分要标注是人工评分
4. **不省略强制指标** —— 大盘表28个指标行、15列，一个都不能少

---

## 两种模式

| 模式 | 触发条件 | 报告格式 |
|------|---------|---------|
| **单视频拆解** | 用户明确说"只拆这一条" | JSON注入 `.claude/skills/v3-report-template/template.html`（节省85% token）|
| **竞品对比拆解**（默认） | 其余所有情况 | MD报告 → 按下方「HTML输出格式规范」生成 Artifact |

> ⚠️ **MD-First原则**：竞品对比模式先生成 Markdown 报告（~200行，生成快），
> 用户确认数据和结论无误后，再生成HTML并发布Artifact。
> 避免直接写900+行HTML导致等待过长、且用户无法中途纠错。

---

## ★ HTML输出格式规范（竞品对比模式，固定不变）

> **所有竞品对比报告必须严格遵守本节规范，禁止自行调整颜色、字体、区块结构。**
> 本节是格式的唯一权威来源，不依赖外部模板文件。

### CSS Token（禁止修改）

生成报告时，`<style>` 块的 `:root` 必须包含以下完整 token，原样复制，一个都不能少：

```css
:root {
  --bg:#FFFFFF; --bg-alt:#F8FAFC; --bg-card:#FFFFFF;
  --text:#111827; --text-mid:#4B5563; --text-light:#9CA3AF; --border:#E5E7EB;
  --orange:#F97316; --orange-bg:#FFF7ED;
  --blue:#2563EB;   --blue-bg:#EFF6FF;
  --purple:#7C3AED; --purple-bg:#F5F3FF;
  --green:#059669;  --green-bg:#ECFDF5;
  --red:#DC2626;    --red-bg:#FEF2F2;
  --yellow:#D97706; --yellow-bg:#FFFBEB;
  --shadow:0 1px 3px rgba(0,0,0,.08);
  --shadow-lg:0 4px 12px rgba(0,0,0,.1);
}
@media(prefers-color-scheme:dark){:root:not([data-theme="light"]){
  --bg:#0F172A;--bg-alt:#1E293B;--bg-card:#1E293B;
  --text:#F1F5F9;--text-mid:#94A3B8;--text-light:#64748B;--border:#334155;
  --orange-bg:#431407;--blue-bg:#172554;--purple-bg:#2E1065;
  --green-bg:#052E16;--red-bg:#450A0A;--yellow-bg:#451A03;
  --shadow:0 1px 3px rgba(0,0,0,.3);--shadow-lg:0 4px 12px rgba(0,0,0,.4);
}}
:root[data-theme="dark"]{
  --bg:#0F172A;--bg-alt:#1E293B;--bg-card:#1E293B;
  --text:#F1F5F9;--text-mid:#94A3B8;--text-light:#64748B;--border:#334155;
  --orange-bg:#431407;--blue-bg:#172554;--purple-bg:#2E1065;
  --green-bg:#052E16;--red-bg:#450A0A;--yellow-bg:#451A03;
}
```

### 字体（禁止修改）

```html
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600&family=Syne:wght@600;700;800&display=swap" rel="stylesheet">
```

| 角色 | 字体 | 用途 |
|------|------|------|
| 正文 | `'Inter'` | body、段落、列表 |
| 数字/代码 | `'JetBrains Mono'` | 所有数字、指标值、播放量、GMV |
| 标题 | `'Syne'` | h1/h2/区块编号/区块标题 |

### 固定布局参数

```css
body { max-width:1200px; margin:0 auto; padding:24px 20px; }
.block-header { margin:48px 0 20px; padding-bottom:12px; border-bottom:2px solid var(--border); }
.block-num { width:32px; height:32px; border-radius:8px; /* 颜色按区块 */ }
/* 区块编号颜色: 01=orange / 02=blue / 03=green / 04=purple */
.card { border-radius:12px; padding:20px; box-shadow:var(--shadow); }
.matrix { min-width:1180px; font-size:13.5px; } /* 转置表宽度，必须 wide-wrap 包裹 */
```

### 4个区块的固定顺序和主色

| 区块 | 编号颜色 | 禁止包含 |
|------|---------|---------|
| 01 竞品大盘总览 | `var(--orange)` | 我方结构分析细节（留区块3）|
| 02 竞品逐条拆解 | `var(--blue)` | 我方视频分析（留区块3）|
| 03 我方视频拆解 | `var(--green)` | 竞品比较结论（已在区块1）|
| 04 行动方案 | `var(--purple)` | 同一条建议重复出现 |

### 区块01 矩阵表固定格式

- **方向**：转置（指标=行，达人=列），禁止改成"达人=行，指标=列"
- **列顺序**：`指标行头 | #1…#10 | 我方(green-bg) | 竞品均值(agg) | 竞品最优(agg) | 我方差距(agg)`
- **分区行**：基础信息 / 达人账号 / 流量与互动 / 观看深度 / 商业转化 / 内容评分（共6个）
- **差距列颜色**：`gap-b`=绿(优势) / `gap-w`=红(劣势) / `gap-n`=灰(中性)
- **表格下方固定2张解读卡**：关键发现（红色左边框）+ 观看深度解读（橙色左边框），不多不少

### 区块02 竞品卡片固定格式

每张卡片结构（10条全部一致，禁止差异化对待）：

```
<details [#1 加 open 属性]>
  <summary>
    <span style="color:var(--orange)">#N</span>
    @handle · 播放 · GMV · 时长
    <span class="badge badge-ad/badge-organic" style="margin-left:auto">投流/自然</span>
  </summary>
  <div class="detail-body">
    [左栏] 脚本时间线（.timeline > .tl-item）
    [右栏] 5维评分（.score-row，颜色固定：钩子=orange/收藏=blue/分享=purple/完播=green/评论=red）
    [底部] 元数据条（标题原文 + 标题策略分析 + 话题标签色块）
  </div>
</details>
```

5维评分颜色固定（禁止调换）：

| 维度 | 条形颜色 |
|------|---------|
| 钩子力 | `var(--orange)` |
| 收藏驱动 | `var(--blue)` |
| 分享驱动 | `var(--purple)` |
| 完播引导 | `var(--green)` |
| 评论激活 | `var(--red)` |

### 区块02 末尾：共性小结 + 话题标签卡片

10张卡片之后，固定追加2个元素：

**1. 共性小结卡**（紫色左边框）：时长规律 / 展示方式 / GMV分布 / 投流比例

**2. 话题标签卡**（蓝色左边框，见「前5热门话题标签分析方法论」）：

```
5个格子固定颜色方案:
  格子1 核心词       → 蓝色边框+蓝色背景 (var(--blue) / var(--blue-bg))
  格子2 高GMV信号词  → 绿色边框+绿色背景 (var(--green) / var(--green-bg))
  格子3 解决方案词   → 灰色边框 (var(--border))，紫色标签
  格子4 大众流量词   → 灰色边框，橙色标签
  格子5 品牌词       → 灰色边框，黄色标签
  底部修正框         → 黄色背景 (var(--yellow-bg))，必须包含推荐标签组合公式
```

### 结论区固定格式

渐变背景（blue→purple），3段文字：
1. 竞品为什么能爆
2. 我方为什么没爆
3. 怎么复制

末行：数据来源注脚（FastMoss工具清单 + "内容评分为人工拆解"声明）

---

## 全局规定：所有指标名称使用中文

**报告中所有指标必须使用中文，禁止出现英文指标标签**。映射关系如下：

| 英文 | 中文 | 说明 |
|------|------|------|
| Lift / viral lift | **爆发倍数** | 视频播放 ÷ 达人均播 |
| Engagement Rate | **互动率** | (点赞+评论+分享+收藏) ÷ 播放 |
| IPM | **互动强度（IPM）** | 互动数/千次播放 |
| Save Rate | **收藏率** | 收藏 ÷ 播放 |
| Share Rate | **分享率** | 分享 ÷ 播放 |
| GMV | **带货金额（GMV）** | 可直接用GMV缩写，但旁边注明"带货金额" |
| viral_index | **爆款指数** | FastMoss商品热度评分 |
| Hook | **钩子** | 可用英文，通常已是行业惯用词 |
| CTA | **行动引导（CTA）** | 第一次出现时注明中文 |
| is_ad | **是否投流** | true=⚠️投流，false=✓自然流量 |

---

## 可选维度说明（用户未指定时主动反问）

**触发条件**：用户只说品类词（如"找爆款 香水"），未附加任何筛选条件时，输出以下维度菜单，**然后停下来等用户回复**，不自动执行搜索。等用户选择维度或说"直接找"后再继续。

> 示例反问话术：
> "你想用什么维度筛选？（不说的话我用默认参数搜）"

---

### 第一类：搜索筛选维度（缩小候选池）

> 说法示例：`找爆款 香水 粉丝5万以下 不投流 互动率1%以上 最近7天`

| 维度 | 怎么说 | 默认值 | 典型用途 |
|------|--------|--------|---------|
| 粉丝规模 | 粉丝X万以下 / X万以上 | 不限 | 找小账号高爆发倍数案例（越小越可复制） |
| 投流/自然 | 不投流 / 只看投流 | 不限 | 不投流=有机爆款，更易复制；投流=看付费打法 |
| GMV门槛 | GMV $X万以上 | 不限 | 过滤低商业转化，只看真正卖货的 |
| 互动率 | 互动率X%以上 | 不限 | 1%以上=真实高参与，过滤低质量流量视频 |
| 播放量 | 播放X万以上 | 不限 | 只看已经爆的视频 |
| 时间范围 | 最近X天 | 近28天 | 7天=最新鲜；90天=更大样本 |
| 地区 | US / UK / AU | US | 针对特定市场 |
| 点赞量 | 点赞X万以上 | 不限 | 控制互动绝对量 |

---

### 第二类：拆解重点维度（决定报告分析侧重）

> 说法示例：`v3拆解 https://... 重点拆钩子` 或 `找爆款 香水 看买家反馈`

| 说法 | 含义 | 报告哪一步放大 |
|------|------|--------------|
| `重点拆钩子` | 深挖钩子类型、话术公式、情绪触发机制 | Step 2/3：钩子归类+逐句脚本映射 |
| `看怎么卖货的` / `商业转化` | 分析GMV路径、互动强度、CTA布局 | Step 2：带货金额+互动强度拆解；Step 3：CTA段落 |
| `拆脚本` | 逐句映射 Hook→Problem→Solution→Proof→CTA | Step 3：5段结构全展开+病毒评分 |
| `看买家反馈` / `买家心理` | 买家真实评论洞察 | Step 4：评论洞察放大，高频词+核心疑虑 |
| `找能抄的` / `可复制性` | 判断是否值得复制，给出具体可复制框架 | Step 5/6：RIDE/BEND判定+完整脚本框架 |
| `看竞争` | 分析该商品有多少达人在推、窗口是否饱和 | Step 5：爆款指数+竞争达人数+窗口判断 |

> 未指定拆解重点时，6步全部正常执行，报告各步骤权重相同。

---

## 入口反问逻辑（最优先执行，在入口判断之前）

**当用户表达的意图模糊**（只说想"拆解视频"、"分析视频"、"看看竞品"，但没有提供足够信息时），**必须先反问，不能自行假设**。

### 触发反问的条件

满足以下任意一条，就停下来反问：
1. 用户提到"拆解"/"分析"/"看看"但**没有提供任何URL**，也没有提供品类关键词
2. 用户提供了一个URL，但**语气暗示可能想对比**（如"想看看我们的视频比竞品差在哪"）
3. 用户说"想做竞品对比"但**只给了一个URL或一个品类**，没给够两个视频

### 标准反问话术

**情况1：完全没提供URL和品类，只说想拆解**

> 好的，请问你想做哪种分析？
>
> **A · 单视频爆款拆解**
> 拆一条视频为什么爆、怎么复制
> 需要提供：TikTok 视频链接（或品类关键词让我来找）
>
> **B · 竞品对比拆解**
> 我们的达人视频 vs 竞品爆款，找出差距根因
> 需要提供：两条视频链接（我方一条 + 竞品一条）
>
> 你想做哪个？或者直接把视频链接发给我也行。

---

**情况2：只有一个URL（默认进入竞品对比模式）**

> 收到，我会以这条视频为基准，自动搜索近7天同品类 Top 10 竞品，完整对比拆解。
>
> 请确认：**这是你们自己的视频**，还是**竞品视频**？
> - 自己的 → 我来找竞品
> - 竞品 → 我来找同品类其他爆款一起对比
>
> 如果只想拆解这一条（不做竞品对比），直接说一下。

---

**情况3：提到竞品但信息不全**

> 明白，我来帮你做竞品对比。需要确认两个视频：
>
> 1. **我们的视频**：[已有 / 请提供链接]
> 2. **竞品视频**：[已有 / 请提供链接，或告诉我品类让我搜一条]
>
> 两个都有了就立刻开始。

---

> ⚠️ 反问只问一次，用户回答后立即进入对应流程，不要再次确认。

---

## 入口判断（反问后执行，或信息已足够时直接执行）

> ⚠️ **默认模式为竞品对比**：所有视频拆解请求默认进入 Step 0-COMPARE，不存在单视频模式。
> 用户提供自己的视频 → 自动搜索近7天Top 10竞品 → 完整对比拆解。

| 用户输入 | 路径 |
|---------|------|
| 任意情况（包含一个或两个URL / 关键词 / 达人名） | → **Step 0-COMPARE 对比拆解模式（默认）** |
| 用户明确说"只拆这一条，不要竞品" | → 单视频模式（仅此例外）|

**竞品视频来源优先级：**
1. 用户主动提供竞品URL → 直接用
2. 用户只提供我方URL / 达人名 → 自动进入 Step 0-A 近7天发现模式，搜同品类Top 10竞品
3. 用户只说品类关键词 → 先搜竞品Top 10，再问用户提供我方视频（或跳过我方对比）

---

## ══════════════════════════════════════
## Step 0-COMPARE: 对比拆解模式（竞品 vs 我们的达人视频）
## ══════════════════════════════════════

### 触发语法

```
对比拆解 [竞品URL] [我们的URL]
对比拆解 [我们的URL] vs [竞品URL]
爆款对比 [URL1] [URL2]
找爆款 香水 跟我们这条视频对比 [我们的URL]
```

> **"竞品"**：其他达人/品牌推同类商品的爆款视频  
> **"我们的"**：我方合作达人推自家商品的视频  
> 如果用户只给一条URL + "对比"，则自动进入发现模式找同品类竞品，再做对比。

---

### 数据来源说明

| 数据类型 | 来源工具 | 说明 |
|---------|---------|------|
| 播放/点赞/评论/分享/收藏 | `video_detail_analysis` | FastMoss采集 |
| 带货金额 / 带货件数 / 互动强度 / 互动率 | `video_detail_analysis` | 同上，商业指标 |
| 是否投流 (is_ad) | `video_detail_analysis` | true=⚠️投流，false=✓自然流量 |
| 达人粉丝数 | `video_detail_analysis` | creator.follower_count |
| 达人均播 / 均赞 | `creator_profile_overview` | avg_video_play_count（爆发倍数分母）⚠️ 不要用 video_detail_analysis，它没有均播字段 |
| **爆发倍数** | 计算得出 | `视频播放 ÷ 达人均播`，来自FastMoss真实均值 |
| 视频字幕/脚本 | `video_script_info` | 有字幕则直接读文字，无则标注依赖画面 |
| 每日播放趋势/爆发节点 | `video_data_trends` | 哪天起飞、是否仍在增长 |
| 商品爆款指数 / 竞争达人数 | `product_detail_info` | 商品热度和赛道拥挤度 |
| 商品评分 / 买家评论 | `product_review_list` | 实际购买者评价 |
| 视频画面帧 | `yt-dlp + extract_frames.py` | 本地采集，分析Hook/产品/CTA镜头 |
| 佣金率 | `product_detail_info` | commission_rate（%），同商品共享同一值 |
| 话题标签数量 | `video_script_info` caption 文字 | 解析 #xxx 计数；caption 为空则手动 |

---

### 执行顺序（固定5步，按顺序执行）

---

**第1步：抓取Top 10竞品视频（近7天标准）**

进入Step 0-A发现模式，用近7天标准筛选，返回Top 10条视频，**全部10条都进入后续分析，不做单条筛选**。

```
📊 竞品分析模式启动
竞品视频: 近7天Top 10（自动搜索）
我方视频: [用户提供URL]
→ 10条竞品 + 1条我方，共11条视频进入分析...
```

---

**第2步：拆解分析10条竞品视频**

对10条视频**分批并行**采集FastMoss数据（每批5条，共2批）：

```
每条视频调用5个工具（共50个FastMoss调用）：
  video_detail_analysis {video_id: 视频N}   → 互动指标 + 带货数据 + 达人uid
  video_script_info     {video_id: 视频N}   → 字幕脚本
  video_data_trends     {video_id: 视频N}   → 播放趋势
  product_detail_info   {product_id: 视频N关联商品}  → 商品数据
  product_review_list   {product_id: 视频N关联商品}  → 买家评论

同一个product_id只调用一次，结果复用到其他视频
```

对每条视频完成 Step 1→Step 4 拆解，依次输出 `[竞品#1]`...`[竞品#10]`

---

**第3步：采集达人账号数据 + 计算观看深度代理指标（Step 0-D + Step 0-E）**

> ⚠️ 采集结果不单独成表，全部作为区块1转置表的「达人账号」和「观看深度」两个分区。

```
数据采集（3个来源并行）：

来源1: video_detail_analysis（Step 0-B已有，复用）
  → 每位达人的 follower_count（粉丝数）
  → 每个视频的 plays/likes/comments/shares/saves（互动深度计算）

来源2: creator_profile_overview × 11（分2批并行，每批5-6个）
  → 每位达人的 avg_video_play_count / interaction_rate / ipm

来源3: product_video_list（Step 0-A已有，复用）
  → 每位达人的 product_contribution.window_gmv（28天该商品GMV）
```

汇总后**不单独成表**，全部作为区块1转置表的行：
- 粉丝数 / 达人均播 → 区块1「达人账号」分区
- 互动深度比 / 评论·播放比 / 收藏·播放比 / 推测完播 → 区块1「观看深度」分区
- 达人IPM 与视频IPM 数值相同，去重；近28天该商品GMV 即「销售额(28d)」，去重

---

**第4步：拆解分析我方视频**

对我方视频调用5个FastMoss工具 + 画面采集：

```
mcp__FastMoss-MCP__video_detail_analysis {video_id: 我方}
mcp__FastMoss-MCP__video_script_info     {video_id: 我方}
mcp__FastMoss-MCP__video_data_trends     {video_id: 我方}
mcp__FastMoss-MCP__product_detail_info   {product_id: 我方关联商品}
mcp__FastMoss-MCP__product_review_list   {product_id: 我方关联商品}

yt-dlp + extract_frames.py (我方视频画面)
```

完成我方视频 Step 1→Step 4 完整拆解，输出 `[我们]`

---

**第5步：提取共性规律 + 生成行动方案 + 输出报告**

基于10条竞品的共性规律 + 我方视频短板，生成四节行动方案（见报告区块4规范）：
- 4.1 脚本怎么写（结合Top 10最高频的钩子类型和脚本结构）+ 两版中英双语成稿
- 4.2 视频怎么拍（结合Top 10的镜头/时长/节奏规律）
- 4.3 商家需要做哪些配合（投流/价格/库存/佣金率）
- 4.4 需要给达人提供哪些内容（脚本以外的物料）

每条建议带内联优先级标签，全报告只出现一次。
然后按「对比报告输出流程」出报告：先MD对数据 → 再填HTML模板 → 最后过自检清单。

---

### 对比报告输出流程（MD-First → 模板填充）

#### 第一步：生成MD报告（快速交付，先对数据）

```
MD模板路径: .claude/skills/v3-report-template/template-same-product.md
```

**读该模板 → 替换 `{{...}}` 占位符 → 补齐重复结构（10条竞品的 `<details>` 块、
矩阵表的10个竞品列）→ 删掉 `<!-- -->` 提示注释**。

模板已经把大盘矩阵表的 15 列表头、28 个指标行、7 个分区标题、表注、
两张解读卡的骨架、中英双语成稿的 beat 格式全部写死，直接填即可，不要自己排表。

跨品牌模式暂无MD模板，按下方 **MD结构B** 的说明手写。

文件命名：`报告/[达人]_[商品]_竞品对比报告.md`
（相对当前 Claude Code 工作目录；`报告/` 子目录不存在就先建。
⚠️ 不要写死任何用户名或绝对路径，不同员工的机器路径不一样。）

> ⚠️ **为什么MD-First**：对比报告的HTML有900+行（10条竞品卡片+转置大表+时间线+双语脚本），
> 直接写HTML耗时长且用户无法中途纠错。MD阶段先把**数据和结论**对准，再进入排版。

#### 第二步：填充HTML模板并发布 Artifact（用户确认后）

用户确认MD内容无误后（或直接要求HTML时），
**读取 `.claude/skills/v3-report-template/template-same-product.html`，把MD里的数据填进占位符**，
不要从零写HTML。填充完成后发布 Artifact。

文件命名：`报告/[达人]_[商品]_竞品对比报告.html`

#### 第三步：对照交付前自检清单逐条核对（见本文件末尾）

清单未全部通过，不算交付完成。

---

### 对比报告HTML规范（转HTML时遵循，MD阶段仅参考结构）

#### ★★ 必须基于模板文件生成，禁止从零手写 CSS ★★

```
模板路径: .claude/skills/v3-report-template/template-same-product.html
```

该模板包含**完整的CSS**（配色token / 深浅色主题 / 转置矩阵表 / 达人对照条 /
行动条目 / 时间线 / 中英脚本块 / 评分条）和**完整骨架**
（Hero + 区块01–04 + 结论），占位符为 `{{...}}`。

**生成步骤**：
1. 读取模板 → 2. 逐个替换 `{{...}}` 占位符 → 3. 补齐重复结构（10张竞品卡片、
   矩阵表的10个竞品列、行动条目）→ 4. 删掉骨架里的 `<!-- … -->` 提示注释 → 5. 发布

**禁止**：
- ❌ 不要改模板的 CSS（改了就和历史报告不一致，用户会看出样式漂移）
- ❌ 不要增删区块、不要改区块顺序和编号
- ❌ 不要自创 class 名，模板已有的 class 够用
- ❌ 不要把 `{{...}}` 占位符残留在成品里（交付前 grep 一遍 `{{`）

> 跨品牌模式（模式B）暂无模板，需手写时**复用本模板的 `<style>` 块**，只改 body 结构。

---

HTML版本为**完整自包含文件**（不使用JSON注入，因为双视频结构更复杂）。

#### 报告模式说明

对比报告分为两种模式，根据竞品定义自动选择：

| 模式 | 竞品定义 | 结构 | 大盘表布局 | 触发条件 |
|------|---------|------|-----------|---------|
| **同商品对比**（默认） | 同一商品的不同达人视频 | Hero + 区块1–4 + 结论（共6块） | **转置**：指标作行、达人作列 | 用户提供视频URL / 搜同商品竞品 |
| **跨品牌对比** | 外观类似、使用场景属性一致的**不同品牌**商品 | Hero + 区块01–09（共10块） | 常规：达人作行（需突出「品牌·商品」分组） | 用户要求跨品牌/不同产品对比 |

> ⚠️ 两种模式的大盘表**指标项均为强制**，不允许省略任何一项（见「全模式强制字段清单」）。
> ⚠️ 跨品牌模式的7天产品级数据使用 `product_investment` 工具获取。
> ⚠️ **两种模式的区块数不同是刻意的**：同商品模式已把所有「一行一条视频」的表并进大盘表，
> 故只剩4个区块；跨品牌模式需要按品牌维度做二次聚合（品牌矩阵/价格/投流），无法并表。

---

#### 模式A: 同商品对比 — 必须包含的区块（Hero + 4区块 + 结论，缺一不可）

```
区块0: 顶部Header（深色渐变）
  ├── 标签: 近7天竞品全量拆解 · FastMoss数据支撑
  ├── 标题: [品类名] · 近7天Top 10竞品 vs 我方视频
  ├── 副标题: 10条竞品全量拆解 + 我方差距诊断 + 落地方案
  └── 我方视频TikTok链接（绿色按钮）

区块1: 竞品大盘总览（★转置矩阵表：指标竖排 · 达人横排）
  │
  │ ⚠️ 表格必须转置：指标作「行」，达人作「列」。禁止把28个指标横排。
  │    理由：指标名是长中文（如"广告消耗(近7天)"）横排会强行拉宽每列，
  │    表格宽度超1800px；转置后行标签自然换行，数据格只放短数字。
  │
  ├── 列结构（共15列）：
  │     指标 | #1 … #10（10条竞品）| 我方 | 竞品均值 | 竞品最优 | 我方差距
  │     · 首列「指标」sticky固定，横向滚动时不消失
  │     · 达人列头**只放 `#序号`**（17px Syne粗体），不放 @handle
  │     · 我方列绿色高亮（--green-bg），置于10条竞品之后
  │     · 右侧三列（均值/最优/差距）为浅底聚合列，由10条竞品计算
  │
  ├── ⚠️ 达人名必须做成表格上方的「达人对照条」，不能塞进列头：
  │     19字符的 handle（如 @david_loves_trave6）物理上装不进80px的列，
  │     塞进去只能压到9-11px并在任意字符处断行，正是「压缩严重」的来源。
  │     对照条格式：胶囊chip横向排列并自动换行，每个 = `#序号`(蓝/绿) + 完整@handle，
  │     整体超链接→该达人的TikTok视频URL，字号13.5px，我方chip绿色高亮。
  │     上方配一行说明：「达人对照 · 点击打开对应的 TikTok 原视频（按销售额排序）」
  │
  ├── 行分区（7个分区，共28个指标行），每行数据来源：
  │
  │   ⚠️ 下面是 28 个**指标行**。`#序号` 和 `达人` 不在其中 ——
  │      转置后它们是**列的身份**（列头写 #序号，@handle 放对照条），不是行。
  │
  │   指标行名         │ FastMoss工具                          │ 字段路径
  │   ───────────────────────────────────────────────────────────────────
  │   关联商品·店铺    │ product_detail_info                   │ product_name + shop_name（合并为一列）
  │   视频发布时间     │ video_detail_analysis                 │ published_at_ts（Unix时间戳→ET，格式：MM-DD HH:MM:SS ET，精确到秒）
  │   播放量           │ product_video_list                    │ engagement_metrics.play_count
  │   点赞数           │ video_detail_analysis                 │ likes
  │   评论数           │ video_detail_analysis                 │ comments
  │   分享数           │ video_detail_analysis                 │ shares
  │   互动率           │ video_detail_analysis                 │ interaction_rate_percent
  │   IPM              │ video_detail_analysis                 │ ipm（每千次播放互动数）
  │   销售额(28d)      │ product_video_list(time_range_days=28)│ product_contribution.window_gmv
  │   销售额(近7天)    │ product_video_list(time_range_days=7) │ product_contribution.window_gmv
  │   广告消耗(近7天)  │ ad_data_overview                      │ summary.ad_performance.estimated_ad_spend
  │   ROAS(近7天)      │ ad_data_overview                      │ summary.ad_performance.roas
  │   时长             │ product_video_list                    │ video_meta.duration_seconds
  │   爆发倍数         │ video_detail_analysis + creator_profile_overview │ play_count ÷ avg_video_play_count
  │   病毒评分         │ 人工评分（5维×20=100分）
  │   投流             │ product_video_list                    │ traffic_flags.is_ad
  │   产品出镜时机     │ 人工拆解（首次出现产品的秒数）
  │   话题数量         │ 人工拆解（视频讲了几个不相干话题）
  │   有效产品秒数     │ 人工拆解（真正讲产品的秒数 / 占总时长%）
  │   粉丝数           │ video_detail_analysis                 │ creator.follower_count
  │   达人均播         │ creator_profile_overview              │ avg_video_play_count
  │   互动深度比       │ 计算: (赞+评+藏+转) ÷ 播放量
  │   评论/播放比      │ 计算: 评论 ÷ 播放量
  │   收藏/播放比      │ 计算: 收藏 ÷ 播放量
  │   推测完播         │ 推断: 由上面三个代理指标定级（高/中/中低/低/极低）
  │   佣金率           │ product_detail_info                   │ commission_rate（%）同商品=所有列相同，colspan处理
  │   话题标签数量     │ video_script_info caption文字         │ 统计#xxx标签个数；无caption则手动数TikTok视频页
  │   音乐策略         │ 人工拆解（听视频）                    │ 原创音频/热门音效/纯BGM；是否卡点剪辑
  │   封面帧类型       │ v3-video-scanner 开场帧（0s）         │ 人物特写/产品展示/文字冲击/动作瞬间
  │
  │   行按7个分区排列，分区标题行横跨全表：
  │     ① 基础信息    关联商品·店铺 / 发布时间 / 时长 / 投流
  │     ② 达人账号    粉丝数 / 达人均播
  │     ③ 流量与互动  播放量 / 点赞数 / 评论数 / 分享数 / 互动率 / IPM / 爆发倍数
  │     ④ 观看深度    互动深度比 / 评论·播放比 / 收藏·播放比 / 推测完播（★代理指标）
  │     ⑤ 商业转化    销售额(28d) / 销售额(近7天) / 广告消耗(近7天) / ROAS(近7天) / 佣金率
  │     ⑥ 内容评分    病毒评分 / 产品出镜时机 / 话题数量 / 有效产品秒数（★人工拆解，非FastMoss）
  │     ⑦ 元数据层    话题标签数量 / 音乐策略 / 封面帧类型（★人工/帧分析，非FastMoss）
  │
  │   ⚠️ 达人IPM 不要单列一行 —— creator_profile_overview 的 like_comment_ipm
  │      与 video_detail_analysis 的 ipm 数值相同，重复列会让读者以为是两个指标。
  │   ⚠️ 「推测完播」是文字等级，该行加 class 允许换行（其他行 nowrap）。
  │
  │   ⚠️ 关联商品·店铺: 同商品模式下所有列相同 → 用 colspan 横跨一行只写一次，不要重复11遍
  │   ⚠️ 销售额(近7天): 超出7天窗口的视频标注"—"并加脚注
  │   ⚠️ ROAS(近7天): 来自FastMoss ad_data_overview真实数据，不是估算。自然流量视频=∞
  │   ⚠️ 广告消耗(近7天): 来自ad_data_overview，自然流量视频=$0
  │   ⚠️ 点赞数/评论数/发布时间: 来自video_detail_analysis，每条视频必须单独采集
  │   ⚠️ 发布时间精度: 使用 published_at_ts（Unix时间戳，秒级）而非 publish_time（只有日期）
  │       转换规则: ET = UTC-4（EDT，美国东部夏令时，3月-11月），日期边界按ET算
  │       显示格式: 矩阵表格「MM-DD」下方附「HH:MM:SS」小字（mono字体）
  │       ⚠️ video_detail_analysis 调用时必须传 page=1, pagesize=1（否则报错缺少必填参数）
  │   ⚠️ 佣金率: 同商品模式下所有列相同 → 用colspan横跨，只写一次（跨品牌模式按产品各自填）
  │   ⚠️ 内容评分分区规则:
  │     - 病毒评分: 所有竞品都必须填（基于字幕+画面判断，不需要帧采集）
  │     - 产品出镜时机/话题数量/有效产品秒数: 仅对有字幕或已做逐帧拆解的竞品填写
  │     - 无字幕且未做帧采集的竞品，这三项标注"—"，禁止凭空填数
  │     - 我方视频: 四项全部必须填，不允许"—"
  │   ⚠️ 元数据层分区规则:
  │     - 话题标签数量: 先从 video_script_info caption 数 #xxx 标签；caption 为空则标 "—/手动数"
  │     - 音乐策略: 必须听视频才能判断，无法从FastMoss自动获取，无法看视频则标"—"
  │     - 封面帧类型: 从 v3-video-scanner 开场帧分析直接填，所有有帧的视频必须填
  │     - 我方视频: 三项全部必须填，不允许"—"
  │
  ├── 聚合三列的算法：
  │     竞品均值 = 10条竞品算术平均（ROAS只统计投流视频，自然流量的∞不参与）
  │     竞品最优 = 10条中该指标最好的值
  │     我方差距 = (我方 − 竞品均值) ÷ 竞品均值，绿色=优势 / 红色=劣势 / 灰色=中性
  │
  ├── 大盘规律小结：
  │     ├── 平均播放量 / 平均GMV / 平均互动率
  │     ├── 最高频钩子类型（Top 3）
  │     └── 最优时长区间
  │
  └── 表格下方**固定2张**解读卡片（表格只放数字，解读全部落在卡片里）：
        ├── 关键发现：粉丝效率倒挂
        │     粉丝量/互动率与GMV是否背离 → 说明「天花板不在流量，在内容结构」
        │     ⚠️ 只写横向对比，不写我方结构问题细节（那是区块3），末尾指向区块3
        └── 观看深度解读
              为什么要用代理指标 + 三个公式 + 核心洞察
        ⚠️ 不要再加第三张卡。曾有的「差距解读」卡已并入上面第一张。

区块2: 10条竞品逐条拆解（卡片折叠式，每条可展开）
  ⚠️ 重要：所有10条竞品必须使用完全相同的卡片格式，不允许：
  - 把 #4-#10 缩为简化表格/一行摘要
  - 只对 Top 3 展开完整卡片，其余降级
  - 用"其余X条竞品"分组折叠
  每条竞品一张独立可展开卡片，格式完全一致。

  每条卡片包含（10条全部一样，不分等级）：
  ├── 卡片头: @handle / 播放量 / GMV / 时长 / 是否投流
  ├── 左栏 - 脚本结构:
  │     逐段时间线（Hook→Problem→Solution→Demo+Proof→Value→CTA）
  │     每段: 时间戳 + 段落类型 + 字幕原文/画面描述
  │     ⚠️ 无字幕的视频标注"无字幕"，用画面描述替代
  ├── 右栏 - 5维病毒评分（人工评分，逐维对照根 SKILL.md 锚点定义打分）:
  │     钩子力/收藏驱动/分享驱动/完播引导/评论激活（各/20，每维只选 20/15/10/5 四档）
  │     横向条形图（颜色区分5个维度）
  │     + 核心驱动力总结（1-2句）
  │     ⚠️ 1句评价必须说明选了哪档、为什么（不能只写分数）
  ├── 底部元数据条（每张卡片必须有，紧接评分下方）:
  │     视频标题/Caption — 原文（从 video_script_info caption 或 TikTok 视频页提取）
  │     标题策略 — 1句分析（极简动作词/痛点声明/竞品对比提问/促销紧迫/POV格式/功能承诺/悬念挑战）
  │     话题标签 — 列出全部 #xxx 标签（从 caption 解析，视觉上用小色块呈现）
  └── 底部共性小结（仅在最后一张卡片之后）:
        时长规律 / 展示方式 / GMV分布 / 前5热门话题标签（见下方方法论）

## 前5热门话题标签分析方法论（品类维度）

**错误方法（禁止使用）**：只统计手头10条竞品视频的标签频率 → 样本偏小，且这10条本身可能是被刻意挑选的投流视频，标签使用习惯不代表高GMV视频的真实规律。

**正确方法：product_video_list × GMV加权分析**：

```
Step 1: 获取全量关联视频
  mcp__FastMoss-MCP__product_video_list
    {product_id, time_range_days: 90, orderby: [{field: "gmv", order: "desc"}]}
  → 拉前3-4页（30-40条），按GMV从高到低排序

Step 2: 从 caption_text 解析标签
  每条视频的 caption_text 字段已包含话题标签（#xxx 格式）
  直接解析，不需要额外调用 video_script_info

Step 3: GMV加权统计
  重点关注：
  ① Top 10 高GMV视频中哪些标签出现最频繁（高GMV相关性）
  ② 哪些标签在高GMV视频独有、中低GMV视频少见（差异化信号词）
  ③ 哪些标签全层级普遍（大众流量词）
```

**标签分级框架**：

| 级别 | 特征 | 示例 |
|------|------|------|
| **核心词**（每条必用） | 出现在几乎所有高GMV视频 | #nailglue（产品品类主词） |
| **高GMV信号词**（优先使用） | 仅在Top高GMV视频出现，中低GMV视频少见，竞争相对低 | #semisolidnailglue（差异化词） |
| **解决方案词**（配合使用） | 与信号词同现，锁定有需求用户 | #pressonnailhack（FAQ/痛点词） |
| **大众流量词**（补充覆盖） | 全层级均有，宽泛曝光 | #pressonnails（受众覆盖词） |
| **品牌词**（必用） | 品牌归属 | #curvlife（账号关联） |

**⚠️ 常见错误认知纠正**：
- `#tiktokshop` 等平台通用标签在投流视频中频繁出现，但在自然高GMV视频中反而很少使用，**不应将其列为"核心标签"**
- 标签频率 ≠ GMV贡献，必须做 GMV × 标签出现 的交叉分析，而非单纯统计出现次数

**在报告中的调用时机**：区块02最后一张竞品卡片（#10）之后，在「底部共性小结」下方紧接插入话题标签卡片（见模板 `{{HASHTAG_CARD}}` 位置）。话题标签数据**必须在填充模板前就已完成采集**，不能等到生成HTML时再跑。

---

## 模板填充规范（template-same-product.html）

> 模板位于 `.claude/skills/v3-report-template/template-same-product.html`
> CSS Token 和字体在模板中已固定，**禁止修改 CSS**，只替换 `{{PLACEHOLDER}}` 数据。

### 必须替换的 Placeholder 列表

| Placeholder | 填入内容 | 数据来源 |
|-------------|---------|---------|
| `{{PRODUCT_NAME}}` | 完整商品名 | product_detail_info |
| `{{PRODUCT_DESC}}` | 简短产品描述（英文） | 同上 |
| `{{OUR_HANDLE}}` | 我方达人@handle（不含@） | video_detail_analysis |
| `{{N_VIDEOS}}` | 竞品数量（通常10） | 实际采集条数 |
| `{{TIME_WINDOW}}` | 如"14天+28天混合" | 实际选取窗口 |
| `{{TOTAL_VIEWS}}` | 竞品总播放量（如"92.1万"） | 计算 |
| `{{TOTAL_GMV}}` | 竞品总GMV（如"$12,843"） | 计算 |
| `{{OUR_VIEWS}}` | 我方视频播放量 | video_detail_analysis |
| `{{OUR_GMV}}` | 我方视频GMV | video_detail_analysis |
| `{{PRICE}}` | 售价（如"$12.99"） | product_detail_info |
| `{{RATING}}` | 评分（如"4.6"） | product_detail_info |
| `{{VIRAL_INDEX}}` | viral_index数值 | product_detail_info |
| `{{REPORT_DATE}}` | 报告日期YYYY-MM-DD | 当天 |
| `{{CATEGORY_ZH}}` | 品类中文名（如"美甲胶"） | 人工填写 |
| `{{SHOP_NAME}}` | 店铺名 | product_detail_info |
| `{{CREW_LINKS}}` | 10个达人+我方 `<a>` 标签 | product_video_list |
| `{{MATRIX_HEADER_COLS}}` | 矩阵表列头（#1…#10+我方+3聚合） | — |
| `{{ROW_*}}` 系列 | 矩阵每行数据（共28行） | FastMoss |
| `{{TABLE_FOOTNOTE}}` | 表格底部数据说明 | 固定文案+窗口说明 |
| `{{KEY_FINDING_TITLE}}` | 关键发现标题（如"粉丝效率倒挂"） | 分析得出 |
| `{{KEY_FINDING_BODY}}` | 关键发现正文（含具体数字对比） | 分析得出 |
| `{{WATCH_DEPTH_INSIGHT}}` | 观看深度解读正文 | 分析得出 |
| `{{COMPETITOR_CARDS_1_TO_10}}` | 10张竞品折叠卡片（格式见模板注释） | Step 1-4 拆解结果 |
| `{{DURATION_PATTERN}}` | 时长规律一句话 | 统计得出 |
| `{{DISPLAY_PATTERN}}` | 展示方式一句话 | 统计得出 |
| `{{GMV_DISTRIBUTION}}` | GMV分布一句话 | 统计得出 |
| `{{AD_RATIO}}` | 投流比例（如"90%投流"） | 统计得出 |
| `{{TOTAL_VIDEOS}}` | 品类关联视频总数 | product_video_list返回 |
| `{{HASHTAG_1}}` ~ `{{HASHTAG_5}}` | 5个话题标签（含#号） | GMV加权分析 |
| `{{HASHTAG_N_COVERAGE}}` | 覆盖描述（如"Top40高GMV视频均含"） | GMV加权分析 |
| `{{HASHTAG_N_DESC}}` | 标签战略价值一句话 | 分析得出 |
| `{{HASHTAG_CORRECTION_NOTE}}` | 重要修正说明（若有早期错误分析） | 分析得出 |
| `{{OUR_VIDEO_FULL_BREAKDOWN}}` | 区块3我方完整拆解HTML | Step 1-5 |
| `{{ACTION_SCRIPT/SHOOT/MERCHANT/CREATOR_MATERIALS}}` | 4个行动方案板块 | 区块4 |
| `{{CONCLUSION_*}}` | 3段核心结论 | 全局 |

### 矩阵表行的填充规则

```
每个 {{ROW_XXX}} 展开为一个 <tr>:
  <tr>
    <th class="rowlab">中文指标名</th>
    <td class="val">竞品#1数据</td>
    ...  (10个td，我方用 class="val ours")
    <td class="val ours" [颜色样式]>我方数据</td>
    <td class="val agg">竞品均值</td>
    <td class="val agg">竞品最优</td>
    <td class="agg gap-b/gap-w/gap-n">差距百分比或说明</td>
  </tr>

颜色规则:
  - gap-b（green）: 我方优于竞品均值
  - gap-w（red）: 我方劣于竞品均值
  - gap-n（gray）: 中性或不可比
```

### 话题标签卡片填充规则

话题标签卡片有**5个格子**，固定颜色方案：
- 格子1（核心词）: 蓝色边框 `var(--blue)`，背景 `var(--blue-bg)`
- 格子2（高GMV信号词）: 绿色边框 `var(--green)`，背景 `var(--green-bg)`
- 格子3（解决方案词）: 灰色边框 `var(--border)`，紫色标签
- 格子4（大众流量词）: 灰色边框，橙色标签
- 格子5（品牌词）: 灰色边框，黄色标签

重要修正框（黄色）必须包含：早期分析对比说明 + 推荐标签组合公式。

区块3: 我方视频完整拆解（5个Step完整展开，绿色主题）
  ├── Hero Card（含TikTok链接、达人信息、商品信息、5大数字）
  ├── Step 1: 视频深度扫描
  │     ├── TL;DR总结
  │     ├── 逐段时间线（含字幕原文，每段含状态图标✅⚠️❌）
  │     └── 电商5维诊断评分（钩子时效/产品出镜/CTA布局/留存机制/卖点传递）
  ├── Step 2: 爆款诊断
  │     ├── 爆发倍数判定卡
  │     ├── 与竞品Top 10均值对比
  │     └── 播放趋势条形图
  ├── Step 3: 脚本结构拆解
  │     ├── 病毒评分（100分制，人工评分，逐维对照根 SKILL.md 锚点定义打分，每维只选 20/15/10/5）
  │     ├── 5段结构 + 硬规则检查
  │     └── 修复建议（含改前→改后话术）
  ├── Step 4: 买家洞察
  └── Step 5: 复制公式 / RIDE/BEND判定

区块4: 行动方案（★原「行动清单」+「方案建议」合并）
  │
  │ ⚠️ 禁止再拆成两个区块。两者原本是两条不同的切分轴
  │    （一个按优先级切，一个按执行面切），同一条建议会出现两次。
  │    合并后**只按执行面切**，优先级降级为每条建议的内联标签。
  │
  ├── 顶部图例：立即可抄（绿）/ 评估后推进（黄）/ 不能直接抄（红）
  │
  ├── 4.1 脚本怎么写
  │     ├── 若干条建议，每条格式: [优先级标签] + 粗体要点 + 一句理由（附竞品证据）
  │     ├── 钩子话术（直接给出0-5s开场台词原文）
  │     ├── 正文段落结构（Problem/Solution/Proof各几秒说什么）
  │     ├── CTA话术（原文，含购物车引导方式）
  │     └── 末尾附2个可直接拍的完整脚本成稿（分时间段，对标不同竞品）
  │
  ├── 4.2 视频怎么拍
  │     ├── 画面配比（特写/口播/全景各占比）
  │     ├── 剪辑节奏（每几秒切一次）
  │     ├── 音频策略
  │     └── 产品出镜方式（何时出现/怎么展示）
  │
  ├── 4.3 商家需要配合什么
  │     ├── 广告投放（是否投流/预算建议/前置条件）
  │     ├── 价格策略（调价/优惠券/限时促销）
  │     ├── 库存准备（根据GMV预估备货量）
  │     └── 佣金率调整（当前佣金率是否足够吸引达人投流）
  │
  └── 4.4 需要给达人提供什么（脚本之外）
        ├── 产品寄送（哪几款SKU/规格/数量）
        ├── 对比道具 / 演示道具
        ├── 话术卡（痛点关键词 + 产品卖点）
        ├── 话术禁区（违禁词/不能夸大的功效）
        └── 拍摄参考（附竞品视频链接或截图）

  ⚠️ 每条建议在整份报告中只能出现一次。写完后自检：
     若某条建议在4.1和4.3都出现，必须合并到更贴切的那一节。

⚠️ 不再有独立的「达人账号数据 + 互动深度分析」区块。
   这两张子表的每一行都对应一条视频/一位达人，与区块1的列一一对应，
   因此全部并入区块1转置表：
     · 粉丝数 / 达人均播        → 「达人账号」分区
     · 互动深度比 / 评论·播放比 / 收藏·播放比 / 推测完播 → 「观看深度」分区
     · 达人IPM 与视频IPM数值相同，去重，只保留「流量与互动」分区的 IPM 一行
     · 近28天该商品GMV 即「销售额(28d)」，已在「商业转化」分区
   原区块的两段解读文字（粉丝效率倒挂 / 观看深度核心洞察）改为区块1表格下方的解读卡片。

⚠️ 不再有独立的「差距矩阵」区块。
   原12维中8维（播放量/GMV/时长/互动率/IPM/爆发倍数/病毒评分/投流）与区块1完全重复，
   已改为在区块1转置表右侧追加「竞品均值 / 竞品最优 / 我方差距」三列，
   差距对比直接贴在原始数据旁边；原矩阵独有的内容层维度
   （产品出镜时机 / 话题数量 / 有效产品秒数）并入区块1的「内容评分」分区。
   粉丝数差距在区块1「达人账号」分区中已可直接读出，不再单列。

结论
  ├── 核心结论（3段：竞品为什么能爆 / 我方为什么没爆 / 怎么复制）
  └── 数据来源注脚
```

---

#### 模式B: 跨品牌对比 — 必须包含的10大区块（Hero + 9板块，缺一不可）

> 跨品牌模式用于对比**外观类似、使用场景属性一致但品牌不同**的竞品视频。
> 表格需要额外的"品牌·商品"列，7天数据来自 `product_investment`（产品级）。

```
Hero: 顶部Header（深色渐变）
  ├── 标签: 跨品牌竞品深度分析 · FastMoss数据支撑
  ├── 标题: [品类名] · 跨品牌竞品对比分析
  ├── 副标题: [N]个品牌 · [M]条视频全量拆解
  └── 我方视频TikTok链接（绿色按钮）

区块01: 跨品牌竞品大盘（汇总表格：竞品行 + 我方绿色高亮行）
  ├── 表格字段（固定18列，强制不可省略），每列数据来源：
  │
  │   列名               │ FastMoss工具                            │ 字段路径
  │   ─────────────────────────────────────────────────────────────────────────
  │   #                  │ 序号（按GMV排序）
  │   品牌·商品          │ product_detail_info                     │ brand_name + product_name（跨品牌模式专用列）
  │   达人               │ product_video_list                      │ creator.creator_handle（附TikTok视频URL超链接）
  │   发布时间           │ video_detail_analysis                   │ published_at_ts（Unix时间戳→格式MM-DD）
  │   时长               │ product_video_list                      │ video_meta.duration_seconds
  │   播放量             │ product_video_list                      │ engagement_metrics.play_count
  │   点赞数             │ video_detail_analysis                   │ likes
  │   评论数             │ video_detail_analysis                   │ comments
  │   分享数             │ video_detail_analysis                   │ shares
  │   互动率             │ video_detail_analysis                   │ interaction_rate_percent
  │   IPM                │ video_detail_analysis                   │ ipm
  │   销售额(28d)        │ product_video_list(time_range_days=28)  │ product_contribution.window_gmv
  │   销售额(近7天)†     │ product_investment                      │ ad_performance_summary.product_total_gmv
  │   广告消耗(近7天)†   │ product_investment                      │ ad_performance_summary.estimated_ad_spend
  │   ROAS(近7天)†       │ product_investment                      │ ad_performance_summary.roas
  │   爆发倍数           │ video_detail_analysis + creator_profile_overview │ play_count ÷ avg_video_play_count
  │   病毒评分           │ 人工评分（5维×20=100分，与模式A同一套口径），报告中标注为人工评分
  │   投流               │ product_video_list                      │ traffic_flags.is_ad
  │
  │   ⚠️ † 标注的列为产品级数据（非视频级），同一商品的不同视频共享相同的7天数据
  │   ⚠️ 必须在表格底部添加脚注说明: "† 近7天数据为产品级汇总（product_investment），非单视频归因"
  │   ⚠️ 达人名必须是超链接 → TikTok视频URL
  │   ⚠️ 每条视频必须单独调用 video_detail_analysis 获取 发布时间/点赞数/评论数
  │   ⚠️ 每个产品必须单独调用 product_investment 获取 7天销售额/广告消耗/ROAS
  │   ⚠️ 品牌名使用彩色标签(chip)区分不同品牌
  │
  ├── 我方行绿色高亮，置于表格最后一行
  └── 大盘规律小结：
        ├── 品牌分布 / 价格区间
        ├── 平均播放量 / 平均GMV / 平均互动率
        └── 投流比例 / 最优时长区间

区块02: 品牌竞争矩阵（按品牌维度汇总对比）
  ├── 每个品牌一行: 品牌名 / 视频数 / 总播放量 / 平均互动率 / 总GMV / 7天广告消耗
  ├── 品牌综合评分（基于GMV+播放+互动率加权）
  └── 品牌定位分析（高端/中端/性价比/新锐等）

区块03: 达人画像对比
  ├── 子表A: 达人账号数据（全部达人 + 我方绿色高亮）
  │   每行字段: 粉丝数 / 视频平均播放量 / 互动率 / 视频IPM / 近28天GMV
  └── 子表B: 互动深度分析
      每行指标: 互动深度比 / 评论/播放比 / 收藏/播放比 / IPM / 推测完播等级

区块04: 内容模式与时长分析
  ├── 时长分布统计（<15s / 15-30s / 30-60s / >60s）
  ├── 各时长段的平均GMV和互动率
  ├── 钩子类型分布（Top 3最高频钩子）
  └── 内容模式归纳（对比各品牌的内容策略差异）

区块05: 投流vs自然流量分析
  ├── 投流/自然分布统计
  ├── 投流视频 vs 自然视频的平均表现对比（播放/GMV/互动率）
  ├── 各品牌的投流策略差异
  └── ROAS效率分析

区块06: 价格策略分析
  ├── 各品牌产品价格对比
  ├── 价格与GMV/互动率的相关性
  ├── 佣金率对比
  └── 定价建议

区块07: 核心发现（5-8条关键洞察）
  ├── 数据驱动的核心发现（每条含数据支撑）
  ├── 品牌层面发现
  ├── 内容层面发现
  └── 投放层面发现

区块08: 战略建议（三级优先级）
  ├── 🔴 立即行动（基于竞品共性的可复制策略）
  ├── 🟡 短期优化（需评估后推进的改进）
  └── 🟢 长期布局（品牌/产品层面的战略方向）

区块09: 结论
  ├── 核心结论（3段: 竞品为什么能爆 / 我方差距在哪 / 怎么追上）
  └── 数据来源注脚（标注 product_investment 产品级数据 vs 视频级数据）
```

---

#### ★ 全模式强制字段清单（同商品模式 + 跨品牌模式均适用）

> ⚠️ **以下字段在任何模式的大盘总览表格中都必须出现，不允许省略。**
> 缺少任何一项视为报告不合格，必须补齐后再输出。
>
> ⚠️ **本表只规定「哪些指标必须有」，不规定摆放方向。**
> - **同商品模式**：表格**转置** —— 下表的指标是**行**，列是达人（#1…#10 + 我方 + 均值 + 最优 + 差距）。
>   `#序号` 写在列头、`@达人` 放对照条，两者都**不是指标行**，故不在下表中。
> - **跨品牌模式**：常规布局 —— 下表的指标是**列**，达人是行，此时才需要 `#` 和 `达人` 两列。

| 指标 | 同商品模式 | 跨品牌模式 | 数据来源 |
|------|-----------|-----------|---------|
| #（序号） | 列头，非指标行 | ✅ 作为列 | 按GMV排序 |
| 达人 | 对照条，非指标行 | ✅ 作为列 | product_video_list → creator_handle |
| 品牌·商品 | ❌（用"关联商品·店铺"） | ✅ | product_detail_info |
| 关联商品·店铺 | ✅ | ❌（用"品牌·商品"） | product_detail_info |
| 发布时间 | ✅ | ✅ | video_detail_analysis → published_at_ts（Unix时间戳，转ET=UTC-4，精确到秒，格式 MM-DD HH:MM:SS ET） |
| 时长 | ✅ | ✅ | product_video_list |
| 播放量 | ✅ | ✅ | product_video_list |
| 点赞数 | ✅ | ✅ | video_detail_analysis |
| 评论数 | ✅ | ✅ | video_detail_analysis |
| 分享数 | ✅ | ✅ | video_detail_analysis |
| 互动率 | ✅ | ✅ | video_detail_analysis |
| IPM | ✅ | ✅ | video_detail_analysis |
| 销售额(28d) | ✅ | ✅ | product_video_list |
| 销售额(近7天) | ✅ | ✅ | 同商品: ad_data_overview / 跨品牌: product_investment |
| 广告消耗(近7天) | ✅ | ✅ | 同商品: ad_data_overview / 跨品牌: product_investment |
| ROAS(近7天) | ✅ | ✅ | 同商品: ad_data_overview / 跨品牌: product_investment |
| 爆发倍数 | ✅ | ✅ | video_detail + creator_profile |
| 病毒评分 | ✅ | ✅ | **人工评分**（5维×20=100分），报告中必须标注为人工评分 |
| 投流 | ✅ | ✅ | product_video_list |
| 产品出镜时机 | ✅ | ✅ | 人工拆解 |
| 话题数量 | ✅ | ✅ | 人工拆解 |
| 有效产品秒数 | ✅ | ✅ | 人工拆解 |
| 粉丝数 | ✅ | ✅ | video_detail_analysis → creator.follower_count |
| 达人均播 | ✅ | ✅ | creator_profile_overview → avg_video_play_count |
| 互动深度比 | ✅ | ✅ | 计算: (赞+评+藏+转) ÷ 播放 |
| 评论/播放比 | ✅ | ✅ | 计算 |
| 收藏/播放比 | ✅ | ✅ | 计算 |
| 推测完播 | ✅ | ✅ | 推断（由上三项定级） |
| 佣金率 | ✅ | ✅ | **FastMoss自动** product_detail_info → commission_rate；同商品=colspan |
| 话题标签数量 | ✅ | ✅ | video_script_info caption 解析 #xxx；无caption则手动或标"—" |
| 音乐策略 | ✅ | ✅ | **人工拆解**（听视频）原创/热门音效/纯BGM；无法看则标"—" |
| 封面帧类型 | ✅ | ✅ | v3-video-scanner 开场帧（人物特写/产品/文字冲击/动作瞬间） |
| **竞品均值** | ✅ | ✅ | 10条竞品算术平均（聚合列） |
| **竞品最优** | ✅ | ✅ | 10条竞品最佳值（聚合列） |
| **我方差距** | ✅ | ✅ | (我方 − 均值) ÷ 均值（聚合列） |

---

#### ★ 排版规范（字号 / 间距 / 宽度）

> ⚠️ 报告是给人长时间阅读的中文文档，**中文在同等字号下比英文更难读**。
> 以下为最低标准，生成HTML时不得低于这些值。

| 元素 | 字号 | 行高 | 说明 |
|------|------|------|------|
| body 正文 | **15px** | 1.75 | 全局基准，不要用14px |
| `.text-sm` 段落 | **14px** | 1.8 | 卡片内说明文字 |
| `.text-xs` 注释 | **12.5px** | 1.7 | 脚注、数据来源说明 |
| 普通表格 | **13.5px** | — | 单元格padding `12px 14px` |
| 转置矩阵表 | 见模板 | — | **不要手写，直接用模板的 `.matrix` 规则** |
| 脚本时间线条目 | **14px** | 1.75 | 条目间距 `margin-bottom:16px` |
| 时间戳 / 段落标签 | **12–12.5px** | — | 次级标签，可略小 |
| 评分条标签 | **13px** | — | 宽度≥68px防截断 |
| 徽章 / 优先级标签 | **11–12px** | — | 最小允许值，不可再小 |

**禁止**：正文出现 11px 及以下；表格单元格 padding 小于 `10px 10px`。

#### ★ 宽表格必须突破容器宽度

body 容器为 `max-width:1200px`，而转置矩阵表有15列，硬塞进1200px会导致每列仅约70px、
字号被迫降到9–12px，正是「太小且挤在一起」的根因。

解决方案：给该表的 `.table-wrap` 追加 `.wide-wrap` 类，让它居中撑开到整页宽：

该规则**已写在模板的 `<style>` 里**（`.wide-wrap` / `.matrix`），直接用即可。
⚠️ 不要在这里抄一份CSS数值 —— 抄了就会和模板对不上。以模板为准。

效果：1440px屏上表格宽1384px、每列约92px、无需横向滚动；
窄屏时自动收缩到容器宽度，表格在自己的容器内横向滚动，页面本身不产生横向滚动条。

> ⚠️ 只对大盘矩阵表用 `.wide-wrap`。正文段落、卡片、建议列表必须留在1200px内，
> 否则单行字数过多反而难读。

#### ★ 达人列头的两个坑

1. **`th` 全局样式带 `text-transform:uppercase`** → 会把 `@handle` 变成全大写。
   必须在 `.matrix thead th` 和 `.matrix .rowlab` 上写 `text-transform:none;letter-spacing:0`。
2. **不要用 `word-break:break-all`** → 会在任意字符处断行，`@katieeeemancebo` 被切成
   `@katieeeem / ancebo` 非常难看。用 `overflow-wrap:anywhere` + `max-width:98px`，
   长handle换成两行是可接受的（列宽物理上装不下19字符）。

#### 颜色主题规范

```
我们的视频: 绿色系
  --our: #059669 / 背景: #D1FAE5 / 中值: #6EE7B7

竞品视频: 紫色系
  --comp: #7C3AED / 背景: #EDE9FE / 中值: #C4B5FD

状态颜色（统一）:
  通过✓: 绿色 #3EA876
  警告⚠️: 琥珀色 #C98A1A
  失败✗: 红色 #D94444
  
对比矩阵:
  我们胜: 绿底绿字
  竞品胜: 紫底紫字
  平局: 琥珀底琥珀字
```

#### 差距对比维度（已并入区块1转置表，不再单独成块）

> ⚠️ 旧版有独立的「12维差距矩阵」区块，其中8维与大盘表重复，**已废弃**。
> 现在差距对比 = 区块1转置表右侧的三列（竞品均值 / 竞品最优 / 我方差距），
> 每一个指标行自动获得差距对比，无需再列一张表。

必须能读出差距的维度（对应区块1的行）：

```
① 流量与互动  播放量 / 点赞数 / 评论数 / 分享数 / 互动率 / IPM / 爆发倍数
② 商业转化    销售额(28d) / 销售额(近7天) / 广告消耗 / ROAS / 佣金率
③ 基础信息    时长 / 是否投流 / 发布时间
④ 内容评分    病毒评分 / 产品出镜时机 / 话题数量 / 有效产品秒数
⑤ 达人层      粉丝数 / 达人均播（区块1「达人账号」分区）
⑥ 观看深度    互动深度比 / 评论·播放比 / 收藏·播放比 / 推测完播（区块1「观看深度」分区）
⑦ 元数据层    话题标签数量 / 音乐策略 / 封面帧类型（仅对有帧/有音频的视频填写）
```

> 收藏率、佣金率、商品在架状态、受众语言等维度如有数据，
> 若是「一行一条视频」的指标就加为区块1的新行；否则写进区块3我方拆解。
> **任何情况下都不要为它们新开一张对比表。**

#### 归因诊断情况分类

> ⚠️ 这是**分析框架，不是报告区块**。报告中已取消独立的「归因诊断」板块，本框架的结论写进区块3核心诊断、区块4行动方案和结论段。

```
情况A: 同一商品，不同内容/达人
→ 商品需求一样，根因在内容/钩子/时机
→ 重点看：钩子类型、时长、发布时机、互动率

情况B: 不同商品，相似内容类型
→ 先比商品需求（爆款指数 / 竞争达人数 / 佣金率）
→ 根因可能是选品，而不是内容
→ 明确列出：钩子力差距 + 语言市场差距 + 佣金激励差距

情况C: 商品不同 + 内容风格也不同
→ 多变量问题，按影响权重排序：
   ① 商品热度差距（爆款指数）
   ② 钩子类型差距（最高权重内容变量）
   ③ 时机差距（季节/节日）
   ④ 时长/格式差距
```

---

## Step 0-A: FastMoss 发现模式（无URL时执行）

触发词：`找爆款 [品类]` / `发现 [品类] 爆款` / `拆解最爆 [品类] 视频` / 无URL时自动进入

---

### ★ 竞品视频选品标准

> ⚠️ **这是选择竞品视频的核心标准，每次搜索竞品都必须应用**。
> 不需要用户指定，这是默认的竞品搜索标准。
> 同商品模式和跨品牌模式使用不同的门槛参数（见下方两套标准）。

#### 标准A: 同商品对比模式 — 5个硬门槛（默认）

> **第一步必须限定近7天视频**，然后依次过滤。

#### 5个硬门槛（必须全部满足）

| # | 维度 | 门槛 | FastMoss工具/参数 | 说明 |
|---|------|------|------------------|------|
| 1 | 发布时间 | **近7天内** | `product_video_list(time_range_days: 7)` | 第一步过滤，只看近7天发布的视频 |
| 2 | 同行业视频平均观看时长 | ≥ 10秒 | `duration_seconds ≥ 10`（代理指标） | FastMoss无法获取真实观看时长，用视频时长≥10s替代 |
| 3 | 视频播放量 | ≥ 10万 | `play_count ≥ 100000` | 过滤低曝光视频 |
| 4 | 视频近7天销售额 | ≥ $1,000 | `window_gmv ≥ 1000`（7天窗口） | 过滤无商业转化视频 |
| 5 | ROAS | ≥ 2 | `ad_data_overview → summary.ad_performance.roas ≥ 2` | **FastMoss提供真实ROAS**，通过 `ad_data_overview` 获取 |

#### ROAS获取方法（重要）

```
工具: mcp__FastMoss-MCP__ad_data_overview
输入: {"filter": {"video_id": "<video_id>", "time_range_days": 7}}
输出:
  summary.ad_performance.estimated_ad_spend → 广告花费（美元）
  summary.ad_performance.roas → 真实ROAS（GMV÷广告花费）
  summary.commerce.ad_attributed_gmv → 广告归因GMV

⚠️ 自然流量视频(is_ad=false)无广告数据，ad_spend=0，ROAS=∞
⚠️ ROAS是真实数据，不是估算！此前"用佣金率估算"的方法已废弃
```

#### 其他默认条件

| 维度 | 要求 | FastMoss参数 | 备注 |
|------|------|-------------|------|
| 类目 | Beauty优先 | `category_id` | 优先搜Beauty，无结果再放开 |
| 返回数量 | Top 10 | `pagesize: 10` | 固定前10条 |
| 排序 | GMV降序 | `orderby: gmv desc` | 按带货金额排序 |

#### 选品执行流程

```
Step 1: product_video_list(product_id, time_range_days=7, orderby=gmv desc)
        → 获取近7天所有关联视频（可能需要翻页，每页10条）

Step 2: 过滤 duration_seconds ≥ 10 AND play_count ≥ 100000 AND window_gmv ≥ 1000

Step 3: 对通过过滤的视频，逐条调用 ad_data_overview(video_id, time_range_days=7)
        → 获取真实ROAS，过滤 ROAS ≥ 2（自然流量视频自动通过）

Step 4: 取Top 10（按GMV排序）

⚠️ 降级策略：近7天不足10条达标视频时：
   1. 先放宽至14天 → 仍不足则28天
   2. 报告中注明实际使用的时间窗口
   3. 近7天GMV列对超出7天窗口的视频标注"—"
```

> ⚠️ **数据说明**：
> - FastMoss不提供"平均观看时长"，用视频时长≥10s作为代理指标
> - **ROAS来自FastMoss `ad_data_overview`**，是真实广告花费和归因GMV的比值，不是估算
> - 近7天GMV来自 `product_video_list(time_range_days=7)` 的 `window_gmv`
> - 广告花费来自 `ad_data_overview` 的 `estimated_ad_spend`

---

#### 标准B: 跨品牌对比模式 — 放宽门槛

> 跨品牌模式搜索**外观类似、使用场景属性一致但品牌不同**的竞品。
> 因为跨品牌候选池更广，门槛适当放宽以确保足够的对比样本。

| # | 维度 | 门槛 | FastMoss工具/参数 | 说明 |
|---|------|------|------------------|------|
| 1 | 发布时间 | **近28天内** | `product_video_list(time_range_days: 28)` | 扩大时间窗口，确保跨品牌样本充足 |
| 2 | 视频时长 | ≥ 10秒 | `duration_seconds ≥ 10` | 同标准A |
| 3 | 视频播放量 | ≥ 3万 | `play_count ≥ 30000` | 放宽至3万（跨品牌候选池更分散） |
| 4 | 视频28天销售额 | ≥ $500 | `window_gmv ≥ 500`（28天窗口） | 放宽至$500（不同品牌GMV差异大） |
| 5 | ROAS | 不做硬门槛 | — | 跨品牌模式以品牌覆盖多样性为优先 |

#### 跨品牌选品执行流程

```
Step 1: 确定目标品类（如: nail glue / press-on nails）
        → 搜索该品类下的Top畅销商品: product_rank_top_selling / product_search

Step 2: 筛选不同品牌的商品（至少5个品牌），排除我方品牌
        → 每个品牌选取1-2个代表商品

Step 3: 对每个竞品商品调用 product_video_list(product_id, time_range_days=28)
        → 过滤: duration_seconds ≥ 10 AND play_count ≥ 30000 AND window_gmv ≥ 500

Step 4: 每个品牌选取GMV最高的1-2条视频，凑齐约10条竞品视频

Step 5: 对每条视频调用 video_detail_analysis 获取完整互动数据+发布时间

Step 6: 对每个产品调用 product_investment(product_id) 获取7天产品级投放数据
        → 输出: ad_performance_summary.estimated_ad_spend, roas, product_total_gmv

⚠️ 品牌多样性优先: 宁可少选1条高GMV视频，也要保证品牌覆盖面
⚠️ product_investment 返回的是产品级7天数据，同一产品的多条视频共享相同数据
⚠️ 7天数据在报告表格中使用 † 标注，脚注说明数据粒度
```

#### product_investment 工具使用方法

```
工具: mcp__FastMoss-MCP__product_investment
输入: {"product_id": "<product_id>"}
输出:
  ad_performance_summary.estimated_ad_spend → 近7天广告消耗（美元）
  ad_performance_summary.roas → 近7天ROAS
  ad_performance_summary.ad_gmv → 近7天广告归因GMV
  ad_performance_summary.product_total_gmv → 近7天产品总GMV

⚠️ 这是产品级数据，不是视频级！同一产品的所有视频共享相同的7天投放数据
⚠️ 报告中必须用 † 标注产品级数据列，并在脚注说明
```

---

### 执行步骤

**1. 解析意图 + 筛选条件**

先应用近7天默认标准，再叠加用户额外指定的条件：

| 用户说的 | 映射参数 |
|---------|---------|
| 粉丝X万以上/以下 | `followers_min` / `followers_max` |
| 点赞X万以上/以下 | `likes_min` / `likes_max` |
| GMV $X以上/以下 | 覆盖默认 `gmv_min` |
| 互动率X%以上 | `interaction_rate_min` |
| 不投流 / 自然流量 | `is_ad: false` |
| 只看投流 | `is_ad: true` |
| 最近X天 | 覆盖默认7天 |

**2. 双路并行发现**

```
路线A: mcp__FastMoss-MCP__video_search
  keyword, country, sort_by: "gmv", + 用户筛选条件

路线B（路线A结果少于3条时）:
  product_rank_top_selling → product_video_list → 手动过滤
```

**3. 展示Top 10并全部进入分析**

```
🔍 近7天竞品 Top 10 — [品类] · Beauty类目优先
筛选标准: 近7天 · 播放≥10万 · GMV≥$1,000 · 时长≥10s · 按GMV排序

#1  @creator   播放 X万  GMV $X,XXX  互动率X%  时长Xs  [✓自然/⚠️投流]
#2  @creator   播放 X万  GMV $X,XXX  互动率X%  时长Xs  [✓自然/⚠️投流]
...（共10条）

→ 10条全部进入拆解分析，不做单条筛选
```

**4. 对10条视频并行采集全量数据，同时采集10个达人账号数据（Step 0-D）**，然后进入分析阶段。

---

## Step 0-B: FastMoss 全量商业数据采集（5路并行）

```
工具1: video_detail_analysis {video_id}
  → 播放/点赞/评论/分享/收藏 + 互动率 + 互动强度 + 带货金额 + 佣金率
  → is_ad + 达人uid/粉丝数/均播/均赞 + 关联商品ID

工具2: video_script_info {video_id}
  → 视频字幕/脚本（时间轴文本）
  → 无字幕时标注"无字幕，依赖画面分析"

工具3: video_data_trends {video_id}
  → 按天播放/点赞/评论/分享增长曲线
  → 判断爆发节点、是否仍在增长窗口

工具4: product_detail_info {product_id}
  → 商品总GMV + 总件数 + 竞争达人数 + 爆款指数 + 评分

工具5: product_review_list {product_id, page:1, pagesize:10}
  → 买家真实评论（抓2页，~20条）
  → ⚠️ 商品评论，不是视频评论；更精准，噪音更少
```

**采集完成后流式输出**:
```
✓ Step 0-B FastMoss全量采集完成
· 视频: @XX · Xs · 播放X万/点赞X/评论X/分享X/收藏X · 互动率X%
· 带货金额: $X,XXX · 带货X件 · 互动强度=X · 是否投流: [⚠️投流/✓自然]
· 达人: X万粉 · 均播X万 → 爆发倍数预估=Xx
· 商品: [商品名] $XX · ⭐X.X(X条评) · 竞争达人X个 · 爆款指数=XX
· 字幕: [有X行脚本/无字幕] · 趋势: [X天起爆/持续增长/已衰退]
· 买家评论: 已获取X条（X月-X月）
```

---

## Step 0-D: 达人账号数据采集（每条竞品+我方视频必须执行）

确定分析哪些视频后，**对所有达人（10位竞品+我方）并行采集账号级数据**。

### 数据来源（3个工具组合，已验证可行）

```
工具1: video_detail_analysis {video_id}（Step 0-B已采集，复用）
  → creator.follower_count  → 粉丝数
  ⚠️ 只有这个工具返回粉丝数，creator_profile_overview不返回

工具2: creator_profile_overview {creator_uid}（新增调用）
  → avg_video_play_count    → 视频平均播放量（达人级均播）
  → interaction_rate_percent → 互动率（达人级）
  → like_comment_ipm        → 视频IPM（达人级互动强度）
  ⚠️ 分批并行调用（每批5个），所有11位达人都必须调用

工具3: product_video_list {product_id, sort_by:"gmv", pagesize:10}（Step 0-A已采集，复用）
  → 每条视频的 product_contribution.window_gmv → 近28天该商品归因GMV
  ⚠️ window_gmv是28天滚动GMV，精确到单个达人对该商品的贡献
  ⚠️ 不要用creator_cargo_summary的total_gmv（那是全品类累计GMV，不准确）
```

### 字段映射（5个必填字段，缺一不可）

| 字段 | 来源工具 | 字段路径 | 说明 |
|------|---------|---------|------|
| 粉丝数 | `video_detail_analysis` | `creator.follower_count` | 唯一来源 |
| 视频平均播放量 | `creator_profile_overview` | `avg_video_play_count` | 达人级均播，也用于爆发倍数计算 |
| 互动率 | `creator_profile_overview` | `interaction_rate_percent` | 达人级互动率 |
| 视频IPM | `creator_profile_overview` | `like_comment_ipm` | 达人级IPM |
| 近28天带货视频GMV | `product_video_list` | `product_contribution.window_gmv` | 该达人对该特定商品的28天GMV |

### 输出格式（流式输出 + 并入报告区块1「达人账号」分区）

```
📊 达人账号数据 — @[handle]
┌──────────────────────────────────────────┐
│ 粉丝数：X万                              │
│ 视频平均播放量：X万                       │
│ 互动率：X%                               │
│ 视频IPM：X                               │
│ 近28天Curvlife GMV：$X,XXX               │
└──────────────────────────────────────────┘
```

### 报告中展示

作为区块1转置表的「达人账号」分区（粉丝数 / 达人均播两行），我方列绿色高亮。
不要单独建「达人账号数据」区块。

---

## Step 0-E: 互动深度分析（替代无法获取的人均观看时长）

**FastMoss不提供per-viewer平均观看时长**，因此用以下4个代理指标推测"观众看得多深"：

### 代理指标定义

| 指标 | 公式 | 含义 |
|------|------|------|
| 互动深度比 | (点赞+评论+收藏+分享) ÷ 播放量 | 越高=看得越深才会互动 |
| 评论/播放比 | 评论 ÷ 播放量 | 评论需要看完或看够久才留 |
| 收藏/播放比 | 收藏 ÷ 播放量 | 收藏=觉得值得再看=看得够多 |
| 视频IPM | FastMoss直接提供 | 每千次播放的点赞+评论数 |

### 推测完播等级

| 互动深度比 | 评论/播放比 | 推测完播 |
|-----------|-----------|---------|
| ≥3% | ≥0.05% | 高完播 |
| 1-3% | 0.02-0.05% | 中完播 |
| <1% | <0.02% | 低完播 |

### 数据来源

所有数据从 `video_detail_analysis` 获取（Step 0-B已采集，直接复用）：
- plays, likes, comments, shares, saves → 计算互动深度比/评论播放比/收藏播放比
- like_comment_ipm → 视频IPM

### 报告中展示

作为区块1转置表的「观看深度（代理指标 · FastMoss 不提供人均观看时长）」分区，
共4行：互动深度比 / 评论·播放比 / 收藏·播放比 / 推测完播。
不要单独建「互动深度分析」区块。

「推测完播」是文字等级（高 / 中 / 中低 / 低 / 极低），该行需允许换行（其余行 nowrap）。
公式说明和核心洞察不写进表格，写进表格下方的「观看深度解读」卡片。

---

## Step 0-C: 视频画面采集

```bash
yt-dlp --write-info-json -o "videoX/videoX.%(ext)s" "TIKTOK_URL"
python extract_frames.py videoX/videoX.mp4 videoX/frames/ --width 320 --max 10
```

降级路径（yt-dlp失败）：浏览器截帧，Step 1照常，标注"帧来源: 浏览器截图"

---

## Step 1: 视频深度扫描
**调用**: `v3-video-scanner`  
**输入**: composite.jpg + video_script_info字幕（有则结合字幕读帧）

**流式输出**:
```
✓ Step 1 视频扫描
· TL;DR: [1句话]
· 节奏: [快/慢/混合] · 时长[Xs] · [X]帧展示
· 钩子时效 [X/10] · 产品出镜 [X/10] · CTA [X/10] · 留存 [X/10] · 卖点 [X/10]
· 关键帧: [0s:功能] / [Xs:功能] / [Xs:功能]
· 音频/字幕: [摘要] — [设计意图]
```

**报告中展示**（模式A：竞品在区块02用统一紧凑卡片，我方在区块03完整展开）:
- **TL;DR总结**: 1句话
- **逐段时间线**: 时间戳 + 功能标签 + 字幕原文（斜体引用）+ ✅⚠️❌状态
- **电商5维诊断评分柱**: 钩子时效/产品出镜/CTA布局/留存机制/卖点传递，各/10，横向条形图

---

## Step 2: 爆款诊断
**调用**: `v2-hook-lift`  
**数据来源**: creator_profile_overview（avg_video_play_count，爆发倍数分母）+ video_data_trends（爆发时间线）

**爆发倍数计算**:
- 公式：`视频播放量 ÷ FastMoss达人均播 = 爆发倍数`
- 标注"来源: FastMoss实测"
- 分级：`<1×`=低于均值（红）/ `1-10×`=正常 / `10-100×`=强爆（绿）/ `>100×`=超级爆发（紫）

**流式输出**:
```
✓ Step 2 爆款诊断
· 爆发倍数 [FastMoss实测]: 播放[x]× / 点赞[x]×（最异常指标加粗）
· 带货金额: $X,XXX（占商品总销量X%）· 投流: [是⚠️/否✓] · 互动强度=[X]
· 爆发节点: 发布后第X天起飞，目前[增长中/平稳/衰退]
· 钩子类型: [主类型] (置信度[高/中])
· 互动模式: [信息型/内容型/流量型] — [核心驱动力1句]
```

**报告中展示**（模式A：竞品在区块02用统一紧凑卡片，我方在区块03完整展开）:
- **爆发倍数判定卡**: 大数字（红=差/绿=好/紫=超强）+ 均播来源注释
- **爆发倍数计算**: 播放量 ÷ 均播 = X× + 点赞量 ÷ 均赞 = X×
- **钩子类型分析**: 类型名 + 心理机制解读（1-2段）
- **互动模式分析**: 互动率 / 收藏率（收藏÷播放）/ 分享率 / 互动强度 各自数值
- **播放趋势条形图**: 来自video_data_trends，每天一条，含日期/数值/峰值🔥/起飞🚀标注

---

## Step 3: 脚本结构拆解
**调用**: `v2-script-mapper`  
**数据来源**: video_script_info字幕

**流式输出**:
```
✓ Step 3 脚本拆解
· 病毒评分: [X]/100（钩子[x] 收藏[x] 分享[x] 完播[x] 评论[x]）
· 5段状态: Hook✅ Problem❌ Solution⚠️ Proof❌ CTA❌
· 硬规则: [X]/6通过
· 最大问题: [最重要缺失段落+1句影响]
· 首要修复: [最高优先修复建议，含改前→改后话术]
```

**报告中展示**（模式A：竞品在区块02用统一紧凑卡片，我方在区块03完整展开）:
- **病毒传播评分**（人工评分）: 5维各20分（每维只选 20/15/10/5），总分100
  - 逐维对照根 SKILL.md 锚点定义打分，1句评价说明选了哪档、为什么
  - 钩子力（停留）/ 收藏驱动（收藏）/ 分享驱动（分享）/ 完播引导（看完）/ 评论激活（评论）
- **5段结构**: Hook/Problem/Solution/Proof/CTA，含时间戳 + 字幕原文 + ✅⚠️❌
- **硬规则检查**: 6条规则，✓绿/✗红，含规则描述
  - 0-3秒出现核心卖点信号
  - 核心关键词在10秒内出现
  - 有明确CTA行动引导
  - 视频时长≤30秒（或≤60秒，视品类）
  - Problem显性化（有痛点或FOMO）
  - 产品差异化细节展示
- **修复建议**: 优先级R🚨/A⚠️/G💡，含改前→改后具体话术

---

## Step 4: 买家洞察
**调用**: `v3-comment-insight`  
**数据来源**: product_review_list（买家评论）

**流式输出**:
```
✓ Step 4 买家洞察（X条商品评论）
· 好评率: X% · 差评集中: [主要问题]
· 购买驱动: [高频正向词3个] — "[最典型好评原话]"
· 核心疑虑: [高频负面词2个] — [影响复购的风险]
· 爆发期印证: 视频起爆期X月，评论量[激增/平稳]
· 视频未说的: [买家反馈揭示但视频中没展示的卖点/问题]
```

**报告中展示**（含评论时展示分布图，无评论时推断）:
- 评论情感分布横向条形图（购买驱动/香味/质量/疑虑等分类）
- 买家驱动分析文字（正向/负向/购买动机推断）
- ⚠️ 若product_review_list返回空：说明原因（商品较新/未建索引），基于同类产品评论模式推断洞察

---

## Step 5: 复制公式引擎
**调用**: `v2-trend-content`  
**数据来源**: product_detail_info（爆款指数/竞争达人数）+ video_data_trends（窗口判断）

**流式输出**:
```
✓ Step 5 复制公式
· 判定: [RIDE/BEND/BEND HARD/SKIP] — [1句理由]
· 竞争态势: 同款达人[X]个在推 · 爆款指数=[XX]/100 · 窗口=[开放/收窄/饱和]
· 关键角色发现: [最重要角色诊断]
· AI痕迹: ✓无 / ✗有[说明]
· Top优化建议: [最高优先级1条，含改前→改后]
```

**报告中展示**（模式A：竞品在区块02用统一紧凑卡片，我方在区块03完整展开）:
- **判定卡**: BEND HARD/RIDE等 + 判定理由
- **生命周期分析**: 内容层/商品层/竞争层各自状态
- **达人角色诊断**: 当前角色类型 + 适配性 + 建议
- **可复用框架**: FW-XX格式，含
  - 框架名称（中文）
  - 钩子话术（具体语言版本）
  - 分段脚本结构（0s/5s/10s格式）
  - 最强驱动力
- **可复用/不可直接复制**: 两栏对比

---

## 单视频HTML报告：JSON注入格式

单视频模式**只生成数据JSON，不写HTML/CSS**，注入到模板。

**爆发倍数计算**：`lift.plays_mult = round(video_plays / creator_profile.avg_plays)`

```json
{
  "meta": {
    "creator": "达人昵称",
    "handle": "@handle",
    "title": "视频标题",
    "date": "YYYY-MM-DD",
    "duration_s": 100,
    "url": "https://www.tiktok.com/@handle/video/VIDEO_ID",
    "is_ad": false,
    "data_source": "FastMoss 5路采集 + 本地帧采集"
  },
  "stats": {
    "views": 14700000, "likes": 165400, "comments": 831,
    "shares": 10500, "saves": 48319
  },
  "fastmoss_data": {
    "video_commercial": {
      "gmv": 174189.7, "units_sold": 8873, "ipm": 20,
      "interaction_rate_pct": 2.12, "is_ad": true, "commission_rate_pct": 12
    },
    "creator_profile": {
      "followers": 37014, "avg_plays": 79372, "avg_likes": 1665
    },
    "lift": { "plays_mult": 243, "likes_mult": 228 },
    "product": {
      "name": "商品名称", "viral_index": 100, "linked_creator_count": 11719,
      "total_gmv": 5072939, "rating": 4.5, "review_count": 30174
    },
    "trend": { "viral_day": null, "current_status": "持续高销量" }
  },
  "step1": {
    "tldr": "1句话总结",
    "frames": [{"ts": "0s", "desc": "【钩子】画面+字幕描述"}],
    "scores": {"hook": 9, "product": 10, "cta": 6, "retain": 8, "selling": 9}
  },
  "step2": {
    "hook_type": "钩子类型", "hook_desc": "含爆发节点说明", "hook_conf": "高",
    "lift": [{"metric": "播放量", "actual": "1470万", "avg": "11.3万(FastMoss均值)", "mult": 130}],
    "save_share_note": "收藏率X% / 分享率X% / 爆发节点第X天"
  },
  "step3": {
    "segments": [{"name": "Hook", "ts": "0–2s", "status": "pass", "content": "字幕原文+画面"}],
    "virus": {"hook": 18, "save": 19, "share": 10, "watch": 16, "comment": 8},
    "rules": [{"text": "规则描述", "pass": true}],
    "fixes": [{"priority": "R", "title": "标题", "detail": "改前→改后"}]
  },
  "step4": {
    "rates": [{"label": "好评率", "val": "X%"}],
    "mode_title": "买家反馈模式", "mode_detail": "洞察分析"
  },
  "step5": {
    "dist": [{"emoji": "👍", "label": "好评-香味", "count": 9, "pct": 45, "color": "#3EA876"}],
    "top3": [{"user": "买家ID", "date": "YYYY-MM-DD", "text": "评论原文"}],
    "signals": [{"type": "信号类型", "content": "分析"}]
  },
  "step6": {
    "verdict": "X× 强爆（自然流量）", "verdict_reason": "判定理由",
    "roles": [{"icon": "📊", "name": "角色名", "diag": "诊断"}],
    "frameworks": [{"num": "FW-01", "name": "框架名", "hook": "钩子话术", "segs": "分段", "strongest": "最强驱动"}],
    "reuse": {"can": ["可复用元素"], "cannot": ["不可直接复制"]}
  },
  "conclusion": {
    "why": "爆款原因（内容层+商业层，数据支撑）",
    "how": "复制方法（结合买家反馈）"
  }
}
```

注入命令：
```bash
python inject_report.py videoX/report_data.json .claude/skills/v3-report-template/template.html videoX/report_videoX.html
```

---

## FastMoss MCP 工具清单

| 工具 | 步骤 | 用途 | 关键输出字段 |
|------|------|------|-------------|
| `video_search` | Step 0-A | 按GMV/关键词发现爆款视频 | video_id, play_count, gmv |
| `product_rank_top_selling` | Step 0-A | 发现畅销商品 | product_id, total_gmv |
| `product_video_list` | Step 0-A/0-D/选品 | 商品关联视频 + 7天/28天window_gmv | creator_handle, play_count, window_gmv, duration_seconds, is_ad |
| `video_detail_analysis` | Step 0-B/0-D | 互动指标+带货金额+**达人粉丝数**+商品ID | interaction_rate_percent, creator.follower_count, product_id |
| `video_script_info` | Step 0-B | 视频字幕/脚本文本 | script_segments(时间轴文本) |
| `video_data_trends` | Step 0-B | 播放趋势曲线+爆发节点 | daily_trend(按天播放/点赞) |
| `product_detail_info` | Step 0-B | 商品详情+竞争达人数+爆款指数 | viral_index, linked_creator_count, rating |
| `product_review_list` | Step 0-B | 买家评论（替代TikTok评论抓取） | review_text, star_rating |
| `creator_profile_overview` | Step 0-D | **达人级均播/互动率/IPM**（粉丝数不在此工具） | avg_video_play_count, interaction_rate_percent, like_comment_ipm |
| `ad_data_overview` | **选品/区块1** | **视频级广告花费+真实ROAS+广告归因GMV** | estimated_ad_spend, roas, ad_attributed_gmv, daily_trend |
| `product_investment` | **跨品牌区块01** | **产品级7天广告消耗+ROAS+GMV** | ad_performance_summary.estimated_ad_spend, roas, ad_gmv, product_total_gmv |

> ⚠️ **`ad_data_overview` 是获取视频级ROAS的工具**（同商品对比模式使用）
> ⚠️ **`product_investment` 是获取产品级7天投放数据的工具**（跨品牌对比模式使用）
> 两个工具的区别：
> - `ad_data_overview`: 输入 video_id，返回单视频的广告数据（视频级归因）
> - `product_investment`: 输入 product_id，返回整个产品的7天广告汇总（产品级归因，同一产品的所有视频共享）
> 输入: `{"filter": {"video_id": "<id>", "time_range_days": 7}}`
> 输出: `summary.ad_performance.estimated_ad_spend`（广告花费）、`summary.ad_performance.roas`（真实ROAS）
> 自然流量视频(is_ad=false)返回空数据，ad_spend=0，ROAS=∞

## 本地工具（仅视频画面）

| 工具 | 用途 |
|------|------|
| `yt-dlp` | 下载视频文件（获取画面） |
| `extract_frames.py` | 帧提取，composite.jpg输出 |
| 浏览器截帧（降级） | yt-dlp失败时替代 |

## 降级策略

| 失败场景 | 处理方式 |
|---------|---------|
| 发现模式无结果 | 双路切换；两路均空则提示手动提供URL |
| video_detail_analysis 失败 | 跳过，用yt-dlp metadata + 行业估算爆发倍数 |
| video_script_info 空返回 | 标注"无字幕"，Step 3依赖画面推断 |
| video_data_trends 失败 | 跳过趋势图，不影响其他步骤 |
| product_review_list 失败/空 | Step 4标注原因 + 基于同类产品推断 |
| creator_profile_overview 失败 | 用 video_detail_analysis 的 creator.avg_video_play_count 降级；互动率/IPM用视频级数据估算 |
| yt-dlp 失败 | 浏览器截帧降级 |
| 对比模式：我方视频FastMoss无商业数据 | 标注"商业数据缺失，仅做内容层对比" |
| 对比模式：两视频差距极小 | 输出"差异不显著"，聚焦最大差距维度 |

---

## MD报告结构规范（第一步输出）

> ⚠️ MD-First原则: 先生成MD报告发送给用户确认，确认后再转HTML。
> MD报告包含完整区块，使用Markdown表格+`<details>`折叠。

### MD结构A: 同商品竞品对比模式

> ⚠️ **不要照下面的说明手搓 MD**，直接用现成模板：
> `.claude/skills/v3-report-template/template-same-product.md`
> 下面只是该模板的结构说明，供理解「为什么这样排」，不是填写入口。

```markdown
# [商品名] 竞品对比报告
> @[我方达人] vs Top 10 竞品达人 · [日期]

## 区块1: 竞品大盘总览
- 关键指标卡: 竞品总播放/总GMV/头部差距/平均时长
- **达人对照条**: `#1 @handle` … `#10 @handle` `我方 @handle`，每项链接到TikTok视频
- **转置矩阵表**（MD表格）: 第一列=指标名，其后依次为 #1…#10 / 我方 / 竞品均值 / 竞品最优 / 我方差距
  行必须包含（按7分区排列，共28行）:
    ① 基础信息    关联商品·店铺 / 发布时间 / 时长 / 投流
    ② 达人账号    粉丝数 / 达人均播
    ③ 流量与互动  播放量 / 点赞数 / 评论数 / 分享数 / 互动率 / IPM / 爆发倍数
    ④ 观看深度    互动深度比 / 评论·播放比 / 收藏·播放比 / 推测完播
    ⑤ 商业转化    销售额(28d) / 销售额(近7天) / 广告消耗(近7天) / ROAS(近7天) / 佣金率
    ⑥ 内容评分    病毒评分 / 产品出镜时机 / 话题数量 / 有效产品秒数
    ⑦ 元数据层    话题标签数量 / 音乐策略 / 封面帧类型
  ⚠️ 表头列只写 `#1`…`#10`/`我方`，@handle 一律放对照条，不进列头
  ⚠️ 同商品模式下「关联商品·店铺」所有列相同 → 单独写一行，值只写一次
  ⚠️ 达人IPM 与视频IPM 数值相同，只保留一行
- 两张解读卡片（固定2张，不要加第三张）:
  ① 关键发现：粉丝效率倒挂 —— 只讲横向对比，末尾指向区块3，**不写结构问题细节**
  ② 观看深度解读 —— 为什么用代理指标 + 三个公式 + 核心洞察
- 大盘规律 bullet points

## 区块2: 竞品逐条拆解
每条竞品用 `<details>` 折叠：
- 摘要行: #序号 @达人 · 播放 · GMV · 时长 · 投流标签
- 展开内容: 脚本时间线 + 5维病毒评分 + 核心驱动力

## 区块3: 我方视频拆解
- 数据面板 + 5维评分 + 脚本时间线 + 核心诊断
- RIDE/BEND/SKIP 判定卡并入本区块末尾

## 区块4: 行动方案
- 顶部图例: 立即可抄 / 评估后推进 / 不能直接抄
- 4.1脚本 / 4.2拍摄 / 4.3商家配合 / 4.4达人物料
- 每条建议格式: `[优先级] **要点** — 理由（附竞品证据）`
- 4.1 末尾附**两版中英双语成稿**，每个 beat 三行：
  ```
  [0-3s] Hook
    EN: "英文口播原话"
    CN: 中文含义（镜头/节奏说明）
  ```
- ⚠️ 本区块只给动作，不重新论证问题（问题在区块3已说清）

## 结论
- 3段总结: 为什么竞品能爆 / 为什么我方没爆 / 怎么复制
- 数据来源注脚
```

> ⚠️ **区块顺序的理由**：读者看完竞品拆解（区块2）后，注意力最集中的时刻应该立刻看到「我方差在哪 → 该怎么做」，所以我方拆解和行动方案紧跟其后，报告以行动方案收尾。
> ⚠️ **不再有独立的「归因诊断」区块**：其结论已分散到区块3的核心诊断、区块4和结论段，单开一块会与前面内容重复。
> ⚠️ **不再有独立的「差距矩阵」区块**：差距对比已并入区块1转置表右侧三列。
> ⚠️ **不再有独立的「行动清单」区块**：已与「方案建议」合并为区块4，优先级改为内联标签。
> ⚠️ **不再有独立的「达人账号数据 / 互动深度分析」区块**：两张子表的行与区块1的列一一对应，已并入转置表的「达人账号」「观看深度」两个分区。
>
> **判断某张表该不该并进区块1的通用规则**：若该表**每一行恰好对应一条视频（或一位达人）**，
> 它就是区块1的一个分区，必须并进去；只有当表格的行是另一种实体
> （如脚本段落、行动项、品牌）时，才允许单独成表。

### MD结构B: 跨品牌竞品对比模式

```markdown
# [品类名] 跨品牌竞品对比报告
> @[我方达人] · [我方品牌] vs [N]个竞品品牌 · [日期]

## 区块01: 跨品牌竞品大盘
- 关键指标卡: 品牌数/总播放/总GMV/平均互动率
- 完整汇总表（MD表格，全部强制字段列）
  必须包含: #/品牌·商品/达人/发布时间/时长/播放量/点赞数/评论数/分享数/互动率/IPM/销售额(28d)/销售额(近7天)†/广告消耗(近7天)†/ROAS(近7天)†/爆发倍数/病毒评分/投流
  † 产品级数据脚注
- 大盘规律 bullet points（含品牌分布、投流比例）

## 区块02: 品牌竞争矩阵
- 品牌汇总表: 品牌名/视频数/总播放/平均互动率/总GMV/7天广告消耗
- 品牌定位分析

## 区块03: 达人画像对比
- 子表A: 达人账号数据（粉丝/均播/互动率/IPM/28天GMV）
- 子表B: 互动深度分析（深度比/评论比/收藏比/IPM/完播等级）

## 区块04: 内容模式与时长分析
- 时长分布统计 + 各时长段表现
- 钩子类型分布 + 内容策略差异

## 区块05: 投流vs自然流量
- 投流/自然分布 + 表现对比
- 各品牌投流策略 + ROAS分析

## 区块06: 价格策略分析
- 各品牌价格对比 + 价格与GMV相关性
- 佣金率对比 + 定价建议

## 区块07: 核心发现
- 5-8条数据驱动的关键洞察
- 分层: 品牌层/内容层/投放层

## 区块08: 战略建议
- 🔴 立即行动 / 🟡 短期优化 / 🟢 长期布局

## 区块09: 结论
- 3段: 竞品为什么能爆 / 我方差距 / 追赶策略
- 数据来源注脚（标注产品级 vs 视频级数据）
```

> **通用规则**:
> 区块2/竞品卡片在MD中使用`<details>`标签折叠，确保报告可读性。
> MD表格中数字右对齐，中文左对齐。我方行用 **加粗** 标注。
> 生成MD后立即发送文件给用户，等用户确认或要求转HTML后再进入HTML生成阶段。
> **大盘表格的指标项必须与"全模式强制字段清单"一致，不允许省略任何一项。**
> 同商品模式（MD结构A）的大盘表为**转置**布局：指标作行、达人作列，右侧追加均值/最优/差距三列。
> 跨品牌模式（MD结构B）因需突出「品牌·商品」分组，仍保持达人作行的常规布局。

---

## ★★ 区块职责边界（防止内容重复）★★

> 同一个结论只能出现在一个地方。下表规定每个区块**只能讲什么**。
> 写完后自查：若某个数字或判断在两个区块都展开讲了，删掉职责之外的那处。

| 区块 | 只负责 | 禁止写 |
|------|--------|--------|
| **01 大盘总览** | **横向对比**：我方在11条里排第几、哪些指标领先/落后、为什么粉丝多却卖得少 | ❌ 不写我方的结构问题细节（第几秒出产品 / 几个话题 / 时长超长 / 有效秒数）——那是03的事 |
| **02 竞品拆解** | **竞品各自**的脚本结构和评分，最后一段共性小结 | ❌ 不写我方情况，不给建议 |
| **03 我方拆解** | **纵向深挖**：我方这条视频的时间线、结构缺陷、5段诊断、修复话术、RIDE/BEND判定 | ❌ 不重复01的排名和倍数对比 |
| **04 行动方案** | **要做什么**：分脚本/拍摄/商家/物料四节，每条带优先级标签 | ❌ 不重新论证问题（问题在03已说清），直接给动作 |
| **结论** | 三段收口，可以扼要复述前面的关键数字 | ❌ 不引入任何前面没出现过的新论据 |

**典型重复（真实踩过的坑）**：
区块01曾同时有「差距解读」和「粉丝效率倒挂」两张卡，
前者又把「88秒才出产品 / 4个话题 / 191秒超长 / 有效11秒」讲了一遍，
与区块03的核心诊断完全重复 → 现已合并为**一张**「关键发现：粉丝效率倒挂」卡，
只讲横向对比，末尾用一句「具体结构问题见区块03」做指向。

> **区块01 的解读卡固定为3张**：
> 1. **关键发现**（粉丝效率倒挂）——横向比较达人流量vs GMV差距
> 2. **观看深度解读**——代理指标说明+互动深度分析
> 3. **发布时段分析**——基于 `published_at_ts` 精确到秒，转换为ET（UTC-4），分析竞品发布时间集中在哪些区间，给出最优发布窗口建议
>
> 发布时段分析卡格式要求：
> - 标题行注明 `published_at_ts 精确到秒 · ET (UTC-4)`
> - 按4个时段展示分布：深夜异常档 / 午间档 / 傍晚档(4-6PM ET) / 黄金晚间(6-10PM ET)
> - 每个时段给出视频数 + 具体时间
> - 关键洞察bullet：① 最高峰时段 ② Top GMV视频时段相关性 ③ 异常值说明 ④ 我方建议精调区间

---

## ★★ 拍摄成稿必须中英双语 ★★

区块04 的 4.1 脚本成稿是**要交给达人直接开拍的东西**，美区视频的口播是英文，
所以英文才是可直接用的那一版，中文是给运营和达人理解用的。

每个 beat 三行：

```
[时间戳] [段落名 Hook/Problem/Solution/Demo+Proof/CTA]
EN: "达人实际出镜说的英文原话"        ← 主体，字号更大更醒目
CN: 中文含义（括号里补镜头/节奏的导演说明）
```

**要求**：
- EN 必须是**能直接念出来的完整口语句子**，不是关键词罗列，不是中式英语直译
- CN 括号里给拍摄提示（如「手部特写」「快切3个镜头」「这段不要剪」）
- 两版成稿分别对标**不同竞品的打法**（如痛点故事版 vs Demo冲击版），不要两版雷同
- 各 beat 时间戳加总 = 标注的目标时长

HTML 用模板里的 `.script` / `.beat` / `.bt` / `.bl` / `.en` / `.cn` / `.dir` 类。
MD 版本用三行缩进表达，不要压成一行。

---

## ★★ 交付前自检清单（每次生成报告后必须逐条核对）★★

> 下面任何一条不通过，都算报告不合格，必须修好再发给用户。

### A. 结构

- [ ] 结构恰好为：Hero → 01大盘 → 02竞品拆解 → 03我方拆解 → 04行动方案 → 结论（编号区块只有4个）
- [ ] 没有出现已废弃的独立区块：差距矩阵 / 归因诊断 / 行动清单 / 方案建议 / 达人账号数据 / 互动深度分析
- [ ] 区块01 的解读卡恰好3张（粉丝效率倒挂 + 观看深度解读 + 发布时段分析）
- [ ] 10条竞品卡片格式完全一致，没有把 #4–#10 降级成摘要行
- [ ] 按「区块职责边界」表逐区块检查，没有跨区块重复论证

### B. 大盘转置表

- [ ] 表格是**转置**的：指标作行、达人作列
- [ ] 列数 = 15（指标 + 10竞品 + 我方 + 均值 + 最优 + 差距），**逐行核对每行都是15格**
- [ ] 指标行 = 28 行，分 7 个分区，一个都不少
- [ ] 表头只有 `#1`…`#10` / `我方`，**没有 @handle**
- [ ] 达人对照条存在，11个chip，每个都能点开TikTok视频
- [ ] `.table-wrap` 带了 `wide-wrap` 类（否则会被压缩）
- [ ] 「推测完播」行带了 `wrapok` 类
- [ ] 我方列绿色高亮；差距列用 gap-b（绿）/ gap-w（红）/ gap-n（灰）区分

### C. 数据可信度

- [ ] 均值/最优/差距三列是**真算出来的**，不是沿用上一版报告的旧数字
- [ ] ROAS 均值只统计投流视频（自然流量的 ∞ 不参与平均）
- [ ] 人工评分（病毒评分 / 5维 / 产品出镜时机 / 话题数量 / 有效产品秒数）已标注非FastMoss数据
- [ ] 未做逐帧拆解的竞品，内容评分区填「—」而不是编造数字
- [ ] 元数据层：佣金率来自FastMoss（product_detail_info）；话题标签数量已从caption解析或手动数；音乐策略无法听视频时标「—」
- [ ] 「推测完播」写成「推测」，没有写成「完播率」
- [ ] 全报告的同一个数字处处一致（如竞品ROAS均值，不能这里4.33那里4.44）

### D. 成稿

- [ ] 两版成稿都是中英双语，EN 是完整可念的口语句子
- [ ] 两版对标不同竞品打法，不雷同
- [ ] 各 beat 时间戳加总 = 目标时长

### E. 排版

- [ ] 正文没有 11px 及以下的字号（徽章/优先级标签除外）
- [ ] 1440px 宽度下大盘表不横向滚动；400px 宽度下页面本身不横向滚动
- [ ] 无 `{{` 占位符残留
- [ ] HTML标签闭合平衡

> 自检方法建议：用脚本核对「每行15格」「标签闭合」「`{{` 残留」，比肉眼可靠。
