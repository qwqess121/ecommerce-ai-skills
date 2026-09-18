---
name: amazon-product-financials
description: "Amazon产品财务测算全链路（销量估算→FBA成本→真实利润分析）。合并自amazon-sales-estimator/amazon-fba-calculator/amazon-profit-analyzer三个skill。硬性规则：真实COGS必须来自领星ERP，缺失时不得用类目估算值替代给出利润结论。适用场景：估算产品销量、算FBA各项费用、做完整P&L分析、判断一个产品是否值得继续投入。"
metadata: {"nexscope":{"emoji":"💰","category":"amazon"}}
---

# Amazon Product Financials 💰

产品财务测算三步走：销量估算 → FBA成本拆解 → 真实利润分析。合并原 amazon-sales-estimator、amazon-fba-calculator、amazon-profit-analyzer 三个skill为一条流水线，因为三者本质是同一个财务判断链条的三个阶段，拆开跑容易漏掉环节。

## ⚠️ 硬性规则（源于真实教训）

2026-09-16 实测：卖家精灵 `market_research` 给出的类目平均"profit"字段是51.76%，但同一批产品用领星ERP `query_order_profit_list_gross_profit` 查出的真实综合毛利率只有11.03%，其中一款产品实际毛利率仅3.48%，接近保本线。**类目估算值和真实成本能差5倍以上。**

因此：
1. **任何"净利润率""毛利率"结论，必须先尝试从领星ERP拉真实COGS**。领星连不上（常见故障：MCP Key失效，报错"MCP Key无效或已失效"）时，明确告知用户"这一步无法给出可信利润结论"，不得用卖家精灵的类目profit字段冒充真实利润率。
2. 卖家精灵的market_research/product_research里的profit字段只能标注为"⚠️类目估算值，非真实成本"，且不能进入最终的Go/No-Go判断。
3. 已有真实历史财务数据的产品（已上架在卖），优先用领星真实数据；全新产品（还没做过）没有历史数据，允许用供应商真实报价（不是类目估算）作为COGS输入。

## 🔌 MCP 数据采集（自有工具链）

### 第一步：销量估算
输入三选一：(A) BSR+站点+价格+类目 (B) ASIN/产品URL (C) 关键词
- 卖家精灵 `asin_detail` → 已上架产品：直接拿真实月销量/月销售额（`units`/`revenue`字段），不需要BSR反推
- 卖家精灵 `asin_sales_trend` → 销量历史趋势
- 卖家精灵 `market_research` → 关键词/类目模式：估算整体市场规模

### 第二步：FBA成本拆解
- 卖家精灵 `asin_detail` → 已上架产品自动获取尺寸/重量/售价/类目，不用手动量
- 领星ERP `erp_listing` → 查真实SKU/MSKU映射
- 按2025年FBA费率表（Small/Large Standard等分级）计算配送费、仓储费、佣金

### 第三步：真实利润分析
- 领星ERP `query_order_profit_list_gross_profit` → **真实毛利率、毛利润、ROI、退货量**，支持按asin/msku/sku/spu/品牌等维度汇总和时间段筛选，这是本skill里权重最高的数据源
- 领星ERP `settings_get_statistics_storage_fee_config` + `settings_get_statistics_refund_config` → 查询MSKU利润前需要的仓储费/退款配置（用`finance_page_list_msku`时的前置调用）
- 领星ERP `ad_campaign_report` → 广告花费数据，用于判断销量对广告的依赖程度
- SIF `ads_get_asin_ad_structure`/`ads_get_asin_ad_traffic_trend` → 广告投放规模的公开信号（不需要账户授权，但精确到花费金额仍需领星或sys-amazon-ads）

### 降级方案
领星ERP不可用时：只输出已确认的收入侧数字（真实销量×真实售价）和平台费用侧数字（FBA配送费+佣金，按公开费率表估算），COGS和净利润率标注"数据不足，待领星连通后补充"，不强行给结论。

## 工作流

### Step 1：销量确认
已上架产品：直接查 `asin_detail`/`product_research` 拿真实月销量和月销售额。
全新产品候选：用BSR区间对照表估算，或用同类竞品的真实销量做类比（不是凭空猜）。

### Step 2：尺寸分级与平台费用
自动判定FBA尺寸分级（Small/Large Standard, Oversize等）→ 查当前费率表算配送费 → 算月度仓储费（标准+旺季）和长期仓储费（超271天）→ 算平台佣金（按类目比例，Automotive通常15%）。

### Step 3：COGS获取（关键节点）
- 已上架产品：领星ERP查真实采购成本
- 全新产品：找供应商要真实报价，不接受"类目均值"作为替代

### Step 4：真实P&L拼装
收入 - FBA配送费 - 佣金 - COGS - 广告花费 - 退货损失 = 真实净利润。
对比：真实毛利率 vs 你们自己过去的真实历史水平（不是跟类目估算比），环比趋势变化（月环比下滑超过30%需要立即排查原因：COGS涨了/费率变了/广告暴增/退货率上升）。

### Step 5：判断与建议
- 净利润率环比骤降（如6.61%→3.48%）→ 标记为P1紧急排查项，不是"继续观察"级别
- 多款产品对比时，用ROI（毛利润/成本投入）而不是单纯毛利率排资源分配优先级——ROI差5倍意味着同样的钱投在不同产品上效率差5倍
- 全新产品：COGS报价出来后，倒推能否达到目标净利润率（建议不低于15-20%），达不到就暂缓，不要带着"以后广告优化了利润会变好"的假设强行推进

## 输出格式

```markdown
## 产品财务测算：{产品名}

### 销量（真实/估算标注清楚）
月销量：{数字} | 数据来源：{真实ASIN数据 / 类目估算}

### FBA成本拆解
配送费：${X} | 仓储费：${X} | 佣金：${X}

### 真实利润（或数据缺口说明）
{有领星数据：真实毛利率/毛利润/ROI/退货量表格}
{无领星数据：明确写"COGS数据缺失，以下净利润结论暂不可用，待领星连通/供应商报价后补充"}

### 环比趋势
{月环比变化，骤降需P1标记}

### 判断
{Go / Hold / No-Go，附具体触发这个判断的数字依据}
```
