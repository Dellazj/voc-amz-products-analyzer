# VOC Amazon Products Analyzer 🏆

> **Amazon品类VOC（Voice of Customer）评论分析工具**  
> 输入3~10个竞品ASIN → 自动获取Sorftime数据 → 生成14品类洞察HTML报告

---

## 产生的报告长什么样？

生成一个**羊皮纸暖色风格**的单页HTML报告，包括：

- 14个分析模块（从决策卡到创新机会）
- 20+ ECharts可视化图表（柱状图/饼图/雷达图/散点图等）
- 2469+条评论自动情感分类+话题提取
- 逐品好差评精选 + 中文简译
- 品类级创新机会 + 量化投入产出评估
- 侧边栏导航 + 无缝Vercel部署

[👉 **查看示例报告**](https://voc-report-v7-deploy.vercel.app)

> 示例报告是对Amazon US直发梳品类Top10 ASIN的VOC分析，
> 覆盖TYMO、Wavytalk、Bopcal三个品牌共10款产品。

## 报告模块总览

| # | 模块 | 说明 |
|---|------|------|
| 📋 | **一页决策卡** | 竞争格局/均价/核心话题/入局风险，7行快速决策 |
| 📊 | **品类总览Dashboard** | 4KPI + 价格柱状图 + 情感饼图 + 商品月销表 |
| 🧠 | **AI品类总结** | 4段分析：竞争格局→品类健康度→情感基调→入局建议 |
| 👤 | **PSPS用户画像** | Persona×Scenario×Pain 三列各5项+占比 |
| 📐 | **ABSA方面级情感** | TOP8话题柱状图 + TOP4雷达 + 话题/提及率/ACT建议表 |
| 💎 | **$APPEALS竞争力** | 10款产品×8维度南丁格尔玫瑰图（功能/易用/安全等） |
| 📈 | **KANO需求分类** | 基本型/期望型/魅力型 + 进度条+百分比 |
| 🎯 | **痛爽痒三维图谱** | 三列+进度条+提及率%+详细场景描述 |
| 🗺️ | **用户旅程摩擦** | 8阶段雷达(1-10分) + 每阶段详解+改进建议 |
| 📦 | **逐品ASIN拆解** | 10个折叠卡×(5KPI+环形情感饼图+话题柱+好差评各5含翻译+创新机会) |
| 🏆 | **好差评横向对比** | 好评/差评维度表(覆盖ASIN数+进度条+原声) + 产品定位卡 |
| 🚀 | **创新机会汇总** | 立刻能做+短期突破+长期布局+入局策略+投入产出表 |

## 快速开始

### 前提条件

```bash
# 1. Python 3.10+
python3 --version

# 2. Sorftime CLI（数据源）
npm install -g sorftime-cli
export PATH="$HOME/.npm-global/bin:$PATH"
sorftime add default <your-account-sk>
sorftime use default
```

### 安装

```bash
git clone https://github.com/dellazj/voc-amz-products-analyzer.git
cd voc-amz-products-analyzer
uv venv .venv && source .venv/bin/activate
uv pip install -r requirements.txt
```

### 运行完整工作流

#### 1️⃣ 批量获取ASIN产品数据

```bash
python3 fetch_voc_data.py \
  --asins B07MMQ4BZH,B0DCK8P752,B0BL34CGLM,B0FJDK6BMT,B091KHSV2X,\
B07RLTPSLB,B0C2C9TC42,B0F3CXQVT3,B0GZZRGJTN,B0FT2PQY7R
```

#### 2️⃣ 获取评论数据（翻页，每ASIN最多300条）

```bash
# 单个ASIN
python3 fetch_all_reviews.py --asin B07MMQ4BZH --pages 3

# 或批量使用fetch_voc_data.py（包含评论拉取）
```

#### 3️⃣ 生成VOC品类报告

```bash
python3 generate_voc_report.py
```

输出到：`data/voc/voc_report_full.html`

#### 4️⃣ 部署到Vercel（可选）

```bash
mkdir -p /tmp/voc-deploy
cp data/voc/voc_report_full.html /tmp/voc-deploy/index.html
echo '{"version":2}' > /tmp/voc-deploy/vercel.json
vercel deploy --prod --yes --force --cwd /tmp/voc-deploy
```

## 数据集说明

本工具依赖 **Sorftime API** 获取亚马逊美国站的产品数据：

| 数据类型 | API | 输出 |
|---------|-----|------|
| 产品元数据 | `ProductRequest` | 品牌/价格/评分/评论量/月销/BSR等 |
| 评论数据 | `ProductReviewsQuery` | 评论正文/星级/标题/日期/变体信息 |

### 关键参数

- `ProductRequest.asin`：逗号分隔字符串（**不是数组！**）
- `ProductReviewsQuery.pageIndex`：1~3，每页100条
- `ProductReviewsQuery.Asin`：返回中混入变体评论，需过滤

### 可用字段

**ProductRequest**：`Title`, `Price`, `Ratings`, `RatingsCount`, `AsinSalesCount`, `Brand`, `BuyboxSeller`, `BsrCategory`, `OnlineDate`, `FiveStartRatings`, `OneStarRatings`, `Description`, `Feature`, `Photos`

**ProductReviewsQuery**：`Content`, `Star`, `Title`, `ReviewsDate`, `VariationInfo`, `Asin`

## 自定义配置

### 修改ASIN列表

编辑 `generate_voc_report.py` 中的 `ASINS` 和 `PRODUCT` 字典：

```python
ASINS = ["B07MMQ4BZH","B0DCK8P752"]  # 你的竞品ASIN列表

PRODUCT = {
    "B07MMQ4BZH": {
        "brand": "TYMO",
        "title": "Ring Hair Straightening Brush",
        "price": 39.85,
        "rating": 4.4,
        "reviews": 83592,
        "sales": 7000,
        "seller": "TYMO US"
    },
    # ... 更多ASIN
}
```

### 修改品牌映射

```python
BRAND_CHECK = {
    "B0DCK8P752": "Wavytalk",  # 非TYMO
    "B0GZZRGJTN": "Bopcal",    # 非TYMO
}
```

### 话题关键词调整

编辑 `TOPIC_MAP` 字典可增加/修改话题提取关键词：

```python
TOPIC_MAP = {
    "straighten|straight": "直发效果",
    "curl|curling|wave": "卷发造型",
    "frizz|anti.*frizz": "抗毛躁",
    # 添加你自己的话题规则
}
```

## 常见陷阱 ⚠️

### ❌ ProductRequest用错了参数名
```python
# 错误
sorftime api ProductRequest '{"asinList": ["B0XXX"]}'  # Code 10

# 正确
sorftime api ProductRequest '{"asin": "B0XXX,B0YYY"}'
```

### ❌ 子代理虚构数据
当你用子代理生成报告时，它没有API权限会虚构价格/评分。**始终在主进程拉取真实数据再传入。**

### ❌ f-string花括号嵌套
```python
# 错误 — 深层嵌套导致解析失败
h(f'{{"data":{json.dumps({...})},...}}')

# 正确 — 预计算变量
indicator = json.dumps([{"name": d, "max": 10} for d in dims])
h(f'{{radar:{{indicator:{indicator}}}}}')
```

### ❌ 中文引号嵌套
```python
# 错误
desc = "用户反馈"很好""

# 正确
desc = '用户反馈很好'
```

## 文件结构

```
voc-amz-products-analyzer/
├── SKILL.md              # Hermes Agent Skill入口
├── README.md             # 本文件
├── requirements.txt      # Python依赖
├── .gitignore
├── generate_voc_report.py  # 🎯 主生成器（618行）
├── fetch_voc_data.py       # 批量获取产品数据
├── fetch_all_reviews.py    # 翻页获取评论
└── references/
    ├── voc-report-structure.md    # 14模块结构定义
    ├── voc-multi-asin-workflow.md # 多ASIN工作流完整文档
    └── sorftime-cli-workflow.md   # Sorftime CLI使用指南
```

## 技术栈

- **数据源**: Sorftime API (npm)
- **分析引擎**: Python (requests + pandas + numpy)
- **可视化**: ECharts 5 (CDN加载)
- **报告风格**: 羊皮纸暖色 CSS (Warm Parchment)
- **部署**: Vercel (serverless static hosting)

## 许可证

MIT — 自由使用和修改。

## 致谢

- 原始电商评论分析引擎 [review-analyzer-skill](https://github.com/buluslan/review-analyzer-skill) 由 @buluslan 开发
- 数据支持：Sorftime API（亚马逊第三方数据服务）
- 图表渲染：Apache ECharts 5
