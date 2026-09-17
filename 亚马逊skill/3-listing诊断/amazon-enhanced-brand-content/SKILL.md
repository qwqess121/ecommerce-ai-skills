---
name: amazon-enhanced-brand-content
description: "Premium A+ and Brand Story — module design, lifestyle imagery, comparison charts, mobile optimization"
metadata:
  nexscope:
    category: amazon
---

# Amazon Enhanced Brand Content

Premium A+ and Brand Story — module design, lifestyle imagery, comparison charts, mobile optimization

**Supported platforms:** Amazon (US, UK, DE, CA, JP, AU, and all marketplaces).

Built by [Nexscope](https://www.nexscope.ai/?co-from=skill) — your AI assistant for smarter e-commerce decisions.

## Install

```bash
npx skills add nexscope/amazon-enhanced-brand-content
```

## Usage

```
Help me with amazon enhanced brand content for my e-commerce business.
```

## Capabilities

- Premium A+ and Brand Story
- module design
- lifestyle imagery
- comparison charts
- mobile optimization

## 🔌 MCP 数据采集（自有工具链）

> 在执行下方工作流之前，优先通过 MCP 工具自动获取数据，减少手动输入。

### Brightdata
- `scrape` → 抓取竞品 Premium A+ 页面和品牌故事内容，分析模块设计和视觉策略

### Canva（2dc429e6）
- `generate-design` → 根据品牌故事 brief 生成品牌内容设计初稿（品牌 Banner、故事模块、生活方式图等）

### 降级方案
如果 MCP 工具不可用，回退到原有的手动竞品分析 / 外部设计工具方式。

---

## How This Skill Works

**Step 1:** Collect information from the user's message — product, platform, current situation, and goals.

**Step 2:** Ask one follow-up with all remaining questions using multiple-choice format. Allow shorthand answers (e.g., "1b 2c 3a").

**Step 3:** Research and analyze using the frameworks and methodology below.

**Step 4:** Deliver structured, actionable output with specific recommendations, not vague advice.

## Output Format

- Start with a summary of findings
- Include specific data points and benchmarks where available
- Provide prioritized action items
- Mark estimates with ⚠️ when based on incomplete data
- End with concrete next steps

## Other Skills

More e-commerce skills: [nexscope-ai/eCommerce-Skills](https://github.com/nexscope-ai/eCommerce-Skills)

Amazon-specific skills: [nexscope-ai/Amazon-Skills](https://github.com/nexscope-ai/Amazon-Skills)

Built by [Nexscope](https://www.nexscope.ai/?co-from=skill) — your AI assistant for smarter e-commerce decisions.
