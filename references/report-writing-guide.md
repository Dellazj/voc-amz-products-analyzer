# 独立VOC报告编写指南

> 当现有 `generate_voc_report.py` 不适用于新品类时，使用此指南编写独立的品类报告生成器。

## 何时编写独立报告（而不修改旧脚本）

当旧脚本的以下内容与当前品类严重不匹配时：

- `TOPIC_MAP` — 正则话题映射（如直发梳的"抗毛躁/卷发造型" vs 厨房水龙头的"水压水流/下拉喷头"）
- `PRODUCT` — 产品数量和品牌结构完全不同（如10个ASIN vs 4个ASIN）
- `EN_CN_MAP` — 品类专有翻译词库
- 品类名称、标题、品类描述

## 独立脚本结构模板

```python
# STEP 1: 品类数据
ASINS = [...]    # 真实ASIN
PRODUCT = {...}  # 品牌/价格/评分/评论量/月销

# STEP 2: 话题映射（品类核心）
TOPIC_MAP = {
    "regex_pattern_1": "话题中文1",
    "regex_pattern_2": "话题中文2",
    # 15-30个话题维度
}

# STEP 3: 评论分析
# - 情感分类
# - 话题提取
# - 统计计算

# STEP 4: HTML生成
# - 从旧脚本的CSS变量开始（羊皮纸暖色主题）
# - 14个模块按顺序渲染
# - ECharts JS配置
# - 侧边栏导航

# STEP 5: 验证
```

## 需特别留意的陷阱

### 1. 中文引号 `\u201c` `\u201d`（中文左右引号）
- ❌ 错误的：`desc = "中国话"好"啊"`  — Python 解析为字符串结束
- ✅ 正确的：用 `「」` 或 `[]` 替代：`"中国话「好」啊"` 或 `"中国话[好]啊"`
- 检查所有 f-string 内容的引号嵌套级数

### 2. f-string 内嵌 json.dumps
- ❌ 不要写：`h(f'...{json.dumps(data)}...')` — 大括号嵌套导致 JS 语法错误
- ✅ 预计算：`data_json = json.dumps(data)` 然后用 `{data_json}`

### 3. 输出路径计算
脚本位置 vs 期望输出目录：

```
skills/voc-amz-products-analyzer/
├── data/voc/
│   ├── generate_kitchen_faucet_report.py   ← 脚本在此
│   └── voc_report_full.html                 ← 输出到此处
├── generate_voc_report.py                   ← 旧脚本在根目录
```

- 脚本在 `data/voc/` 内 → 需要 `os.path.dirname` 两次 + `"data/voc/xxx.html"`
- 脚本在根目录 → 需要一次 `os.path.dirname` + `"data/voc/xxx.html"`

### 4. 自定验证清单
最后一步，验证检查项必须覆盖14个模块的锚点ID和品类独有字符串。

```python
checks = [
    "sec-decision-card", "sec-data-quality", "sec-dashboard", "sec-ai-summary",
    "sec-psps", "sec-absa", "sec-appeals", "sec-kano", "sec-pain-joy-itch",
    "sec-journey", "sec-asin-breakdown", "sec-compare-reviews", "sec-innovation-summary",
    "品类总体分析总结", "产品创新机会", "品类创新机会汇总",
]
```

### 5. 评论数据来自离线生成器
当没有真实Sorftime API数据时，使用 `scripts/generate_offline_reviews.py` 生成模拟评论。生成后：
- 验证 `all_reviews.json` 中的 ASIN 列表是否与当前品类一致
- 验证评论数量是否与产品数据中的 `reviews` 字段大致匹配
- 如果离线生成器也是旧品类数据，需要重写生成逻辑

### 6. ❗ 报告验证清单 AFTER 生成（部署前必做）

子代理或独立脚本生成的HTML报告经常有JS问题。生成后必须手动验证：

**① JS语法检查**
```bash
# 检查Python语法混入JS（最常见错误）
grep -n "show:True\|show:False\|None\b" data/voc/voc_report_full.html | head -10
```
- `show:True` / `show:False` → JS中必须是 `show:true` / `show:false`（小写）
- `None` → JS中必须是 `null`
- `\\n` → JS中应该是 `\n`（单反斜杠；`\\n`显示为字面反斜杠+n）

**② ECharts渲染验证**
- 每个ECharts容器div都有对应的 `echarts.init()` JS调用
- **`#positioning`（评分×月销×评论量散点图）**最常被遗漏——必须检查
- 没有重复的 `init(document.getElementById("positioning"))` — 子代理可能在多个script块中重复写入
- 所有 `echarts.init()` 调用必须在对应 `div` 渲染**之后**（script放在section末尾）

**③ 数据完整性**
- 价格、评分、月销数值与真实 `product_info.json` 一致
- 评论情感分布（正向/中立/负向）与平均评分合理对应（4.5★→~90%正向）
- 品牌名拼写正确
- section锚点数量 = 预期模块数（14）

**④ HTML结构检查**
- `<footer>` 在 `</body>` 之前且 `text-align:center` 居中
- footer内容仅含：`<footer>数据来源：Sorftime ProductRequest</footer>`
- ❌ 不加"分析工具：Hermes Agent"
- ❌ 除非用户要求，否则不留署名
- 侧边栏 `.sidebar-shell` 应为 `position:fixed` 在右侧
- 没有多余闭合标签（如两个 `</div>` 连在一起？）

## 常见品类话题映射参考

### 厨房水龙头（15维度）
```
水压水流|spray|安装便捷|防漏耐用|质量做工|表面处理/耐污|
外观设计|噪音|旋转灵活|易用操作|性价比|售后服务|水温控制|节水气泡|风格配色
```

### 直发梳/美发工具（30维度）
```
直发效果|抗毛躁|卷发造型|光泽顺滑|速热性能|温控调节|
防烫安全|自动关机|电池续航|便携便携|易用操作|设计手感|
噪音控制|性价比|质量做工|负离子|涂层技术|断发拉扯|
护发健康|电源线|售后服务|蒸汽护发|顺发不打结|包装送礼|
持久定型|细软发|粗硬发|安全隐患|配件附件|颜色外观
```
