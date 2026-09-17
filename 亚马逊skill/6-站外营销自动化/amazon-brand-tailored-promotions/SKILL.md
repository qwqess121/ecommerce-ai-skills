---
name: amazon-brand-tailored-promotions
description: "Brand Tailored Promotions — audience targeting, discount tiers, customer segmentation, repeat purchase incentives"
metadata:
  nexscope:
    category: amazon
---

# Amazon Brand Tailored Promotions

Brand Tailored Promotions — audience targeting, discount tiers, customer segmentation, repeat purchase incentives

**Supported platforms:** Amazon (US, UK, DE, CA, JP, AU, and all marketplaces).

Built by [Nexscope](https://www.nexscope.ai/?co-from=skill) — your AI assistant for smarter e-commerce decisions.

## Install

```bash
npx skills add nexscope/amazon-brand-tailored-promotions
```

## Usage

```
Help me with amazon brand tailored promotions for my e-commerce business.
```

## Capabilities

- Brand Tailored Promotions
- audience targeting
- discount tiers
- customer segmentation
- repeat purchase incentives

## How This Skill Works

**Step 1:** Collect information from the user's message — product, platform, current situation, and goals.

**Step 2:** Ask one follow-up with all remaining questions using multiple-choice format. Allow shorthand answers (e.g., "1b 2c 3a").

**Step 3:** Research and analyze using the frameworks and methodology below.

**Step 4:** Deliver structured, actionable output with specific recommendations, not vague advice.

## 🔌 MCP 数据采集（自有工具链）

> 在执行下方工作流之前，优先通过 MCP 工具自动获取数据，减少手动输入。

### 领星 ERP
- `search` → 查询复购率和客户分层数据（Brand Tailored Promotions 的受众细分依据）

### sys-amazon-ads MCP
- `ask_report_analyst` → 拉取广告受众数据（受众画像、触达人群特征，辅助精准定向促销）

### 卖家精灵（237a35ba）
- `asin_sales_trend` → 获取销售趋势数据（识别促销最佳时机、评估历史促销效果）

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
