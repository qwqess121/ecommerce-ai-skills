---
name: amazon-coupon-strategy
description: "Coupon and promotion planning — coupon types, stacking rules, deal timing, redemption optimization"
metadata:
  nexscope:
    category: amazon
---

# Amazon Coupon Strategy

Coupon and promotion planning — coupon types, stacking rules, deal timing, redemption optimization

**Supported platforms:** Amazon (US, UK, DE, CA, JP, AU, and all marketplaces).

Built by [Nexscope](https://www.nexscope.ai/?co-from=skill) — your AI assistant for smarter e-commerce decisions.

## Install

```bash
npx skills add nexscope/amazon-coupon-strategy
```

## Usage

```
Help me with amazon coupon strategy for my e-commerce business.
```

## Capabilities

- Coupon and promotion planning
- coupon types
- stacking rules
- deal timing
- redemption optimization

## How This Skill Works

**Step 1:** Collect information from the user's message — product, platform, current situation, and goals.

**Step 2:** Ask one follow-up with all remaining questions using multiple-choice format. Allow shorthand answers (e.g., "1b 2c 3a").

**Step 3:** Research and analyze using the frameworks and methodology below.

**Step 4:** Deliver structured, actionable output with specific recommendations, not vague advice.

## 🔌 MCP 数据采集（自有工具链）

> 在执行下方工作流之前，优先通过 MCP 工具自动获取数据，减少手动输入。

### 卖家精灵（237a35ba）
- `asin_coupon_trend` → 获取竞品优惠券历史和效果数据（折扣幅度、使用频率、转化提升）
- `asin_detail` → 获取当前售价和竞品价格（计算优惠券折扣基准）

### 领星 ERP
- `search` → 查询产品利润率数据（计算最优折扣幅度，确保优惠券后仍有正利润）

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
