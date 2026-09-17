# amazon-title-image-compliance

按亚马逊 2025-01-21 生效的**商品名称新规**（或需求人自定义规则）批量清洗/改写商品标题、批量重命名商品图片，并输出合规报告。规则由 `rules.json` 配置驱动，可被需求人附件覆盖；配合 SP-API Feeds 可批量上传到亚马逊店铺。

**双模式**：
- **合规模式 `clean-titles`**：确定性规则清洗（超长/禁用符号/促销语/重词/全大写），保证符合硬规则。
- **改写模式 `optimize-titles`**：集成 `amazon-listing-optimization`（nexscope-ai/Amazon-Skills, MIT）标题方法论——`[品牌] + [主关键词] + [属性] + [差异化]`，主关键词前置、≤200 字符、禁促销语，输出 before→after。

---

## 目录结构

```
amazon-title-image-compliance/
├── SKILL.md                        ← skill 说明（Agent 读取此文件识别能力）
├── config/
│   └── rules.example.json          ← 规则配置模板（需求人规则来了改这里）
├── examples/
│   ├── products.csv                ← 合规模式样例（5 条违规标题）
│   ├── products_optimize.csv       ← 改写模式样例（含品牌+主关键词）
│   └── map.csv                     ← 图片重命名映射样例
├── references/
│   └── rules.md                    ← 默认规则与覆盖说明
└── scripts/
    ├── amazon_compliance.py        ← 核心引擎（4 个子命令）
    └── selftest.py                 ← 一键自测
```

---

## 一、Claude 怎么安装这个 skill

本 skill 采用 **Anthropic Agent Skills 格式**（一个文件夹 + `SKILL.md`），Claude Code / Claude Desktop 及其它支持该格式的 Agent（Codex、Cursor、Windsurf、OpenClaw 等）均可直接安装。

### 方式 0：自然语言一句话安装（别人最省事，推荐给非技术用户）

**不用自己敲任何命令**——把下面这段话**原样复制**发给 Claude（Claude Code / Claude Desktop 均可）：

> 请帮我从 GitHub 下载并安装一个 skill 到 Claude：
> 仓库是 https://github.com/qwqess121/amazon-title-image-compliance
> 1. 用 git clone（或下载 ZIP 解压）把仓库拉下来
> 2. 把 `amazon-title-image-compliance` 整个文件夹安装到 `~/.claude/skills/`（目录不存在就创建）
> 3. 运行 `~/.claude/skills/amazon-title-image-compliance/scripts/selftest.py` 做一键自测
> 4. 确认输出 [PASS] 全部通过后，检查环境：运行 `python -c "import openpyxl"`，如果报错就执行 `python -m pip install openpyxl` 装好（这个 skill 处理 Excel 时需要它）
> 5. 告诉我这个 skill 是干什么的、怎么用

更短的版本：

> 下载并安装这个 GitHub 仓库里的 skill 到 Claude：https://github.com/qwqess121/amazon-title-image-compliance ，装完跑一下它的 selftest 验证，并检查环境缺不缺 openpyxl，缺的话自动装好。

**Claude 会自动执行**：clone/下载 → 建目录 → 复制 → 跑自测 → 检查并安装 openpyxl → 汇报结果。安装完成后**重启会话**，就能用自然语言触发了，例如：
- "批量改亚马逊标题，符合新标题格式"
- "检查这些标题是否符合亚马逊新规"
- "按亚马逊规则批量改图片命名"

> 提示：如果 Claude 说"没有权限访问文件系统"或"不会 git"，可能是会话没开启工具权限，需要重新开启（Claude Code 需在项目目录运行，或在 Claude Desktop 里确认允许文件操作）。

### 方式 1：git clone（推荐）

```bash
# 1) 克隆仓库
git clone https://github.com/qwqess121/amazon-title-image-compliance.git

# 2) 复制到 Claude 的 skills 目录
#    Windows（PowerShell）：
Copy-Item -Recurse amazon-title-image-compliance $HOME\.claude\skills\
#    macOS / Linux：
cp -r amazon-title-image-compliance ~/.claude/skills/
```

### 方式 2：手动下载

1. 打开 https://github.com/qwqess121/amazon-title-image-compliance → **Code → Download ZIP**
2. 解压得到文件夹 `amazon-title-image-compliance`
3. 把整个文件夹放进 Claude 的 skills 目录（见下方位置说明）

### 安装位置

| 使用场景 | 目录 |
|---|---|
| 所有项目通用（个人级） | `~/.claude/skills/amazon-title-image-compliance/` |
| 仅当前项目（项目级） | `<项目根目录>/.claude/skills/amazon-title-image-compliance/` |

> 装到 `~/.claude/skills/` 后，所有项目的 Claude 都能用；装到项目 `.claude/skills/` 则只在该项目生效。

### 验证安装

```bash
# 1) 确认 SKILL.md 在位
ls ~/.claude/skills/amazon-title-image-compliance/SKILL.md

# 2) 一键自测（会临时生成样例数据跑通全链路）
cd ~/.claude/skills/amazon-title-image-compliance
python scripts/selftest.py
# 期望输出: [PASS] make-rules / clean-titles / optimize-titles / rename-images → 全部通过 ✅
```

### 在 Claude 里使用

安装后**重启 Claude 会话**（新会话才会加载新 skill），然后直接说：
- "批量改亚马逊标题，符合新标题格式"
- "按亚马逊规则批量改图片命名"
- "检查这些标题是否符合亚马逊新规"
- "把店铺标题清洗成 200 字符内、去符号、去重词"
- "先诊断我的 listing 再改标题" / "诊断后优化标题"

Claude 会自动匹配本 skill 并执行。

### 诊断驱动模式（先诊断，再修改，改完复诊）

修改标题前可先让 Claude 调用亚马逊 Listing 诊断 skill 摸清现状，诊断结论直接决定改什么。配套 3 个 GitHub 开源 skill（MIT，与本 skill 安装方式相同：clone 或下载 ZIP → 放入 `~/.claude/skills/` → 重启会话）：

| Skill | 来源仓库 | 诊断什么 |
|---|---|---|
| `sif-amazon-research` | liangdabiao/amazon-sorftime-research-MCP-skill | 基于 Sif 数据：市场验证、竞品分析、流量/广告根因诊断、关键词策略（需 Sif MCP 数据源） |
| `zach-listing-health-checker` | zach22-1999/amazon-skills | 真实消费者视角健康检查：页面可访问/价格/卖家/购物车/配送/类目节点/BSR/差评/搜索可见性（curl 抓公开页面，零 API） |
| `amazon-listing-optimization` | nexscope-ai/Amazon-Skills | 标题审计与关键词缺口：8 维评分、竞品关键词提取、重写建议（本 skill 改写模式已集成其方法论） |

**工作流**：诊断（health-checker 看页面健康、sif-amazon-research 看流量结构+关键词信号、amazon-listing-optimization 看标题审计与缺口）→ 诊断出的 Top 流量词/流失词/缺口词填入 `primary_keyword`、品牌名进 `preserve_case_words`、类目长度覆盖 `max_length` → 跑 clean/optimize → 上架 1~2 周后复诊对比页面健康/自然流量占比/关键词覆盖评分。

> 这三个 skill 未安装时自动降级为纯规则清洗（仍可用，结果会标注「未诊断」）。诊断返回的是分析结论，不执行任何店铺写操作；上传店铺仍需 `linkfox-amazon-store-operations`。

---

## 二、命令行用法（不依赖 Agent 也可用）

```bash
# 导出默认规则模板
python scripts/amazon_compliance.py make-rules --out rules.json

# 合规模式：批量清洗标题 → cleaned.csv（含合规报告）
python scripts/amazon_compliance.py clean-titles \
  --input products.csv --output cleaned.csv \
  --rules rules.json --key-col sku --title-col item_name

# 改写模式：品牌 + 主关键词前置 → optimized.csv（before→after）
python scripts/amazon_compliance.py optimize-titles \
  --input products.csv --output optimized.csv \
  --brand-col brand --keyword-col primary_keyword --rules rules.json

# 批量重命名图片（复制到输出目录，不删原件）
python scripts/amazon_compliance.py rename-images \
  --mapping map.csv --image-dir ./imgs --output-dir ./renamed --rules rules.json
```

依赖：Python 3.8+，纯标准库；读/写 `.xlsx` 需 `openpyxl`。

### 环境依赖（Claude 会自动安装，无需你操作）

唯一可选依赖是 XLSX 读写用的 `openpyxl`（纯 CSV 场景零依赖）：

```bash
# 检测是否已安装
python -c "import openpyxl; print(openpyxl.__version__)"
# 缺失时安装
python -m pip install openpyxl
```

**在 Claude 里使用时**：如果你上传的是 Excel（.xlsx），而环境缺少 `openpyxl`，脚本会明确报错并提示安装命令——Claude 会自动执行 `pip install openpyxl` 后重试，**你不需要自己装任何东西**。如果更想省事，也可以直接把表格另存为 CSV 再上传。

### 输出说明

- `clean-titles` 输出列：`sku / old_title / new_title / status / original_compliant / changed / issues`
  - `status`：`compliant`（已合规未改动）| `normalized`（仅规范化大小写）| `fixed`（已修复违规）——三者和等于总数，统计口径自洽。
- `optimize-titles` 输出列：`sku / brand / primary_keyword / old_title / new_title / changed / note`

---

## 三、规则配置（需求人规则怎么覆盖）

规则全部由 `rules.json` 驱动，需求人附件规则只需改配置，引擎逻辑不动：

| 字段 | 默认 | 说明 |
|---|---|---|
| `title.max_length` | 200 | 标题最大字符数（部分类目更短，如 80/150） |
| `title.forbidden_symbols` | `! $ ? _ { } ^ ¬ ¦ ~ # < > *` | 禁用符号（品牌名含符号时删掉该符号） |
| `title.exempt_small_words` | in/on/over/with/and/or/for/the/a/an/of/to/by/from | 豁免小词（不判重、非首词小写） |
| `title.promo_phrases` | free shipping / best seller / 100% quality ... | 促销语库，命中整段移除 |
| `title.single_word_promo` | super / premium / new / best / top ... | 单字促销词（改写模式剔除） |
| `title.preserve_case_words` | USB / LED / iPhone / iPad / MacBook / AirPods ... | 保留原始大小写的词（缩写/品牌名），Title Case 时不被小写化。品牌名被误小写（如 AmazonBasics→Amazonbasics）时，把品牌名加进此列表即可修复 |
| `title.max_word_repeat` | 2 | 同一词允许次数（>2 移除） |
| `image.key_field` | sku | 图片命名主键（可改 asin） |
| `image.format` / `image.padding` | jpg / 2 | 扩展名、附图序号位数（`_01`） |

完整说明见 `references/rules.md`。

---

## 四、批量上传到亚马逊店铺

本 skill 负责「出合规结果」，上架走 `linkfox-amazon-store-operations`（SP-API 通道）：

1. **授权前置**：需 `LINKFOX_AGENT_API_KEY` + 店铺 OAuth（`store_tokens.py` 取 `accessToken`）
2. **整理 flat file**：`cleaned.csv` / `optimized.csv` 转成 `item_sku` + `item_name` 模板
3. **Feeds 上传**：`create_feed_document` → `upload_feed_document` → `create_feed` → `get_feed` 轮询 → `get_feed_document`
4. **无 API 备选**：卖家中心「库存 > 批量上传商品 > 部分更新」手动上传

> 上传前必须确认 `sellerId / sku / ASIN / marketplaceIds / feedType` 等关键参数，写操作不可误改误删。

---

## 官方依据

- 亚马逊商品名称新规：2025-01-21 生效，适用所有卖家与品类（媒体类目除外），覆盖所有站点。
- 各站点/类目细节以卖家平台帮助页「商品名称要求和指南」为准。

## License

MIT
