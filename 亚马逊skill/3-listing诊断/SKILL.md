---
name: m3-listing-diagnosis
description: "模块 3 · Listing 诊断：抓取本品与真竞品的 listing、图片和 A+，用八维评分（九项）打分，输出 模块3-Listing诊断-<ASIN>.md（输出格式固定在本目录 references/）。"
---

# 模块 3 · Listing 诊断

流程见 `M3-ORCHESTRATOR.md`，依赖模块 1 的真竞品结果。

## 本目录内的资料

- `references/输出格式强制规定.md`、`references/格式检查清单.md`、`references/报告格式规范.md`。
- `references/章节标题.json`：本模块章节标题（22 条，取自参考标题 Xk3D）。

## 随附脚本

- 抓取脚本位于 `../2-竞品销售策略分析/amazon-review-insights/scripts/`：`amazon_listing_capture.js`、`amazon_image_capture.js`。

## 共享资料（亚马逊skill 根目录下）

- `../工具/八维评分.py`：九项评分（满分合计 100），档位表见 `M3-ORCHESTRATOR.md`。
- `../共享规则/取数/`、`../共享规则/交叉验证规则.md`。

## 输出

- 模块报告：`REPORT/模块3-Listing诊断-<OWN>.md`。
