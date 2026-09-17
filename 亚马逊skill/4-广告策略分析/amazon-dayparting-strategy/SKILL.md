---
name: amazon-dayparting-strategy
description: "PPC dayparting — bid scheduling by hour/day, peak shopping times, budget optimization by time slot"
metadata:
  nexscope:
    category: amazon
---

# Amazon Dayparting Strategy

PPC dayparting — bid scheduling by hour/day, peak shopping times, budget optimization by time slot

**Supported platforms:** Amazon (US, UK, DE, CA, JP, AU, and all marketplaces).

Built by [Nexscope](https://www.nexscope.ai/?co-from=skill) — your AI assistant for smarter e-commerce decisions.

## Install

```bash
npx skills add nexscope/amazon-dayparting-strategy
```

## Usage

```
Help me with amazon dayparting strategy for my e-commerce business.
```

## Capabilities

- PPC dayparting
- bid scheduling by hour/day
- peak shopping times
- budget optimization by time slot

## 🔌 MCP 数据采集（自有工具链）

> 在执行下方工作流之前，优先通过 MCP 工具自动获取数据，减少手动输入。

### SIF（广告分析）
- `ads_get_campaign_traffic_trend` → 按时间段的流量和转化数据，识别高峰/低谷时段

### sys-amazon-ads MCP
- `ask_report_analyst` → 分时段广告报告，查询特定时间维度的花费、点击、转化数据

### 降级方案
如果 MCP 工具不可用，回退到原有的用户手动输入方式。

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
