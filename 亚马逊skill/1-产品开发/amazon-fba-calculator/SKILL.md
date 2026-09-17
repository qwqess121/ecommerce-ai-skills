---
name: amazon-fba-calculator
version: 1.0.0
description: Amazon FBA Calculator - Complete fee breakdown and profit analysis
platform: amazon
lang: en
---

# Amazon FBA Calculator (Lite)

Precise FBA fee calculation based on product dimensions and weight.

## Features

- **Size Tier Detection** - Automatic classification
- **FBA Fulfillment Fee** - 2024 rates
- **Monthly Storage Fee** - Standard & Peak season
- **Long-term Storage Fee** - 271+ days aging
- **Referral Fee** - By category
- **Profit Analysis** - Gross/Net margin, ROI
- **Optimization Tips** - Size, weight, inventory

## 🔌 MCP 数据采集（自有工具链）

> 在执行下方工作流之前，优先通过 MCP 工具自动获取数据，减少手动输入。

### 卖家精灵（237a35ba）
- `asin_detail` → 自动获取产品尺寸/重量/售价/类目（输入 ASIN 即可）

### 领星 ERP
- `search` → 采购价和物流费

### 降级方案
如果 MCP 工具不可用，回退到用户手动输入方式。

## Size Tiers (2024)

| Tier | Max Weight | Max Dimensions |
|------|------------|----------------|
| Small Standard | 1 lb | 15"×12"×0.75" |
| Large Standard | 20 lb | 18"×14"×8" |
| Small Oversize | 70 lb | 60"×30" |
| Medium Oversize | 150 lb | L+Girth ≤108" |
| Large Oversize | 150 lb | L+Girth ≤165" |
| Special Oversize | >150 lb | >165" |

## Input

```json
{
  "length": 10.0,
  "width": 6.0,
  "height": 3.0,
  "weight": 1.2,
  "selling_price": 29.99,
  "product_cost": 8.00,
  "inbound_shipping_cost": 1.50,
  "category": "kitchen"
}
```

## Output

- Size tier classification
- Fee breakdown table
- Profit metrics (margin, ROI)
- Optimization suggestions

## Usage

```bash
python3 scripts/calculator.py
python3 scripts/calculator.py '{"length": 10, "width": 6, ...}' --zh
```

---

_Version 1.0.0 | Platform: Amazon | Variant: Lite_

---

**Part of [Nexscope AI](https://www.nexscope.ai/?co-from=skill) — AI tools for e-commerce sellers.**
