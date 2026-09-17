# TikTok 电商爆款视频拆解工作流 V3 — 安装说明

> **写给 Claude 的执行手册。用户不会读任何文档，所有交接信息由你在安装结束时讲出来。**
>
> 用户可能只说一句「安装这个」「帮我装一下」甚至只是把文件夹拖进来——
> 不要反问他想干什么，直接按下面的阶段顺序执行。
> **能自己查的绝不问用户**，只有出现【需要用户决策】标记时才停下来。
> 全程只应该问用户两次：装到哪个目录（且当前目录可用时连这次也免了）、拿哪条视频做验证。

---

## 文件清单

```
skill/
├── README_CLAUDE.md               ← 本文件
├── SKILL.md                       ← 索引skill（报告长什么样 + 判定逻辑）
├── extract_frames.py              ← 关键帧提取脚本
├── inject_report.py               ← 报告注入脚本
├── v3-tk-workflow/SKILL.md        ← 主调度 skill
├── v3-video-scanner/SKILL.md      ← 视频扫描 skill
├── v3-comment-insight/SKILL.md    ← 评论洞察 skill
├── v2-hook-lift/SKILL.md          ← Lift诊断 skill
├── v2-script-mapper/SKILL.md      ← 脚本拆解 skill
├── v2-trend-content/SKILL.md      ← 复制公式 skill
└── v3-report-template/
    ├── template-same-product.md   ← ★竞品对比 MD模板（第一步）
    ├── template-same-product.html ← ★竞品对比 HTML模板（第二步）
    └── template.html              ← 单视频模式模板
```

---

## 前置要求（你自己查，不要问用户）

**不要问「你用的是不是 Claude Code」** —— 你就运行在 Claude Code 里，这是自明的。

**不要问「你连没连 FastMoss-MCP」** —— 直接调用工具验证：

```
调用 mcp__FastMoss-MCP__credit_usage_summary（无需参数）
```

- 返回余额数据 → 已连接，继续，并记下余额待会儿一起汇报
- 工具不存在 / 调用失败 → **【需要用户决策】** 这是硬阻塞，停止并告知：

  > "FastMoss-MCP 没有连接，这是这套工具唯一的数据源，没有它跑不了。
  > 请在 Claude Code 的设置里连接 FastMoss-MCP 插件，连好后跟我说一声，我继续安装。
  > （注意：每台电脑都要单独连一次。）"

**安装目录**：默认用**当前工作目录**，不要专门问。
先确认当前目录（Mac/Linux `pwd`，Windows `cd`），然后一句话告知用户：

> "我把工具装到当前目录 `<路径>`，以后在这个目录下用。如果想换个地方现在告诉我。"

说完直接往下走，不要停下来等回复。用户没异议就是同意。
后续所有操作以该路径为 `<PROJECT>`。

---

## 阶段一：确认项目目录

已在前置要求阶段确定（默认当前目录）。用户若中途说了别的目录，改用他说的。

---

## 阶段二：复制所有文件

以下命令全部执行，不需要询问：

```bash
# 创建 skill 目录结构
mkdir -p "<PROJECT>/.claude/skills/tk视频爆款拆解"
mkdir -p "<PROJECT>/.claude/skills/v3-tk-workflow"
mkdir -p "<PROJECT>/.claude/skills/v3-video-scanner"
mkdir -p "<PROJECT>/.claude/skills/v3-comment-insight"
mkdir -p "<PROJECT>/.claude/skills/v2-hook-lift"
mkdir -p "<PROJECT>/.claude/skills/v2-script-mapper"
mkdir -p "<PROJECT>/.claude/skills/v2-trend-content"
mkdir -p "<PROJECT>/.claude/skills/v3-report-template"

# 复制 SKILL.md 文件（从 skill 文件夹所在位置执行）
cp SKILL.md                       "<PROJECT>/.claude/skills/tk视频爆款拆解/SKILL.md"
cp v3-tk-workflow/SKILL.md        "<PROJECT>/.claude/skills/v3-tk-workflow/SKILL.md"
cp v3-video-scanner/SKILL.md      "<PROJECT>/.claude/skills/v3-video-scanner/SKILL.md"
cp v3-comment-insight/SKILL.md    "<PROJECT>/.claude/skills/v3-comment-insight/SKILL.md"
cp v2-hook-lift/SKILL.md          "<PROJECT>/.claude/skills/v2-hook-lift/SKILL.md"
cp v2-script-mapper/SKILL.md      "<PROJECT>/.claude/skills/v2-script-mapper/SKILL.md"
cp v2-trend-content/SKILL.md      "<PROJECT>/.claude/skills/v2-trend-content/SKILL.md"
cp v3-report-template/template-same-product.md   "<PROJECT>/.claude/skills/v3-report-template/template-same-product.md"
cp v3-report-template/template-same-product.html "<PROJECT>/.claude/skills/v3-report-template/template-same-product.html"
cp v3-report-template/template.html              "<PROJECT>/.claude/skills/v3-report-template/template.html"

# 复制工具脚本到项目根目录
cp extract_frames.py     "<PROJECT>/extract_frames.py"
cp inject_report.py      "<PROJECT>/inject_report.py"
```

复制完成后，逐一确认以下文件存在（任何一个缺失要立即报告具体路径并停止）：

- `<PROJECT>/.claude/skills/v3-tk-workflow/SKILL.md`
- `<PROJECT>/.claude/skills/v3-video-scanner/SKILL.md`
- `<PROJECT>/.claude/skills/v3-comment-insight/SKILL.md`
- `<PROJECT>/.claude/skills/v2-hook-lift/SKILL.md`
- `<PROJECT>/.claude/skills/v2-script-mapper/SKILL.md`
- `<PROJECT>/.claude/skills/v2-trend-content/SKILL.md`
- `<PROJECT>/.claude/skills/tk视频爆款拆解/SKILL.md`
- `<PROJECT>/.claude/skills/v3-report-template/template-same-product.md`
- `<PROJECT>/.claude/skills/v3-report-template/template-same-product.html`
- `<PROJECT>/.claude/skills/v3-report-template/template.html`
- `<PROJECT>/extract_frames.py`
- `<PROJECT>/inject_report.py`

---

## 阶段三：环境检查与自动修复

**逐项检查，发现缺失立即安装，不询问用户。**

### 3-A 检测操作系统

```bash
# Mac/Linux
uname -s

# Windows（PowerShell）
$env:OS
```

记录系统类型，后续安装命令依此选择。

### 3-B 检查 ffmpeg

```bash
ffmpeg -version
```

- ✅ 有输出 → 跳过
- ❌ 报错 → 立即安装：

```bash
# Windows
winget install --id Gyan.FFmpeg -e

# Mac
brew install ffmpeg

# Linux
sudo apt-get install -y ffmpeg
```

安装后再次运行 `ffmpeg -version` 确认成功。

### 3-C 检查 Python 和 pip

```bash
python --version
pip --version
```

- ✅ 两者均有输出 → 跳过
- ❌ python 不存在 → **【需要用户决策】** 告知用户："需要先安装 Python 3.8+，请访问 https://python.org 下载安装后告知我继续。"

### 3-D 检查 yt-dlp

```bash
pip show yt-dlp
```

- ✅ 有版本信息 → 跳过
- ❌ 没有 → 立即安装：

```bash
pip install yt-dlp
```

### 3-E 检查 FastMoss-MCP 连接

```
请调用 mcp__FastMoss-MCP__credit_usage_summary 工具（无需参数）。
```

- ✅ 返回数据（余额信息）→ FastMoss-MCP 已连接，跳过
- ❌ 工具不存在 / 调用失败 → **【需要用户决策】** 停止安装，告知用户：

  > "FastMoss-MCP 未连接。这是 V3 工作流的核心数据源，没有它无法运行。  
  > 请在 Claude Code 设置中连接 FastMoss-MCP 插件后，重新发送这个文件夹开始安装。"

### 3-F 汇报检查结果

向用户输出一张表格：

```
✅ 文件复制      12/12 个文件就位
✅ ffmpeg        已安装（版本 x.x）
✅ Python        已安装（版本 3.x.x）
✅ yt-dlp        已安装
✅ FastMoss-MCP  已连接（余额：XXX credits）
```

如有任何 ❌ 且无法自动修复，列出原因和手动解决方法，然后停止。

---

## 阶段四：跑一个真实视频验证

**环境全部就绪后，执行此阶段。**

**【需要用户决策】** 告知用户：

> "环境已就绪！现在我要用一个真实 TikTok 视频跑一遍完整流程来验证安装是否正确。  
> 请粘贴一条 TikTok 视频链接（推荐选一条带货的电商视频），或者说"找爆款 [品类]"让我自动发现。"

收到链接后，在 `<PROJECT>` 目录下直接执行：

```
v3拆解 <用户提供的链接>
```

或发现模式：

```
找爆款 <用户说的品类>
```

这会触发**默认的竞品对比流程**：选品(近7天Top10) → 采集 → 逐条拆解 → 算聚合 →
出MD → 填HTML模板 → 自检 → 发布。

**验证标准（逐条核对，不要只看"没报错"）：**
- 先产出 MD 报告，再产出 HTML 报告
- HTML 报告结构为：Hero + 区块01大盘 + 02竞品拆解 + 03我方拆解 + 04行动方案 + 结论
- 区块01 是**转置矩阵表**：指标作行、达人作列，15列 × 25指标行
- 表格上方有**达人对照条**（11个可点击chip），表头里**没有** @handle
- 区块04 的两版成稿是**中英双语**
- 浏览器打开正常，1440px 宽度下大盘表不横向滚动
- 报告里没有 `{{` 占位符残留

> ⚠️ 上述任何一条不满足，说明模板没被正确使用（很可能是 Claude 从零写了HTML）。
> 重读 `.claude/skills/v3-report-template/template-same-product.html` 重新生成。

**如果某步骤出错：**
- 读取错误信息，判断是哪个环节（FastMoss采集 / 视频下载 / 帧提取 / 报告生成）
- 尝试修复后重跑，最多重试 2 次
- 两次仍失败则告诉用户具体错误和建议

---

## 阶段五：安装完成通知

验证通过后，向用户发送以下消息：

---

✅ **安装完成，验证通过！**

**以后使用方式：**
在这个目录下的 Claude Code 对话中，直接说：

| 说这些 | 效果 |
|--------|------|
| `v3拆解 https://www.tiktok.com/...` | 最常用：自动找同商品Top 10竞品做完整对比 |
| `爆款拆解 https://...` | 同上 |
| `找爆款 香水` | 发现模式：自动找GMV最高的香水视频来拆 |
| `找爆款 香水 粉丝10万以下` | 发现模式 + 筛选条件 |
| `只拆这一条 https://...` | 关闭竞品对比，单视频模式 |

**默认行为**：给一条视频链接 → 自动搜同商品近7天Top 10竞品 → 完整对比。
只想拆单条不做对比，要明确说「只拆这一条」。

**每次输出两个文件**（都在工作目录的 `报告/` 下）：
1. `.md` —— 先给你看，核对数据和结论
2. `.html` —— 确认后生成，同时发布为可分享链接

**报告内容**：
| 区块 | 内容 |
|------|------|
| 01 竞品大盘总览 | 达人对照条 + 转置矩阵表（25指标 × 11条视频 + 竞品均值/最优/我方差距）+ 2张解读卡 |
| 02 竞品逐条拆解 | 10条竞品，每条：脚本时间线 + 5维病毒评分 |
| 03 我方视频拆解 | 数据面板 + 5维评分 + 时间线 + 核心诊断 + RIDE/BEND判定 |
| 04 行动方案 | 4.1脚本(含2版中英双语成稿) / 4.2拍摄 / 4.3商家配合 / 4.4达人物料 |
| 结论 | 竞品为什么能爆 / 我方差距 / 怎么复制 |

---

**几个必须提醒你的点：**

- **跑一次会消耗 FastMoss credits**。一次要拉 11 条视频的多个接口，跑之前留意余额。
  当前余额：{{安装时查到的余额}}。

- **看到「已降级到14天/28天」不是出错**。竞品按「近7天 + 播放≥10万 + 近7天GMV≥$1000 +
  ROAS≥2」筛选，近7天凑不满10条就自动放宽窗口，报告里会注明用的是哪个窗口。

- **报告里有两类数字，别混为一谈**：
  播放量 / GMV / ROAS / 粉丝数 是 FastMoss **实测数据**；
  病毒评分 / 5维诊断 / 产品出镜时机 是 **AI 人工评分**，报告里都会标注。
  人工评分只适合在同一份报告内横向排序，**不要拿两份报告的分数直接比**。

- **「推测完播」不是真实完播率**。FastMoss 拿不到人均观看时长，这个值是用互动深度比、
  评论/播放比、收藏/播放比三个行为指标推算的。

- **如果哪次报告的样式和这次不一样**（比如表格变成横排、字变小挤在一起），
  说明我没用模板生成。直接跟我说「重读模板重新生成」即可。

---

> **注意**：换了新电脑或新工作目录，需要重新发送这个文件夹重新安装。
> FastMoss-MCP 需要在每台电脑的 Claude Code 中单独配置。

---

## ⚠️ 给 Claude：阶段五的输出要求

上面这段是**模板，不是原样复制**。发给用户前：
- 把 `{{安装时查到的余额}}` 换成阶段 3-E 查到的真实数字
- 把目录路径换成真实路径
- 用户从头到尾不会读任何文档，**这段话是他唯一获得的使用说明**，不要省略任何一条提醒
