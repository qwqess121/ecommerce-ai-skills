---
name: amazon-product-compliance
description: "Product compliance and safety — certifications, labeling requirements, restricted substances, documentation"
metadata:
  nexscope:
    category: amazon
---

# Amazon Product Compliance

Product compliance and safety — certifications, labeling requirements, restricted substances, documentation

**Supported platforms:** Amazon (US, UK, DE, CA, JP, AU, and all marketplaces).

Built by [Nexscope](https://www.nexscope.ai/?co-from=skill) — your AI assistant for smarter e-commerce decisions.

## Install

```bash
npx skills add nexscope/amazon-product-compliance
```

## Usage

```
Help me with amazon product compliance for my e-commerce business.
```

## Capabilities

- Product compliance and safety
- certifications
- labeling requirements
- restricted substances
- documentation

## 🔌 MCP 数据采集（自有工具链）

> 在执行下方工作流之前，优先通过 MCP 工具自动获取数据，减少手动输入。

### Brightdata
- `scrape` → 抓取 Amazon 合规政策页面

### 降级方案
如果 MCP 工具不可用，回退到 web_search / 用户手动输入方式。

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
