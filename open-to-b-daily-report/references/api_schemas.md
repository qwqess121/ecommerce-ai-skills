# 接口参数参考

本文件只描述接口的用途、关键参数和使用规则,不含代码。接口名称与领星 MCP 工具名一致。

## 一、产品管理列表(products_list)

- 用途: 取产品属性(创建时间、创建人、状态、品牌、产品类型、开发人、开发日期、采购员、采购交期、采购成本、供应商、最小采购量、标签)
- 关键参数: 分页(offset/length,length 最大 500)、is_aux 固定为 0、product_type 取 [1, 2]
- 总量约 3850 条,分约 8 页拉取
- 最小采购量来自报价阶梯(quote_step_prices)的第一档 moq
- 产品标签来自 global_tags 的 tagName 或 tag_name
- 开发日期为空时可用创建日期代替

## 二、采购报表(analytics_show_product_list)

- 用途: 取采购量、待到货量、到货量及金额
- 关键参数: start_date、end_date(两者之间最多 90 天)、time_type(1 为下单时间,2 为到货时间)、分页(length 最大 200)
- 2026 全年约 2327 条记录,需按季度分 4 段拉取
- 合并时按记录 ID 去重
- 同一 SKU 多个供应商会出现多行,X/Y/Z 求和

## 三、库存明细(inventory_detail_list)

- 用途: 取各仓库的可用量、锁定量、待检、待到货、调拨在途、安全库存、期望量
- 关键参数: 分页(offset/length)
- 约 4922 条,分约 25 页拉取
- 按仓库名区分本地仓(WH-CN 开头或含"中国")和海外仓(WH-US 开头或含"美国")后汇总
- 待检待上架 = 质检数量 + 待上架数量

## 四、产品表现(query_product_performance_asin_lists)

- 用途: 取 ASIN/SKU 维度的销量、销售额、订单量、广告、毛利、ROI、排名相关指标
- 关键参数: start_date、end_date(日期为前一日)、summary_field 设为 sku、summary_field_level2 设为 mid(按店铺展开,这是取得按店铺数据的关键)、sids(店铺 ID,用逗号分隔)、currency_code、turn_on_summary=1
- 按币种分组查询: USD(美国店)、CAD(加拿大店)、MXN(墨西哥店)、BRL(巴西店)
- 每条记录的 sids 只含一个店铺时,即为该店铺的独立数据
- 返回中部分字段(如标签、断货时间)常为空,这是领星源头未录入

## 五、Listing(erp_listing)

- 用途: 取售价、各类费用、昨日和 30 日销量及广告费、大类排名、评分、首单时间
- 关键参数: 分页(offset/length)、pvi_ids 传空字符串
- 约 4973 条,分约 25 页拉取
- 匹配键: (local_sku, seller_name),不用 sid
- 同一键多条时取售价非 0 的一条

## 六、FBA 库存(get_fba_stock_list)

- 用途: 取 FBA 可用库存、可售、待调仓、在途、入库中、各档库龄及成本、AWD 库存
- 关键参数: 分页(offset/length)
- 约 4753 条,分约 24 页拉取
- 匹配键: (sku, seller_name)
- 同一键多条时取可用库存最大的一条

## 七、TikTok 产品表现(platform_tiktok_product_analysis_list)

- 用途: 取 TikTok 店铺的挂牌价、销量、库存、退款、毛利、佣金、广告费等
- 关键参数: start_date、end_date、dimension_type 设为 3(按 SKU)、page_num、page_size
- 返回中记录列表在 data 字段下,不在 list 下
- 主键 local_sku
- 挂牌价在 base_info_list 中,每个店铺一条,取 price 字段,按店铺名匹配
- 有销量时 avg_price 为实际成交均价,无销量时为 0

## 八、TikTok 账单(platform_tiktok_bill_list)

- 用途: 取 TikTok 订单的配送费、物流赔偿、平台调整、FBT 仓储服务费等明细
- 关键参数: sids(TikTok 店铺的长 store_id 列表)、transactionTypes(建议全部 1 到 27 传入)、startDate、endDate、排序及分页
- 按 (sku, storeName) 汇总各金额字段
- 常用交易类型: 1 订单、4 物流赔偿、10 FBT 仓储服务费、22 平台补偿、23 平台佣金调整

## 九、加工单列表(StorageProcess/getOrderLists)

- 用途: 取加工单和拆分单,用于计算 AA 总加工和 AC 已完成
- 关键参数: type(1 加工单,2 拆分单)、分页
- 返回字段包括: 单号、仓库名、状态、创建时间、完成时间、产品明细(含 SKU 与数量)
- 已于 2026-11-09 实测通过：直连 OpenAPI 调用，type=1 与 type=2 分别拉全量，共 2074 条，目标仓 880 条
- 过滤: 仓库 ∈ {WH-US-SDG-YU-OEM-1, WH-US-BRE-AM-OEM-2}，状态 0/1/2 计入 AB，状态 2 计入 AD
- 聚合: 整单数量求和（订单内每个 SKU 都加整单总量），与领星页面「总计」一致
- 注意: 常见的"仓库计划单列表"（warehouse_order_plan_list，仅 30 条中国仓）和"海外仓备货单"不是加工单，不能替代

## 十、店铺列表(get_multi_platform_shop_list)

- 用途: 查询店铺及其 store_id、平台、站点、币种
- 关键参数: platform_code 数组(10001 为亚马逊,10011 为 TikTok)
- 用来建立店铺名与 sid、store_id 的对应关系

## 十一、直连 OpenAPI 的通用规则

- 域名为 openapi.lingxing.com
- 需要先用 AppID 和 AppSecret 换取 access token,token 有效期约 2 小时,过期前重新获取
- 每个请求都要签名: 把参数按 key 排序拼接(空值跳过),对拼接串做 MD5 并转大写,再用 AppID 作为密钥做 AES(ECB 模式、PKCS7 填充)加密,结果经 Base64 编码
- 待实测: 嵌套参数（dict/list）的序列化。`lingxing_direct.py` 第 42 行使用 `json.dumps(..., sort_keys=True)`，记忆笔记写的是不加 sort_keys。当前所有调用参数都是扁平的，未暴露问题。遇到嵌套参数的接口，先用一个已知接口实测确认再使用
- 直连时不要走本地代理(代理下 SSL 握手常超时)
- AppID 和 AppSecret 必须通过环境变量读取,不写入任何文件
