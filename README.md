# TikTok Shop Skill 工作流使用指南

> AB America Corp / HOOGALIFE 内部工具包
> 包含三套 TikTok Shop 分析工作流，供 Claude Code 自动执行

---

## 快速开始

### 前置条件

| 条件 | 必须/可选 | 说明 |
|------|---------|------|
| Claude Code | 必须 | 桌面版或 CLI 版均可 |
| FastMoss MCP | 强烈推荐 | 提供完整 TikTok 数据（达人、销量、趋势等）。未连接时部分工作流可降级为 Chrome MCP |
| Chrome MCP | 可选（备选） | 直接从 TikTok Shop 页面抓取公开数据，FastMoss 不可用时的降级方案 |
| Python 3.10+ | tk视频拆解需要 | 用于关键帧提取和评论抓取脚本 |
| ffmpeg | tk视频拆解需要 | 视频帧提取依赖 |
| yt-dlp | tk视频拆解需要 | TikTok 视频下载 |

### 安装 Skill

将本 `skill` 文件夹整个复制到 Claude Code 项目的 `.claude/skills/` 目录下，或者直接告诉 Claude：

```
请读取 C:\Users\Administrator\Desktop\skill\README.md，然后按照说明执行对应的工作流
```

### 检查 FastMoss MCP 是否可用

在 Claude Code 中说：
```
帮我检查 FastMoss MCP 是否已连接，调用 credit_usage_summary 看看额度
```

如果返回 **402 / 余额不足**，需要去 FastMoss 充值后再使用。

---

## 三套工作流概览

| # | 工作流 | 目录 | 用途 | 输入 | 输出 |
|---|--------|------|------|------|------|
| 1 | TK Listing 诊断 | `tk诊断/` | 对单个产品做六维度全面体检 | 产品链接/ID/关键词 | HTML 诊断报告（Artifact） |
| 2 | TK 竞品分析 | `tk竞品分析/` | 7阶段深度竞品情报分析 | 产品链接/品类关键词 | HTML 竞品报告（Artifact） |
| 3 | TK 视频拆解 | `tk视频拆解/` | 拆解爆款视频的脚本结构和病毒机制 | TikTok 视频链接 | HTML 拆解报告（Artifact） |

---

## 工作流 1：TK Listing 诊断

### 入口文件
```
tk诊断/SKILL.md          ← Claude 读这个文件启动整个工作流
```

### 触发方式
```
请读取 tk诊断/SKILL.md，然后帮我诊断这个 TikTok Shop 产品：[粘贴产品链接]
```

### 工作流程（6步）
```
Step 1  数据采集           → 自动选择 FastMoss 或 Chrome MCP
Step 2  类目基准线         → 拉取同类目 TOP10 对标数据
Step 3  六维度诊断（上）   → 标题描述 + 图片视频 + SEO关键词
Step 4  六维度诊断（下）   → 定价佣金 + 达人内容 + 合规评论
Step 5  综合评分           → 六维度加权计算总分（满分60）
Step 6  报告生成           → HTML Artifact 报告
```

### 六维度
1. 标题与描述质量
2. 图片与视频质量
3. SEO 关键词覆盖（含类目归属校验）
4. 定价与佣金策略（含创作者每单收入、运费占比）
5. 达人与内容生态（含渠道分布、达人激活率）
6. 合规与评论管理

### 包含的 Skill 文件
| 文件 | 作用 |
|------|------|
| `SKILL.md` | 主调度（Claude 入口） |
| `skills/01-数据采集.md` | FastMoss/Chrome 数据采集 |
| `skills/02-类目基准.md` | 类目 TOP10 基准线 |
| `skills/03-标题描述诊断.md` | 标题+描述质量评分 |
| `skills/04-图片视频诊断.md` | 主图+视频质量评分 |
| `skills/05-SEO关键词诊断.md` | 关键词覆盖+类目校验 |
| `skills/06-定价佣金诊断.md` | 价格+佣金+达人收入 |
| `skills/07-达人内容诊断.md` | 达人网络+渠道分布 |
| `skills/08-合规评论诊断.md` | 合规风险+评论分析 |
| `skills/09-报告生成.md` | 综合评分+HTML报告 |
| `skills/10-WorkBuddy报告格式.md` | CSS/HTML 报告样式规范 |
| `report-template.html` | HTML 报告模板 |

---

## 工作流 2：TK 竞品分析

### 入口文件
```
tk竞品分析/TK竞品分析工作流.md     ← Claude 读这个文件启动
```

### 触发方式
```
请读取 tk竞品分析/TK竞品分析工作流.md，然后帮我分析这个品类的竞品：[粘贴产品链接或品类关键词]
```

### 工作流程（7阶段）
```
阶段1  竞品发现与地图          skill: tiktok-shop-analytics
阶段2  产品与店铺深挖          skill: product-differentiation-tiktok
阶段3  达人与内容策略分析      skill: tiktok-shop-analytics
阶段4  市场定位与差异化        skill: tiktok-shop-branding
阶段5  直播与广告渗透分析      skill: tiktok-shop-conversion
阶段6  Listing SEO与行动计划   skill: tiktok-shop-seo
阶段7  竞品分析报告输出        Claude Artifact（HTML仪表盘）
```

### 包含的 Skill 文件
| 目录 | 作用 | 需要安装？ |
|------|------|-----------|
| `TK竞品分析工作流.md` | 主调度（Claude 入口） | 已包含 |
| `tiktok-shop-analytics/` | 品类数据+达人内容分析 | 已包含 |
| `product-differentiation-tiktok/` | 产品差异化深挖 | 已包含 |
| `tiktok-shop-branding/` | 品牌定位与差异化 | 已包含 |
| `tiktok-shop-conversion/` | 直播+广告渗透分析 | 已包含 |
| `tiktok-shop-seo/` | Listing SEO 优化 | 已包含 |
| `workbuddy-competitor-report/` | HTML 报告样式规范 | 已包含 |

### 注意事项
- 本工作流对 FastMoss MCP 依赖度最高（约30+次 API 调用）
- 每个阶段的具体 FastMoss 工具调用顺序在主工作流文件中有详细说明
- 各子 skill 可独立加载执行单个阶段

---

## 工作流 3：TK 视频拆解

### 入口文件
```
tk视频拆解/v3-tk-workflow/SKILL.md     ← Claude 读这个文件启动
```

### 触发方式
```
请读取 tk视频拆解/v3-tk-workflow/SKILL.md，然后帮我拆解这个 TikTok 视频：[粘贴视频链接]
```

### 首次使用需要安装
第一次使用前，让 Claude 读取安装说明：
```
请读取 tk视频拆解/README_CLAUDE.md，帮我安装视频拆解工具到当前项目
```

安装会自动完成：复制文件到 `.claude/skills/`、检查 Python/ffmpeg/yt-dlp 依赖、安装 Playwright。

### 工作流程（6步）
```
Step 0  数据采集        → FastMoss 商业数据 + 下载视频 + 抓取评论
Step 1  视频扫描        → 关键帧提取 + 场景节奏分析
Step 2  Lift 爆款诊断   → 数据倍率 + 钩子类型识别
Step 3  脚本结构映射    → 5段式拆解 + 病毒评分
Step 4  评论洞察        → 6类评论分布 + 购买意图分层
Step 5  趋势+复制公式   → 趋势验证 + 6框架处方
```

### 包含的 Skill 文件
| 文件/目录 | 作用 |
|---------|------|
| `README_CLAUDE.md` | 安装说明（首次使用必读） |
| `v3-tk-workflow/SKILL.md` | 主调度（Claude 入口） |
| `v3-video-scanner/SKILL.md` | 视频扫描+帧分析 |
| `v2-hook-lift/SKILL.md` | Lift倍数+钩子诊断 |
| `v2-script-mapper/SKILL.md` | 脚本5段式映射 |
| `v3-comment-insight/SKILL.md` | 评论6类分布洞察 |
| `v2-trend-content/SKILL.md` | 趋势验证+复制公式 |
| `v3-report-template/template.html` | HTML 报告模板 |
| `extract_frames.py` | 关键帧提取脚本（Python） |
| `inject_report.py` | 报告数据注入脚本（Python） |
| `tk_comment_scraper.py` | TikTok 评论抓取脚本（Python） |

### 额外依赖安装
如果 Claude 安装时报错缺依赖，手动执行：
```bash
pip install playwright
playwright install chromium
```

---

## 常见问题

### Q: FastMoss 余额不足怎么办？
tk诊断 可以自动降级为 Chrome MCP 模式（数据有限但能完成诊断）。tk竞品分析 和 tk视频拆解 对 FastMoss 依赖较重，建议充值后使用。

### Q: 三个工作流可以对同一个产品一起跑吗？
可以，建议顺序：先跑 tk诊断（了解产品本身）→ 再跑 tk竞品分析（了解竞争格局）→ 最后挑竞品爆款视频跑 tk视频拆解。

### Q: 员工需要看什么来理解报告？
每个工作流生成的 HTML 报告（Artifact）是自包含的，不需要额外知识就能看懂。分享 Artifact 链接即可。

### Q: 某个 Skill 找不到怎么办？
所有 Skill 文件都已包含在本目录中。如果 Claude 提示某个 skill 未安装，让它读取对应目录下的 `SKILL.md` 文件即可，不需要从外部下载。

### Q: 报告结果链接在哪？
Claude 生成报告后会给出一个 Artifact 链接（`https://claude.ai/code/artifact/...`），点击即可在浏览器中查看和分享。

---

## 最新报告示例

- TK诊断: https://claude.ai/code/artifact/95b7699c-a3bf-4624-9804-13c78cac99c8
- TK竞品分析: https://claude.ai/code/artifact/840e8b91-866f-4d2d-b3a4-da861029a7ee
- TK视频拆解: https://claude.ai/code/artifact/ca0ec0ea-3492-4c04-b144-af654619c1be

---

## Cookie 配置（评论爬虫可选）

`listing和竞品分析/scripts/tiktok_cookies.json` **不包含在本仓库中**（含真实登录态 Cookie，已加入 `.gitignore`）。

评论爬虫默认走浏览器 UC 模式，无需 Cookie。只有在 UC 模式失败、需要回退到 HTTP 模式时才用到：

```bash
# 方式 1：让脚本自动从 Chrome 读取（需先关闭 Chrome）
python tiktok_review_scraper.py <product_id> --mode http

# 方式 2：手动准备 Cookie 文件
cp tiktok_cookies.example.json tiktok_cookies.json
# 填入自己的 msToken 等值后
python tiktok_review_scraper.py <product_id> --mode http --cookies-file tiktok_cookies.json
```

⚠️ 切勿把自己的 `tiktok_cookies.json` 提交到任何公开仓库。
