# TikTok Shop Listing 诊断 + 竞品分析（v6.3）

## 这是什么

输入一个 TikTok Shop 产品链接/ID/关键词/店铺名，产出一份 **Listing 诊断 + 竞品分析** 报告（Markdown，发布为在线 Artifact）。

**完整规则见 [SKILL.md](SKILL.md)**，该文件是唯一权威（与 `skills/` 子文件冲突时以它为准）。

**报告结构（4 板块）**：★概览 → Section 1 TOP10竞品矩阵（含达人与内容）→ Section 2 Listing诊断 → Section 3 风险评估

**五条硬性规则**
1. **数据必须实取**：矩阵每个单元格都是当次 API 取值，核心行不允许 `≈`
2. **类目大盘一律 L3 口径**：L3 榜单 1–50 名逐条加总
3. **竞品 7+3 选取法**：前 7 名按自然排名，后 3 席必须是与本品同形态的产品
4. **禁止把"同形态竞品少"写成"蓝海"**：必须先用 4 项证据证伪"死海"假设
5. **评分只出数字**：`X/10`、`X/60`，不展示权重、公式、进度条

## 如何触发

用户给出 TikTok Shop 产品链接 / 产品ID / 关键词 / 店铺名时，读取 [SKILL.md](SKILL.md) 并按 5 步全部执行。

## 数据源

- **FastMoss MCP**（主）：产品/竞品/类目/达人全部结构化数据
- **FastMoss 产品页 + Browser JS**（图片提取，100% 可靠）：打开 `fastmoss.com/e-commerce/detail/{id}` → JS 提取全部 Thumbnail URL（`s.500fd.com` CDN）→ WebFetch 下载 → Read 查看。**不受反爬影响，任何机器可用**
- **`tiktok_product_scraper.py`**（辅，描述正文+评分分布）：FastMoss API 不返回这 2 类数据，需从 TikTok 产品页获取。使用 SeleniumBase UC 模式绕过反爬，成功率取决于 IP 信誉度
- **Browser `get_page_text`**（备用，脚本不可用时）：可能被 TikTok 反爬拦截，非必须
- **WebFetch + Read**（图片分析）：下载 `s.500fd.com` CDN 图片，不受反爬影响
- **禁止 Browser 截图**（`screenshot` 超时风险高、token 消耗大）

## ⚡ 性能强制规则（最高优先级，覆盖 SKILL.md）

### 阶段隔离

任务拆成**数据采集阶段**和**报告生成阶段**：
- **数据采集阶段**：加载 SKILL.md 调度逻辑 + [skills/12-统一报告格式.md](skills/12-统一报告格式.md)（一次性读入，后续不重复读取）；只拉取 FastMoss 数据、提炼要点写入本地 01~10 中间 MD 文件；不渲染报告、不绘制表格
- **报告生成阶段**：全部 API 采集完成后，分批读取中间文件组装报告（格式模板已在采集阶段预加载，无需重读）

### 核心约束

1. **数据采集允许子代理并行**：Batch A/B/C 可使用子代理并行执行（每个子代理负责一组 API 调用，采集完写入对应中间 MD 文件）；报告组装阶段仍由主线程直接执行
2. **原始 JSON 不进上下文**：API 返回的原始 JSON 只写入本地磁盘，会话内存仅保留精简后的中间 MD 摘要
3. **分批读取**：组装报告时单次最多同时读取 **4 份**中间文件，写完对应片段就释放
4. **MCP 优化**：按需指定返回字段；报错不无限重试，降级兜底标记【数据缺失】；可并行的请求并行执行
5. **token 预算 ≤80K**：接近阈值立即落盘清理（目标：单会话内完成全部采集+报告，避免跨会话续跑）
6. **SKILL 文件只读一次**：采集阶段一次性读入 SKILL.md 调度逻辑 + skills/12 格式模板，生成阶段直接使用，不重复读取
7. **Browser 零截图 + 图片走 FastMoss + 并行下载**：形态识别用三层筛选法（标题初筛 → WebFetch 下载 cover_url 图片验证 → 少量产品页确认，详见 SKILL.md §6.2）；**产品图片**通过 Browser 打开 FastMoss 产品页 → JS 提取全部 Thumbnail URL → **所有图片 WebFetch 并行发出**（一次性发出 8 个 WebFetch 调用下载全部图片）→ **所有图片 Read 并行发出**（一次性发出 8 个 Read 调用查看全部图片）；描述正文/评分分布优先用 `tiktok_product_scraper.py`（Layer 1），其次 `get_page_text`（Layer 2），最后标注缺失（Layer 3）；SEO 分析是纯计算不需要 Browser；**禁止 `screenshot`**
8. **报告写入必须用 Write 工具**：禁止用 Bash heredoc 写报告文件（heredoc 遇到内容中的引号会失败），一律使用 Write 工具写入 `report_{product_id}.md`

### 工作流

采集阶段合并为 3 个并行批次 + 1 个后台任务，最大化并行度：

```
┌─ 后台任务（Batch 0）: tiktok_product_scraper.py 后台启动（描述+评分分布，可选）
│
├─ 子代理 A（本品数据）: detail_info + overview + sku + shop_base + video_list + creator_analysis + review_list
│  → 写 01/02/03/04/05 → 丢弃
│
├─ 子代理 B（类目大盘）: ranking page 1-5（全部并行）
│  → 写 06（含三层筛选形态判定） → 丢弃
│
└─ 主线程等待 A+B 完成后 ──→ 子代理 C: TOP7 detail_info + 同形态搜索（并行）
                              → 写 07/08 → 丢弃

收尾（子代理 D + 主线程并行）:
├─ 子代理 D（图片）: FastMoss产品页 → JS提取全部URL → 8张WebFetch并行下载 → 8张Read并行查看 → 写图片分析部分到 09
└─ 主线程: 收集 Batch 0 爬虫结果 → 写描述+评分分布+评论兜底到 09 + 纯计算写 10（SEO）

最终: 分段生成报告（概览→S1→S2→S3 逐段落盘，用 Write 工具写入） → 发布为在线 Artifact → 回传链接
```

> **并行说明**: 子代理 A 合并了原 Batch 1+2 的 7 个 API 调用（全部并行发出），子代理 B 并行拉取 L3 排行 5 页。A 和 B 同时启动。C 依赖 A+B 的结果（需要知道 TOP7 是谁 + 同形态候选），因此等 A+B 完成后再启动。爬虫（Batch 0）在最开始后台启动，不阻塞任何批次。子代理 D 负责图片提取+分析，与主线程的爬虫结果收集+SEO计算并行执行。
> 
> **图片并行规则**: E1b 图片下载必须并行——JS 提取到 N 张图片 URL 后，一次性发出 N 个 WebFetch 调用（不要一张一张串行），全部下载完成后再一次性发出 N 个 Read 调用查看。从原来的 2N 轮串行调用（每张图 WebFetch→Read 交替）压缩为 2 轮并行调用（一轮 WebFetch、一轮 Read），节省约 60-80 秒。

> **数据来源分工：** **评论原文**采用两层策略——FastMoss `product_review_list` 不限评论数都先调用（≥500 评论商品通常返回 10+ 条完整评论），API 返回 0 时才用爬虫 SSR 的 3 条样本兜底（TikTok 反爬保护限制，爬虫无法获取更多，详见 SKILL.md §B6）。**产品图片**通过 FastMoss 产品页提取（Browser 打开 `fastmoss.com/e-commerce/detail/{id}` → JS 提取 Thumbnail URL → WebFetch 下载 CDN 图片），**100% 可靠，不依赖爬虫，不受反爬影响**。**描述正文 / 评分分布**从 TikTok 产品页获取：`tiktok_product_scraper.py` v1.2（Layer 1）→ Browser `get_page_text`（Layer 2）→ 标注缺失（Layer 3）。Layer 1 是否成功取决于机器 IP 信誉度，失败不影响报告图片诊断。

## 内容完整性（不可删减 — 最高优先级）

报告内容深度必须对标 HOOGALIFE 参照报告（Artifact 5x94Zq8fJEXMwgDJ4CcxTS）。**内容量和格式必须与参照报告一致，只是数据和产品不同**。以下模块缺一不可：
- 矩阵 ≥16行×12列 + 同形态逐款明细表 + 4项证据
- 达人流量多产品对比表 + 达人明细逐人占比
- SEO 关键词 TOP20 表（含方法论≥3句 + 热度分级 + 同形态覆盖列 + 每词诊断结论）
- **商品描述诊断** ≥6项检查（逐项独立行）+ 逐段新旧对比表（≥5段）
- 图片竞品对比表 + 图1-图7逐张优化（8行5列不留空）+ SKU缩略图优化
- 评论原文样本（好评+差评引用）+ 竞品痛点差异化表（≥3行）
- 风险 ≥5条（每条含数据+影响+缓解三行）+ 数据核验说明
- **每张数据表后必须有分析引用块（≥2句），禁止空表或只放表无分析**
- **所有优化建议必须有新旧对比 + 具体数据依据，禁止空话**

**防删减硬性规则详见 SKILL.md §7.6**——该章节列出了典型违规示例和各板块最低内容量，交付前必须逐条对照。

**速度优化的对象是过程，不是结果。禁止以 token 预算为由删减任何模块——接近上限时分段落盘，不砍内容。**

## 输出

1. 全程使用精简 Markdown 推进，中间结果写入 `{scratchpad}/batch/`
2. 最终报告为 **Markdown 格式**，文件名 `report_{product_id}.md`
3. 发布为在线 Artifact，回传链接给用户
4. 更新时复用同一 Artifact URL
5. **报告内容不删减**，SKILL.md 全部格式要求 + 内容完整性标准必须满足
6. 格式模板从 [skills/12-统一报告格式.md](skills/12-统一报告格式.md) 加载（Markdown 结构模板）
7. 交付前逐条对照 SKILL.md §十 检查清单 + skills/12 §四 完整性清单
