# 亚马逊报告 Skill（模块 1–5）

本文件夹是亚马逊分析报告的完整 skill，产出五份模块报告，并拼装成单页在线报告 `report.html`。每个模块自己的输出格式固定在其目录下的 `references/` 中（如 `1-产品开发/references/`）。

## 目录

```
亚马逊skill/
├── 1-产品开发/
│   ├── SKILL.md              模块入口与资料清单
│   ├── M1-ORCHESTRATOR.md    流程（取数、判定、写报告）
│   └── references/           输出格式强制规定、格式检查清单、报告格式规范、章节标题（31 条）
├── 2-竞品销售策略分析/
│   ├── SKILL.md / M2-ORCHESTRATOR.md / references/（章节标题 29 条）
│   └── amazon-review-insights/  图片与 listing 抓取脚本（M2、M3 调用）
├── 3-listing诊断/
│   ├── SKILL.md / M3-ORCHESTRATOR.md / references/（章节标题 22 条）
├── 4-广告策略分析/
│   ├── SKILL.md / M4-ORCHESTRATOR.md / references/（章节标题 23 条）
├── 5-内容生产工具/
│   ├── SKILL.md / M5-ORCHESTRATOR.md / references/（章节标题 55 条）
├── 工具/                     判定与计算脚本：竞品门槛、选类目Top15、推荐头号词、八维评分、差评分类
└── 共享规则/
    ├── 取数/                 取数清单.json、取数手册.md、差评分类规则.md、竞品门槛词表.json
    ├── 参考结构/             参考标题_Xk3D.json、参考标题_Vy3j.json（完整章节，供各模块 references 复制）
    ├── 报告格式/             输出格式强制规定.md、格式检查清单.md、报告格式规范.md
    ├── 在线报告生成/          convert.js、build.js、template.html（生成 report.html）
    ├── 竞品判定标准.md、深度分析层.md、交叉验证规则.md、图片标准.md
```

## 依赖

- Node.js 18 以上（在线报告、抓取脚本）。
- Python 3（`工具/` 脚本，用 `python -X utf8` 运行）。
- Playwright（抓取脚本）：`cd 2-竞品销售策略分析/amazon-review-insights && npm install && npx playwright install chromium`。
- 在线报告生成：`cd 共享规则/在线报告生成 && npm install`。
- MCP：卖家精灵、Sif、领星。

## 只跑一个模块

每个模块的编排器都能单独执行。输出的 Markdown 放进报告目录后，同样可以单独渲染：

```bash
cd 共享规则/在线报告生成
node convert.js "<报告目录>"
node build.js "<报告目录>"
```

报告目录里只有 `模块2-*.md` 时，产物就只有模块 2 一页。模块之间的依赖见下文各模块说明。

## 运行一次完整报告

1. 选定本品 ASIN，建立数据目录（放在本文件夹之外，如 `D:\数据\<ASIN>\`）和报告目录（如 `D:\报告\<ASIN>\`）。
2. 按顺序执行模块流程：
   - 模块 1：`1-产品开发/M1-ORCHESTRATOR.md`。
   - 模块 2：`2-竞品销售策略分析/M2-ORCHESTRATOR.md`（依赖模块 1 的判定结果）。
   - 模块 3：`3-listing诊断/M3-ORCHESTRATOR.md`（用 `工具/八维评分.py` 打分）。
   - 模块 4：`4-广告策略分析/M4-ORCHESTRATOR.md`。
   - 模块 5：`5-内容生产工具/M5-ORCHESTRATOR.md`（依赖模块 1–4 的结果）。
3. 在报告目录写 `overview.json`（导航与品牌信息）和 `overview.html`（总览正文）。
4. 拼装：
   ```bash
   cd 共享规则/在线报告生成
   node convert.js "<报告目录>"
   node build.js "<报告目录>"
   ```
   产物：`<报告目录>/report.html`。
5. 交付前按各模块目录下 `references/格式检查清单.md` 核对，并按 `共享规则/交叉验证规则.md` 6.3.4 执行 grep 检查。

## 格式

- 每个模块的输出格式固定在其目录下的 `references/输出格式强制规定.md`，检查项在 `references/格式检查清单.md`，呈现规范在 `references/报告格式规范.md`。
- 章节标题在各模块的 `references/章节标题.json`（取自 `共享规则/参考结构/参考标题_Xk3D.json`）。

## 已知限制

- `竞品门槛.py` 的成功路径（分页直到提前停止）需要足够多的候选池分页，尚未在完整数据上验证。
- `推荐头号词.py` 可能选出泛品类词，需要人工复核。
- `review` 接口每次最多返回 20 条，样本量必须写进报告。
- 总览页的 `overview.json` 与 `overview.html` 目前需要手写，尚未自动生成。
