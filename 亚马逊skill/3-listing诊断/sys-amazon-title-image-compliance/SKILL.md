---
name: sys-amazon-title-image-compliance
display_name: "亚马逊标题/图片批量合规"
display_name_en: "Amazon Title & Image Bulk Compliance"
description: "按亚马逊新规批量清洗商品标题、批量重命名商品图片并输出合规报告。用户要求批量改亚马逊标题、改图片命名、检查标题合规或按新标题格式清洗 Listing 时使用。"
category: e-commerce
version: 1.1.0
author: WorkBuddy
visibility: "public"
---

# 亚马逊标题 / 图片批量合规（Amazon Title & Image Bulk Compliance）

按亚马逊 2025-01-21 生效的**商品名称新规**（或需求人提供的自定义规则）批量处理商品标题与图片命名，输出「新标题 + 合规报告 + 重命名后的图片」。

**双模式**：
- **合规模式 `clean-titles`**：确定性规则清洗（超长/符号/促销语/重词/全大写），保证符合硬规则。
- **改写模式 `optimize-titles`**：集成 `amazon-listing-optimization`（nexscope-ai/Amazon-Skills, MIT）的标题方法论——`[品牌] + [主关键词] + [属性] + [差异化]`，主关键词前置紧贴品牌，≤200 字符、禁促销语/全大写，输出 before→after。

## 能力边界

### ✅ 能力范围
- **批量清洗标题**：读源表（CSV/XLSX，含 SKU/ASIN 与旧标题）→ 按规则引擎清洗 → 输出新标题表 + 每条合规判定/命中规则。
- **批量方法论改写标题**：给定品牌 + 主关键词列，按 amazon-listing-optimization 标题结构重排（品牌开头、主关键词前置、保留尺寸/颜色/数量属性）。
- **批量重命名图片**：按 `<SKU>.jpg`（主图）、`<SKU>_01.jpg`（附图）等亚马逊命名规范，把图片复制并重命名为合规文件名。
- **规则可配置**：最大长度、禁用符号、促销语库、豁免小词、重复词上限、图片主键字段等全部由 `rules.json` 驱动；需求人附件规则直接改配置即可，引擎逻辑不动。
- **非破坏**：图片采用「复制到输出目录」而非移动/删除原件，原件安全。

### ❌ 边界与限制
- **上架需 linkfox 授权**：本 skill 不直接持有店铺凭证；批量上传走 `linkfox-amazon-store-operations`（需 `LINKFOX_AGENT_API_KEY` + 店铺 OAuth，见文末「批量上传到亚马逊店铺」章节）。无 API key 时可改用卖家中心手动批量上传。
- **不校验图片画质**：只管文件名，不管主图白底/占比/分辨率（那是亚马逊图片内容规范，需另行工具）。
- **重复词为启发式**：单复数按去尾 `s` 归一判断，复杂形态（如 `quality`/`qualify`）可能误判；建议跑完人工复核报告中的 `repeat_word` 行。
- **XLSX 依赖 openpyxl**：读/写 `.xlsx` 需 `openpyxl`；未安装时脚本会明确报错并给出修复命令。**Agent（Claude 等）遇到该报错应自动执行 `python -m pip install openpyxl` 后重试**，无需用户手动处理。

### 环境依赖（Agent 自动安装）
本 skill 脚本为纯标准库，唯一可选依赖是 XLSX 读写用的 `openpyxl`：

```bash
# 检测（任一命令成功即已安装）
python -c "import openpyxl; print(openpyxl.__version__)"
# 缺失时安装（Agent 遇到 ImportError 报错时自动执行）
python -m pip install openpyxl
```

- 只在用户上传/要求输出 `.xlsx` 时需要；纯 CSV 场景零依赖。
- Agent 调用流程：检测 `openpyxl` → 缺失则 `pip install openpyxl` → 重跑命令。全程无需用户介入。

## 触发场景
- "批量改亚马逊标题，符合新标题格式"
- "按亚马逊规则批量改图片命名"
- "检查这些标题是否符合亚马逊新规"
- "把店铺标题清洗成 200 字符内、去符号、去重词"
- "先诊断我的 listing 再改标题" / "诊断后优化标题"

> ⚠️ 执行前先检查环境：若用户上传/要求输出 `.xlsx`，先运行 `python -c "import openpyxl"` 检测；缺失则 `python -m pip install openpyxl` 后继续。CSV 场景跳过此步。

## 诊断前置工作流（先诊断，再修改，修改后复诊）

本 skill 支持**诊断驱动**的标题修改：修改前先调用亚马逊 Listing 诊断/优化 skill（`sif-amazon-research` / `zach-listing-health-checker` / `amazon-listing-optimization`）摸清 Listing 现状，诊断结论直接决定改什么、怎么改；改完后建议隔期复诊验证效果。**这些 skill 未安装时降级为纯规则清洗**（仍可用，只是不带数据依据）。

### 0) 诊断工具（GitHub 开源 skill，需先安装到 skills 目录）
| Skill | 来源仓库（MIT） | 诊断能力 | 安装方式 |
|---|---|---|---|
| `sif-amazon-research` | liangdabiao/amazon-sorftime-research-MCP-skill | 基于 Sif 数据的市场验证、竞品分析、流量/广告根因诊断、关键词策略、发布评估 | clone 仓库后把 `sif-amazon-research` 文件夹放入 `~/.claude/skills/`（需 Sif MCP 数据源） |
| `zach-listing-health-checker` | zach22-1999/amazon-skills | 以真实消费者视角检查 Listing 健康：页面可访问性/价格/卖家/购物车/配送/类目节点/BSR/差评/关键词搜索可见性（curl 抓公开页面，无需 API） | clone 仓库后把 `zach-listing-health-checker` 文件夹放入 `~/.claude/skills/` |
| `amazon-listing-optimization` | nexscope-ai/Amazon-Skills | 标题审计与关键词缺口分析：8 维评分（标题/要点/描述/图片/A+/价格/评论/SEO 覆盖）、竞品关键词提取、重写建议（本 skill 改写模式已集成其方法论） | clone 仓库后把 `amazon-listing-optimization` 文件夹放入 `~/.claude/skills/` |

> 安装这三个 skill 的方法与本 skill 相同（clone 或下载 ZIP → 放入 `~/.claude/skills/` → 重启会话）。它们不互相依赖、各自独立可用；`sif-amazon-research` 需要 Sif MCP 数据源，其余两个零 API 依赖。未安装时本 skill 跳过诊断步骤直接清洗，并在结果中标注「未诊断」。

### 1) 诊断阶段（改之前必做）
- 从源表取 ASIN/SKU 列表，对每个 ASIN 调用已安装的诊断 skill：
  - **Listing 健康检查**（`zach-listing-health-checker`）：页面是否可访问（狗狗页/404/下架）、价格/划线价/优惠券、卖家名称是否匹配、购物车按钮、配送时效、类目节点、BSR 排名、星级差评、关键词搜索可见性——**发现异常项（如类目节点错、BSR 骤降）先人工处理再改标题**。
  - **流量与关键词诊断**（`sif-amazon-research`）：流量结构（自然/广告占比）、Top 流量词、流失词、增长词、排名断档词、竞品关键词布局——**这些词应出现在新标题里**（主关键词/属性词从这取）。
  - **标题审计与缺口**（`amazon-listing-optimization`）：对现有标题做 8 维评分、找关键词缺口、给出重写建议——**直接作为 optimize-titles 的输入依据**。
- 诊断产出写入结果表（每行加列：`health_check / top_keywords / keyword_gaps / issues_from_diag`），供第 2 步使用。

### 2) 修改阶段（诊断驱动）
- **合规模式 `clean-titles`**：规则由诊断微调——品牌名/专有名词进 `preserve_case_words`；类目长度上限覆盖 `max_length`；诊断出的流量流失词若在标题中位置靠后被前移。
- **改写模式 `optimize-titles`**：`primary_keyword` 优先取诊断的 Top 流量词/增长词/关键词缺口（而非人工拍脑袋）；属性词保留诊断确认的规格（尺寸/颜色/数量）；`amazon-listing-optimization` 的重写建议作为标题结构参考。
- 其余流程不变（见「工作流」与「调用方式」）。

### 3) 复诊阶段（改之后建议）
- 修改上架后 1~2 周，再次调用诊断 skill 对比：`zach-listing-health-checker` 看页面指标是否正常、`sif-amazon-research` 看自然流量占比/流失词排名是否回升、`amazon-listing-optimization` 看关键词覆盖评分是否提升。
- 复诊结论追加到结果表末尾（`post_check` 列），供运营复盘。

> 注意：这三个 skill 返回的是**诊断结论/建议**，不是可执行命令；本 skill 只消费诊断数据来指导规则与参数，不执行任何店铺写操作。上传店铺仍需 `linkfox-amazon-store-operations`。

## 工作流
0. （可选·推荐）**诊断**：调用 `zach-listing-health-checker`（健康检查）+ `sif-amazon-research`（流量/关键词）+ `amazon-listing-optimization`（标题审计）摸清各 ASIN 现状（见「诊断前置工作流」），诊断结论驱动规则与参数。
1. 准备源表 `products.csv`：至少含 `sku`（或 `asin`）+ `item_name`（旧标题）两列；做改写模式时另加 `brand` + `primary_keyword` 列（诊断出 Top 流量词可直接填这里）。
2. （可选）`python amazon_compliance.py make-rules` 导出 `rules.json`，按需求人附件调整（诊断出的品牌名/专有名词加进 `preserve_case_words`）。
3. `python amazon_compliance.py clean-titles --input products.csv --output cleaned.csv` → 合规模式，得到 `cleaned.csv`（旧标题/新标题/**status**（compliant=已合规未改动 / normalized=仅规范化大小写 / fixed=已修复违规）/是否合规/命中规则/是否改动）。
4. `python amazon_compliance.py optimize-titles --input products.csv --output optimized.csv` → 改写模式（amazon-listing-optimization 方法论），得到 `optimized.csv`（before→after + 改写说明）。
5. （有图片时）`python amazon_compliance.py rename-images --mapping map.csv --image-dir ./imgs --output-dir ./renamed` → 图片按 SKU 重命名输出到 `./renamed`。
6. 把结果整理成亚马逊 flat file（`item_sku` + `item_name`），用 `linkfox-amazon-store-operations` 的 Feeds 批量上传推到店铺（授权/上传见文末「批量上传到亚马逊店铺」章节）。
7. （可选·建议）上架 1~2 周后**复诊**：再次调用诊断 skill 对比页面健康/自然流量占比/关键词覆盖变化，结论追加到结果表。

## 默认标题规则（可被 rules.json 覆盖）
- 最大长度 200 字符（含空格，多数类目）。
- 禁用符号：`! $ ? _ { } ^ ¬ ¦`（默认另含 `~ # < > *` 一并清除；可配置）。
- 同一词/词组 ≤2 次；单复数算重复；介词/冠词/连词豁免。
- 禁促销语：free shipping / 100% quality / best seller / top rated / hot item / high quality 等。
- 首字母大写（小词小写），禁全大写。
- 保留词大小写：`preserve_case_words`（默认含 USB/LED/iPhone 等缩写与品牌名）在 Title Case 时保持原样，不会被小写化；斜杠枚举（如 Black/White）各段分别首字母大写。
- 单字促销形容词（super/premium/new 等）仅在改写模式剔除，合规模式保留（它们是有信息量的修饰语）。

## 默认图片规则
- 主键字段 `sku`（可改 `asin`）。
- 主图 `<key>.jpg`，附图 `<key>_01.jpg`、`<key>_02.jpg`…
- 映射表 `map.csv` 列：`key,original_file,index`（index=0 主图，1/2…附图）。

## 一键自测（验收 skill 是否可用）
```bash
cd <skill 根目录>
python scripts/selftest.py
# 输出 [PASS] make-rules / clean-titles / optimize-titles / rename-images，全部通过=✅
```
自测脚本会在临时目录自动生成样例数据（含各类违规标题 + 6 张占位图 + 映射表），跑通全链路后打印 PASS/FAIL。

## 调用方式
```bash
# 导出默认规则模板
python scripts/amazon_compliance.py make-rules --out rules.json

# 合规模式：批量清洗标题
python scripts/amazon_compliance.py clean-titles \
  --input products.csv --output cleaned.csv \
  --rules rules.json --key-col sku --title-col item_name

# 改写模式：amazon-listing-optimization 方法论（品牌开头 + 主关键词前置）
python scripts/amazon_compliance.py optimize-titles \
  --input products.csv --output optimized.csv \
  --brand-col brand --keyword-col primary_keyword --rules rules.json

# 批量重命名图片（复制，不删原件）
python scripts/amazon_compliance.py rename-images \
  --mapping map.csv --image-dir ./imgs --output-dir ./renamed --rules rules.json
```
- 脚本位置：`scripts/amazon_compliance.py`（纯标准库；XLSX 需 `openpyxl`）。
- 输出落盘到 `--output`/输出目录；终端打印汇总（总数 / 原已合规 / 已改动 / 各规则命中数）。

## 批量上传到亚马逊店铺（linkfox-amazon-store-operations）

本 skill 负责「出合规结果」，**上架走 `linkfox-amazon-store-operations`**（SP-API 通道）。完整链路：**本 skill 清洗/改写 → 整理 flat file → Feeds 批量上传 → 店铺生效**。

### 1) 前置：店铺授权（SP-API / API key）

需要两样东西，缺一不可：

| 凭证 | 怎么拿 | 说明 |
|---|---|---|
| `LINKFOX_AGENT_API_KEY` | 在 linkfox 平台注册并开通 SP-API 网关（登录注册时 channel 必须传 `workbuddy`） | 环境变量，网关鉴权用 |
| 店铺 OAuth 授权 | 用 `linkfox-amazon-store-auth` 生成授权链接，卖家在亚马逊后台点同意 | 授权后换取 `accessToken`（约 1 小时过期，可用 refreshToken 刷新） |

授权命令（来自 linkfox-amazon-store-auth）：
```bash
# 1) 生成授权链接（卖家点开授权）
python store_tokens.py '{"region":"NA","sellerName":"My Store"}'
# 2) 取访问令牌（供下游所有 SP-API 调用）
#    返回 accessToken / refreshToken / expiresIn
```

> 若未安装 linkfox-amazon-store-auth，脚本会以 `DEPENDENCY_MISSING:` 提示，需先安装该 skill 完成授权。

### 2) 整理上传文件（flat file）

把 `cleaned.csv` / `optimized.csv` 整理成亚马逊批量模板，核心列只需：`item_sku`（SKU）+ `item_name`（新标题），可选 `feed_product_type` / `external_product_id` / `external_product_id_type` / `brand_name`。

### 3) Feeds 批量上传（linkfox-amazon-store-feeds）

```bash
# 流程：建文档 → 传文件 → 建 Feed 任务 → 轮询 → 取结果
python create_feed_document.py '{"region":"NA","marketplaceIds":["ATVPDKIKX0DER"],"feedType":"POST_FLAT_FILE_INVLOADER_DATA"}'
python upload_feed_document.py '<上传文档参数>'        # PUT 预签名 URL
python create_feed.py '{"sellerId":"A1...","region":"NA","feedType":"POST_FLAT_FILE_INVLOADER_DATA","inputFeedDocumentId":"amzn1.tdoc.1.1.xxx"}'
python get_feed.py '{"feedId":"<feedId>"}'             # 轮询 DONE
python get_feed_document.py '{"feedDocumentId":"<resultFeedDocumentId>"}'   # 取处理结果，非 DONE 需人工复核
```

### 4) 不加 API 的手动方案（卖家中心）

把 flat file 下载到本地 → 卖家中心「库存 > 批量上传商品 > 下载模板/部分更新」上传 → 查看处理报告。适合没有 API key 的场景。

> 上传前必须向用户确认 `sellerId / sku / ASIN / marketplaceIds / feedType` 等关键参数，写操作不可误改误删。
