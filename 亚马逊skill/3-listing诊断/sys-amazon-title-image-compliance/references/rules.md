# 默认规则与覆盖说明（rules.json）

`amazon_compliance.py` 的规则全部由 `rules.json` 驱动。运行 `make-rules` 导出模板后，按需求人附件修改对应字段即可，引擎逻辑不变。

## title 段

| 字段 | 默认 | 含义 / 覆盖方式 |
|---|---|---|
| `max_length` | 200 | 标题最大字符数（含空格）。部分类目更短（如消费类 80/150），附件给定类目上限时改这里。 |
| `forbidden_symbols` | `! $ ? _ { } ^ ¬ ¦ ~ # < > *` | 命中的符号被移除。品牌名含这些符号时，从数组里删掉该符号。 |
| `exempt_small_words` | in/on/over/with/and/or/for/the/a/an/of/to/by/from | 不计入重复词限制，且非首词时小写。 |
| `promo_phrases` | free shipping / 100% quality / best seller / top rated / hot item / high quality ... | 大小写不敏感，命中整段移除。公司禁用语增补在此。 |
| `single_word_promo` | super / premium / new / best / top / hot / great / amazing / perfect / genuine | 单字促销形容词，**仅改写模式剔除**（合规模式保留）。 |
| `preserve_case_words` | USB / LED / DIY / IPX / TWS / PC / TSA / HD / SD / TV / AI / VR / AR / 3D / WiFi / iPhone / iPad / MacBook / AirPods | **保留原始大小写的词**（缩写/品牌名）。Title Case 时命中即输出规范写法，不会被小写化（如 `usb`→`USB`、`iphone`→`iPhone`）。品牌名被误小写时，把品牌名加进此列表即可。 |
| `max_word_repeat` | 2 | 同一词允许出现次数（>2 移除多余）。 |
| `singular_plural_as_duplicate` | true | 单复数按去尾 s 归一判重（apple/apples 算重复）。 |

## image 段

| 字段 | 默认 | 含义 |
|---|---|---|
| `key_field` | sku | 图片命名主键，可改 `asin`。 |
| `format` | jpg | 输出扩展名。 |
| `padding` | 2 | 附图序号位数，如 `_01`、`_02`。 |

## 命名结果

- 主图：`{key}.jpg`
- 附图：`{key}_01.jpg`、`{key}_02.jpg` …

## 处理顺序（保证可复现）

去促销语 → 去禁用符号 → 合并空白 → 去重词 → 按词边界截断 → 首字母大写

## 官方依据

- 亚马逊商品名称新规，2025-01-21 生效；适用所有卖家与品类（媒体类目除外），覆盖所有站点。
- 各站点/类目细节以卖家平台帮助页「商品名称要求和指南」为准；类目长度例外清单从该页获取。
