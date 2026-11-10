# 踩过的坑和解决方法

## 一、必须遵守

### 1. 当天拉当天数据会漏单
现象: 同一个 SKU,下午拉到的销量约 310,次日 EOD 拉到约 379。
原因: 当天还在卖,订单没有全部结算。
规则: 销售类字段一律拉前一天数据,日报在次日制作。

### 2. 白色列被误填
现象: T 单价、库龄列被 API 数据覆盖,破坏了模板结构。
规则: 只填彩色列。白色列按模板保留原值,白色公式列按行重写公式,白色空列保持为空。

### 3. 公式写入后显示为文本
现象: 写入公式后 Excel 打开显示"=T3*X3"之类的文字,或者结果都是 0。
原因: 程序写入的公式没有缓存计算结果。
解决: 用 Excel 打开文件,执行全表重算(强制计算),保存。这一步在 Excel 或 WPS 里做,不要依赖程序写入后的结果。

### 4. T 单价不能自动填
现象: 为了让公式有结果,把采购成本填进 T 列。
规则: T 列是白色列,由用户从领星"采购单详情"手工填写。为空时公式结果为 0 是预期行为。

## 二、产品表现与店铺

### 5. 不按店铺拿数据会合并错误
现象: 同一 SKU 在美国店和加拿大店的销量加在一起,填到每一行都偏大。
原因: 接口默认按 SKU 汇总,不带店铺维度。
解决: 按店铺展开(每个店铺单独一条记录),再按(SKU, 店铺)匹配到表格行。
注意: 不同币种(USD、CAD、MXN、BRL)要分开查询。

### 6. Listing 和 FBA 不能用 sid 匹配
现象: 大量 SKU 的售价和 FBA 库存为 0 或错位。
原因: 领星返回的 sid 字段经常为空或不准。
解决: 用(SKU, 店铺名)匹配。

### 7. 同一 SKU 多条记录的处理
- FBA 库存在多个分页里可能出现同一(SKU, 店铺)的多条记录,数值不同。取可用量最大的一条。
- Listing 同样可能有多条,取售价非 0 的一条。
- 采购报表同一 SKU 多个供应商会出现多行,X/Y/Z 要求和,并按记录 ID 去重。

### 8. 同一 SKU 多个 listing 变体价格不同
现象: 某店铺的 SKU 有多个变体(不同的 listing ID),售价不同。例如 PA-FG-FS-V3-30-1P 在 PureAmor 店有 29.99 到 59.99 多个价格。
策略: 优先取有销量的变体价;都没有销量时取多数值。验证时如果对不上,要先确认是不是变体问题。

### 9. 合并新旧数据时的取舍
现象: 同一 SKU 新拉的 Listing 售价为 0,旧数据有 12.99。
原因: 实时查询时 Buy Box 可能临时失效。
策略: 合并时字段逐个处理,新数据有有效值才覆盖旧数据,否则保留旧值。

## 三、TikTok 相关

### 10. 挂牌价不是平均成交价
现象: D 列售价全部为 0 或远低于实际挂牌价。
原因: 平均成交价字段在无销量时为 0。
规则: D 列取店铺 listing 的价格(挂牌价)。

### 11. TikTok 数据结构特殊
- 产品表现的记录不在通用的列表字段里,要用对应的数据字段取。
- 主键是 local_sku,不是 sku。
- 订单利润接口只返回亚马逊店铺,TikTok 店铺在里面找不到。TikTok 的费用数据要从产品表现字段和账单接口里取。
- TikTok 店铺的 sid 全为 0,必须用长 store_id 匹配。

## 四、加工单与采购报表

### 12. 加工单的 AA 不能按 SKU 单独算
现象: 按 SKU 求和得到 681,领星页面显示 981。
原因: 页面的总计是订单级别的。一个订单里含多个 SKU 时,页面把整单数量都算进来。
规则: 对每个含此 SKU 的订单,把整单所有产品的数量加总,再计入该 SKU。

### 13. 加工单接口的筛选
- 只统计两个目标仓: WH-US-SDG-YU-OEM-1 和 WH-US-BRE-AM-OEM-2
- 状态: 0 待配货、1 待完成、2 已完成、3 已撤销
- AA 统计状态 0、1、2;AC 只统计状态 2
- 常用的其他加工单查询接口返回的数据不对(数量或仓库不符),要用"加工单列表"接口

### 14. 采购报表单次最多 90 天
现象: 查询 2026 全年时接口报错或返回不完整。
解决: 按季度分 4 段拉取: 1-3 月、4-6 月、7-9 月(到 9 月 29 日)、9 月 30 日到当日。合并时按记录 ID 去重。

## 五、Excel 操作

### 15. 文件被占用无法保存
现象: 保存时提示权限错误。
原因: WPS 或 Excel 还开着该文件。
解决: 关闭所有相关进程后再保存。

### 16. 大批量数据的接口返回很大
现象: 接口一次返回几百 KB 到几 MB,直接读取会超出上下文。
解决: 分页拉取,每页 200 条左右,分批处理。

## 六、常见数值问题诊断

| 现象 | 可能原因 | 排查方向 |
|---|---|---|
| Sheet 2 大量 SKU 的售价为 0 | Listing 没按店铺名匹配 | 检查匹配键 |
| Sheet 2 的销量比领星页面少约 20% | 当天拉取,数据未结算 | 次日重拉 |
| Sheet 1 的 X 为 0 但有采购 | 采购报表时间范围不够 | 改为 2026 全年分季度拉 |
| Sheet 1 的 AA 比页面少 | 按 SKU 求和而非整单 | 改为整单数量聚合 |
| Sheet 3 的 D 售价大多为 0 | 取了平均成交价 | 改取挂牌价 |
| 公式列显示为文字 | 没有全表重算 | 用 Excel 重算 |
| T 单价被填入数据 | 误填白色列 | 清空 T,保留为空 |
| 库龄列被填入 0 | 误填白色列 | 清空,保留用户手填 |


## 七、新表（2026-11 版）相关

### 17. 列字母已整体移位，不能照搬旧映射
现象：旧 skill 写死的列字母（如亚马逊 BO=售价、产品管理 S=采购金额）在新表里已偏移（亚马逊售价现移到 BU，产品管理采购金额现移到 T）。
规则：一律以工作簿内 `字段数据来源` sheet（198 行）为权威逐列映射，或查 `references/field_mapping.md` 的新列索引；不要凭记忆写列字母。

### 18. 新增字段/汇总列
新表新增：各表 `2026年*` 累计字段、昨日/30日系列、平台拆分采购量(亚马逊/TK/供应链)、国内仓+海外仓总采购量/金额/已付款/未付款/采购ToC利润、本地/海外/总库存、总货值、FBA 14 档库龄(含成本)、AWD 四列、TikTok 订单利润块(BC–BW)。这些都要按各自口径取数，部分标 `NEW-待确认` 口径待定。

### 19. 特殊指令列勿当 API 填
亚马逊 DE/DF、TikTok AD/AG/AH 单元格写的是文字指令（如"抓取CZ列为7的日期"），DC/AE 是 ÷7 类公式且可能出 `#VALUE!`。按文字指令计算写入，不要用 API 覆盖。

### 20. 数据来源 sheet 与 skill 冲突时
以工作簿内 `字段数据来源` sheet 为准（它由制表人在 Excel 内维护，最新）。

### 21. LingXing MCP Key 失效
现象：调用返回 `code:102 / MCP Key无效或已失效`。
原因：连接器 Key 过期或被重置。解决：在 MCP 管理页重新生成 X-Mcp-Key，更新 `~/.workbuddy/mcp.json` 后**重建 MCP 连接**（重启 WorkBuddy 或在连接器页重新 Trust），否则仍用旧连接。

### 22. [已推翻，见 #35] 加工数量（AB/AD）的领星页面口径复现不了
`warehouse_processing_order_list` 2026 全年只有 2068 张（`type` 全为 1，无拆分单；查 2024/2025 全年 total=0）。按「OEM 两仓(WH-US-SDG-YU-OEM-1 / WH-US-BRE-AM-OEM-2) + 状态 0/1/2 + PL.sku 成品产出量」聚合，总计 609,337，而表内值合计 1,147,021（**系统性低 47%**）；241 个有值 SKU 中仅 48 个逐位吻合，相对偏差中位数 54%，且个别 SKU 我算的反而更大（如 HG-FG-CF-P38-08-CL-2P 已完成 17,640 vs 表内 17,208）→ 不是「漏加」而是**不同口径**。
`字段数据来源` 给的 `warehouse_order_plan_list` 只有 30 条计划（待完成），`warehouse_outbound_order_list` 根本不存在（`code:102 未找到已发布工具`）。
**此结论已被 2026-11-09 实测推翻**：改用 OpenAPI 直连 `StorageProcess/getOrderLists` 后可以复现，见 #35。

### 23. `max_process_num` 不在库存明细返回字段里
`inventory_detail_list` 返回 93 个字段（good_num / qc_num / pending_num / expect_valid_num / transit_num / storage_safe_num / section1-8 / child_list …），**没有 `max_process_num`**，也没有参数可以打开。最大可加工量(AK/AY)只能保留原值或另找接口，不要拿 `product_type_num`（品类数量）冒充。

### 24. 总库存 BM 只加 5 列，别加期望量和安全库存
`AT`=AL+AM+AN+AO+AR、`BH`=AZ+BA+BB+BC+BF、`BM`=AT+BH。把 AP/AQ/AS（期望可用/期望待到货/安全库存）算进去会让 BO/BQ 的平台拆分基数虚高。

### 25. 采购时间/到货时间是「倒推」出来的，不是查出来的
按可售天数倒推：采购时间=基准日+(可售天数-45)，为负则基准日+45；到货时间=基准日+(可售天数-77)，为负则基准日+7；发货时间仅在可售天数≤7 时取「下周一」。基准日=**获取数据当天**（不是数据日 T-1）。可售天数>365 视为无采购需求，留空，否则会出现 2030 年这种荒谬日期。

### 26. TikTok 产品表现接口的分页路径与别家不同
记录在 `data.data.data`，总数在 `data.data.count`，SKU 字段是 `local_sku`（不是 `sku`）。`dimension_type`：1=MSKU、2=商品ID、3=SKU、4=店铺。用 `page_num`/`page_size` 翻页（不是 offset/length）。

### 27. 「版本间单调性」比采样对点更能验证口径
拿上一版已填好的表比：采购量/待到货量/到货量应当**只增不减**。2026-11-08 实测 1329 行不变、7 行增加、0 行减少 → 口径正确；任何「减少」都说明时间窗口/去重/店铺展开出了问题。

### 28. `字段数据来源` 表里的 API 字段名有一批是「文档名」，实测并非接口真名
2026-11-08 逐列实测校正（左=按文档写、右=接口真实返回），照文档写会**整列取空或取错列**：

| 列 | 文档写的字段 | 实测正确字段 |
|---|---|---|
| 亚马逊 X 退款率 | `refund_rate` | `return_rate`（amz 产品表现；`refund_rate` 只有 TikTok 有） |
| 亚马逊 CD 平台费率 | `estimated_referral_fee_rate` | `platform_fee_rate`，为空时回退 `estimated_referral_fee_rate`（值是 `"12.0%"` 字符串，需去 % 除 100） |
| 亚马逊 CE 平台费 | `estimated_referral_fee` | `platform_fee` → 回退 `estimated_referral_fee` |
| 亚马逊 CL 大类排名 | `rank` / `category_rank.rank` | `seller_rank`（`category_rank` 是 dict，`small_rank` 是 **JSON 字符串** 要先 json.loads） |
| 亚马逊 CO Rating总数 | `review_num` | `reviews_num`（`review_num` 全为 null） |
| 亚马逊 CP 评分 | `star_score` | `stars`（`star_score` 全为 null） |
| 亚马逊 CB 预估FBA费(API) | `fba_fee` | `estimated_fba_fee`，为空回退 `fba_fee` |
| 亚马逊 Tiktok 表 AR/AU 毛利率 | — | `gross_profit_margin` / `settlement_profit_margin`，分母不稳，一致率仅 0-6% |
| TikTok AX 联盟伙伴佣金 | `affiliate_commission` | `affiliate_partner_commission`（`affiliate_commission` 是另一个概念） |
| TikTok BQ 广告费(TKS) | `ad_fee` / `affiliate_marketing` | `tk_ad_fee`（`ad_fee` 是 BB 列那个广告费） |

**教训：先 `search(toolId)` 拿 schema、再取一条真实记录 `sorted(rec.keys())` 核对字段是否存在，最后才写映射。不要直接信 `字段数据来源` 的字段列。**

### 29. 亚马逊 CPO/CPU 不是接口原值，是算出来的
- `BS CPO`（单订单广告成本）= `spend / ad_direct_order_quantity`
- `BT CPU`（单销量广告成本）= `spend / volume`
接口自带的 `cpo` / `cpu` 字段只有 160/236 行有值，且与大表口径不符（一致率 2%/68%）。用上面两个公式算，逐位吻合。

### 30. TikTok 平台佣金/配送费/采购成本不在「产品表现」接口里
`platform_tiktok_product_analysis_list` 只有 158 个字段，**没有** `platform_commission` / `platform_shipping_fee` / `product_cost` / `cost_subtotal` 等。这些在 **`finance_settlement_profit_list`（财务-利润报表明细）** 里，且是 **camelCase**：

`queryMode=1, summaryField="4"(SKU), startDate/endDate, sids=[店铺], pageNum/pageSize≤200`，返回 `data.data.dataList`，总数为 `data.data.totalCount`。
字段映射：`platformCommission / platformServiceFee / platformCompensation / platformPenalty / platformOtherFee / platformAdjustmentFee / feeRefund / platformDeliveryFee / thirdPartyDeliveryFee / storageFee / otherLogisticsFee / logisticsCompensation / advertisingFee / affiliateMarketingFee / otherPromotionFee / productCost / firstLegCost / otherCost / costSubtotal`。
**只覆盖当天有结算单的 SKU**（TikTok 全店 8 个店一天约 263 条），其余行必须保留原值，否则会把成本清空。

### 31. `auto_tags` / `product_tags` / `out_stock_date` 全账号为空
amz 产品表现 1433 条记录里这三个字段 **0 条非空**；`settings_tag_page_list(subType=110)` 只有 5 个 Listing 标签且 `ruleContentList` 全为 null（=账号没配自动标签规则）。处理方式：
- **E 自动标签**：确实无源，留空（不要拿别的标签冒充）。
- **F 产品标签**：用产品库 `products.json → global_tags[].tagName`（`ruleContentList` 为空的是手动标签）兜底，可覆盖 901/911 行。
- **AM 断货时间**：接口无值 → 写公式 `=IFERROR(IF(AND(ISNUMBER($AF3),$AF3>0),TODAY()+ROUND($AF3,0),""),"")`（今天+FBA可售天数）。

### 32. 时间列必须「报错/0/>7 都不出现」→ 用带守卫的公式，不要写死值
所有派生列统一成：`=IFERROR(IF(AND(ISNUMBER(...),...>0,...<阈值), 计算, ""),"")`
- 发货时间：仅 `在途+可售天数 ≤7` 才给「下周一」`TODAY()+(8-WEEKDAY(TODAY(),2))`
- 到货时间：`TODAY()+MAX(可售天数-70-7, 7)`，`>365` 留空
- 采购时间：`TODAY()+MAX(可售天数-45, 45)`，`>365` 留空
- 发货数量：`DA`(周快照) 不在 0~7 区间就留空，否则 `(7-DA)*(30日销量/30)`
这样 0 销售、除零、超一年都会自动变空白，不会在后面的时点列里冒出假日期。

### 33. 供应链采购量 BS/BU 不能用「总库存 − 平台采购量」
当前 11.10 原表公式为 BS=BM−BO、BU=BM−BQ。如果 BO/BQ 大于总库存会出现负数。业务上如口径不同需重新确认。

### 34. 销售表里的 SKU 不一定在库存主表里
2026-11-10 发现 40 个 SKU 只在销售表出现，销售额合计约 4.7 万，不纳入会漏算。核对时要用两边 SKU 的并集。只在销售表的 SKU 没有 U 单价，发货金额为 0，需要单独补。

### 35. 已删除 listing 的销量
PA-FG-HP-P10 的 3 件 TikTok 销量属于 PureamorCalifornia-HL-25-13-US（已删除），工作簿里没有该店铺的行，3 件未计入。要计入需新增行并补全公式列。

### 33. 写列前先确认「这张表的列语义」与别张表不同
同一字母在两张表含义不同的坑：**I/J** 在 TikTok 是「2026年/当日实际订单毛利润」（公式 `=AP-U-BC` / `=AQ-V-BD`），在亚马逊是 **品牌 / 采购成本**。2026-11-08 曾把 TikTok 的 I/J 公式套到亚马逊表，直接把品牌和采购成本两列整列覆盖成毛利公式。**公式表要按表分开定义，不要跨表复用。**

### 34. 逐列质量闸：一致率过低就保留原值
新值与旧值逐格比对（相对误差 ≤5% 算一致），**一致率 <15% 且旧值已有数据 → 保留原值**并列入待查清单。这条闸门救回了 `AJ 存销比 / AK 月库销比 / CN 小类1 / H 创建时间` 等口径不明的列。但 `BS/BT` 这类已手工核验过公式的列要放进 FORCE 白名单强制写入。
另注意：**接口返回全空（nfill=0）时也要保留原值**，否则一次「字段名写错」就会把整列历史数据清空。写入时只写非空值（`None` 不覆盖旧值）。

## 八、2026-11-09 实测新增（汇总表 / 加工单 / 字段）

### 35. 加工单 AB/AD：用 OpenAPI 直连可以复现（推翻 #22）
- 接口：`/erp/sc/routing/inventoryReceipt/StorageProcess/getOrderLists`，`type=1` 加工单、`type=2` 拆分单，分页。
- 实测：2074 条记录，其中目标仓（WH-US-SDG-YU-OEM-1、WH-US-BRE-AM-OEM-2）880 条。
- 聚合：**整单数量求和**，对订单内每个 SKU 都加整单总量（与领星页面「总计」一致）。状态 0/1/2 计入 AB，仅状态 2 计入 AD。
- 验证：每张表抽 50 个 SKU，共 4701 个字段，与领星一致。
- MCP 的 `warehouse_order_plan_list` 只有 30 条中国仓数据，`warehouse_outbound_order_list` 不存在，都不能替代。

### 36. 不要用 PowerShell 的 `python -c` 传含双引号的代码
PowerShell 会吞掉内嵌的双引号，报 `NameError`。把代码写进 `.py` 文件再运行。

### 37. pywin32 的 Excel 对象：`Address` 是属性不是方法
写 `ws.UsedRange.Address()` 会报 `'str' object is not callable`，应写 `ws.UsedRange.Address`。

### 38. 用 COM 写 datetime 会有时区偏移
写入 `datetime(2026,11,9)` 后显示成 2026-11-08。改用 `=DATE(2026,11,9)` 公式。

### 39. 残留的 `~$` 锁文件
`~$xxx.xlsx` 存在但没有 Excel 进程占用时，`shutil.copy2` 仍会报 WinError 32。不要强杀未知进程，直接换一个输出文件名。锁文件是 Office 在打开文件时创建的，关闭文件后会消失，残留时通常是上一次进程异常退出。

### 40. 透视表要求数据源是连续区域，且列头唯一
- openpyxl 不能创建透视表，必须用 COM（`PivotCaches().Create` → `CreatePivotTable`）。
- 数据源用隐藏辅助 sheet 承接：第一行是列头，之后每行用公式引用明细表。辅助 sheet 的公式用 `FormulaR1C1`，再 `FillDown`。
- 透视表的值字段名不能与源字段名完全相同，否则会报错，需要使用不同的显示名。

### 41. 透视表里的 0 日期
MIN/MAX 对无值的日期会返回 0，显示为 1900-01-00。把日期列的数字格式设为 `yyyy-mm-dd;;`，使 0 显示为空白。

### 42. 发货金额列在明细表中不存在
曾把「采购量」误映射到「发货金额」，导致汇总表金额错误。正确做法：先确认目标列在数据表中是否存在；不存在时按口径计算（发货数量 × PM 单价），并告知用户口径。

### 43. 汇总表的采购时间取错列
PM 汇总表的「亚马逊采购时间」曾取了发货时间列（DB），应取采购时间列（DF）。TikTok 同理，应取 AH 而非 AD。字段名相似不代表是同一列，要以列字母和工作簿表头为准。

### 44. `字段数据来源` sheet 与工作簿公式冲突
- 例：PM 的 T（采购金额）、V、W、X、AC、AE，sheet 写的是 API，工作簿实际是公式（如 `=U3*Y3`、`=AB3*U3`）。
- 例：AMZ 的 DD 采购量，sheet 写 `purchase_num`，工作簿实际是 `=IF(CG>0,CG/30*15,"")`。
- 例：TK 的 I/J、AF，sheet 写 API，工作簿实际是公式。
- 规则：**以工作簿实际公式为准**。字段表中的备注会标出冲突。

### 45. sheet 缺少 2026年* 与平台采购列
`字段数据来源` sheet 只有 197 行，缺少「2026年销量」等字段和「亚马逊采购量/亚马逊采购时间」等平台拆分列。处理：2026年* 列复用对应基础字段的接口，窗口改为 2026-01-01 ~ 昨日；平台采购列用 `products_purchase_history` 按平台过滤。

### 46. TikTok 平台费用不在产品表现接口中
`platform_tiktok_product_analysis_list` 只有约 158 个字段，没有平台佣金、配送费、采购成本、成本小计等。这些字段在 `finance_settlement_profit_list`（camelCase，queryMode=1，summaryField="4"）中，只覆盖当天有结算单的 SKU。

### 47. 匹配时先做精确匹配，再做包含匹配
字段名做包含匹配时，「样品销量」会抢走「样品销量占比」。生成映射时应先做全表精确匹配，再做去掉「2026年」前缀的匹配，最后才做包含匹配。

### 48. 签名对嵌套参数的 sort_keys 未确认
`lingxing_direct.py` 第 42 行对嵌套参数使用了 `sort_keys=True`，与记忆笔记「不加 sort_keys」相反。当前所有调用的参数都是扁平的，因此没有暴露问题。遇到嵌套参数的接口时，需要先实测确认签名是否通过。
