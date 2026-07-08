---
name: voc-amz-products-analyzer
version: 1.2.0
author: Della Zheng (based on review-analyzer-skill by @buluslan)
description: |
  Amazon品类VOC（Voice of Customer）评论分析工具。
  从Sorftime API获取3~10个竞品ASIN的产品数据和评论，
  自动生成14模块品类洞察HTML报告（含ECharts可视化图表），
  支持一键部署到Vercel。

  什么时候用：
  - 用户说"分析这个品类的评论"、"生成VOC报告"、"品类洞察"
  - 用户提供了多个ASIN要求做竞品分析
  - 用户遇到了Sorftime API错误（Code 10等）
  - 用户问如何从亚马逊拉取评论数据做分析
  - 凡是涉及亚马逊选品、竞品分析、评论分析、品类调研，即使没明确说VOC，也应该加载此Skill
  - 用户给出多个ASIN让你做「竞争格局定位」分析（定位/散布/泡泡图）
  - 用户说「帮我看看这个品类怎么样」
  - 用户要求对现有品类报告做增量更新（修复JS错误、数据不匹配、缺失图表）

  核心能力：
  - Sorftime API批量获取产品元数据和评论（支持翻页300条/ASIN）
  - 基于星级+关键词的情感分类（正/中/负三级）
  - 30+维度话题自动提取
  - 14模块品类洞察报告（PSPS/ABSA/APPEALS/KANO/痛爽痒/旅程摩擦/创新机会等）
  - 品牌自动校验
  - 羊皮纸暖色风格HTML（主题色：#f5ebd8 主色 / #e8dcc5 辅色 / #405345 文字）
  - Vercel一键部署生成在线链接
license: MIT
allowed-tools:
  - terminal
  - file
  - web
  - search
---

# VOC Amazon Products Analyzer

> **Amazon 品类 VOC 评论分析工具** — 输入3~10个竞品ASIN，自动生成14模块品类洞察HTML报告。

## 快速开始

### 方式1：作为Hermes Agent Skill使用

```bash
# 安装skill
npx skills add dellazj/voc-amz-products-analyzer

# 加载skill
# 在Hermes对话中使用：skill_view(name='voc-amz-products-analyzer')
```

### 方式2：直接使用Python脚本

```bash
git clone https://github.com/dellazj/voc-amz-products-analyzer.git
cd voc-amz-products-analyzer
uv venv .venv && source .venv/bin/activate
uv pip install -r requirements.txt
```

## 数据准确性 — 不可妥协的规则

**这是使用本Skill最重要的规则。违反以下任何一条将导致报告包含虚假数据。**

### 生成报告前的数据检查

在运行 `generate_voc_report.py` 或委托子代理生成报告之前，必须验证：

1. **数据文件存在且可读**：
   ```bash
   test -f data/voc/product_info.json && echo "PRODUCT OK" || echo "MISSING"
   test -f data/voc/all_reviews.json && echo "REVIEWS OK" || echo "MISSING"
   ```
   如果文件缺失，先运行数据获取步骤（见下方工作流），**不要跳过数据获取直接生成**

2. **数据来源必须是真实的Sorftime API输出**：
   - `product_info.json` = 来自 `sorftime api ProductRequest ...` 的返回结果（或离线数据生成器）
   - `all_reviews.json` = 来自 `sorftime api ProductReviewsQuery ...` 的返回结果（或离线数据生成器）
   - ❌ **禁止**：子代理自行虚构价格、评分、月销量、品牌名等数据
   - ❌ **禁止**：在`product_info.json`和`all_reviews.json`不存在时自行创建包含虚构数据的数据文件

3. **子代理数据污染防护** —— 当使用 `delegate_task()` 委托子代理生成报告时：
   - ❌ 子代理没有Sorftime API凭证，会在API调用失败时**虚构数据**
   - ✅ **正确的做法**：在主进程中预先验证真实数据文件已存在，将文件路径和摘要作为`context`字段传入子代理
   - ✅ 在子代理的`goal`中明确写明：**"所有价格、评分、月销量、品牌名等数据必须从提供的JSON文件读取。如果JSON文件不存在，报告创建失败也不要虚构任何数据。"**
   - ✅ **核实结果**：子代理报告完成后，检查输出HTML中是否有真实的品牌名、价格值和ASIN，与原始数据文件对比确认

4. **离线模式**（Sorftime API不可用时的替代方案）：
   ```bash
   python3 scripts/generate_offline_reviews.py
   ```
   这会生成**结构正确的模拟数据**（但数值可被用户自定义编辑）。编辑脚本开头的`PRODUCT_INFO`字典可自定义ASIN/品牌/价格。

5. **ASIN独立过滤**：ProductReviewsQuery返回的数据中会混入变体ASIN的评论。在分析时**只保留当前ASIN的评论**（用`Asin`字段过滤），不要混入变体评论。

### 发布前清理清单

将Skill发布到GitHub或公开分享前，必须：

- `generate_voc_report.py` — 将 `ASINS` 列表清空为模板占位符
- `generate_voc_report.py` — 删除 `PRODUCT` 字典中所有真实的ASIN/品牌/价格/销量
- `fetch_voc_data.py` — 将 `ASINS` 列表清空
- `fetch_all_reviews.py` — 将 `ASINS` 列表清空
- `SKILL.md` — 删除所有真实ASIN引用、品牌映射表、具体品类名称
- `references/` — 检查是否有真实数据引用
- 原则：**除了示例数据，不应出现任何真实ASIN、品牌名、具体价格和销量**

## 工作流

### 第一步：安装Sorftime CLI

```bash
npm install -g sorftime-cli
export PATH="$HOME/.npm-global/bin:$PATH"
sorftime add default <your-account-sk>
sorftime use default
```

### 第二步：获取产品基础信息

```bash
# 批量获取3~10个竞品ASIN的产品数据
sorftime api ProductRequest '{"asin": "ASIN1,ASIN2,ASIN3,...", "trend": 2}' --domain 1
```

> **关键**：`ProductRequest` 参数名是 `asin`（逗号分隔字符串），**不是** `asinList`（数组）。用错了返回Code 10错误。

### 第三步：获取评论数据

每ASIN最多翻3页（每页100条，最多300条）：

```bash
sorftime api ProductReviewsQuery '{"asin": "YOUR_ASIN", "pageIndex": 1}' --domain 1
```

> **关键：终端输出截断**：ProductReviewsQuery响应可能超过65KB，`terminal()`默认截断50KB导致JSON解析失败。必须重定向到文件再读取：
> ```bash
> sorftime api ProductReviewsQuery '{"asin": "ASIN1", "pageIndex": 1}' --domain 1 > /tmp/reviews_ASIN1_p1.json
> ```
> 然后用 `json.loads(strict=False)` 解析（评论内容包含控制字符，strict模式会报错）。

### 第四步：生成VOC品类分析报告

**首选**：使用已有的品类报告生成器：

```bash
python3 generate_voc_report.py
```

输出文件：`data/voc/voc_report_full.html`

**备选（推荐给新品类）**：如果现有脚本是针对完全不同的品类（话题映射TOPIC_MAP、产品数据PRODUCT字典都不匹配），不要强行修改——直接编写品类专属的独立报告脚本。

## 报告生成规范

### Footer（数据来源标注）

报告底部的footer格式**严格遵循以下规范**：

```html
<footer>数据来源：Sorftime ProductRequest</footer>
```

- ❌ **不加**「分析工具：Hermes Agent」
- ❌ **不加**署名（除非用户明确要求，见下方署名规则）
- ✅ footer必须在`.page`div外部（作为body直接子元素），否则可能因父级flex/grid布局跑偏
- ✅ CSS确保`text-align:center; display:block; width:100%`

### 署名规则

- 生成报告前**必须询问用户**：「报告底部需要署名吗？如果需要请提供署名文字。如果不需要，底部留空。」
- 用户提供了署名文字 → 在报告尾部单独一行（不在footer内）
- 用户说不需要 → 不留任何署名

### 主题风格

- **主题色**：羊皮纸暖色风格
  - 主背景：`#f5ebd8`
  - 卡片背景：`#e8dcc5`
  - 文字色：`#405345`（深墨绿）
  - 标题色：`#2b3a30`
  - 强调色：`#486052`
  - 边框线：`#d4c9b0`
- **字体**：系统无衬线（`-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif`）
- **侧边栏导航**：右侧悬浮，hover展开，14个锚点

### 月销售额标注

报告中显示的月销售额（monthly sales / 月销）**必须标注为估算值**：
- 在商品表表头或脚注写："*月销售额为Sorftime估算值，非Amazon官方数据"
- 不要将月销售额作为精确数字呈现

## 报告模块（14个，按顺序）

| # | 模块 | 内容 | ECharts数 |
|---|------|------|----------|
| 0 | **一页决策卡** | 竞争格局/均价/核心话题/入局风险 | 0 |
| 1 | **数据说明与质量分级** | 6行数据块：来源/可信级别/处理方式 | 0 |
| 2 | **品类总览Dashboard** | 4KPI+价格柱状图+情感饼图+商品表(含月销) | 2 |
| 3 | **品类总体分析总结** | AI驱动的4段分析：竞争格局/健康度/情感/入局建议 | 0 |
| 4 | **PSPS用户画像** | Persona×Scenario×Pain三列各5项+% | 0 |
| 5 | **ABSA方面级情感** | TOP8话题柱状图+TOP4雷达+话题表格 | 2 |
| 6 | **$APPEALS竞争力** | 10款×8维雷达图 | 1 |
| 7 | **KANO需求分类** | 基本/期望/魅力三栏+进度条+描述 | 0 |
| 8 | **痛爽痒三维图谱** | 三列布局+进度条+提及率%+详细描述 | 0 |
| 9 | **用户旅程摩擦** | 8阶段雷达(1-10分)+详解卡片+场景+改进建议 | 1 |
| 10 | **逐品ASIN拆解** | N折叠卡×(KPI+环形饼图+话题柱+好差评各5条含翻译+创新机会) | N×2 |
| 11 | **好差评横向对比** | 好评/差评维度表(覆盖ASIN+进度条+原声)+定位评价卡 | 0 |
| 12 | **品类创新机会汇总** | 立刻能做+短期突破+长期布局+入局策略+量化投入产出表 | 0 |
| 13 | **定位矩阵** | 评分×月销×评论量散点图 — **最常被遗漏的图表** | 1 |
| 14 | **侧边栏导航** | 右侧悬浮导航杆(hover展开14锚点) | 0 |

## 关键陷阱 & 最佳实践

### 数据获取
1. **ProductRequest参数名**：`asin`（字符串逗号分隔），不是`asinList`（数组）
2. **翻页限制**：ProductReviewsQuery每页100条，最多3页=300条/ASIN
3. **大输出重定向**：评论输出超50KB会被terminal截断。**必须**：`> /tmp/reviews_{asin}.json` → `json.loads(strict=False)` 解析
4. **变体评论**：返回数据中混入变体ASIN评论，需用`Asin`字段过滤
5. **月销字段**：`AsinSalesCount`可能是父体级别数据，变体级别可能为0
6. **星级分布格式**：`FiveStartRatings`/`OneStarRatings`格式为`"X,XXX"`，需parse

### 报告生成
7. **子代理数据污染**：❗ 子代理没有API权限时会虚构价格/评分数据。始终在主进程拉取真实数据再传入
8. **f-string陷阱**：ECharts JS嵌入HTML时，`{` `}`需双写`{{}}`。预计算JSON变量再传入
9. **中文引号问题**：Python字符串中的"中文引号"会被解析为字符串结束。用英文引号或「」
10. **dict[:N]不兼容**：Python 3.9+不支持`dict.keys()[:3]`，用`list(dict.keys())[:3]`
11. **品牌数据来源**：品牌信息来自 `product_info.json` 中的 `Brand` 字段

### 部署前验收清单（必做）

子代理生成的HTML**几乎每次都有问题**。生成报告后部署前必须验证：

```bash
# 1. JS语法错误：Python True/False/None 混入JS
grep -n 'show:True\|show:False\|None\b' data/voc/voc_report_full.html

# 2. 定位矩阵散点图（最常遗漏）
grep 'document.getElementById("positioning")' data/voc/voc_report_full.html || echo "MISSING"

# 3. 无重复init（同一个div被init两次）
grep -c 'document.getElementById("positioning")' data/voc/voc_report_full.html
# 如果>1，说明有重复脚本——删除较早的那份

# 4. HTML结构完整性——section嵌套是否正确
# patch操作可能误删id="sec-compare-reviews"导致关联内容丢失section样式
grep 'id="sec-compare-reviews"' data/voc/voc_report_full.html

# 5. footer格式
grep '<footer>' data/voc/voc_report_full.html

# 6. 图表script必须在对应div之后（DOM顺序）
# 特别是positioning散点图——如果script在div之前，ECharts渲染到不存在元素
```

### 定位矩阵散点图快速修复

当定位矩阵（评分×月销×评论量）图表为空时，原因通常是JS缺失。最小化修复：

```python
# 在最后一个<script>块末尾追加：
echarts.init(document.getElementById("positioning")).setOption({
  xAxis:{type:"value",name:"月销"},
  yAxis:{type:"value",name:"评分",min:4.3,max:4.7},
  series:[{type:"scatter",
    data:[[月销, 评分, 评论量], ...],
    label:{show:true}
  }]
});
```

注意：
- `\n` 要用双反斜杠 `\\n`（JSON字符串中表示换行）
- 如果已经有 `show:True`（Python写法），替换为 `show:true`

## 脚本说明

| 脚本 | 用途 | 参数 |
|------|------|------|
| `fetch_voc_data.py` | 批量获取ASIN产品数据 | `--asins` 逗号分隔 |
| `fetch_all_reviews.py` | 翻页获取评论并保存CSV | `--asin` + `--pages` |
| `generate_voc_report.py` | 主生成器：分析评论→14模块HTML | 编辑`ASINS`和`PRODUCT`字典 |
| `scripts/generate_offline_reviews.py` | 离线模式：生成模拟评论数据 | 编辑`PRODUCT_INFO`字典 |

## 参考文档（按需加载）

| 文件 | 内容 | 何时加载 |
|------|------|---------|
| `references/voc-report-structure.md` | 14模块结构定义 | 生成报告时 |
| `references/voc-multi-asin-workflow.md` | 完整多ASIN工作流 | 首次使用或需要完整流程时 |
| `references/sorftime-cli-workflow.md` | Sorftime CLI使用指南 | API调用遇到问题时 |
| `references/vercel-deploy-workflow.md` | Vercel部署工作流 | 需要部署时 |
| `references/report-writing-guide.md` | 独立报告编写指南 + 部署前验证清单 | 旧品类脚本不匹配需编写新品类独立报告时 |

## License

MIT

## 致谢

- 原始电商评论分析引擎 [review-analyzer-skill](https://github.com/buluslan/review-analyzer-skill) by @buluslan
- 数据支持：Sorftime API
- 图表渲染：ECharts 5
