---
name: voc-amz-products-analyzer
version: 1.3.0
author: Della Zheng
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

## 📌 评论数据量说明（拉取前先告知用户）

**每个ASIN最多拉取300条评论**（ProductReviewsQuery翻页3页×100条/页）。

这**不是**全量评论——Sorftime API限制最多3页。对于评论量大的ASIN（数千条），300条是**最新评论的抽样样本**。但在品类VOC分析中，300条足够做情感分析、话题提取和用户画像——统计显著性足够。

**拉取前需跟用户确认**：
- 如果产品评论量很小（<300条），问是否需要调高`pageIndex`（但最多3页=300）
- 如果产品有几万条评论，告知只拉取最新300条样本，问是否接受
- 默认就是3页×100条，不需要每次都问，但SKILL使用者需要知道这个细节

### 变体评论过滤（重要）

ProductReviewsQuery返回的数据中**会混入变体ASIN的评论**（同父体的其他颜色/尺寸）。拉取后必须按以下步骤过滤：

1. 每条评论有一个 `Asin` 字段，标识该评论真正归属的ASIN
2. 在数据清洗阶段，**只保留当前目标ASIN的评论**，丢弃所有 `Asin != 目标ASIN` 的数据
3. 这一步在 `fetch_all_reviews.py` 或数据处理脚本中完成

> ❌ **不要**在拉取阶段过滤——先全量拉取3页，在保存到 `all_reviews.json` 时再按目标ASIN列表做过滤，确保不丢失数据。

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

### 第三步：确认评论拉取量

**重要：拉取评论前必须先询问用户需要多少条。**

向用户确认：
> 每个ASIN需要拉取多少条评论？选项如下：
>
> A. **100条**（快速预览，1页）
> B. **300条**（标准分析，3页 — 推荐，默认）
> C. **500条**（深入分析，5页 — 耗时较长）
> D. **全部拉取**（不限量 — 需先确认该ASIN评论总量，可能耗时很久）

用户选择后，用 `--max-per-asin` 参数控制。

### 第四步：获取评论数据

```bash
# 标准分析：300条/ASIN，过滤变体，过滤仅目标ASIN的评论
python3 fetch_all_reviews.py --asins ASIN1,ASIN2 --max-per-asin 300 --pages 3
```

> **关键：变体过滤** — Sorftime的ProductReviewsQuery返回中会混入变体ASIN的评论。
> `fetch_all_reviews.py` 已内置按 `Asin` 字段过滤，只保留目标ASIN的评论，变体评论被丢弃。
>
> **关键：终端输出截断** — ProductReviewsQuery响应可能超过65KB，`terminal()`默认截断50KB导致JSON解析失败。必须重定向到文件再读取：
> ```bash
> sorftime api ProductReviewsQuery '{"asin": "ASIN1", "pageIndex": 1}' --domain 1 > /tmp/reviews_ASIN1_p1.json
> ```
> 然后用 `json.loads(strict=False)` 解析（评论内容包含控制字符，strict模式会报错）。

### 第四步：清洗评论数据（过滤变体）

拉取并解析JSON后，必须按ASIN过滤：

```python
import json
with open("/tmp/reviews_all.json") as f:
    raw = json.loads(f.read())

# ProductReviewsQuery返回结构：data/Data/datas/items 中包含评论列表
reviews = raw.get("data", raw.get("Data", raw.get("datas", raw.get("items", []))))

# 按当前ASIN过滤（丢弃变体评论）
TARGET_ASINS = ["ASIN1", "ASIN2", "ASIN3"]
filtered = [r for r in reviews if r.get("Asin") in TARGET_ASINS]
```

### 第五步：生成VOC品类分析报告

**首选**：使用已有的品类报告生成器（当品类匹配时）：

```bash
python3 generate_voc_report.py
```

输出文件：`data/voc/voc_report_full.html`

**备选（新品类/品类不匹配时）**：如果 `generate_voc_report.py` 的 `TOPIC_MAP`/`PRODUCT` 字典与当前品类完全不匹配（比如上次是直发梳、这次是厨房水龙头），有两种策略：

**方案A（推荐）**：直接编写品类专属的独立报告脚本 `data/voc/generate_{品类名}.py`，在此脚本中硬编码品类特有的 `TOPIC_MAP`、`EN_CN_MAP` 和 `PRODUCT` 字典。参考 `scripts/generate_offline_reviews.py` 的骨架结构。

**方案B**：避免让子代理从0写千行报告脚本——在主进程中用 `execute_code` 生成核心JS/HTML模块（ECharts初始化、图表布局等），子代理只负责文本分析内容（PSPS/痛爽痒/创新机会等），然后合并。这比让子代理写完整报告质量高得多。

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
4. **变体评论自动过滤**：`fetch_all_reviews.py` 已按 `Asin` 字段过滤，只保留目标ASIN的评论。如果手动调用Sorftime CLI，需在代码中自行过滤。
5. **月销字段**：`AsinSalesCount`可能是父体级别数据，变体级别可能为0
6. **星级分布格式**：`FiveStartRatings`/`OneStarRatings`格式为`"X,XXX"`，需parse

### 报告生成
7. **子代理数据污染**：❗ 子代理没有API权限时会虚构价格/评分数据。始终在主进程拉取真实数据再传入
8. **f-string陷阱**：ECharts JS嵌入HTML时，`{` `}`需双写`{{}}`。预计算JSON变量再传入
9. **中文引号问题**：Python字符串中的"中文引号"会被解析为字符串结束。用英文引号或「」
10. **dict[:N]不兼容**：Python 3.9+不支持`dict.keys()[:3]`，用`list(dict.keys())[:3]`
11. **品牌数据来源**：品牌信息来自 `product_info.json` 中的 `Brand` 字段

### 部署前验收清单（必做）

子代理生成的HTML**几乎每次都有问题**。生成报告后部署前必须运行验证脚本：

```bash
python3 scripts/validate_report.py data/voc/voc_report_full.html
```

如果脚本报错，根据提示修复。脚本自动检查下面所有6项。如果无法运行脚本，手动检查：

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

当定位矩阵（评分×月销×评论量）图表为空时，有两种情况：

#### 情况A：JS完全缺失（子代理没写）

原因：子代理生成JS脚本时遗漏了positioning图表的初始化代码。
修复：在最后一个`<script>`块末尾追加：

```python
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
- `\\n` 要用双反斜杠 `\\\\n`（JSON字符串中表示换行）
- 如果已经有 `show:True`（Python写法），替换为 `show:true`

#### 情况B：JS存在但script在div之前执行（DOM顺序错误）

原因：子代理将所有ECharts代码堆积在`</body>`之前的最后一个`<script>`块中，但positioning的`<div>`没有提前出现在HTML中（因为子代理把定位矩阵HTML放在了script之后，或者patch操作意外删除了section div）。

验证：如果在预览中看到ECharts报错`Initialize failed: invalid dom`，或页面底部有JS错误但没有影响其他图表，就是这个原因。

修复：将positioning的`<div>`和对应的`<script>`移动到**所有其他图表script之前**，或者确保`<div id="positioning">`在对应`<script>`调用`echarts.init()`之前出现在DOM中。

### 常见patch操作陷阱

当用`patch()`编辑HTML报告时，注意：

1. **section id可能被误删**：替换`<script>...</script></div><h2>`时，`</div>`是关闭ASIN拆解的，然后`<h2>`本应属于`<div class="section" id="sec-compare-reviews">`。如果patch字符串去掉了中间的section div，这个模块就失去了样式。修复：重新插入缺失的`<div class="section" id="sec-compare-reviews">`。

2. **footer偏右**：原因通常是footer在`.page`div内部（后者用了`max-width:1400px; margin:0 auto`），footer继承了居中div的宽度约束。修复：
   - 第一步：移动footer到`.page`div**外部**（在最后一个`</div>`和`<script>`之间）
   - 第二步：CSS加`display:block!important;width:100%!important;clear:both!important`

3. **创新机会偏左**：原因是被嵌套在`chart-box`或`chart-row`布局内。修复：把`sec-innovation-summary` section独立出来，不在任何grid/flex容器内。

## 脚本说明

| 脚本 | 用途 | 参数 |
|------|------|------|
| `fetch_voc_data.py` | 批量获取ASIN产品数据 | `--asins` 逗号分隔 |
| `fetch_all_reviews.py` | 翻页获取评论并保存CSV | `--asin` + `--pages` |
| `generate_voc_report.py` | 主生成器：分析评论→14模块HTML | 编辑`ASINS`和`PRODUCT`字典 |
| `scripts/generate_offline_reviews.py` | 离线模式：生成模拟评论数据 | 编辑`PRODUCT_INFO`字典 |
| `scripts/validate_report.py` | 自动验证HTML报告（JS语法/定位矩阵/section完整性等） | 生成报告后部署前运行 |

## 参考文档（按需加载）

| 文件 | 内容 | 何时加载 |
|------|------|---------|
| `references/voc-report-structure.md` | 14模块结构定义 | 生成报告时 |
| `references/voc-multi-asin-workflow.md` | 完整多ASIN工作流 | 首次使用或需要完整流程时 |
| `references/sorftime-cli-workflow.md` | Sorftime CLI使用指南 | API调用遇到问题时 |
| `references/vercel-deploy-workflow.md` | Vercel部署工作流 | 需要部署时 |
| `references/report-writing-guide.md` | 独立报告编写指南 + 部署前验证清单 | 旧品类脚本不匹配需编写新品类独立报告时 |
| `references/quick-fix-catalogue.md` | 常见报告bug快速修复手册（定位矩阵空白/footer偏右/创新机会偏左/JS语法错误等） | 部署前验收发现问题时 |
| `references/CHANGELOG.md` | 版本历史和变更记录 | 需要了解更新内容时 |

## License

MIT

## 致谢

- 数据支持：Sorftime API
- 图表渲染：ECharts 5
