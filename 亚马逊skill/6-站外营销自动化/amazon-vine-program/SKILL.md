---
name: amazon-vine-program
description: "Vine review program strategy — enrollment, product selection, timing, review quality maximization"
metadata:
  nexscope:
    category: amazon
---

# Amazon Vine Program

Vine review program strategy — enrollment, product selection, timing, review quality maximization

**Supported platforms:** Amazon (US, UK, DE, CA, JP, AU, and all marketplaces).

Built by [Nexscope](https://www.nexscope.ai/?co-from=skill) — your AI assistant for smarter e-commerce decisions.

## Install

```bash
npx skills add nexscope/amazon-vine-program
```

## Usage

```
Help me with amazon vine program for my e-commerce business.
```

## Capabilities

- Vine review program strategy
- enrollment
- product selection
- timing
- review quality maximization

## How This Skill Works

**Step 1:** Collect information from the user's message — product, platform, current situation, and goals.

**Step 2:** Ask one follow-up with all remaining questions using multiple-choice format. Allow shorthand answers (e.g., "1b 2c 3a").

**Step 3:** Research and analyze using the frameworks and methodology below.

**Step 4:** Deliver structured, actionable output with specific recommendations, not vague advice.

## 🔌 MCP 数据采集（自有工具链）

> 在执行下方工作流之前，优先通过 MCP 工具自动获取数据，减少手动输入。

### 卖家精灵（237a35ba）
- `review` → 获取当前评论数据（评论数量、平均评分、星级分布，判断是否需要 Vine 补评）
- `asin_detail` → 获取产品详情（判断产品阶段：新品/成长期/成熟期，评估 Vine 适用性）
- `asin_sales_trend` → 获取销量趋势（判断 Vine 入场时机，避免在销量下滑期浪费名额）

### 降级方案
如果 MCP 工具不可用，回退到原有的用户手动输入方式。

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
