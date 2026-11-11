# 字段填写映射（2026-11-10 更新版）

> 本文件基于工作簿 `Open to B - 11.10数据已重新填充.xlsx` 逐列校对，并叠加实测修正。
> **11.10 变更**：亚马逊销售表新增 DC「到货时间（发货+40天）」，DC 之后所有列号比 11.9 v8 偏移 +1（库龄从 DH 起，AWD 从 DX 起）。
> 优先级：**工作簿内公式 > 覆盖项 > 逐列映射 > `字段数据来源` sheet**。
> 颜色不在本表：白色=不抓（标识/公式/手填），彩色=由接口写入，以工作簿单元格填充色为准。

## 覆盖项（2026-11-10 核对，基于 11.10 表格列布局）

> **注意**：11.10 表格在亚马逊销售表 DC 列新增了「到货时间（发货时间+40天）」，导致 DC 之后所有列号比 11.9 v8 偏移 +1。

| 表 | 列 | 正确规则 | 说明 |
|---|---|---|---|
| 亚马逊销售 | DB 发货时间 | `=IF(DA<>"",DATE(2026,11,9),"")` | DA 有值时填基准日（2026-11-09） |
| 亚马逊销售 | DC 到货时间（发货+40天） | 空（11.10 未填） | 11.10 新增列头，但原表单元格为空 |
| 亚马逊销售 | DD 发货数量 | `=IF(DA<>"",(7-DA)*(CG/30),"")` | 补满 7 天周期的发货量 |
| 亚马逊销售 | DE 采购量（15天） | `=IF(AND(DA<>"",DB<>"",DD<>""),CG/30*15,"")` | **关键**：DA/DB/DD 均有值才生效 |
| 亚马逊销售 | DF 到货时间 | `=IF(DB<>"",DB+7,"")` | 发货时间 +7 天（11.10 原表 155 行为 +7） |
| 亚马逊销售 | DG 采购时间 | `=IF(DB<>"",DB+IF(CZ>=-24,CZ+25,45),"")` | 发货时间 + (CZ+25)；CZ < -24 时 +45（11.10 原表 156 行全部吻合） |
| 亚马逊销售 | DH~EA 库龄/AWD | 同 v8 的 DG~DZ，列号 +1 | 因 DC 新增列整体偏移 |
| 亚马逊销售 | CS FBA可售 | 数值 = `afn_fulfillable_quantity`（FBA 可售件数） | 字段数据来源写 available_days，文档有误 |
| Tiktok 销售 | AD 发货时间 | `=IF(AC<>"",DATE(2026,11,9),"")` | AC 有值时填基准日（2026-11-09） |
| Tiktok 销售 | AF 采购量（15天） | `=IF(AND(AC<>"",AD<>"",AE<>""),L/30*15,"")` | **关键**：AC/AD/AE 均有值才生效（与亚马逊统一） |
| Tiktok 销售 | AG 到货时间 | `=IF(AD<>"",AD+7,"")` | 发货时间 +7 天（11.10 原表全部为 +7） |
| Tiktok 销售 | AH 采购时间 | `=IF(AD<>"",AD+IF(AC>=-24,AC+25,45),"")` | 发货时间 + (AC+25)；AC < -24 时 +45（11.10 原表 201 行全部吻合） |
| 产品管理 - 库存 | BO 亚马逊采购量 | 固定值/手填（如 50） | 11.10 原表为手填固定值 |
| 产品管理 - 库存 | BP 亚马逊采购时间 | 固定值/手填（如 2026-12-24） | 11.10 原表为手填固定日期 |
| 产品管理 - 库存 | BQ Tiktok采购量 | 固定值/手填（如 100） | 11.10 原表为手填固定值 |
| 产品管理 - 库存 | BR Tiktok采购时间 | 固定值/手填（如 2026-12-24） | 11.10 原表为手填固定日期 |
| 产品管理 - 库存 | BS 供应链亚马逊采购量 | `=BM-BO` | 本地仓+海外仓总库存 减去 亚马逊采购量 |
| 产品管理 - 库存 | BT 供应链采购时间 | 固定值/手填（如 2026-12-24） | 11.10 原表为手填固定日期 |
| 产品管理 - 库存 | BU 供应链Tiktok采购量 | `=BM-BQ` | 本地仓+海外仓总库存 减去 TK 采购量 |
| 产品管理 - 库存 | BV 供应链采购时间 | 固定值/手填（如 2026-12-24） | 11.10 原表为手填固定日期 |
| 产品管理 - 库存 | U 单价 | 手工填写（采购单详情/供应链成本） | 为空时 T/V/W/X/AC/AE 为 0 |
| Tiktok 销售 | Q/AS | **币种 USD** | 与 CNY 不可直接相加 |
| 亚马逊销售 | U/Z | **币种 CNY** | 与 USD 不可直接相加 |

## 产品管理 - 库存

| 列 | 表头 | 填写方式 | 接口 (MCP/OpenAPI) | 返回字段 / 公式 | 备注 |
|---|---|---|---|---|---|
| A | SKU | 标识列，不抓 | — | — |  |
| B | 品名 | 标识列，不抓 | — | — |  |
| C | 图片 | 标识列，不抓 | — | — |  |
| D | 创建时间 | API写入 | products_list | create_time | 快照 |
| E | 创建人 | API写入 | products_list | creator | 快照 |
| F | 更新时间 | API写入 | products_list | update_time | 快照 |
| G | 产品类型 | API写入 | products_list | product_type（1普通/2组合） | 快照 |
| H | 状态 | API写入 | products_list | status | 快照 |
| I | 品牌 | API写入 | products_list | brand_name | 快照 |
| J | 产品标签 | API写入 | products_list | global_tags[].tagName | 快照 |
| K | 开发人 | API写入 | products_list | developer | 快照 |
| L | 开发日期 | API写入 | products_list | develop_date（为空用创建日期） | 快照 |
| M | 产品负责人 | API写入 | products_list | product_leader | 快照 |
| N | 采购员 | API写入 | products_list | purchaser | 快照 |
| O | 采购交期 | API写入 | products_list | purchase_cycle | 快照 |
| P | 采购成本(CNY) | API写入 | products_list | cg_price（CNY） | 快照 |
| Q | 采购成本($) | 公式（工作簿实际） | （公式） | =P3/6.8 |  |
| R | 供应商名称 | API写入 | products_list | supplier_name | 快照 |
| S | 最小采购量 | API写入 | products_list | quote_step_prices[0].moq（报价阶梯第一档） | 快照 |
| T | 采购金额 | 公式（工作簿实际） | （公式） | =U3*Y3 | 按产品ID查询采购记录后汇总所有在途单据金额；字段数据来源写 products_purchase_history，与工作簿公式不符，以公式为准 |
| U | 单价（采购单详情/供应链成本） | 手工填写（白色） | （不抓取） | — | 采购单详情/供应链成本；由用户从领星采购单详情手工填入，不自动填。为空时 T/V/W/X/AC/AE 公式为0，也导致发货金额为0；产品详情里的"包含产品成本/定位供应链成本"字段 |
| V | 到货金额 | 公式（工作簿实际） | （公式） | =AA3*U3 | 所有已到货单据金额汇总；字段数据来源写 products_purchase_history，与工作簿公式不符，以公式为准 |
| W | 待到货金额 | 公式（工作簿实际） | （公式） | =Z3*U3 | 所有在途中单据的金额汇总；字段数据来源写 products_purchase_history，与工作簿公式不符，以公式为准 |
| X | 已付金额 | 公式（工作簿实际） | （公式） | =V3 | 已付款金额汇总；字段数据来源写 products_purchase_history，与工作簿公式不符，以公式为准 |
| Y | 采购量 | API写入 | products_purchase_history | purchase_quantity | 所有采购单累计采购量 |
| Z | 待到货量 | API写入 | products_purchase_history | pending_quantity | 所有在途中的采购量 |
| AA | 到货量 | API写入 | products_purchase_history | arrived_quantity | 已入库到货量汇总 |
| AB | 总的加工/拆分数量（采购量-取单据状态为待配货+待完成+已完成总和） | 直连OpenAPI，整单聚合 | /erp/sc/routing/inventoryReceipt/StorageProcess/getOrderLists (type=1,2) | product_list[].sku / quantity, status, ware_house_name | 状态0/1/2之和；仓=WH-US-SDG-YU-OEM-1、WH-US-BRE-AM-OEM-2；2026全年；整单数量求和（不是按SKU数量）。字段数据来源原写的 warehouse_order_plan_list 只有30条，不可用。脚本 pull_processing_orders.py |
| AC | 海外仓采购金额 | 公式（工作簿实际） | （公式） | =AB3*U3 | 总加工/拆分数量 × 单价；字段数据来源写 warehouse_order_plan_list + warehouse_outbound_order_list，与工作簿公式不符，以公式为准 |
| AD | 已完成加工/拆分数量（采购量-取单据状态为已完成） | 直连OpenAPI，整单聚合 | /erp/sc/routing/inventoryReceipt/StorageProcess/getOrderLists (type=1,2) | product_list[].sku / quantity, status | 仅状态=2；口径同 AB；加工单状态为"已完成"的数量 |
| AE | 海外仓已付金额 | 公式（工作簿实际） | （公式） | =AD3*U3 | 已完成加工/拆分数量 × 单价；字段数据来源写 warehouse_order_plan_list + warehouse_outbound_order_list，与工作簿公式不符，以公式为准 |
| AF | 国内仓+海外仓总采购量 | 公式（工作簿实际） | （公式） | =Y3+AB3 |  |
| AG | 国内仓+海外仓总采购金额 | 公式（工作簿实际） | （公式） | =AF3*U3 |  |
| AH | 国内仓+海外仓已付款金额 | 公式（工作簿实际） | （公式） | =X3+AE3 |  |
| AI | 国内仓+海外仓未付款金额 | 公式（工作簿实际） | （公式） | =AG3-AH3 |  |
| AJ | 采购To C利润 | 公式（工作簿实际） | （公式） | =AF3*Q3-AG3 |  |
| AK | 最大可加工量 | API写入 | inventory_detail_list | max_process_num | 可用于加工的最大数量 |
| AL | 可用量 | API写入 | inventory_detail_list | good_num | 可用库存数量 |
| AM | 可用锁定量 | API写入 | inventory_detail_list | good_lock_num | 已分配但未出库 |
| AN | 待检待上架量 | API写入 | inventory_detail_list | qc_num | 待质检/上架数量 |
| AO | 待到货量 | API写入 | inventory_detail_list | pending_num | 待到货数量 |
| AP | 期望可用量 | API写入 | inventory_detail_list | expect_valid_num | 期望可用数量 |
| AQ | 期望待到货量 | API写入 | inventory_detail_list | expect_pending_num | 期望待到货数量 |
| AR | 调拨在途 | API写入 | inventory_detail_list | transit_num | 调拨中数量 |
| AS | 安全库存量 | API写入 | inventory_detail_list | storage_safe_num | 安全库存设定值 |
| AT | 本地仓总库存 | 公式（工作簿实际） | （公式） | =AL3+AM3+AN3+AO3+AR3 |  |
| AU | 0-15天库龄 | API写入 | inventory_detail_list | section1 | 分段1库龄 |
| AV | 16-30天库龄 | API写入 | inventory_detail_list | section2 | 分段2库龄 |
| AW | 31-90天库龄 | API写入 | inventory_detail_list | section3 | 分段3库龄 |
| AX | 91天以上库龄 | API写入 | inventory_detail_list | section4 | 分段4库龄 |
| AY | 最大可加工量 | API写入 | inventory_detail_list (wid_list=海外仓ID) | max_process_num | 可用于加工的最大数量 |
| AZ | 可用量 | API写入 | inventory_detail_list (wid_list=海外仓ID) | good_num | 可用库存数量 |
| BA | 可用锁定量 | API写入 | inventory_detail_list (wid_list=海外仓ID) | good_lock_num | 已分配但未出库 |
| BB | 待检待上架量 | API写入 | inventory_detail_list (wid_list=海外仓ID) | qc_num | 待质检/上架数量 |
| BC | 待到货量 | API写入 | inventory_detail_list (wid_list=海外仓ID) | pending_num | 待到货数量 |
| BD | 期望可用量 | API写入 | inventory_detail_list (wid_list=海外仓ID) | expect_valid_num | 期望可用数量 |
| BE | 期望待到货量 | API写入 | inventory_detail_list (wid_list=海外仓ID) | expect_pending_num | 期望待到货数量 |
| BF | 调拨在途 | API写入 | inventory_detail_list (wid_list=海外仓ID) | transit_num | 调拨中数量 |
| BG | 安全库存量 | API写入 | inventory_detail_list (wid_list=海外仓ID) | storage_safe_num | 安全库存设定值 |
| BH | 海外仓总库存 | 公式（工作簿实际） | （公式） | =AZ3+BA3+BB3+BC3+BF3 |  |
| BI | 0-15天库龄 | API写入 | inventory_detail_list (wid_list=海外仓ID) | section1 | 分段1库龄 |
| BJ | 16-30天库龄 | API写入 | inventory_detail_list (wid_list=海外仓ID) | section2 | 分段2库龄 |
| BK | 31-90天库龄 | API写入 | inventory_detail_list (wid_list=海外仓ID) | section3 | 分段3库龄 |
| BL | 91天以上库龄 | API写入 | inventory_detail_list (wid_list=海外仓ID) | section4 | 分段4库龄 |
| BM | 本地仓+海外仓总库存 | 公式（工作簿实际） | （公式） | =BH3+AT3 |  |
| BN | 总货值 | 公式（工作簿实际） | （公式） | =BM3*U3 |  |
| BO | 亚马逊采购量 | 固定值/手填 | — | （当前为固定值，如 50） | 按 SKU 对应亚马逊采购量；11.10 原表为手填固定值 |
| BP | 亚马逊采购时间 | 固定值/手填 | — | （当前为固定日期，如 2026-12-24） | 亚马逊采购时间；11.10 原表为手填固定日期 |
| BQ | Tiktok采购量 | 固定值/手填 | — | （当前为固定值，如 100） | TK 采购量；11.10 原表为手填固定值 |
| BR | Tiktok采购时间 | 固定值/手填 | — | （当前为固定日期，如 2026-12-24） | TK 采购时间；11.10 原表为手填固定日期 |
| BS | 供应链亚马逊采购量 | 公式（工作簿实际） | （公式） | =BM3-BO3 | 本地仓+海外仓总库存 减去 亚马逊采购量 |
| BT | 供应链采购时间 | 固定值/手填 | — | （当前为固定日期，如 2026-12-24） | 供应链采购时间；11.10 原表为手填固定日期 |
| BU | 供应链Tiktok采购量 | 公式（工作簿实际） | （公式） | =BM3-BQ3 | 本地仓+海外仓总库存 减去 TK 采购量 |
| BV | 供应链采购时间 | 固定值/手填 | — | （当前为固定日期，如 2026-12-24） | 供应链采购时间；11.10 原表为手填固定日期 |

## 亚马逊销售

| 列 | 表头 | 填写方式 | 接口 (MCP/OpenAPI) | 返回字段 / 公式 | 备注 |
|---|---|---|---|---|---|
| A | SKU | 标识列，不抓 | — | — |  |
| B | 品名 | 标识列，不抓 | — | — |  |
| C | 店铺 | 标识列，不抓 | — | — |  |
| D | 国家 | 标识列，不抓 | — | — |  |
| E | 自动标签 | 留空 | （无源） | auto_tags 全账号为空 | 账号未配自动标签规则，不要用其它标签冒充；自动打标签 |
| F | 产品标签 | API写入 + 兜底 | products_list（global_tags） | global_tags[].tagName | product_tags 全账号为空；用产品库 global_tags 兜底（ruleContentList 为空的是手动标签）；手动产品标签 |
| G | 负责人 | API写入 | query_product_performance_asin_lists | principal_names | ASIN负责人 |
| H | 创建时间 | API写入 | query_product_performance_asin_lists | product_create_time | 产品创建时间 |
| I | 品牌 | API写入 | query_product_performance_asin_lists | brands | 品牌名称 |
| J | 采购成本 | API写入 | query_product_performance_asin_lists | cg_price | 采购成本(CNY) |
| K | 销量 | API写入 | query_product_performance_asin_lists | volume | 选定日期销量 |
| L | 2026年销量 | API写入 | query_product_performance_asin_lists | volume | 2026年累计窗口(2026-01-01~昨日)；选定日期销量 |
| M | 销售额 | API写入 | query_product_performance_asin_lists | amount | 选定日期销售额 |
| N | 2026年销售额 | API写入 | query_product_performance_asin_lists | amount | 2026年累计窗口(2026-01-01~昨日)；选定日期销售额 |
| O | 订单量 | API写入 | query_product_performance_asin_lists | order_items | 订单量 |
| P | 销量环比 | API写入 | query_product_performance_asin_lists | volume_chain_ratio | 销量环比 |
| Q | 销售额环比 | API写入 | query_product_performance_asin_lists | amount_chain_ratio | 销售额环比 |
| R | 销量同比 | API写入 | query_product_performance_asin_lists | volume_yoy_ratio | 销量同比 |
| S | 销售额同比 | API写入 | query_product_performance_asin_lists | amount_yoy_ratio | 销售额同比 |
| T | 净销售额 | API写入 | query_product_performance_asin_lists | net_amount | 扣掉折扣后的净销售额 |
| U | 2026年净销售额 | API写入 | query_product_performance_asin_lists | net_amount | 2026年累计窗口(2026-01-01~昨日)；扣掉折扣后的净销售额 |
| V | 2026年净销售额同比 | API写入 | query_product_performance_asin_lists | amount（2026年窗口，同比口径） | 字段数据来源未列出，待核实同比口径 |
| W | 销售均价 | API写入 | query_product_performance_asin_lists | avg_custom_price | 销售均价 |
| X | 退款率 | API写入 | query_product_performance_asin_lists | return_rate | 字段数据来源写 refund_rate 实测取空，正确为 return_rate；退款率 |
| Y | 结算毛利润 | API写入 | query_product_performance_asin_lists | gross_profit | 结算口径毛利润 |
| Z | 2026年结算毛利润 | API写入 | query_product_performance_asin_lists | gross_profit | 2026年累计窗口(2026-01-01~昨日)；结算口径毛利润 |
| AA | 订单毛利润 | API写入 | query_product_performance_asin_lists | predict_gross_profit | 按订单预估毛利润 |
| AB | 2026年订单毛利润 | API写入 | query_product_performance_asin_lists | predict_gross_profit | 2026年累计窗口(2026-01-01~昨日)；按订单预估毛利润 |
| AC | 结算毛利率 | API写入 | query_product_performance_asin_lists | gross_margin | 结算毛利率 |
| AD | 订单毛利率 | API写入 | query_product_performance_asin_lists | predict_gross_margin | 订单预估毛利率 |
| AE | ROI | API写入 | query_product_performance_asin_lists | roi | 投入产出比 |
| AF | FBA可售天数预估 | API写入 | query_product_performance_asin_lists | available_days | FBA可售天数 |
| AG | 海外仓可用 | API写入 | query_product_performance_asin_lists | oversea_quantity | 海外仓可用库存 |
| AH | 本地可用 | API写入 | query_product_performance_asin_lists | local_quantity | 本地仓可用库存 |
| AI | 采购量 | API写入 | query_product_performance_asin_lists | purchase_num | 备货/采购量 |
| AJ | 存销比 | API写入 | query_product_performance_asin_lists | inventory_sales_ratio | 库存销售比 |
| AK | 月库销比 | API写入 | query_product_performance_asin_lists | month_stock_sales_ratio | 月库销比 |
| AL | 可用货值 | API写入 | query_product_performance_asin_lists | whs_value | 可用库存货值 |
| AM | 断货时间 | 公式 | （公式） | =IFERROR(IF(AND(ISNUMBER(AF),AF>0),TODAY()+ROUND(AF,0),""),"") | out_stock_date 全为空，改用 今天 + FBA可售天数；预估断货时间 |
| AN | 展示 | API写入 | query_product_performance_asin_lists | impressions | 广告展示 |
| AO | 点击 | API写入 | query_product_performance_asin_lists | clicks | 广告点击 |
| AP | 广告花费 | API写入 | query_product_performance_asin_lists | spend | 广告总花费 |
| AQ | SP广告费 | API写入 | query_product_performance_asin_lists | ads_sp_cost | SP广告费 |
| AR | SB广告费 | API写入 | query_product_performance_asin_lists | shared_ads_sb_cost | SB广告费 |
| AS | SBV广告费 | API写入 | query_product_performance_asin_lists | shared_ads_sbv_cost | SBV广告费 |
| AT | SD广告费 | API写入 | query_product_performance_asin_lists | ads_sd_cost | SD广告费 |
| AU | ST广告费 | API写入 | query_product_performance_asin_lists | shared_ads_sar_cost | ST广告费 (SAR) |
| AV | Live广告费 | API写入 | query_product_performance_asin_lists | shared_ads_al_cost | Live广告费 |
| AW | 广告销售额 | API写入 | query_product_performance_asin_lists | ad_sales_amount | 广告销售额 |
| AX | SP广告销售额 | API写入 | query_product_performance_asin_lists | ads_sp_sales | SP广告销售额 |
| AY | SB广告销售额 | API写入 | query_product_performance_asin_lists | shared_ads_sb_sales | SB广告销售额 |
| AZ | SBV广告销售额 | API写入 | query_product_performance_asin_lists | shared_ads_sbv_sales | SBV广告销售额 |
| BA | SD广告销售额 | API写入 | query_product_performance_asin_lists | ads_sd_sales | SD广告销售额 |
| BB | 广告销量 | API写入 | query_product_performance_asin_lists | ads_sales_volume_quantity | 广告销量 |
| BC | SP广告销量 | API写入 | query_product_performance_asin_lists | ads_sp_sales_volume_quantity | SP广告销量 |
| BD | SB广告销量 | API写入 | query_product_performance_asin_lists | shared_ads_sb_sales_volume_quantity | SB广告销量 |
| BE | SBV广告销量 | API写入 | query_product_performance_asin_lists | shared_ads_sbv_sales_volume_quantity | SBV广告销量 |
| BF | SD广告销量 | API写入 | query_product_performance_asin_lists | ads_sd_sales_volume_quantity | SD广告销量 |
| BG | 广告订单占比 | API写入 | query_product_performance_asin_lists | adv_rate | 广告订单占比 |
| BH | 直接成交销售额 | API写入 | query_product_performance_asin_lists | ad_direct_sales_amount | 广告直接成交销售额 |
| BI | 直接成交订单量 | API写入 | query_product_performance_asin_lists | ad_direct_order_quantity | 广告直接成交订单量 |
| BJ | CTR | API写入 | query_product_performance_asin_lists | ctr | 广告点击率 |
| BK | 广告CVR | API写入 | query_product_performance_asin_lists | ad_cvr | 广告转化率 |
| BL | CPC | API写入 | query_product_performance_asin_lists | cpc | 单次点击成本 |
| BM | CPM | API写入 | query_product_performance_asin_lists | cpm | 千次展示成本 |
| BN | ROAS | API写入 | query_product_performance_asin_lists | roas | 广告投入回报率 |
| BO | ACOS | API写入 | query_product_performance_asin_lists | acos | 广告销售成本比 |
| BP | TACOS | API写入 | query_product_performance_asin_lists | tacos | 总广告销售成本比 |
| BQ | ACoAS | API写入 | query_product_performance_asin_lists | acoas | ACoAS |
| BR | ASoAS | API写入 | query_product_performance_asin_lists | asoas | ASoAS |
| BS | CPO | 计算 | （由 spend、ad_direct_order_quantity 计算） | spend / ad_direct_order_quantity | CPO = 广告花费 / 广告直接订单量；接口自带 cpo 字段一致率仅 2%，不用；单订单广告成本 |
| BT | CPU | 计算 | （由 spend、volume 计算） | spend / volume | CPU = 广告花费 / 销量；接口自带 cpu 字段一致率仅 68%，不用；单销量广告成本 |
| BU | 售价(总价) | API写入 | erp_listing | landed_price | 含税到岸价 |
| BV | 运费 | API写入 | erp_listing | shipping_price | 运费 |
| BW | 价格 | API写入 | erp_listing | price | 售价 |
| BX | 优惠价 | API写入 | erp_listing | promotion_price | 促销价 |
| BY | List Price | API写入 | erp_listing | list_price | Amazon List Price |
| BZ | 划线价 | API写入 | erp_listing | reference_price | 划线价 |
| CA | 划线价类型 | API写入 | erp_listing | reference_price_type | 划线价类型 |
| CB | 预估FBA费（API） | API写入 | erp_listing | estimated_fba_fee（为空回退 fba_fee） | 字段数据来源写 fba_fee，实测正确字段见左；API预估的FBA费 |
| CC | 预估FBA费（报表） | API写入 | erp_listing | report_fba_fee | 报表的FBA费 |
| CD | 平台费率 | API写入 | erp_listing | platform_fee_rate（为空回退 estimated_referral_fee_rate，值形如 "12.0%" 需除100） | 字段数据来源写 estimated_referral_fee_rate，实测不稳；佣金费率 |
| CE | 平台费 | API写入 | erp_listing | platform_fee（为空回退 estimated_referral_fee） | 佣金 |
| CF | 昨日销量 | API写入 | erp_listing | yesterday_volume | 昨日销量 |
| CG | 30日销量 | API写入 | erp_listing | thirty_volume | 30日销量 |
| CH | 昨日销售额 | API写入 | erp_listing | yesterday_amount | 昨日销售额 |
| CI | 30日销售额 | API写入 | erp_listing | thirty_amount | 30日销售额 |
| CJ | 昨日广告费 | API写入 | erp_listing | yesterday_ad_cost | 昨日广告费 |
| CK | 30日广告费 | API写入 | erp_listing | thirty_ad_cost | 30日广告费 |
| CL | 大类排名 | API写入 | erp_listing | seller_rank（category_rank 为 dict；small_rank 为 JSON 字符串需 json.loads） | 字段数据来源写 rank，实测无此字段；大类排名 |
| CM | 大类名称 | API写入 | erp_listing | category_name | 大类名称 |
| CN | 小类1 | API写入 | erp_listing | small_category_name | 小类名称 |
| CO | Rating总数 | API写入 | erp_listing | reviews_num（review_num 全为 null） | 评论总数 |
| CP | 评分 | API写入 | erp_listing | stars（star_score 全为 null） | 评分 |
| CQ | 首单时间 | API写入 | erp_listing | first_order_time | 首单时间 |
| CR | FBA可用库存 | API写入 | get_fba_stock_list | available_inventory | FBA可用库存总量 |
| CS | FBA可售 | API写入 | get_fba_stock_list | afn_fulfillable_quantity | FBA可售数量 |
| CT | FBA待调仓 | API写入 | get_fba_stock_list | reserved_fc_transfers | FBA待调仓 |
| CU | FBA实际在途 | API写入 | get_fba_stock_list | afn_inbound_shipped_quantity | FBA实际在途 |
| CV | FBA入库中 | API写入 | get_fba_stock_list | afn_inbound_receiving_quantity | FBA入库中 |
| CW | FBA总库存 | 公式（工作簿实际） | （公式） | =CS3+CT3+CU3+CV3 |  |
| CX | 70天库存周期差值 | 公式（工作簿实际） | （公式） | =CW3-(CG3/30)*70 |  |
| CY | FBA总库存预估可售天数 | 公式（工作簿实际） | （公式） | =IF(CG3>0,CW3/CG3*30,"") |  |
| CZ | 在途+FBA可售取70天 | 公式（工作簿实际） | （公式） | =IF(CY3<>"",ROUND(CY3-70,0),"") |  |
| DA | 在途+FBA可售取70天(每周三抓取） | 公式（工作簿实际） | （公式） | =IF(AND(CZ3<>"",CZ3<=7),CZ3,"") |  |
| DB | 发货时间 | 公式（工作簿实际） | （公式） | =IF(DA3<>"",DATE(2026,11,9),"") | DA 有值时填基准日（2026-11-09） |
| DC | 到货时间（发货时间+40天） | 空（11.10 未填） | — | （原表为空） | 11.10 新增列头，但原表未填公式 |
| DD | 发货数量(7天发一次） | 公式（工作簿实际） | （公式） | =IF(DA3<>"",(7-DA3)*(CG3/30),"") | 补满 7 天周期的发货量 |
| DE | 采购量（采购频率15天） | 公式（工作簿实际） | （公式） | =IF(AND(DA3<>"",DB3<>"",DD3<>""),CG3/30*15,"") | **DA/DB/DD 均有值才生效**；15 天采购周期 |
| DF | 到货时间 | 公式 | （公式） | =IF(DB3<>"",DB3+7,"") | 发货时间 +7 天 |
| DG | 采购时间 | 公式 | （公式） | =IF(DB3<>"",DB3+IF(CZ3>=-24,CZ3+25,45),"") | 发货时间 + (CZ+25)；CZ < -24 时 +45 |
| DH | 30天内库龄 | API写入 | get_fba_stock_list | inv_age_0_30 | 30天内库龄数量 |
| DI | 30天内库龄(成本) | API写入 | get_fba_stock_list | inv_age_0_30_cost | 30天内库龄成本 |
| DJ | 31-60天库龄 | API写入 | get_fba_stock_list | inv_age_31_60 | 31-60天库龄数量 |
| DK | 31-60天库龄(成本) | API写入 | get_fba_stock_list | inv_age_31_60_cost | 31-60天库龄成本 |
| DL | 61-90天库龄 | API写入 | get_fba_stock_list | inv_age_61_90 | 61-90天库龄数量 |
| DM | 61-90天库龄(成本) | API写入 | get_fba_stock_list | inv_age_61_90_cost | 61-90天库龄成本 |
| DN | 91-180天库龄 | API写入 | get_fba_stock_list | inv_age_91_180 | 91-180天库龄数量 |
| DO | 91-180天库龄(成本) | API写入 | get_fba_stock_list | inv_age_91_180_cost | 91-180天库龄成本 |
| DP | 181-270天库龄 | API写入 | get_fba_stock_list | inv_age_181_270 | 181-270天库龄数量 |
| DQ | 181-270天库龄(成本) | API写入 | get_fba_stock_list | inv_age_181_270_cost | 181-270天库龄成本 |
| DR | 271-330天库龄 | API写入 | get_fba_stock_list | inv_age_271_330 | 271-330天库龄数量 |
| DS | 271-330天库龄(成本) | API写入 | get_fba_stock_list | inv_age_271_330_cost | 271-330天库龄成本 |
| DT | 331-365天库龄 | API写入 | get_fba_stock_list | inv_age_331_365 | 331-365天库龄数量 |
| DU | 331-365天库龄(成本) | API写入 | get_fba_stock_list | inv_age_331_365_cost | 331-365天库龄成本 |
| DV | 大于365天库龄 | API写入 | get_fba_stock_list | inv_age_365_plus | 365+天库龄数量 |
| DW | 大于365天库龄(成本) | API写入 | get_fba_stock_list | inv_age_365_plus_cost | 365+天库龄成本 |
| DX | AWD在库 | API写入 | get_fba_stock_list | awd_available | AWD可用库存 |
| DY | AWD可用量 | API写入 | get_fba_stock_list | awd_available_qty | AWD可用数量 |
| DZ | AWD待发货量 | API写入 | get_fba_stock_list | awd_pending_shipment | AWD待发货 |
| EA | AWD实际在途 | API写入 | get_fba_stock_list | awd_in_transit | AWD实际在途 |

## Tiktok 销售

| 列 | 表头 | 填写方式 | 接口 (MCP/OpenAPI) | 返回字段 / 公式 | 备注 |
|---|---|---|---|---|---|
| A | 店铺 | 标识列，不抓 | — | — |  |
| B | 站点 | 标识列，不抓 | — | — |  |
| C | 状态 | 标识列，不抓 | — | — |  |
| D | 售价 | API写入 | platform_tiktok_product_analysis_list | base_info_list[].price（按 local_sku + store_name 匹配，挂牌价） | 不是 avg_price（无销量时为0） |
| E | 商品负责人 | 标识列，不抓 | — | — |  |
| F | SKU | 标识列，不抓 | — | — |  |
| G | 品名 | 标识列，不抓 | — | — |  |
| H | 品牌 | 标识列，不抓 | — | — |  |
| I | 2026年实际订单毛利润 | 公式（工作簿实际） | （公式） | =AP3-U3-BC3 |  |
| J | 当日实际订单毛利润 | 公式（工作簿实际） | （公式） | =AQ3-V3-BD3 |  |
| K | 2026年销量 | API写入 | platform_tiktok_product_analysis_list | sales_qty | 2026年累计窗口(2026-01-01~昨日)；选定日期销量 |
| L | 30天销量 | API写入 | platform_tiktok_product_analysis_list | sales30d | 近30日销量 |
| M | 销量 | API写入 | platform_tiktok_product_analysis_list | sales_qty | 选定日期销量 |
| N | 样品销量 | API写入 | platform_tiktok_product_analysis_list | sample_qty | 样品销量 |
| O | 销量占比 | API写入 | platform_tiktok_product_analysis_list | sales_ratio | 销量占比 |
| P | 样品销量占比 | API写入 | platform_tiktok_product_analysis_list | sample_ratio | 样品销量占比 |
| Q | 2026年净销售额 | API写入 | platform_tiktok_product_analysis_list | net_sales_amount | 2026年累计窗口(2026-01-01~昨日)；净销售额 |
| R | 净销售额 | API写入 | platform_tiktok_product_analysis_list | net_sales_amount | 净销售额 |
| S | 销售均价 | API写入 | platform_tiktok_product_analysis_list | avg_price | 销售均价 |
| T | 客付运费 | API写入 | platform_tiktok_product_analysis_list | buyer_freight | 客户支付的运费 |
| U | 2026年平台补贴 | API写入 | platform_tiktok_product_analysis_list | platform_subsidy | 2026年累计窗口(2026-01-01~昨日)；平台补贴 |
| V | 平台补贴 | API写入 | platform_tiktok_product_analysis_list | platform_subsidy | 平台补贴 |
| W | FBT可售 | API写入 | platform_tiktok_product_analysis_list | fbt_available | FBT可售 |
| X | FBT可售天数预估 | API写入 | platform_tiktok_product_analysis_list | fbt_available_days | FBT可售天数 |
| Y | FBT总库存预估可售天数 | 公式（工作簿实际） | （公式） | =IF(L3>0,Z3/(L3/30),"") |  |
| Z | FBT总库存 | 公式（工作簿实际） | （公式） | =W3+AI3 |  |
| AA | 70天库存周期差值 | 公式（工作簿实际） | （公式） | =(Z3)-(L3/30)*70 |  |
| AB | 在途+FBT可售取70天 | 公式（工作簿实际） | （公式） | =IF(Y3<>"",ROUND(Y3-70,0),"") |  |
| AC | 在途+FBT可售取70天(每周三抓取） | 公式（工作簿实际） | （公式） | =IF(AND(AB3<>"",AB3<=7),AB3,"") |  |
| AD | 发货时间 | 公式（工作簿实际） | （公式） | =IF(AC3<>"",DATE(2026,11,9),"") | AC 有值时填基准日（2026-11-09） |
| AE | 发货数量(7天发一次） | 公式（工作簿实际） | （公式） | =IF(AC3<>"",(7-AC3)*(L3/30),"") | 补满 7 天周期的发货量 |
| AF | 采购量（采购频率15天） | 公式（工作簿实际） | （公式） | =IF(AND(AC3<>"",AD3<>"",AE3<>""),L3/30*15,"") | **AC/AD/AE 均有值才生效**；15 天采购周期（与亚马逊 DE 统一） |
| AG | 到货时间 | 公式 | （公式） | =IF(AD3<>"",AD3+7,"") | 发货时间 +7 天 |
| AH | 采购时间 | 公式 | （公式） | =IF(AD3<>"",AD3+IF(AC3>=-24,AC3+25,45),"") | 发货时间 + (AC+25)；AC < -24 时 +45 |
| AI | 转运中 | API写入 | platform_tiktok_product_analysis_list | fbt_in_transit | 转运中数量 |
| AJ | 总库存 | API写入 | platform_tiktok_product_analysis_list | fbt_total | FBT总库存 |
| AK | 本地可用 | API写入 | platform_tiktok_product_analysis_list | local_available | 本地仓可用 |
| AL | 海外可用 | API写入 | platform_tiktok_product_analysis_list | overseas_available | 海外仓可用 |
| AM | 退款金额 | API写入 | platform_tiktok_product_analysis_list | refund_amount | 退款金额 |
| AN | 退款量 | API写入 | platform_tiktok_product_analysis_list | refund_qty | 退款量 |
| AO | 退款率 | API写入 | platform_tiktok_product_analysis_list | refund_rate | 退款率 |
| AP | 2026年订单毛利润 | API写入 | platform_tiktok_product_analysis_list | gross_profit | 2026年累计窗口(2026-01-01~昨日)；订单毛利润 |
| AQ | 订单毛利润 | API写入 | platform_tiktok_product_analysis_list | gross_profit | 订单毛利润 |
| AR | 订单毛利率 | API写入 | platform_tiktok_product_analysis_list | gross_profit_margin | 订单毛利率 |
| AS | 2026年结算毛利润 | API写入 | platform_tiktok_product_analysis_list | settlement_profit | 2026年累计窗口(2026-01-01~昨日)；结算毛利润 |
| AT | 结算毛利润 | API写入 | platform_tiktok_product_analysis_list | settlement_profit | 结算毛利润 |
| AU | 结算毛利率 | API写入 | platform_tiktok_product_analysis_list | settlement_profit_margin | 结算毛利率 |
| AV | FBT仓储费 | API写入 | platform_tiktok_product_analysis_list | fbt_storage_fee | FBT仓储费 |
| AW | 达人佣金 | API写入 | platform_tiktok_product_analysis_list | influencer_commission | 达人佣金 |
| AX | 联盟伙伴佣金 | API写入 | platform_tiktok_product_analysis_list | affiliate_partner_commission | 联盟伙伴佣金 |
| AY | 联盟广告佣金 | API写入 | platform_tiktok_product_analysis_list | affiliate_ad_commission | 联盟广告佣金 |
| AZ | 联盟伙伴广告佣金 | API写入 | platform_tiktok_product_analysis_list | affiliate_partner_ad_commission | 联盟伙伴广告佣金 |
| BA | 达人奖励 | API写入 | platform_tiktok_product_analysis_list | influencer_reward | 达人奖励 |
| BB | 广告费 | API写入 | platform_tiktok_product_analysis_list | ad_fee | 广告费 |
| BC | 2026年分摊折扣 | API写入 | platform_tiktok_product_analysis_list | seller_discount | 2026年累计窗口(2026-01-01~昨日)；卖家分摊折扣 |
| BD | 分摊折扣 | API写入 | platform_tiktok_product_analysis_list | seller_discount | 卖家分摊折扣 |
| BE | 平台佣金 | API写入 | finance_settlement_profit_list（queryMode=1, summaryField="4"） | platformCommission | 平台费用来自财务利润报表，PA 接口无此字段；只覆盖当天有结算单的SKU，其余保留原值；平台佣金 |
| BF | 平台服务费 | API写入 | finance_settlement_profit_list（queryMode=1, summaryField="4"） | platformServiceFee | 平台费用来自财务利润报表，PA 接口无此字段；只覆盖当天有结算单的SKU，其余保留原值；平台服务费 |
| BG | 平台赔付 | API写入 | finance_settlement_profit_list（queryMode=1, summaryField="4"） | platformCompensation | 平台费用来自财务利润报表，PA 接口无此字段；只覆盖当天有结算单的SKU，其余保留原值；平台赔付 |
| BH | 平台罚款 | API写入 | finance_settlement_profit_list（queryMode=1, summaryField="4"） | platformPenalty | 平台费用来自财务利润报表，PA 接口无此字段；只覆盖当天有结算单的SKU，其余保留原值；平台罚款 |
| BI | 平台其他费 | API写入 | finance_settlement_profit_list（queryMode=1, summaryField="4"） | platformOtherFee | 平台费用来自财务利润报表，PA 接口无此字段；只覆盖当天有结算单的SKU，其余保留原值；平台其他费 |
| BJ | 平台调整费 | API写入 | finance_settlement_profit_list（queryMode=1, summaryField="4"） | platformAdjustmentFee | 平台费用来自财务利润报表，PA 接口无此字段；只覆盖当天有结算单的SKU，其余保留原值；平台调整费 |
| BK | 费用退款 | API写入 | finance_settlement_profit_list（queryMode=1, summaryField="4"） | feeRefund | 平台费用来自财务利润报表，PA 接口无此字段；只覆盖当天有结算单的SKU，其余保留原值；费用退款 |
| BL | 平台配送费 | API写入 | finance_settlement_profit_list（queryMode=1, summaryField="4"） | platformDeliveryFee | 平台费用来自财务利润报表，PA 接口无此字段；只覆盖当天有结算单的SKU，其余保留原值；平台配送费 |
| BM | 三方配送费 | API写入 | finance_settlement_profit_list（queryMode=1, summaryField="4"） | thirdPartyDeliveryFee | 平台费用来自财务利润报表，PA 接口无此字段；只覆盖当天有结算单的SKU，其余保留原值；三方配送费 |
| BN | 仓储费 | API写入 | finance_settlement_profit_list（queryMode=1, summaryField="4"） | storageFee | 平台费用来自财务利润报表，PA 接口无此字段；只覆盖当天有结算单的SKU，其余保留原值；仓储费 |
| BO | 其他仓储物流费 | API写入 | finance_settlement_profit_list（queryMode=1, summaryField="4"） | otherLogisticsFee | 平台费用来自财务利润报表，PA 接口无此字段；只覆盖当天有结算单的SKU，其余保留原值；其他仓储物流费 |
| BP | 物流赔偿 | API写入 | finance_settlement_profit_list（queryMode=1, summaryField="4"） | logisticsCompensation | 平台费用来自财务利润报表，PA 接口无此字段；只覆盖当天有结算单的SKU，其余保留原值；物流赔偿 |
| BQ | 广告费 | API写入 | finance_settlement_profit_list（queryMode=1, summaryField="4"） | advertisingFee | 平台费用来自财务利润报表，PA 接口无此字段；只覆盖当天有结算单的SKU，其余保留原值；TikTok Shop广告费 |
| BR | 联盟营销 | API写入 | finance_settlement_profit_list（queryMode=1, summaryField="4"） | affiliateMarketingFee | 平台费用来自财务利润报表，PA 接口无此字段；只覆盖当天有结算单的SKU，其余保留原值；联盟营销费用 |
| BS | 其他推广费 | API写入 | finance_settlement_profit_list（queryMode=1, summaryField="4"） | otherPromotionFee | 平台费用来自财务利润报表，PA 接口无此字段；只覆盖当天有结算单的SKU，其余保留原值；其他推广费 |
| BT | 采购成本 | API写入 | finance_settlement_profit_list（queryMode=1, summaryField="4"） | productCost | 平台费用来自财务利润报表，PA 接口无此字段；只覆盖当天有结算单的SKU，其余保留原值；采购成本 |
| BU | 头程费用 | API写入 | finance_settlement_profit_list（queryMode=1, summaryField="4"） | firstLegCost | 平台费用来自财务利润报表，PA 接口无此字段；只覆盖当天有结算单的SKU，其余保留原值；头程费用 |
| BV | 其他成本 | API写入 | finance_settlement_profit_list（queryMode=1, summaryField="4"） | otherCost | 平台费用来自财务利润报表，PA 接口无此字段；只覆盖当天有结算单的SKU，其余保留原值；其他成本 |
| BW | 成本小计 | API写入 | finance_settlement_profit_list（queryMode=1, summaryField="4"） | costSubtotal | 平台费用来自财务利润报表，PA 接口无此字段；只覆盖当天有结算单的SKU，其余保留原值；成本小计 |

## 汇总表（透视表，不填数）

| 汇总表 | 数据源 | 行字段 | 值字段 | 说明 |
|---|---|---|---|---|
| 亚马逊销售汇总 | 隐藏 sheet `_AMZ汇总数据源`（引用亚马逊销售 DB/DD/DA） | SKU | 最早发货时间(DB, MIN)、发货数量合计(DD, SUM)、发货金额合计(SUM) | 发货金额 = 发货数量 × PM 单价（U 列按 SKU 取 MAXIFS） |
| Tiktok 销售汇总 | 隐藏 sheet `_TK汇总数据源`（引用 Tiktok 销售 AD/AE） | SKU | 最早发货时间(AD, MIN)、发货数量合计(AE, SUM)、发货金额合计(SUM) | 同上 |
| 产品管理 - 库存汇总 | 隐藏 sheet `_PM汇总数据源`（引用 PM/亚马逊销售/Tiktok 销售） | 时间、SKU；筛选「是否有采购=是」 | 亚马逊采购量合计(SUMIFS DE)、亚马逊最早采购时间(MINIFS DG)、TikTok采购量合计(SUMIFS AF)、TikTok最早采购时间(MINIFS AH)、采购金额合计(AG) | 时间 = DATE(2026,11,9) |

注：汇总表是真正的 Excel PivotTable，由 `build_pivot_summary.py` 通过 COM 生成。明细更新后需刷新（全部刷新）；辅助 sheet 的引用行号固定到当前数据末行，明细行数变化时要同步修改脚本中的 `*_last`。
