---
name: voc-amz-products-analyzer
version: 1.0.0
author: Della Zheng (based on review-analyzer-skill by @buluslan)
description: |
  Amazon品类VOC（Voice of Customer）评论分析工具。
  从Sorftime API获取3~10个竞品ASIN的产品数据和评论，
  自动生成14模块品类洞察HTML报告（含ECharts可视化图表），
  支持一键部署到Vercel。

  核心能力：
  - Sorftime API批量获取产品元数据和评论（支持翻页300条/ASIN）
  - 基于星级+关键词的情感分类（正/中/负三级）
  - 30+维度话题自动提取（直发效果/防烫安全/速热性能/断发拉扯等）
  - 14模块品类洞察报告（含PSPS/ABSA/APPEALS/KANO/痛爽痒/旅程摩擦/创新机会等）
  - 品牌自动校验（YMO vs Wavytalk vs Bopcal等）
  - 羊皮纸暖色风格HTML（Warm Parchment CSS主题）
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

（实际为羊皮纸暖色风格ECharts报告，包含14个分析模块、20+可视化图表、2469条评论分析）

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
sorftime api ProductRequest '{"asin": "B07MMQ4BZH,B0DCK8P752,B0BL34CGLM,B0FJDK6BMT,B091KHSV2X,B07RLTPSLB,B0C2C9TC42,B0F3CXQVT3,B0GZZRGJTN,B0FT2PQY7R", "trend": 2}' --domain 1
```

> ⚠️ **关键**：`ProductRequest` 参数名是 `asin`（逗号分隔字符串），**不是** `asinList`（数组）。用错了返回Code 10错误。

### 第三步：获取评论数据

每ASIN最多翻3页（每页100条，最多300条）：

```bash
sorftime api ProductReviewsQuery '{"asin": "B07MMQ4BZH", "pageIndex": 1}' --domain 1
```

使用批处理脚本：

```bash
python3 fetch_voc_data.py --asins B07MMQ4BZH,B0DCK8P752,B0BL34CGLM,B0FJDK6BMT,B091KHSV2X,B07RLTPSLB,B0C2C9TC42,B0F3CXQVT3,B0GZZRGJTN,B0FT2PQY7R
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

### 品牌自动校验

部分ASIN的品牌名与常见推测不同，脚本内置了品牌映射表：
- `B0DCK8P752` → **Wavytalk**（蒸汽护发款，不是TYMO）
- `B0GZZRGJTN` → **Bopcal**（无线便携款）
- 其余 → TYMO系列（7款）

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
10. **品牌校验**：B0DCK8P752=Wavytalk，B0GZZRGJTN=Bopcal（非TYMO）

### 部署
11. **Vercel token**：Base64编码后使用。部署前先`vercel link`关联项目或`--force`新建
12. **部署目录**：只需`index.html`+`vercel.json(version:2)`，无多余依赖

## 脚本说明

| 脚本 | 用途 | 参数 |
|------|------|------|
| `fetch_voc_data.py` | 批量获取ASIN产品数据 | `--asins` 逗号分隔 |
| `fetch_all_reviews.py` | 翻页获取评论并保存CSV | `--asin` + `--pages` |
| `generate_voc_report.py` | 主生成器：分析评论→14模块HTML | 硬编码ASIN列表（可编辑） |

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
