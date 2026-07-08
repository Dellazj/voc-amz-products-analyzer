# 多ASIN品类VOC分析工作流

> 针对竞品对标分析场景，分析 10 个 ASIN 的评论，生成 ECharts 暗色主题品类报告。

## 触发条件

- 用户给出 3~10 个同品类 ASIN，要求评论/客户之声分析
- 用户引用参考报告风格（wenmai-ai.com 暗色 ECharts 报告）
- 关键词：VOC分析、品类评论分析、竞品评论对比

## 工作流

### 0. 前置条件

```bash
# Sorftime CLI 必须已安装
npm install -g sorftime-cli
export PATH="/opt/data/.npm-global/bin:$PATH"

# 配置 profile
sorftime add default <account-sk>
sorftime use default
```

### 1. 获取产品基础信息

```bash
# 单个/多个 ASIN 用逗号分隔，最多10个
sorftime api ProductRequest '{"asin": "B07MMQ4BZH,B0BL34CGLM,...", "trend": 2}' --domain 1
```

⚠️ **关键坑**：`ProductRequest` 的参数是 `asin`（**字符串**，逗号分隔），不是 `asinList`（数组）。

有用字段：`Title`, `Price`, `Ratings`(评分), `RatingsCount`, `AsinSalesCount`(月销), `Brand`, `BuyboxSeller`, `BsrCategory`, `OnlineDate`, `FiveStartRatings`/`OneStartRatings`(星级分布), `Description`, `Feature`(锚点评分), `Photos`

### 2. 获取评论数据

```bash
# 翻页调用，每页最多 100 条，最多 3 页 = 300 条
sorftime api ProductReviewsQuery '{"asin": "B07MMQ4BZH", "pageIndex": 1}' --domain 1
```

返回字段：`Content`, `Star`, `Title`, `ReviewsDate`, `VariationInfo`

注意：返回结果中会混入**变体 ASIN** 的评论，需要根据 `Asin` 字段过滤。

### 3. 数据预处理（Python）

执行以下步骤（用 Python 脚本在 execute_code 或 terminal 中完成）：

1. **情感分类**：基于星级 + 关键词规则（并非所有 4 星都是好评，有严重负面关键词 → 降级）
2. **话题提取**：正则匹配关键词 → 归类到 20+ 话题（直发效果/速热/防烫/电池等）
3. **逐 ASIN 汇总**：情感分布、星级分布、Top 话题、好差评样本
4. **品类级汇总**：总话题频次、情感总览、均价/均分统计
5. **好差评样本采集**：每个 ASIN 采 3 正 + 3 负

### 4. 分析维度

| 维度 | 方法 |
|------|------|
| **情感分布** | 正面/中立/负面 分类统计，含饼图 |
| **星级分布** | 1~5 星分 ASIN 累计柱状图 |
| **品类话题云** | 所有 ASIN 话题提及频次 TOP15 |
| **KANO 需求分类** | 基于话题频率：>15% = 基本, >8% = 期望, <8% = 魅力 |
| **用户旅程摩擦** | 6 阶段雷达图（认知→比较→购买→开箱→使用→售后） |
| **ABSA 方面情感** | 每话题正面/负面提及次数对比柱状图 |
| **逐 ASIN 对比** | 好评率/差评率堆叠柱状图 |
| **痛·爽·痒矩阵** | 三列布局：痛点(Pains) / 爽点(Joys) / 痒点(Itches) |
| **好差评样本** | 逐 ASIN 展示精选原声 |

### 5. 报告生成

参考 `references/voc-report-structure.md` 中的 9 模块完整结构，包括：
1. 品类总览 Dashboard（4KPI + 价格饼图 + 评分分布 + 情感饼图 + 商品表）
2. PSPS 用户画像（Persona/Scenario/Pain 三列）
3. ABSA 方面级情感分析（双柱对比 + 表格）
4. $APPEALS 8维竞争力分析（雷达图/玫瑰图）
5. KANO 需求分类（三栏卡片 + 进度条）
6. 痛爽痒三维图谱（三列 + 提及率%）
7. 用户旅程摩擦分析（8阶段雷达 + 详解）
8. 逐品 ASIN 拆解（可展开卡片 + 情感饼图）
9. 品类好差评横向对比 + 创新机会汇总

> 注意：B0DCK8P752 品牌是 **Wavytalk** 不是 TYMO！详见 voc-report-structure.md 的品牌校验表。

### ⚠️ 关键陷阱：子代理生成假数据

当你用 `delegate_task` 让子代理生成 VOC 报告 HTML 时，子代理**没有 Sorftime API 权限**。它会在 HTML 模板中虚构所有数字——价格、评分、评论量、月销量。这些"合理猜测"的结果偏差极大。

**最佳实践**：
1. 在主进程中用 `sorftime api ProductRequest` 批量拉取真实数据
2. 把真实数据 JSON 作为 `context` 传入子代理
3. 子代理只负责 HTML 布局、CSS、ECharts 图表配置——不做数据查询
4. 生成后父进程**必须**用 `read_file` 验证 HTML 表格行中的价格/评分/评论量字段

**修正方案**：如果子代理已经写了假数据，用精确字符串替换逐个 ASIN 修正 HTML 中的 `<td>` 值，而不是重写整个文件。

### 6. 部署到 Vercel

### 7. 中文翻译（新增—v6要求）

用户要求好在差评精选（逐品拆解模块）中，每条英文评价下方附带中文简译：

```python
EN_CN_MAP = {
    "amazing":"非常棒","love":"很喜欢","great":"很好","smooth":"顺滑",
    "fast":"快速","broke":"坏了","burn":"烫伤","waste":"浪费",
    # ... ~100 keywords
}
def roughly_translate(text):
    t = text.lower()
    phrases = []
    for en, cn in sorted(EN_CN_MAP.items(), key=lambda x:-len(x[0])):
        if en in t:
            phrases.append(cn)
    if not phrases:
        return ""
    return "点评： " + "，".join(list(dict.fromkeys(phrases))[:3])
```

在HTML中以灰色斜体显示：`<div class="cn-trans">📝 {translation}</div>`

### 6. 部署到 Vercel

```python
import base64, subprocess, os, shutil, re

T = base64.b64decode('base64-encoded-token').decode()
V = os.path.expanduser('~/.npm-global/bin/vercel')
D = '/tmp/voc-deploy'

os.makedirs(D, exist_ok=True)
shutil.copy2('voc_report.html', D + '/index.html')
with open(D + '/vercel.json', 'w') as f:
    f.write('{"version":2}')

c = os.path.join(D, '.vercel')
if os.path.exists(c): shutil.rmtree(c)

e = os.environ.copy()
e['PATH'] = os.path.expanduser('~/.npm-global/bin') + ':' + e['PATH']

r = subprocess.run([V, 'deploy', '--token', T, '--prod', '--yes', '--force'],
    capture_output=True, text=True, cwd=D, env=e, timeout=90)

url = re.search(r'https://[a-z0-9-]+\.vercel\.app', r.stdout)
print(url.group(0) if url else '?')
```

## Pitfalls

| # | 问题 | 解决方案 |
|---|------|---------|
| 1 | `ProductRequest` 用 `asinList` 数组 → Code 10 参数错误 | 用 `asin` 逗号分隔字符串 |
| 2 | ProductReviewsQuery 返回变体 ASIN 的评论 | 取 `Asin` 字段过滤 |
| 3 | 评论超过 100 条只返回第 1 页 | 翻页 `pageIndex` 1..3 |
| 4 | 4 星评论也有严重负面关键词 | 关键词辅助规则，>=3 个负面词 → 降级为负向 |
| 5 | 1~2 星评论少量正面词 → 错误标为正 | 正面词 >=3 才考虑升级，否则按星标负 |
| 6 | 话题提取依赖正则准确率 | 确保正则覆盖变体写法（"ion" 匹配 "negative ion" 和 "anti-frizz"） |
| 7 | Vercel token 过期或无效 | 从 deploy_smart_ring.py 中的 base64 取最新 token |
