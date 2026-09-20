# 模块四：广告策略分析

> 本文件是给人看的目录说明，不是可调用的 skill。每个子目录下的 SKILL.md 才是实际工作流。

## 这个模块解决什么问题

Listing 上架之后（或上架前就要规划），把模块二找到的关键词和竞品情报，转成实际的广告结构——Campaign 怎么分、出价多少、否词怎么加、预算怎么分配。依赖模块二的关键词数据，也依赖模块三的Listing是否已经优化好——Listing没做好，广告引流量也是浪费。

---

## 详细清单（含数据获取与评判标准）

### amazon-ppc-campaign — PPC Campaign构建与优化
**定位**：模块四里最核心、最详细的技能，Build和Optimize两种模式覆盖从0到持续运营的全生命周期。
**工作流**：
- Build模式：收集产品信息（成本/预算）→ 算ACoS目标（Break-even/Target/Max CPC）→ 收集关键词 → 建4个Campaign结构（Auto/Manual Exact/Manual Broad/产品定向）→ 设初始出价 → 建否词种子清单 → 生成21天Launch Schedule
- Optimize模式：收集Campaign数据 → 五维度绩效审计 → 关键词漏斗分析 → 出价调整 → 生成4周行动计划
**获取数据 / 用哪个MCP**：SIF `ads_get_asin_ad_structure`（完整广告结构，Optimize模式自动获取）、`ads_get_asin_ad_traffic_trend`、`ads_get_campaign_contribution_breakdown`、`ads_get_ad_group_keyword_breakdown`、`market_get_keyword_demand`；卖家精灵 `keyword_miner`；sys-amazon-ads MCP `ask_report_analyst`（拉搜索词报告，替代手动CSV）
**评判标准**：
- Max CPC = 售价 × Target ACoS × 转化率，作为出价硬上限，任何出价建议不得超过这个数字
- 出价调整规则：ACoS>200%降30-50%，100-199%降20%，达标区间±10%不动，低于目标涨10-20%，10+点击0单直接暂停
- 关键词升级规则：Auto/Broad里出现≥2单转化的词，必须升级到Exact精确匹配
- 否词规则：≥20点击0单的词，或点击量占比高但转化率远低于账户均值的词，加入否词清单

### amazon-advertising-strategy — 综合广告策略
**定位**：全局预算和架构规划，不是单个Campaign的调优。
**工作流**：策略开发与Campaign架构 → Campaign设置与优化实施 → 绩效管理与战略扩张
**获取数据 / 用哪个MCP**：SIF `ads_get_asin_ad_structure`（当前结构和预算分布）、`ads_get_asin_ad_feature_profile`、`ads_get_asin_campaign_contribution_overview`
**评判标准**：
- 预算分配基准：SP 65% / SB 25% / SD 10%，实际比例偏离基准超过15个百分点需要说明原因
- ACoS超出目标区间超过2个月未改善，判定需要重新做全盘架构，不只是局部调优

### amazon-dayparting-strategy — 分时出价策略
**工作流**：收集信息 → 追问补全 → 研究分析（分时段流量数据）→ 交付建议
**获取数据 / 用哪个MCP**：SIF `ads_get_campaign_traffic_trend`；sys-amazon-ads MCP `ask_report_analyst`
**评判标准**：某时段转化率低于全天均值50%以上，判定该时段应降低出价或暂停投放；高峰时段（转化率超均值30%以上）应提高出价争取更多曝光

### amazon-negative-keywords — 否定关键词管理
**工作流**：搜索词分析与浪费评估 → 策略性否词实施（三层）→ 性能监控与持续优化
**获取数据 / 用哪个MCP**：SIF `ads_get_ad_group_keyword_breakdown`；sys-amazon-ads MCP `ask_report_analyst`；配合 `sys-wasted-ad-spend-dashboard` 做可视化
**评判标准**：
- Tier1（完全无关词）：任何与产品品类不符的搜索词，立即精确否词
- Tier2（基于表现的变体）：≥10次点击且0转化，加否词
- Tier3（品牌保护）：竞品品牌词若转化率远低于账户均值，纳入否词考虑

### amazon-display-ads — Sponsored Display广告
**工作流**：受众研究与定向策略 → 创意开发与Campaign设置 → 绩效优化与扩张
**获取数据 / 用哪个MCP**：SIF `ads_get_asin_ad_structure`；sys-amazon-ads MCP `ask_report_analyst`；Canva `generate-design`
**评判标准**：产品定向出价基准$0.50-1.50，兴趣定向$0.25-0.75，再营销$0.75-2.00，超出区间需要说明理由；再营销Campaign的转化率应显著高于新客获取Campaign，否则判定受众定向有问题

### sys-amazon-ads / sys-amazon-ads-marketplace — 广告MCP管理（全自动）
**工作流**：身份确认 → 性能报告查询 → Campaign结构浏览 → 优化建议 →（可选）写操作
**获取数据 / 用哪个MCP**：Marketplace Ad Pros MCP 原生（`whoami`/`list_brands`/`ask_report_analyst`/`list_resources`/`create_resources`/`update_resources`）
**评判标准**：账户级ACoS超出目标、任意AdGroup花费占比与转化占比严重不匹配（花费>20%但转化<5%）判定为需要优化的重点对象

### sys-amazon-ads-optimization — 广告优化手册（五柱框架，全自动）
**获取数据 / 用哪个MCP**：Marketplace Ad Pros MCP 原生
**评判标准**：
- Protect柱：品牌词自然排名跌出前3位，判定需要加大精确匹配防御出价
- Conquer柱：竞品ASIN定向的点击率低于账户均值，判定素材或出价需要调整
- 否词计划目标比例：正词:否词 = 1:3-5，低于此比例判定否词清理不充分
- 季节性：Best组（历史证明高转化）用3倍预算+2倍出价，Good组用2倍预算，提前2周启动

### sys-amazon-dsp — DSP程序化广告（全自动）
**获取数据 / 用哪个MCP**：Marketplace Ad Pros MCP 原生（6种DSP报告）
**评判标准**：NTB%（新客占比）低于30%判定拉新效率不足；DPV（详情页浏览）高但转化低，判定为Listing转化问题而非广告问题，需转交模块三

### sys-search-term-harvest-dashboard — 搜索词收割看板（全自动）
**获取数据 / 用哪个MCP**：Marketplace Ad Pros MCP 原生
**评判标准**：PRIME级（NEW+高购买）→ 优先生成精确匹配上传文件；STRONG级需持续观察；WATCH级零转化词考虑否词处理

### sys-wasted-ad-spend-dashboard — 浪费花费看板（全自动）
**获取数据 / 用哪个MCP**：Marketplace Ad Pros MCP 原生
**评判标准**：CRITICAL级（月浪费≥$100）必须本周处理；HIGH级（$60-100）纳入下周清理计划；自有品牌词零转化，判定为Listing问题，不是广告问题

---

## 内部串联逻辑

1. 新品首次投放 → `amazon-ppc-campaign` Build模式建初始结构
2. 老Campaign优化 → `amazon-ppc-campaign` Optimize模式或直接用 `sys-amazon-ads-optimization` 应用五柱框架
3. 日常监控 → `sys-search-term-harvest-dashboard` 找该收割的词，`sys-wasted-ad-spend-dashboard` 找该砍的词，两个配合 `amazon-negative-keywords` 落地成具体否词清单
4. 全盘策略规划（预算怎么在SP/SB/SD之间分配）→ `amazon-advertising-strategy`
5. 精细化调优 → `amazon-dayparting-strategy` 调时段，`amazon-display-ads` 补展示广告
6. 涉及DSP程序化广告 → 单独走 `sys-amazon-dsp`

## 竞品对比与评分（新增，2026-09-20）

SIF的`ads_get_asin_ad_structure`等接口可以查**任意ASIN**的广告结构，不需要对方账户授权——这意味着广告策略分析也能做真正的竞品对比，不只是自查。按`../_references/竞品匹配与评分规则.md`筛出可比竞品后：
- 对比自己和可比竞品的Campaign数量、SP/SB/SD占比、曝光趋势，找出自己在广告投入结构上跟竞品的差距
- `amazon-advertising-strategy`的预算分配基准（SP65%/SB25%/SD10%）之外，再补一层"跟可比竞品比，谁的结构更接近这个基准"
- 否词/浪费花费判断维持用自己账户真实数据（`sys-amazon-ads`/`sys-wasted-ad-spend-dashboard`），竞品广告结构只用于战略对比，不涉及对方具体花费金额（拿不到）

## 评判标准速查表

| 检查项 | 数据来源 | 判定阈值 |
|---|---|---|
| 出价上限 | 内部计算 | Max CPC = 售价×Target ACoS×转化率，不得超过 |
| 关键词升级 | SIF `ads_get_ad_group_keyword_breakdown` | ≥2单转化，从Auto/Broad升级到Exact |
| 否词触发 | SIF `ads_get_ad_group_keyword_breakdown` | ≥20点击0单加否词 |
| 出价调整 | SIF `ads_get_campaign_contribution_breakdown` | ACoS>200%降30-50%，达标±10%不动 |
| 浪费花费分级 | `sys-wasted-ad-spend-dashboard` | CRITICAL≥$100/月，HIGH $60-100/月 |
| 预算分配基准 | 内部基准 | SP65%/SB25%/SD10%，偏离超15%需说明 |

## MCP 集成程度

6个sys-*技能全部全自动，给广告账号就能直接出真实数据报告。`amazon-ppc-campaign`的Optimize模式和`amazon-negative-keywords`已接入SIF广告数据链，能自动拉现有Campaign结构；但`amazon-ppc-campaign`的Build模式、`amazon-advertising-strategy`、`amazon-display-ads`因为要设定预算和目标受众，仍需要人工输入才能出结果。
