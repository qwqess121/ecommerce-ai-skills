---
name: amazon-seasonal-planning
description: "Seasonal sales calendar — Prime Day, Black Friday, Q4 prep, inventory planning, promotion scheduling"
metadata:
  nexscope:
    category: amazon
---

# Amazon Seasonal Planning

Seasonal sales calendar — Prime Day, Black Friday, Q4 prep, inventory planning, promotion scheduling

**Supported platforms:** Amazon (US, UK, DE, CA, JP, AU, and all marketplaces).

Built by [Nexscope](https://www.nexscope.ai/?co-from=skill) — your AI assistant for smarter e-commerce decisions.

## Install

```bash
npx skills add nexscope/amazon-seasonal-planning
```

## Usage

```
Help me with amazon seasonal planning for my e-commerce business.
```

## Capabilities

- Seasonal sales calendar
- Prime Day
- Black Friday
- Q4 prep
- inventory planning
- promotion scheduling

## How This Skill Works

**Step 1:** Collect information from the user's message — product, platform, current situation, and goals.

**Step 2:** Ask one follow-up with all remaining questions using multiple-choice format. Allow shorthand answers (e.g., "1b 2c 3a").

**Step 3:** Research and analyze using the frameworks and methodology below.

**Step 4:** Deliver structured, actionable output with specific recommendations, not vague advice.

## 🔌 MCP 数据采集（自有工具链）

> 在执行下方工作流之前，优先通过 MCP 工具自动获取数据，减少手动输入。

### 卖家精灵（237a35ba）
- `google_trend` → 获取 Google 搜索趋势（验证产品/关键词的季节性波动规律）
- `asin_sales_trend` → 获取月度销量趋势（识别历史销售高峰和低谷月份）
- `market_research` → 获取类目整体数据（分析类目级别的季节性特征和竞争周期）

### 领星 ERP
- `search` → 查询历史销量和库存数据（用于备货量计算：日均销量 x 备货天数 + 安全库存）

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
