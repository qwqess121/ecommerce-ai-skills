# 模块三：Listing 诊断

> 本文件是给人看的目录说明，不是可调用的 skill。每个子目录下的 SKILL.md 才是实际工作流。
> 2026-09-16 重构：删除`sys-amazon-listing-optimization`（跟`amazon-listing-optimization`完全重复）和`amazon-enhanced-brand-content`（功能被`amazon-a-plus-content`完全覆盖）。9个skill精简为7个。

## 这个模块解决什么问题

把模块二挖出来的关键词、竞品缺口、评论痛点，转化成实际的 Listing 内容——标题、五点、后台关键词、图片、A+页面。新品是"从0搭建"，老品是"审计+改写"。这一步结束，要有一个能上架、能被搜到的完整 Listing。

---

## 详细清单（含数据获取与评判标准）

### amazon-listing-optimization — Listing创建与优化
**定位**：Mode A从0生成新Listing，Mode B审计+改写现有Listing。
**工作流**：
- Mode A：收集关键词（4个来源）→ 按搜索量分Primary/Secondary/Tertiary/Long-tail四层 → 收集产品特征 → 选文案语气 → 生成标题/五点/描述 → 关键词覆盖评分
- Mode B：抓取现有Listing数据 → 发现目标关键词 → 关键词缺口分析 → 8维度审计评分 → 生成优化文案（before/after对比）
**获取数据 / 用哪个MCP**：
- SIF `ops_get_listing_traffic_overview` → 拉当前流量数据（session/转化率/关键词来源）
- SIF `ops_get_listing_keyword_distribution` → 拉当前已覆盖的关键词和排名
- 卖家精灵 `keyword_research` → 拉候选关键词的真实搜索量
- Brightdata `scrape` → 抓竞品Listing全文做对比
**评判标准**：
- 关键词覆盖率 ≥90% 为优秀，70-89% 为良好，<70% 判定"需改进"，必须补词
- 8维度审计（标题/五点/图片/A+/描述/价格/评论/SEO覆盖）单项低于类目均分即标记为优先改进项
- 转化率低于类目平均且流量正常 → 判定为Listing内容问题，不是流量问题

### sys-amazon-listing-audit — Listing质量审计（MCP原生）
**定位**：全自动扫描一批ASIN，找结构性问题（不是内容优化建议，是"有没有硬伤"）。
**工作流**：健康检查（Critical/Warning/Info分级）→ RUFUS三问评分 → 劫持检测 → 合规检查 → 目录结构检查 → 搜索词安全检查 → 变更历史取证
**获取数据 / 用哪个MCP**：Marketplace Ad Pros MCP `audit_listings`（全自动，给ASIN列表即可，无需额外配置）
**评判标准**：
- Critical级问题（banned claims、劫持痕迹、product-type-mismatch）必须立刻处理，不允许拖延
- RUFUS三问（适不适合/有何不同/怎么用）任意一问在五点里找不到明确回答，即判定该问需要改写
- 后台搜索词出现与产品无关的品牌词/竞品词，直接判定为劫持风险

### sys-amazon-title-image-compliance — 标题/图片批量合规
**定位**：批处理工具，处理一批CSV数据里的标题清洗和图片重命名，不做单个ASIN的深度优化。
**工作流**：准备CSV源表 → （可选）导出规则模板 → 合规模式清洗标题 → 或改写模式重排标题结构 → 批量重命名图片 → 整理flat file
**获取数据 / 用哪个MCP**：纯脚本，需要用户提供products.csv；无MCP依赖
**评判标准**：
- 标题超过平台字符上限、含促销语（"免费""特价"）、重复关键词堆砌、全大写——任一条命中即判定"不合规"必须清洗
- 改写模式下标题必须符合[品牌]+[主关键词]+[属性]+[差异化]的固定结构，缺任一段落判定为不完整

### amazon-backend-keywords — 后台搜索词优化
**定位**：专门优化250字节后台关键词栏位，是Listing优化里最容易被忽略、但最高杠杆的一环。
**工作流**：关键词研究与分析（多数据源挖词）→ 策略优化与实施（250字节内去重排优先级）→ 性能监控与持续改进
**获取数据 / 用哪个MCP**：
- 卖家精灵 `keyword_miner`（批量挖词）、`keyword_research`（搜索量+竞争度）、`traffic_keyword`（竞品后台关键词策略）
- SIF `ops_get_listing_keyword_distribution`（当前已覆盖的词，用于去重）
**评判标准**：
- 250字节耗尽率低于90%判定为"未充分利用"，必须补词
- 与前台标题/五点重复的词判定为浪费字节，需替换成未覆盖的同义词/长尾词
- 竞品后台关键词里出现、自己完全没有的高搜索量词，直接判定为优先补充项

### amazon-search-optimization — 搜索排名优化/A9算法
**定位**：从A9算法四个因素的角度做系统性诊断，而不是零散的关键词优化。
**工作流**：SEO审计与A9算法分析 → 策略优化实施 → 性能监控与持续提升
**获取数据 / 用哪个MCP**：SIF `ops_get_listing_traffic_overview`（排名基线）、`market_get_keyword_competition`（关键词竞争度）；卖家精灵 `product_node`（类目节点校验）、`traffic_listing`（流量结构）
**评判标准**：
- A9四因素权重：相关性40% / 转化表现35% / 客户满意度20% / 权威度5%，任一维度显著低于竞品均值即为优先修复项
- 类目节点如果不是最精准的叶子节点，直接判定为需要修正（错误类目会拉低相关性得分）

### amazon-listing-images — 产品图片策略
**定位**：给出7张图的完整拍摄/生成规划，而不是零散的"P个图"。
**工作流**：视觉策略开发（客户画像+竞品视觉分析）→ 专业图片制作（7张图Shot List）→ 性能监控与持续优化
**获取数据 / 用哪个MCP**：Brightdata `scrape`（抓竞品主图做视觉对比）；Canva `generate-design`（生成图片初稿）
**评判标准**：
- 7张图必须依次覆盖：识别产品→理解卖点→验证规格→场景展示→消除顾虑→了解配件→建立信任，缺哪一步判定为该图必须补
- 竞品主图里普遍出现、自己没有的视觉元素（比如尺寸对比图、使用步骤图）判定为差异化机会

### amazon-a-plus-content — A+内容策略
**定位**：设计A+页面的7个模块架构，围绕客户决策旅程展开，不是简单堆卖点图。
**工作流**：策略规划与客户旅程分析 → 内容创建与模块开发（7模块）→ 优化与效果提升
**获取数据 / 用哪个MCP**：Brightdata `scrape`（抓竞品A+页面内容和图片）；Canva `generate-design`（生成模块设计）
**评判标准**：
- 7个模块（Hero Banner/问题-方案/特征-利益/社会证明/竞品对比图/生活场景/CTA）缺失超过2个，判定A+内容不完整
- 停留时间/滚动深度低于同类竞品，判定为内容吸引力不足，需要优化模块顺序或视觉

---

## 竞品对比与评分（新增，2026-09-20）

`amazon-listing-optimization` Mode B 已更新：Step B2的竞品来源必须先按 `../_references/竞品匹配与评分规则.md` 过滤（属性+形态+场景一致），Step B4的Pricing/Reviews两个维度改成"行业对标百分位排名"而不是绝对阈值。其余skill（backend-keywords/search-optimization/listing-images/a-plus-content）涉及竞品对比时同样先过滤再比较，不能拿泛泛的同类目产品。

## 内部串联逻辑

1. 先用 `amazon-backend-keywords` 或模块二的关键词研究确定关键词池
2. 用 `amazon-listing-optimization`（新品用Mode A，老品用Mode B）生成或改写标题/五点/描述
3. 同步用 `amazon-search-optimization` 检查是否踩中A9算法各项因素
4. 用 `amazon-listing-images` 规划主图和信息图，`amazon-a-plus-content` 规划A+页面（这两步需要模块五提供实际图片素材）
5. 全部改完，用 `sys-amazon-listing-audit` 做最终质量审计，确认没有合规/劫持/结构问题
6. 涉及大批量标题清洗或图片改名时，走 `sys-amazon-title-image-compliance` 批处理

## 评判标准速查表（针对 HoogaLife / ABAMERICA 品牌矩阵）

| 检查项 | 数据来源 | 判定阈值 |
|---|---|---|
| 关键词覆盖率 | SIF `ops_get_listing_keyword_distribution` | <70%必须补词，90%+免动 |
| Listing评分 | 卖家精灵 `asin_detail` | 低于类目平均评分（通常4.2左右，以实时数据为准）判定需优化 |
| 后台关键词利用率 | 卖家精灵 `keyword_miner` | 250字节耗尽率<90%需补词 |
| A9类目节点 | 卖家精灵 `product_node` | 非叶子节点判定需要修正 |
| A+完整度 | 内部检查 | 7模块缺失>2个判定不完整 |

## MCP 集成程度

`sys-amazon-listing-audit` 是全自动MCP原生技能，给ASIN列表直接出报告。`amazon-listing-optimization`/`amazon-backend-keywords`/`amazon-search-optimization` 已接入SIF流量数据和卖家精灵关键词工具，给ASIN就能自动拉数据。`amazon-listing-images`/`amazon-a-plus-content` 接了Brightdata和Canva，但仍需人工提供目标受众、品牌故事这类判断性输入。`sys-amazon-title-image-compliance` 需要你准备CSV文件，不是自动拉数据。
