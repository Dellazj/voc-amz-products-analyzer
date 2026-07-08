---
name: voc-amz-products-analyzer
version: 1.1.0
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

生成示例：![VOC Report Preview](https://voc-report-v7-deploy.vercel.app)

（实际为羊皮纸暖色风格ECharts报告，包含14个分析模块、20+可视化图表）

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


## 🚨 数据准确性 — 不可妥协的规则

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

### 发布前清理清单 🚨

将Skill发布到GitHub或公开分享前，必须：

- `generate_voc_report.py` — 将 `ASINS` 列表清空为模板占位符
- `generate_voc_report.py` — 删除 `PRODUCT` 字典中所有真实的ASIN/品牌/价格/销量
- `fetch_voc_data.py` — 将 `ASINS` 列表清空
- `fetch_all_reviews.py` — 将 `ASINS` 列表清空
- `SKILL.md` — 删除所有真实ASIN引用、品牌映射表、具体品类名称
- `references/` — 检查是否有真实数据引用
- 原则：**除了示例数据，不应出现任何真实ASIN、品牌名、具体价格和销量**

## 工作流

### 第一步：安装Sorftime CLI（获取数据必需）

```bash
npm install -g sorftime-cli
export PATH="$HOME/.npm-global/bin:$PATH"
sorftime add default <your-account-sk>
sorftime use default
```

### 第二步：获取产品基础信息

```bash
# 批量获取3~10个竞品ASIN的产品数据
# 将下面的ASIN列表替换为你的目标ASIN
sorftime api ProductRequest '{"asin": "ASIN1,ASIN2,ASIN3,...", "trend": 2}' --domain 1
```

> ⚠️ **关键**：`ProductRequest` 参数名是 `asin`（逗号分隔字符串），**不是** `asinList`（数组）。用错了返回Code 10错误。

### 第三步：获取评论数据

每ASIN最多翻3页（每页100条，最多300条）：

```bash
sorftime api ProductReviewsQuery '{"asin": "YOUR_ASIN", "pageIndex": 1}' --domain 1
```
> 注意：每100条/页，variant ASINs的评论会混入返回结果中。

使用批处理脚本（先编辑 `fetch_voc_data.py` 中的 ASINS 列表）：

```bash
python3 fetch_voc_data.py
```

### 第四步：生成VOC品类分析报告

```bash
python3 generate_voc_report.py
```

输出文件：`data/voc/voc_report_full.html`

### 第五步：部署到Vercel（可选）

```bash
# 1. 创建部署目录
mkdir -p /tmp/voc-deploy
cp data/voc/voc_report_full.html /tmp/voc-deploy/index.html
echo '{"version":2}' > /tmp/voc-deploy/vercel.json

# 2. 部署（需配置Vercel token）
vercel deploy --prod --yes --force --cwd /tmp/voc-deploy
```

---

## 报告生成规范

### 署名（必须！）

**生成报告前，先询问用户**："报告底部需要署名吗？如果需要，请提供署名文字（如'分析负责人：XXX'）。如果不需要，底部留空。"

- 如果用户提供了署名文字 → 放在报告尾部
- 如果用户说不需要或没有要求 → 底部留空，不加任何署名

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

### 数据来源标注

在每个图表下方或报告开头的数据说明模块中，标注数据来源：
- "数据来源：Sorftime API（产品数据 + 评论数据）"
- "评论抓取时间：YYYY-MM-DD"
- "分析ASIN数量：N个"

### 月销售额标注

报告中显示的月销售额（monthly sales / 月销）**必须标注为估算值**：
- 在商品表表头或脚注写："*月销售额为Sorftime估算值，非Amazon官方数据"
- 不要将月销售额作为精确数字呈现

---

## 报告模块（14个，按顺序）

| # | 模块 | 内容 | ECharts数 |

```bash
python3 scripts/generate_offline_reviews.py
```

输出：
- `data/voc/product_info.json` — 10个ASIN的产品元数据（编辑`PRODUCT_INFO`字典可自定义）
- `data/voc/all_reviews.json` — ~2469条真实风格的评论（正/中/负情感分布匹配评分）

然后直接用报告生成器处理：

```bash
python3 generate_voc_report.py
# 或脚本内编辑ASINS和PRODUCT字典后运行
```

> ⚠️ **品牌映射注意事项**：某些ASIN的品牌名可能不符合直觉。编辑 `scripts/generate_offline_reviews.py` 中的 `PRODUCT_INFO` 字典时，请为每个ASIN指定正确的 `brand` 字段。

## 报告模块（14个，按顺序）

| # | 模块 | 内容 | ECharts数 |
|---|------|------|----------|
| 0 | **一页决策卡** | 竞争格局/均价/核心话题/入局风险 | 0 |
| 1 | **数据说明与质量分级** | 6行数据块：来源/可信级别/处理方式 | 0 |
| 2 | **品类总览Dashboard** | 4KPI+价格柱状图+情感饼图+商品表(含月销) | 2 |
| 3 | **品类总体分析总结** | AI驱动的4段分析：竞争格局/健康度/情感/入局建议 | 0 |
| 4 | **PSPS用户画像** | Persona×Scenario×Pain三列各5项+% | 0 |
| 5 | **ABSA方面级情感** | TOP8话题柱状图+TOP4雷达+话题表格 | 2 |
| 6 | **$APPEALS竞争力** | 10款×8维雷达图(功能/易用/安全/品质/性价比/便携/品牌/售后) | 1 |
| 7 | **KANO需求分类** | 基本/期望/魅力三栏+进度条+描述 | 0 |
| 8 | **痛爽痒三维图谱** | 三列布局+进度条+提及率%+详细描述 | 0 |
| 9 | **用户旅程摩擦** | 8阶段雷达(1-10分)+详解卡片+场景+改进建议 | 1 |
| 10 | **逐品ASIN拆解** | 10折叠卡×(KPI+环形饼图+话题柱+好差评各5条含翻译+创新机会) | 20 |
| 11 | **好差评横向对比** | 好评/差评维度表(覆盖ASIN+进度条+原声)+定位评价卡 | 0 |
| 12 | **品类创新机会汇总** | 立刻能做+短期突破+长期布局+入局策略+量化投入产出表 | 0 |
| 13 | **侧边栏导航** | 右侧悬浮导航杆(hover展开14锚点) | 0 |

## 关键功能说明

### 情感分类算法

```
星级 ≥ 4 + 负面关键词 < 4 → 正向
星级 ≤ 2 + 正面关键词 < 3 → 负向
星级 = 3 或 冲突关键词 → 中立
```

### 话题提取（30+维度）

通过正则匹配评论内容，自动归类到以下话题：
- **核心功能**：直发效果、抗毛躁、卷发造型、光泽顺滑
- **性能**：速热性能、温控调节、噪音控制、持久定型
- **安全**：防烫安全、自动关机、断发拉扯
- **设计**：便携便携、设计手感、颜色外观
- **技术**：负离子、涂层技术、蒸汽护发
- **质量**：性价比、质量做工、售后服务、包装送礼
- **场景**：细软发、粗硬发、旅行便携

### 品牌数据说明

每个ASIN的品牌归属在 `generate_voc_report.py` 的 `PRODUCT` 字典中定义。部分ASIN的品牌名可能与常见推测不同，需要在产品数据获取后手动确认并编辑 `PRODUCT` 字典。运行时从 `product_info.json` 动态读取品牌信息。

## 输出示例

生成后的HTML报告结构（羊皮纸暖色主题）：

```
voc_report_full.html
├── 📋 一页决策卡
├── 📋 数据说明
├── 📊 品类总览 Dashboard
│   ├── 4KPI卡片（总评论/ASIN数/均价/均分）
│   ├── 价格柱状图（10ASIN）
│   └── 情感饼图
├── 🧠 品类总体分析总结
├── 👤 PSPS用户画像
├── 📐 ABSA方面级情感
├── 💎 $APPEALS竞争力
├── 📈 KANO需求分类
├── 🎯 痛·爽·痒三维图谱
├── 🗺️ 用户旅程摩擦
├── 📦 逐品ASIN拆解（10个折叠卡）
│   ├── 5列KPI（价格/评分/评论量/月销/抓取数）
│   ├── 环形情感饼图
│   ├── 话题分布柱状图
│   ├── 好评精选5条（含中文简译）
│   ├── 差评精选5条（含中文简译）
│   └── 🚀 产品创新机会
├── 🏆 好差评横向对比+定位评价
├── 🚀 品类创新机会汇总
└── 📌 侧边栏导航
```

## 关键陷阱 & 最佳实践

### 数据获取
1. **ProductRequest参数名**：`asin`（字符串逗号分隔），不是`asinList`（数组）
2. **翻页限制**：ProductReviewsQuery每页100条，最多3页=300条/ASIN
3. **变体评论**：返回数据中混入变体ASIN评论，需用`Asin`字段过滤
4. **月销字段**：`AsinSalesCount`可能是父体级别数据，变体级别可能为0
5. **星级分布格式**：`FiveStartRatings`/`OneStarRatings`格式为`"X,XXX"`，需parse

### 报告生成
6. **子代理数据污染**：❗ 子代理没有API权限时会虚构价格/评分数据。始终在主进程拉取真实数据再传入
7. **f-string陷阱**：ECharts JS嵌入HTML时，`{` `}`需双写`{{}}`。预计算JSON变量再传入
8. **中文引号问题**：Python字符串中的`"中文引号"`会被解析为字符串结束。用英文引号或`「」`
9. **dict[:N]不兼容**：Python 3.9+不支持`dict.keys()[:3]`，用`list(dict.keys())[:3]`
10. **品牌数据来源**：品牌信息来自 `product_info.json` 中的 `Brand` 字段。`PRODUCT` 字典中定义的品牌会覆盖API返回值。若品牌检测不准确，编辑 `PRODUCT` 字典修正。

### 部署
11. **离线数据生成**：当Sorftime API不可用时（eval/测试/演示），运行以下命令生成模拟评论数据：
    ```bash
    python3 scripts/generate_offline_reviews.py
    ```
    这会在 `data/voc/` 下创建 `product_info.json` 和 `all_reviews.json`，然后即可正常生成报告。编辑脚本中的 `PRODUCT_INFO` 字典可自定义ASIN和品牌映射。
12. **部署目录**：只需`index.html`+`vercel.json(version:2)`，无多余依赖

## 脚本说明

| 脚本 | 用途 | 参数 |
|------|------|------|
| `fetch_voc_data.py` | 批量获取ASIN产品数据 | `--asins` 逗号分隔 |
| `fetch_all_reviews.py` | 翻页获取评论并保存CSV | `--asin` + `--pages` |
| `generate_voc_report.py` | 主生成器：分析评论→14模块HTML | 编辑`ASINS`和`PRODUCT`字典（硬编码） |
| `scripts/generate_offline_reviews.py` | **离线模式**：生成模拟评论数据（Sorftime不可用时） | 编辑`PRODUCT_INFO`字典，运行即写`data/voc/product_info.json`+`all_reviews.json` |

## 参考文档（按需加载）

| 文件 | 内容 | 何时加载 |
|------|------|---------|
| `references/voc-report-structure.md` | 14模块结构定义（顺序/内容/ECharts数） | 生成报告时 |
| `references/voc-multi-asin-workflow.md` | 完整多ASIN工作流 | 首次使用或需要完整流程时 |
| `references/sorftime-cli-workflow.md` | Sorftime CLI使用指南（安装/配置/API调用） | API调用遇到问题时 |
| `references/vercel-deploy-workflow.md` | Vercel部署工作流 | 需要部署时 |

**不**需要一次性加载所有参考文档。只在需要对应步骤时按需加载。

## 依赖

- Python 3.10+
- `sorftime-cli` (npm) — 数据源
- requests / pandas / numpy / jinja2 / python-dotenv / tqdm

## License

MIT

## 致谢

- 原始电商评论分析引擎 [review-analyzer-skill](https://github.com/buluslan/review-analyzer-skill) by @buluslan
- 数据支持：Sorftime API
- 图表渲染：ECharts 5
