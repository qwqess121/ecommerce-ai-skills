---
name: lingxing-logistics-backfill
description: "把员工上传的海运费用明细表格，回填到领星 ERP 的物流信息（物流商单号、物流商、物流渠道、快递单号、物流费用）。支持 FBA 发货单（SP26）、OWS 海外仓备货单（OWS）、TK FBT 多平台发货单（SP2026+11位）。触发词：回填海运费用、同步表格到领星、更新发货单物流信息、回填快递单号和金额。"
metadata: {"owner":"AB America Corp / HOOGALIFE","status":"active","last_verified":"2026-11-06 解析/计划/读取(直连)通过；FBA STA 快递号接口(listShipmentBoxes/updateShipmentTrack)已验证；写入接口未在本批次实测"}
---

# 领星 ERP 物流信息回填

## 一句话流程

员工上传表格 → 解析 → 读 ERP 现值 → 生成回填清单（按类别分组）→ 员工确认 3 个示例 → 写入 3 个示例 → 员工去领星核对 → 员工同意后批量写入 → 再读 ERP 验证位置是否正确 → 输出报告。

**Claude 不得跳过任何一步，写入前必须有员工明确的 yes。**

## 文件与脚本

- 脚本：`scripts/backfill_logistics.py`（同目录），四个子命令：
  - `parse --xlsx <表格>` → `groups.json`（纯本地，不联网）
  - `plan --erp erp.json` → `plan.json` + `plan.md`（纯本地，不写入）
  - `write --erp erp.json [--sn ...] [--execute]` → 调用写入接口（**会写入 ERP**，不加 `--execute` 只打印请求体）
  - `verify --erp-after erp_after.json [--sn ...]` → 核对写入后的值（纯本地）
- `erp.json` / `erp_after.json` 由 Claude 通过 MCP 读取 ERP 后生成，格式见下方"ERP 现值文件格式"。
- 环境变量（仅 write 需要）：`LINGXING_APP_ID`（16 位）、`LINGXING_APP_SECRET`（24 位）。**不要把它们打印到对话或写进文件。**
- 依赖：`openpyxl`、`pycryptodome`（Crypto.Cipher）。

## 第 1 步：解析表格

```bash
python scripts/backfill_logistics.py parse --xlsx "<员工表格路径>" --out groups.json
```

输出：每个备货单的行列表（每行含 F/G/H/I/Q 原始值）+ 表格问题清单（如 F 列含顿号、F 列重复）。
把问题清单原样告诉员工，需要员工确认的不要自作主张。

### 表格列（Sheet1，1 起始列号）

| 列 | 含义 | 用途 |
|---|---|---|
| A | 序号 / 第几周 | **行有效性**：A 列不是数字 → 整行跳过（空行、底部备注） |
| C | 备货单号（**合并单元格**） | 决定每行属于哪个备货单 |
| E | FBA 号 / IBR 货件号 | 仅佐证，不写入 |
| F | 货代单号 = 物流商单号 | 回填 A 类字段 |
| G | 快递单号 | 回填 B 类字段；值为"卡派"不写入 |
| H | 出货方式 = 渠道 | 回填 A 类字段（需映射，见下） |
| I | 货代 = 物流商 | 回填 A 类字段 |
| Q | 金额 = 实际物流费 | 回填 B 类字段；按备货单**求和** |

### 行归属规则（必须遵守，不能向下补全）

1. C 列合并单元格块内的所有行 → 归属该块的备货单号。
2. 非合并且 C 列有有效单号（SP26/SP2026/OWS 开头）→ 归属该单号，并设为"当前单号"。
3. 非合并且 C 列为空 → 继承"当前单号"；但**进入合并块后"当前单号"清空**。
4. 当前单号为空时 → 跳过（孤儿行）。
5. A 列非数字的行先整行跳过，再做上面的判断。

这条规则是为了避免"向下补全"把底部空行和其他单据的行错误地归到前一个备货单（例如 SP261103005 原本被错误归入 15 行，实际只有 1 行）。

### 聚合规则（一个备货单多行）

| 字段 | 聚合方式 |
|---|---|
| F 物流商单号 | 非空值按行序用英文句点 `.` 拼接，例 `90026373.90026374.90026375` |
| G 快递单号 | 每行一个，去掉"卡派"，逐条写入 |
| Q 金额 | 所有行求和（含"卡派"行的金额，和 Q 列为 0 的行） |
| I 物流商 / H 渠道 | 取第一个非空值 |

注意：金额为 0 的行仍然参与快递号收集（例如 OWS260722003 的 Q=0 但 G 有单号）。旧版规则"跳过金额为 0 的行"已废弃。

### 表格问题（需员工确认，不自动处理）

- F 列含 `、`、`，`、空格 → 格式可疑（例 OWS261027001 写的是 `90020493、90020494`）
- F 列同一备货单内重复（例 OWS260811003 为 `90026387.90026387`）
- 同一物流单号出现在两个备货单（例 90026150 同时在 OWS260720003 和 OWS260722001；1ZH0720G0444230793 同时在 SP260916006 和 SP260916007）— 需员工确认是否表格错误

## 第 2 步：读 ERP 现值

### 首选：直连读取（脚本 `read`，只读，约 2 分钟读完 69 单）

```bash
python scripts/backfill_logistics.py read --groups groups.json --out erp.json
```

- 需要环境变量 `LINGXING_APP_ID` / `LINGXING_APP_SECRET`，并且本机能连通 `openapi.lingxing.com`（需在 ERP 开放平台白名单内）。
- FBA：`getInboundShipmentListMwsDetailList` 每批 50 个，一次读出物流商单号、渠道、快递号（`track_list` 中 `order_type_code=5`）、金额（`actual_expenses_list.logistics_fee`）。
- OWS：`basicOpen/overSeaWarehouse/stockOrder/detail` 逐单读，物流商单号/物流商/渠道在 `logisticsInfo.head_logistics_info`，快递号在 `head_logistics_tracking_info[].tracking_no`，金额取 `head_logistics_fee_info` 中 `fee_type=2` 的 `logistics_fee`。
- FBT：`basicOpen/multiplatform/query/shippingList` 逐单读，取 `logisticsDetails[]`。
- 读取失败的单号会打印 `[读取失败]`，不会写入 erp.json，需要重跑或用 MCP 补读。

### 备用：MCP 读取（直连不可用时，Claude 逐单调用）

按备货单类型读取，**每个备货单都要读**，结果整理成 `erp.json`。

| 类型 | MCP 工具 | 参数 | 取值 |
|---|---|---|---|
| FBA | `get_delivery_order_list` | `seniorSearchList=[{search_field:"shipment_sn", search_value:[最多5个SN]}]`, `length=50` | 顶层 `logistics_tracking_number`、`logistics_provider_name`、`logistics_channel_name`、`actual_total_fee`、`tracking_list` |
| OWS | `overseas_inbound_list` | `overseas_order_no="OWS..."`, `page_size=5` | 顶层 `logistics_tracking_number`、`logistics_provider_name`、`logistics_way_name`（渠道） |
| OWS 快递号 | `overseas_stock_order_detail` | `overseas_order_no="OWS..."` | `ext_data.express_no`（空串=未填）。注：列表接口的 `ext_data.express_no` 与此一致，可从列表结果直接取 |
| OWS / FBA 金额 | `get_head_logistics_fee_items_by_ref_order_no` | `fee_type=2`, `ref_order_no="备货单号"` | `data[].logistics_fee`（空=未填；**只用 fee_type=2**） |
| FBT | `platform_query_shipping_list` | `platformCodes=["10011"]`, `searchField=2`, `searchSingleValue="SP2026..."`, `length=20`, `offset=0` | `list[].logisticsDetails[]` 的 `logisticsNumber`、`trackingNumber`、`transportationCost`；顶层 `logisticsProviderId`、`logisticsChannelName` |

- **`logistics_money_status` 不是金额是否填写**（1=未结算，3=已结算）。判断金额是否已填，只看费用接口的 `logistics_fee`。
- FBA 的 `logistics_provider_name` / `logistics_channel_name` 为空字符串时，表示 ERP 未填，不是接口不返回。
- FBT 的 `logisticsProviderName` 可能为空，用 `logisticsProviderId` 按下方物流商 ID 表反查名称。
- MCP 调用较慢，尽量批量：FBA 每次最多 5 个 SN；OWS 目前只能一单一次（`overseas_inbound_list` 不支持批量）。

### ERP 现值文件格式（erp.json / erp_after.json）

```json
{
  "FBA": {
    "SP260806004": {"tracking_number": "90026373.90026374.90026375", "provider_name": "捷立信",
                    "channel_name": "海卡", "tracking_list": [], "fee": "3322.00",
                    "fba_shipments": [{"shipmentConfirmationId": "FBA19...", "sid": 17201}]}
  },
  "OWS": {
    "OWS260928004": {"tracking_number": "OWS260928004", "provider_name": "广州合信物流",
                     "channel_name": "海运", "tracking_list": [], "fee": "8178.00"}
  },
  "FBT": {
    "SP202610230040001": {"tracking_number": "", "provider_name": "万达", "channel_name": "海运",
                          "fee": "0.00", "logisticsInfo": []}
  }
}
```

- `provider_name` 可以是全称（脚本按包含关系识别，如"广州合信物流"→合信）。
- `channel_name` 用 ERP 的渠道名（海卡 / 空运 / 海运 / 快递）。
- FBA/OWS 的 `tracking_list` 是快递号字符串数组（ERP 为空则 `[]`）。
- FBA 的 `fba_shipments` 是 `[{shipmentConfirmationId, sid}]` 数组，来自 `getInboundShipmentListMwsDetailList` 的 `items[].shipment_id` 和 `items[].sid`（STA 快递号写入必需）。
- FBT 的 `logisticsInfo` 原样保存 ERP 明细（每个元素含 `logisticsNumber`、`trackingNumber`、`transportationCost`、`transportationCurrency`）。

## 第 3 步：生成回填清单（plan）

```bash
python scripts/backfill_logistics.py plan --erp erp.json --out plan.json
```

生成 `plan.md`，结构：汇总 → 写入 → 覆盖 → 需人工。**按类别分组给员工看**，不要逐单堆数据。

### 字段规则

| 字段 | 表格列 | 类型 | ERP 空 | ERP 有值且不同 | 表格空 |
|---|---|---|---|---|---|
| 物流商单号 | F | A 类 | 写入 | **覆盖** | 跳过 |
| 物流商 | I | A 类 | 写入 | **覆盖** | 跳过 |
| 物流渠道 | H | A 类（FBT 不写，跟随物流商自动关联） | 写入 | **覆盖** | 跳过 |
| 快递号 | G | B 类 | 写入 | 跳过（不覆盖） | 跳过 |
| 金额（实际物流费 = logistics_fee） | Q | B 类 | 写入（ERP 为 0.00 也视为空） | 跳过，列出差额待确认 | 跳过（表格为 0） |

### 物流商 ID（I 列 → ERP 物流商 ID）

| 表格 I 列 | 物流商 ID | ERP 名称 |
|---|---|---|
| 捷立信 | 10125 | 捷立信 |
| 万达 | 10697 | 万达物流商 |
| 积米 | 15889 | 广州积米 |
| 合信 | 16001 | 广州合信物流 |
| 联宇 | 13130 | 联宇 |

### 渠道 ID（物流商 + 渠道名 → 渠道 ID）

| 物流商 | 渠道名 | 渠道 ID | 来源 |
|---|---|---|---|
| 捷立信 | 海卡 | 14316 | `logistics_provider_list` / `fba_plan_logistics_channels` |
| 捷立信 | 空运 | 14993 | 同上 |
| 万达 | 海运 | 35158 | 同上 |
| 万达 | 空运 | 15805 | 同上 |
| 积米 | 海运 | 30589 | 同上 |
| 合信 | 海运 | 27570 | 同上 |
| 联宇 | 快递 | 22109 | 同上 |

表格 H 列 → 渠道名的判断（脚本内置，见 `map_channel`）：
- 捷立信：H 含"空" → 空运；H 含"海运" → **冲突（捷立信无海运）**；其他（以星海派 / 以星卡派 / 以星海卡 / 美森 / 美国干货 / UPS / ZIM 等）→ 海卡。
- 万达：H 含"空" → 空运；H 含"海" → 海运。
- 积米、合信：H 含"空" → **冲突（只有海运）**；否则海运。
- 联宇：任何 H → 快递（Z快线 / 穿越 等路线名都归联宇快递）。
- H 列名称不在脚本的已知列表里（例如"深圳UPS特快"）→ **需人工**，不自动映射。

### 已知冲突（需员工确认后再决定）

- OWS260928003：捷立信 + 海运
- OWS260930001、OWS261008001：合信 + 空运
- FBA SP260916006、SP260916007：合信 + 空运
- OWS260807001：H = 深圳UPS特快（不在已知列表）

**FBT 写入方式（覆盖式 logisticsInfo，逐行合并）**：表格第 n 行对应 ERP 第 n 条明细。F 列以表格为准覆盖；G、Q 列 ERP 已有值则保留，为空才写表格值；FBT 不写渠道。

**金额口径**：Q 列对应 ERP 的实际物流费（logistics_fee）。ERP 里其他费用（other_fee_arr）不参与对比。注意：部分单据表格金额等于 ERP 的物流费 + 其他费用合计（如 SP261008003：物流费 0 + 其他费用 961 = 表格 961），按此口径写入会造成其他费用重复计入，需员工确认。

## 第 4 步：员工确认（先 3 个示例）

plan 生成后，Claude 必须给员工看：

1. 汇总：各字段的 写入 / 覆盖 / 跳过 / 需人工 数量。
2. **三个示例**：每种类型选一个有写入动作的备货单（FBA、OWS、FBT 各一个），逐字段列出 ERP 现值 → 表格值 → 操作。
3. 表格问题清单（第 1 步的 issues）。
4. 问员工："这三个示例是否回填？"

员工回答 yes 后，执行第 5 步。

## 第 5 步：写入示例 → 员工去领星核对

```bash
python scripts/backfill_logistics.py write --erp erp.json --sn <示例SN1> <示例SN2> <示例SN3>            # 先预览请求体
python scripts/backfill_logistics.py write --erp erp.json --sn <示例SN1> <示例SN2> <示例SN3> --execute  # 员工确认后写入
```

写入后告诉员工去 ERP 页面核对：

| 类型 | 页面路径 |
|---|---|
| FBA 发货单 | FBA → 发货单 → 对应单 → 物流信息（物流商单号、物流商、渠道、实际物流费用） |
| OWS 海外仓 | 仓库管理 → 海外仓 → 入库管理 → 对应入库单 → 物流信息（物流商单号、物流商、渠道、单号追踪、费用明细） |
| FBT 多平台 | 仓库管理 → 多平台发货 → 对应发货单 → 物流信息（物流商单号、物流商、渠道、跟踪号、运费） |

员工确认页面显示正确后，才进入第 6 步。页面不对就停下，回到第 1 步排查，不要批量写。

## 第 6 步：批量写入

```bash
python scripts/backfill_logistics.py write --erp erp.json --execute
```

`write` 会逐单打印请求体并要求输入 `yes`。遇到接口返回错误会停止，写入日志保存在 `plan_write_log.json`。

## 第 7 步：二次验证（必须）

1. 再次用第 2 步的 MCP 工具读取**同一批备货单**，生成 `erp_after.json`。
2. 运行：

```bash
python scripts/backfill_logistics.py verify --plan plan.json --erp-after erp_after.json
```

3. 验证失败的项目列给员工，不要自行再写。

## 第 8 步：报告

- 成功：备货单 | 类型 | 字段 | 写入值 | 旧值 → 新值
- 跳过：原因 + 数量（ERP 已有值 / 表格为空 / 无变化 / 需人工）
- 失败：备货单 | 错误信息
- 统计：处理 X 单，写入 X 单 X 字段，跳过 X 单，失败 X 单，写入金额合计

## 写入接口（OpenAPI 直连，无 MCP 对应）

> 2026-11-06：白名单开通后，**读取接口已直连验证通过**（`read` 子命令，69 单约 2 分钟）。**以下写入接口仍未实测**，沿用 2026-11-04 的记录。第一次写入前必须先用员工确认的示例单验证，并用 `verify` 核对。

| 类型 | 路径 | 请求体要点 |
|---|---|---|
| FBA（物流商单号/物流商/渠道/金额） | `POST /erp/sc/routing/storage/shipment/updateListLogistics` | `{"data":[{"order_sn", "logistics_list_type":1, "logistics_provider_id", "logistics_channel_id", "head_logistics_list":{"logistics_tracking_number", "actual_expenses_list":{"logistics_fee", "logistics_fee_currency":"CNY"}}}]}` |
| FBA 快递号（STA 接口） | 见下方 **FBA 快递号写入（STA 流程）** | 脚本已实现，需先查 boxId 再写 trackingId |
| OWS（全部字段） | `POST /erp/sc/routing/owms/inbound/updateLogistics` | 扁平 body（不用 `data[]`）：`{"overseas_order_no", "logistics_list_type":1, "logistics_provider_id", "logistics_channel_id", "head_logistics_list":{"logistics_tracking_number", "tracking_list":[{"tracking_no", "transport_type":1, "order_type_code":5}], "actual_expenses_list":{...}}}` |
| FBT（全部字段） | `POST /basicOpen/multiplatform/shippingList/updateLogistics` | `{"data":[{"shippingListCode", "logisticsProviderId", "logisticsChannelId", "logisticsInfo":[{"logisticsNumber", "trackingNumber", "transportationCost", "transportationCurrency"}]}]}` |

### FBA 快递号写入（STA 流程）

FBA 的快递号（G 列）**不走 `updateListLogistics`**，必须走 STA 的 `updateShipmentTrack`。完整链路如下：

**第一步：从 FBA 原始数据获取 shipmentConfirmationId 和 sid**

在 `read` 阶段，调用 `getInboundShipmentListMwsDetailList` 时，响应的 `data[].items[]` 中每个 item 有：
- `shipment_id`：亚马逊货件确认号（如 `FBA19JG21CC6`），这就是 STA 接口需要的 `shipmentConfirmationId`
- `sid`：店铺 ID（如 `17201`）

一个 SP26xxx 备货计划可能包含多个 `shipment_id`（每个发往不同 FC）。脚本在 `_fba_from_mws()` 中提取唯一的 `(shipment_id, sid)` 对，保存到 ERP 数据的 `fba_shipments` 数组。

示例：SP260717006 → 4 个 shipment：
```
FBA19JG21CC6 (sid=17201) → AVP1
FBA19JG31LZY (sid=17201) → GYR3
FBA19JG4CXPW (sid=17201) → RDU2
FBA19JG3V9WJ (sid=17201) → LGB8
```

**第二步：查询每个 shipment 的 boxId**

接口：`POST /amzStaServer/openapi/inbound-shipment/listShipmentBoxes`

请求参数（已验证 2026-11-06）：
```json
{
  "sid": 17201,
  "shipmentConfirmationId": "FBA19JG21CC6"
}
```
- `sid`：整数，店铺 ID（从第一步的 items[].sid 获取）
- `shipmentConfirmationId`：字符串，亚马逊货件确认号（从第一步的 items[].shipment_id 获取）
- **注意**：参数名是 `shipmentConfirmationId`，不是 `shipmentNo`、`shipmentId`、`taskId`

返回：
```json
{
  "code": 0,
  "message": "操作成功",
  "data": {
    "shipmentList": [{
      "shipmentPackingList": [
        {"boxId": "FBA19JG21CC6U000001", "localBoxId": "...", "total": 120, "weight": "...", "productList": [...]}
      ]
    }]
  }
}
```
- `boxId` 格式：`{shipmentConfirmationId}U{6位数字}`（如 `FBA19JG21CC6U000001`）
- 每个 shipment 可能有多个 box

**第三步：mapping 快递号到 box**

表格 G 列的快递号按行序排列。所有 shipment 的所有 box 按 shipment 顺序 + boxId 顺序排列后，与快递号一一对应：
- box 总数必须等于快递号总数，否则标记"需人工"
- 第 1 个快递号 → 第 1 个 box（第 1 个 shipment 的第 1 个 box）
- 第 N 个快递号 → 第 N 个 box

示例：SP260717006 有 4 个 shipment 各 1 box = 4 box = 4 快递号
```
FBA19JG21CC6U000001 ← 1Z1B0D750334197834
FBA19JG31LZYU000001 ← 1Z1B0D750333660807
FBA19JG4CXPWU000001 ← 1Z1B0D750312619973
FBA19JG3V9WJU000001 ← 1Z1B0D750300586352
```

**第四步：写入快递号**

接口：`POST /amzStaServer/openapi/inbound-shipment/updateShipmentTrack`

请求参数（已验证端点 2026-11-06，空 trackBOList 返回"跟踪编号列表 不能为空"确认参数名正确）：
```json
{
  "sid": 17201,
  "shipmentConfirmationId": "FBA19JG21CC6",
  "trackBOList": [
    {"boxId": "FBA19JG21CC6U000001", "trackingId": "1Z1B0D750334197834"}
  ]
}
```
- 每个 shipmentConfirmationId 单独调用一次
- `trackBOList` 中每个元素：`boxId`（从第二步获取）+ `trackingId`（表格 G 列的快递号）

**脚本实现**：
- `sta_list_boxes(sid, shipment_confirmation_id)` → 返回 boxId 列表
- `sta_build_track_plan(erp, target_tracks)` → 查询所有 box，mapping 快递号，返回 `(sid, shipmentConfirmationId, trackBOList)` 三元组列表
- `cmd_write()` 中，FBA 的 G 字段单独处理：先写 F/I/H/Q（通过 `updateListLogistics`），再写 G（通过 `updateShipmentTrack`）

**另一种获取 shipmentConfirmationId 的方式（STA 任务详情）**：
接口：`POST /amzStaServer/openapi/inbound-plan/detail`
参数：`{"inboundPlanId": "wf...", "sid": 17201}`
返回：`data.shipmentList[].shipmentConfirmationId`
适用场景：已知 STA inboundPlanId（UUID 格式）时。但通常直接从 `getInboundShipmentListMwsDetailList` 的 items[].shipment_id 获取更方便。

**全量覆盖规则**：`head_logistics_list`（FBA/OWS）和 `logisticsInfo`（FBT）是整体覆盖。脚本会把 ERP 现值原样回传未变化的字段，防止金额或单号被清零。手写请求体时同样必须这样做。

签名：AES/ECB/PKCS5Padding 加密 MD5（大写）。嵌套参数用 `json.dumps(v, separators=(',',':'), ensure_ascii=False)`，**不能 `sort_keys=True`**（否则 2001006）。直连需绕过本机 Clash 代理（`ProxyHandler({})`）。

限流：FBA bucket=2，OWS/FBT bucket=1，每次调用间隔 ≥1.2 秒（脚本已按类型设置）。

## 关键陷阱

1. **表格 A 列不是数字 → 整行跳过**，包括底部备注和空行。
2. **合并单元格归属，禁止向下补全**（见行归属规则）。
3. **金额只看费用接口（fee_type=2）**，不看 `logistics_money_status`。
4. **"卡派" 不写快递号**，但金额照常计入合计。
5. **head_logistics_list / logisticsInfo 是整体覆盖**，漏传会清零。
6. **FBA 快递号不走 updateListLogistics**，要走 STA 的 updateShipmentTrack（脚本已实现，见上方 STA 流程）。
7. **FBT `platform_query_shipping_list` 的 `length` 最小为 20**。
8. **seniorSearchList 每批最多 5 个 SN**（FBA）。
9. **ERP 有占位值**（物流商单号写成发货单号本身、`20260929TC`、快递号写成"卡派"、"以星海卡"等文字）。这类值不要当作真实单号；表格对应位置为空时保持不动，并在报告里列出。
10. 已发现的 ERP 格式差异：FBA SP260717006 的 ERP 物流商单号是缩写 `90026153.154.155.166`（末位 166 与表格 156 不一致）。脚本统一用完整拼接写入。

## 独立提示词（发给员工）

员工在 Claude Code 中粘贴下面这段即可：

```
请帮我把海运费用明细表格回填到领星 ERP。
表格路径：<员工填写的文件路径>

请按以下步骤做，每一步都等我确认：
1. 解析表格，告诉我识别到几个备货单（FBA/OWS/FBT），以及表格问题。
2. 读取 ERP 现状（用 MCP 工具），整理成 erp.json。
3. 生成回填清单，按"写入/覆盖/跳过/需人工"分组给我看。
4. 给我三个示例（FBA、OWS、FBT 各一个），逐字段显示 ERP 现值→表格值→操作，我确认后才写入这三个。
5. 写完后告诉我去领星哪个页面核对，我确认没问题后再批量写入。
6. 批量写入后，再次从 ERP 读取，核对是否写到了正确位置，最后给我报告。

规则：
- 物流商单号、物流商、渠道：表格有值且和 ERP 不同 → 覆盖；ERP 为空 → 写入；表格空 → 不动。
- 快递单号、金额：ERP 为空才写入；ERP 有值绝不覆盖（金额差异只列出来，不写）。
- 任何写入前必须我明确回复 yes。
```
