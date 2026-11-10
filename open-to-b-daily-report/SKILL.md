---
name: open-to-b-daily-report
description: "Open to B 日报表填充方法（2026-11 版，2026-11-09 实测更新）— 三张明细表(产品管理-库存/亚马逊销售/Tiktok 销售)的彩色字段从领星取数填写的逐字段规则、接口、踩坑记录，以及三张汇总表（Excel 真透视表）的生成方法。白色列不抓、彩色列才填；公式以工作簿为准；销售类字段 T+1 拉取。"
user_invocable: true
metadata: {"owner":"AB America Corp / HOOGALIFE","status":"verified","last_verified":"2026-11-09"}
---

# Open to B 日报表填充方法

> 本 skill 只记录方法、规则和接口，不含可直接运行的代码。逐字段表见 `references/field_mapping.md`，接口参数见 `references/api_schemas.md`，踩坑见 `references/pitfalls.md`。
> 相较 2026-11-08 版的主要变化：加工单 AB/AD 已改用 OpenAPI 直连取得并通过验证；汇总表改为 Excel 真透视表（不再静态填数）；新增发货金额口径。

## 一、工作簿结构

- 明细表 3 张：`产品管理 - 库存`（74 列，约 1336 行）、`亚马逊销售`（130 列，约 911 行）、`Tiktok 销售`（75 列，约 643 行）。表头在第 2 行，数据从第 3 行开始。
- 汇总表 3 张（**真透视表**，不填数）：`亚马逊销售汇总`、`Tiktok 销售汇总`、`产品管理 - 库存汇总`。
- 辅助 sheet（隐藏）：`_AMZ汇总数据源`、`_TK汇总数据源`、`_PM汇总数据源`。它们用公式引用明细表，作为透视表的数据源。
- `字段数据来源` sheet（约 197 行）：按「所属表 + Excel 列名」给出页面路径、MCP 接口、返回字段。**它与工作簿实际公式有冲突时，以工作簿为准**（见 `field_mapping.md` 备注）。
- 交付文件：每次生成新的带日期文件名，不覆盖源文件。

## 二、铁律

1. **销售类字段 T+1 拉取**：销量、销售额、订单、广告等必须拉前一天数据。当天拉会漏单（实测 310 vs 次日 379）。
2. **只填彩色列**：白色列（标识列、公式列、手填列）不由接口写入。判断依据是单元格填充色，不是列名。
3. **公式列以工作簿为准**：工作簿里是公式的列，即使 `字段数据来源` 写的是 API，也保持公式。写入时按行号重新生成公式，写完必须全表重算。
4. **单价 U 列手工填写**：`产品管理 - 库存` U 列（采购单详情/供应链成本）是白色手填列，不要用 `products_list.cg_price` 代替。U 为空时 T/V/W/X/AC/AE 为 0，发货金额也为 0。
5. **时间窗三类**：
   - 昨日单日：销售类字段，取前一日。
   - 2026 全年累计：列名带「2026年」的字段，以及采购量/待到货量/到货量、加工单（AB/AD）、平台拆分采购量（BO/BP/BQ/BR/BT/BV）。窗口为 2026-01-01 ~ 昨日。
   - 最新快照：产品属性、库存、库龄、期望量、安全库存。
6. **接口返回空 ≠ 不支持**：空数组或空串表示未填写，不能判定为 API 不支持。字段存在但为空，标记为「可查询，空值=未填写」。
7. **只读领星**：所有操作只读，不向领星写入任何数据。
8. **凭据**：AppID/AppSecret 只从环境变量 `LINGXING_APP_ID` / `LINGXING_APP_SECRET` 读取，不写入任何文件、不打印。

## 三、数据源总表

| 数据 | 接口 | 关键参数 / 说明 |
|---|---|---|
| 产品属性 D–S（产品管理） | MCP `products_list` | 分页 length≤500，is_aux=0，product_type∈[1,2]；约 3850 条 |
| 采购量/待到货/到货（Y/Z/AA，国内仓采购单） | MCP `products_purchase_history` | 2026 全年，按季度分 4 段（单次≤90天），按记录 ID 去重，同 SKU 多供应商求和 |
| 平台拆分采购量/时间（BO–BV） | 固定值/手填（11.10 原表） | BO/BQ 为固定采购量，BP/BR/BT/BV 为固定日期，BS=BM-BO，BU=BM-BQ |
| 本地仓/海外仓库存与库龄 | MCP `inventory_detail_list` | 海外仓用 wid_list=海外仓 ID；`max_process_num` 不在返回字段中 |
| 加工单 AB/AD | **OpenAPI 直连** `/erp/sc/routing/inventoryReceipt/StorageProcess/getOrderLists` | type=1 加工单、type=2 拆分单；分页；见 pitfalls #35 |
| 亚马逊产品表现（E–BT、CF–CI、CS、CG、CR 等） | MCP `query_product_performance_asin_lists` | summary_field=sku，summary_field_level2=mid，sids 逗号分隔，同币种店铺一起查；按店铺展开 |
| Listing（BU–CQ） | MCP `erp_listing` | 按 (SKU, 店铺名/seller_name) 匹配，不用 sid；多条取售价非 0 |
| FBA 库存与库龄（CR–DW、DX–EA，11.10 起库龄从 DH 开始） | MCP `get_fba_stock_list` | 按 (SKU, seller_name) 匹配；多条取可用量最大 |
| TikTok 产品表现（D、K–AL、AM–BD 等） | MCP `platform_tiktok_product_analysis_list` | dimension_type=3（SKU）；记录在 `data.data.data`，总数 `data.data.count`；主键 local_sku；分页 page_num/page_size |
| TikTok 平台费用（BE–BW） | MCP `finance_settlement_profit_list` | queryMode=1，summaryField="4"（SKU），camelCase 字段；只覆盖当天有结算单的 SKU，其余保留原值 |
| 店铺列表 | MCP `get_multi_platform_shop_list` | platform_code：10001 亚马逊，10011 TikTok；TK 店铺用长 store_id（s_id 全为 0） |
| 物流费用（如需） | MCP `get_head_logistics_fee_items_by_ref_order_no` | fee_type=2 才是实际费用，fee_type=1 为预估 |

接口返回字段的实际名称以 `references/pitfalls.md` 第 28 条的实测校正为准（如亚马逊退款率是 `return_rate`，不是 `refund_rate`）。

## 四、按表填写流程

### 步骤 1：准备
- 确认环境变量已设置；确认 MCP 连接有效（`code:102 / MCP Key无效` 需在 MCP 管理页重新生成 Key 并重建连接）。
- 关闭已打开该工作簿的 Excel/WPS，否则保存失败。
- 复制源工作簿为工作副本，在副本上操作。

### 步骤 2：拉取数据
- 对每个接口按上表参数分页拉取，大响应落盘后分批读取。
- 2026 全年类接口按季度分段，合并时按记录 ID 去重。
- 加工单：拉 type=1 与 type=2 全部记录，保留 `ware_house_name`、`status`、`product_list`。

### 步骤 3：写入明细表
- 产品管理：按 SKU 写入 D–S、Y/Z/AA、AK–BL（本地仓）、AY–BL（海外仓）、BO–BV 等彩色列。AB/AD 按加工单聚合写入。
- 亚马逊销售：按 (SKU, 店铺) 写入产品表现；店铺用 `store_id` 或店铺名映射到 sid。Listing 与 FBA 按 (SKU, 店铺名) 匹配。
- Tiktok 销售：按 (SKU, 店铺 store_id) 写入；D 售价取 `base_info_list` 中该店铺的挂牌价。
- 多行冲突：同 SKU 多供应商 → 采购量求和；同 (SKU, 店铺) 多条 FBA 库存 → 取可用量最大；Listing 多条 → 取售价非 0。
- 写入规则：新值为空时保留旧值（None 不覆盖）。接口整列返回空时保留原值，不清空。
- 跳过白色列与公式列，公式列按行号重写。

### 步骤 4：公式重算
- 用 Excel COM 打开工作副本，`CalculateFull()` 后保存。openpyxl 写入的公式没有缓存值，不重算会显示为文本或 0。

### 步骤 5：生成汇总透视表
- 运行 `C:\Users\Administrator\领星自动化\build_pivot_summary.py`（COM 脚本）。它会：
  1. 复制源工作簿到 `DST`（脚本顶部设置，每次运行前改成当日日期，避免覆盖上一版）；
  2. 在隐藏辅助 sheet 中用公式引用明细表；
  3. 清空汇总 sheet，创建三张透视表。
- 脚本中的 `*_last` 行号取自当前数据末行。明细行数变化后需要同步修改，否则会漏掉新行。
- 明细表数据更新后，在 Excel 中「全部刷新」透视表。

### 步骤 6：验证
- **版本间单调性**（最有效）：与上一版比较，采购量/待到货/到货量应只增不减。出现减少说明时间窗、去重或店铺展开有误。
- **抽样对比**：每张表抽 30 个 SKU，只比对彩色字段，Excel 当前值与领星最新数据逐项对比，目标通过率 95%+。
- **字段名核对**：新接口字段先取一条真实记录，用 `sorted(rec.keys())` 确认字段存在，再写映射。不要直接信字段数据来源 sheet 的字段列。
- 汇总表：用 COM 读取 `PivotTables().Count` 确认是真透视表；检查发货金额合计是否为 0（为 0 通常是 U 列单价为空）。

### 步骤 7：交付
- 交付文件放在下载目录，名称带日期；源文件不改。
- 发给他人前确认：没有遗留的 `~$` 锁文件，没有残留的旧版本文件。

## 五、时点列（采购时间 / 到货时间 / 发货时间）— 11.10 版

这些列不是查出来的日期，是用「可售天数」倒推的时点。基准日 = **获取数据当天**（DATE(2026,11,9)）。

| 平台 | 30日销量 | 总库存 | 可售天数 | 70天余量 | 触发条件 |
|---|---|---|---|---|---|
| 亚马逊 | CG | CW = CS+CT+CU+CV | CY = CW/CG×30 | CZ = CY−70 | DA = IF(CZ≤7, CZ, "") |
| TikTok | L | Z = W+AI | Y = Z/(L/30) | AB = Y−70 | AC = IF(AB≤7, AB, "") |

**亚马逊时间字段链（DB~DG）**：
- DB 发货时间 = 基准日（2026-11-09），仅 DA 有值时。公式：`=IF(DA3<>"",DATE(2026,11,9),"")`
- DC 到货时间（表头「发货时间+40天」）= 11.10 原表仅 1 个单元格有值，其余为空。规则待确认，暂不写入。
- DD 发货数量 = (7−DA) × CG/30（补满 7 天周期）。
- DE 采购量 = CG/30 × 15（**仅当 DA/DB/DD 均有值时才生效**）。
- DF 到货时间 = 发货时间 + 7 天。公式：`=IF(DB3<>"",DB3+7,"")`
- DG 采购时间 = 发货时间 + 45 天。公式：`=IF(DB3<>"",DB3+45,"")`

**TikTok 时间字段链（AD~AH）**：
- AD 发货时间 = 基准日（2026-11-09），仅 AC 有值时。公式：`=IF(AC3<>"",DATE(2026,11,9),"")`
- AE 发货数量 = (7−AC) × L/30。
- AF 采购量 = L/30 × 15（**仅当 AC/AD/AE 均有值时才生效**，与亚马逊统一）。
- AG 到货时间 = 发货时间 + 7 天。公式：`=IF(AD3<>"",AD3+7,"")`
- AH 采购时间 = 发货时间 + 45 天。公式：`=IF(AD3<>"",AD3+45,"")`

11.10 原表中 DF 有 155 行 +7、DG 有 78 行 +45、AG 全部 +7、AH 有 190 行 +45；其余 DG 78 行、AH 11 行偏移 1–32 天，来源未确认。以上规则是按 11.10 基准日（2026-11-09）推算的，每周重新生成时需人工核对这些偏移行。

- 30日销量为 0 时留空，避免除零。

## 六、汇总表口径（透视表）

| 汇总表 | 行字段 | 值字段 | 说明 |
|---|---|---|---|
| 亚马逊销售汇总 | SKU | 最早发货时间（发货时间 DB，MIN）、发货数量合计（DD，SUM）、发货金额合计（SUM） | 发货金额 = 发货数量 × PM 单价（U 按 SKU 取） |
| Tiktok 销售汇总 | SKU | 最早发货时间（AD，MIN）、发货数量合计（AE，SUM）、发货金额合计（SUM） | 同上 |
| 产品管理 - 库存汇总 | 时间、SKU；筛选「是否有采购=是」 | 亚马逊采购量合计（SUMIFS DE）、亚马逊最早采购时间（MINIFS DG）、TikTok采购量合计（SUMIFS AF）、TikTok最早采购时间（MINIFS AH）、采购金额合计（AG） | 时间 = 2026-11-09（DATE 公式） |

**发货金额口径（用户已确认）**：明细表中没有该列，按「发货数量 × PM 单价」计算。

**注意**：
- 采购时间取 DG/AH（采购时间列），**不是** DB/AD（发货时间列）。曾误用发货时间列，已修正。
- 日期字段的数字格式使用 `yyyy-mm-dd;;`，使无值的 0 显示为空白。
- 透视表不能直接用 openpyxl 创建，必须通过 Excel COM。

## 七、已知问题与状态

| 项目 | 状态 | 处理 |
|---|---|---|
| 加工单 AB/AD | 已解决（OpenAPI） | 见 pitfalls #35 |
| 最大可加工量 AK/AY | 库存明细接口无此字段 | 保留原值，不用其它字段替代 |
| 亚马逊 E 自动标签、断货时间 | 账号无源数据 | E 留空；AM 用公式代替 |
| 亚马逊 F 产品标签 | product_tags 为空 | 用产品库 global_tags 兜底 |
| TK BE–BW 平台费用 | 仅覆盖有结算单的 SKU | 其余保留原值 |
| 亚马逊 V 2026年净销售额同比 | 字段数据来源未列出 | 待核实同比口径 |
| 签名 sort_keys | 代码与记忆笔记不一致 | 待实测：`lingxing_direct.py` 第 42 行对嵌套参数使用了 sort_keys=True，记忆笔记写的是不加。顶层参数不受影响 |

## 八、注意事项

- 不把 API 密钥写进文件，用环境变量。
- 白色列、公式列、模板原值改动前先备份。
- `字段数据来源` 与工作簿公式冲突时，以工作簿为准；与本 skill 冲突时，以本 skill 的实测结论为准。
- 派生的采购时间、发货时间等列依赖「今天」，每次运行的结果会不同。

## 九、调用方式（MCP / OpenAPI 直连）

**MCP（领星 LingXing-MCP）**
- 所有 MCP 接口通过 `mcp__LingXing-MCP__action` 调用，参数为 `toolId`（接口名）和 `params`（业务参数）。
- 调用前用 `mcp__LingXing-MCP__help`（按名称或描述搜索）找到 toolId，再用 `mcp__LingXing-MCP__search`（传 toolId）获取完整 inputSchema。
- 返回很大（单次常超 25 万字符），会落盘到 tool-results 目录。用脚本读取该文件并解析 JSON，不要直接读进上下文。
- 只用读类接口（toolType=read）。`settings_exchange_rate_update` 等 write 类接口不用于取数。

**OpenAPI 直连（加工单等 MCP 不完整的接口）**
- 域名：`openapi.lingxing.com`。先用 AppID/AppSecret 换取 access token（有效期约 2 小时）。
- 签名：参数按 key 排序拼接（空值跳过），MD5 转大写，再用 AppID 做 AES（ECB，PKCS7）加密，Base64 编码。
- 直连时不走本地代理（代理下 SSL 握手常超时）。
- 实现见 `C:\Users\Administrator\领星自动化\lingxing_direct.py`。

**环境变量**：`LINGXING_APP_ID`、`LINGXING_APP_SECRET`，只从环境变量读取。

## 十、公式列详情（写入后必须全表重算）

**产品管理 - 库存**
- Q、T、V、W、X、AC、AE、AF、AG、AH、AI、AJ、AT、BH、BM、BN：按工作簿公式保留。
- BO、BP、BQ、BR、BT、BV：11.10 原表为固定值/手填，不由脚本写入。
- BS = BM−BO，BU = BM−BQ。

**亚马逊销售**
- CW = CS+CT+CU+CV（FBA 总库存）；CY = CW/CG×30（预估可售天数）；CZ = ROUND(CY−70)。
- DA = IF(CZ≤7, CZ, "")（周快照，只保留 ≤7 天的值）。
- DB 发货时间 = 基准日（2026-11-09），DA 有值时；DC 11.10 原表为空；DD 发货数量 = (7−DA)×CG/30。
- DE 采购量 = CG/30×15（**仅当 DA/DB/DD 均有值时才生效**）。
- DF、DG：发货时间 +7 / +45 天（见第五节）。

**Tiktok 销售**
- I = AP−U−BC，J = AQ−V−BD。
- Y（可售天数）、Z、AA、AB = ROUND(Y−70)、AC = IF(AB≤7, AB, "")。
- AD 发货时间 = 基准日（2026-11-09），AC 有值时；AE 发货数量 = (7−AC)×L/30。
- AF 采购量 = L/30×15（**仅当 AC/AD/AE 均有值时才生效**）。
- AG、AH：发货时间 +7 / +45 天（见第五节）。

## 十一、补数顺序（每次填充）

1. 产品属性 → 产品管理 D–S。
2. 采购报表 → 产品管理 Y/Z/AA（2026 全年，季度分段）。
3. 加工单（直连）→ 产品管理 AB/AD。
4. 库存明细 → 本地仓、海外仓列（AK–BL）。
5. 亚马逊产品表现 + Listing + FBA → 亚马逊销售（同一时点的 FBA 数据一次取完）。
6. TikTok 产品表现 → Tiktok 销售；TikTok 平台费用 → BE–BW。
7. 写入公式列（按行号重写），全表 CalculateFull 重算。
8. 派生列：DB/DD/DE（亚马逊）、AD/AE/AF（TK），产品管理 BS/BU。
9. 核对（见第十二节），通过后再交付。

## 十二、核对清单

- **币种**：汇总前检查亚马逊（CNY）与 TK（USD）金额是否已换算。汇率 = 7.0（2026-11-10 实测）。
- **版本间单调性**：采购量、待到货、到货量只增不减；减少说明时间窗、去重或店铺展开有误。
- **抽样对比**：每张表抽约 30 个 SKU，只比对彩色字段，与领星当前数据逐项对比，目标 95%+。
- **FBA 快照**：同一行的 CR–CV 应来自同一次拉取。
- **空值**：接口整列返回空时保留原值，不清空；`None` 不覆盖已有值。
- **主表与销售表 SKU 并集**：销售表里的 SKU 不一定在库存主表里（2026-11-10 发现 40 个，合计约 4.7 万销售额）。
