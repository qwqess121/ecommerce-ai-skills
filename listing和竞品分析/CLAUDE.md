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
- **`tiktok_product_scraper.py`**（辅，产品页数据）：描述正文、图片列表、评论原文、评分分布（FastMoss API 不返回这 4 类数据）。使用 SeleniumBase UC 模式**自动绕过 TikTok 反爬验证**
- **Browser `get_page_text`**（备用，脚本不可用时）：可能被 TikTok 反爬拦截，非必须
- **WebFetch + Read**（图片分析）：下载 cover_url CDN 图片，不受反爬影响
- **禁止 Browser 截图**（`screenshot` 超时风险高、token 消耗大）

## ⚡ 性能强制规则（最高优先级，覆盖 SKILL.md）

### 阶段隔离

任务拆成**数据采集阶段**和**报告生成阶段**：
- **数据采集阶段**：只加载 SKILL.md 调度逻辑，**禁止读取格式模板**；只拉取 FastMoss 数据、提炼要点写入本地 01~10 中间 MD 文件；不渲染报告、不绘制表格
- **报告生成阶段**：全部 API 采集完成后才加载格式规范，分批读取中间文件组装报告

### 核心约束

1. **禁止子代理**：数据采集全程禁用子代理；报告组装也直接执行
2. **原始 JSON 不进上下文**：API 返回的原始 JSON 只写入本地磁盘，会话内存仅保留精简后的中间 MD 摘要
3. **分批读取**：组装报告时单次最多同时读取 2 份中间文件，写完对应片段就释放
4. **MCP 优化**：按需指定返回字段；报错不无限重试，降级兜底标记【数据缺失】；可并行的请求并行执行
5. **token 预算 ≤40K**：接近阈值立即落盘清理
6. **SKILL 文件只读一次**：采集阶段读一次调度逻辑，生成阶段读一次格式模板，不重复读取
7. **Browser 零截图 + 产品页三层降级**：形态识别用三层筛选法（标题初筛 → WebFetch 下载 cover_url 图片验证 → 少量产品页确认，详见 SKILL.md §6.2）；产品页数据（描述/图片/评论/评分分布）优先用 `tiktok_product_scraper.py`（Layer 1，绕过反爬），其次 `get_page_text`（Layer 2），最后降级标注缺失（Layer 3）；图片诊断用 WebFetch 下载 cover_url（不受反爬影响）；SEO 分析是纯计算不需要 Browser；**禁止 `screenshot`**

### 工作流

```
Batch 1: detail_info + overview + sku + shop_base → 写 01/02/03 → 丢弃
Batch 2: video_list + creator_analysis + review_list → 写 04/05 → 丢弃
Batch 3: ranking page 1-5（全部并行） → 写 06（含三层筛选形态判定） → 丢弃
Batch 4+5: TOP7 detail_info + 同形态搜索（并行） → 写 07/08 → 丢弃
Batch 5.5: tiktok_product_scraper.py（优先）或 get_page_text（备用）+ WebFetch cover_url → 写 09（图片+描述+评论） + 纯计算写 10（SEO）
最终: 分段生成报告（概览→S1→S2→S3 逐段落盘） → 发布为在线 Artifact → 回传链接
```

> **为什么需要三层降级？** FastMoss API 不返回 4 类数据：产品描述正文、图片完整列表、评论原文（<500条时API常空）、评分星级分布。`tiktok_product_scraper.py`（Layer 1）使用 SeleniumBase UC 模式自动绕过 TikTok 反爬验证，成功率最高；内置 Browser `get_page_text`（Layer 2）可能被拦截；Layer 3 确保报告一定能生成。**员工使用前需安装依赖：`pip install seleniumbase`**

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
