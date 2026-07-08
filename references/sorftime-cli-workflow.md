
# Sorftime CLI → review-analyzer-skill 工作流

从 Sorftime CLI 获取产品评论 → 转为 CSV → 用 review-analyzer-skill 分析。

## 安装 CLI

```bash
npm install -g sorftime-cli
# 二进制安装在 ~/.npm-global/bin/sorftime
```

## 配置 Profile

```bash
export PATH="/opt/data/.npm-global/bin:$PATH"  # 避免 command not found

# 添加 profile（Account-SK 为必填参数）
sorftime add default <account-sk>

# 切换到目标 profile
sorftime use default
```

## 获取评论：ProductReviewsQuery

```bash
# 基本查询（返回该 ASIN + 子体的最近评论）
sorftime api ProductReviewsQuery '{"asin":"B0FCS7NZ35"}' --domain 1

# 分页查询（每页 100 条，最多 3 页 = 300 条）
sorftime api ProductReviewsQuery '{"asin":"B0FCS7NZ35","pageIndex":1}' --domain 1
sorftime api ProductReviewsQuery '{"asin":"B0FCS7NZ35","pageIndex":2}' --domain 1
sorftime api ProductReviewsQuery '{"asin":"B0FCS7NZ35","pageIndex":3}' --domain 1

# 按星级过滤
# star=10 表示差评（1-3星）, star=11 表示好评（4-5星）
sorftime api ProductReviewsQuery '{"asin":"B0FCS7NZ35","star":"10"}' --domain 1
sorftime api ProductReviewsQuery '{"asin":"B0FCS7NZ35","star":"11"}' --domain 1
```

### ⚠️ 终端输出截断陷阱

当使用 `terminal()` 或 `execute_code()` 拉取 ProductReviewsQuery 时，**每条响应可能超过65KB**（包含100条评论+用户头像URL+媒体资源链接），而 `terminal()` 的默认输出上限是 ~50KB，超出后被静默截断，导致 JSON 解析失败。

**正确的做法：将输出重定向到文件，然后读取文件**（不要试图解析 terminal() 的 stdout）：

```python
# ❌ 错误方式 — 输出被截断，JSON 解析失败
r = terminal(cmd)
data = json.loads(r["output"])  # 截断 → JSONDecodeError

# ✅ 正确方式 — 写到文件再读取
terminal(f'{cmd} > /tmp/reviews_{asin}_p{page}.json 2>&1')
with open(f'/tmp/reviews_{asin}_p{page}.json') as f:
    raw = f.read()
# 额外注意：Sorftime CLI 输出包含 "正在调用API..." 等日志行，需提取 JSON 部分
start = raw.find('\n{')  # 跳过日志行，找第一个 JSON 对象
if start == -1: start = raw.find('{')
data = json.loads(raw[start:], strict=False)  # strict=False 处理评论内容中的控制字符
```

### 变体评论过滤

ProductReviewsQuery 返回的数据包含父体下所有变体ASIN的评论。必须用 `Asin` 字段过滤：

```python
asin_only = [rv for rv in items if rv.get("Asin") == target_asin]
```

不要混入变体评论，否则分析结果会失真。

## fetch_all_reviews.py 脚本

`review-analyzer-skill/fetch_all_reviews.py` 自动完成：
1. 翻页 3 次，每页 100 条
2. 按 ASIN 过滤（去掉变体子体，保留目标 ASIN）
3. 保存为 UTF-8 BOM CSV（review-analyzer 兼容格式）

```bash
python3 fetch_all_reviews.py                    # 默认 ASIN=B0FCS7NZ35
python3 fetch_all_reviews.py --asin B0CVM8TXHP  # 指定 ASIN
python3 fetch_all_reviews.py --pages 5          # 最多 500 条（需调整脚本）
```

## CSV 字段映射

| Sorftime 字段 | CSV 列名 | 说明 |
|---------------|----------|------|
| `Title` | `review_title` | 评论标题（短） |
| `Content` | `review_body` | 评论正文（长） |
| `Star` | `rating` | 评分 1-5 |
| `ReviewsDate` | `review_date` | 评论日期 (YYYYMMDD) |
| `ConsumerName` | `reviewer_name` | 用户名 |
| `IsVP` | `verified_purchase` | 是否 VP |
| `Helpful` | `helpful_count` | 有用票数 |

### 关于 ProductRequest（不要混淆）

`ProductRequest` 返回产品基本信息，**不是评论数据**。
评论用单独的 `ProductReviewsQuery` endpoint。

```bash
# 产品信息查询 — 批量查询10个ASIN用逗号分隔
sorftime api ProductRequest '{"asin": "B0FCS7NZ35,B0FC2NCYSL"}' --domain 1

# ⚠️ 参数是 asin（逗号分隔字符串），不是 asinList（数组）
# ❌ sorftime api ProductRequest '{"asinList":["B0FCS7NZ35"]}' --domain 1  # 返回 Code:10 参数错误

# 重要：MCP工具的ProductRequest参数格式是 asinList（数组），
# 而Sorftime CLI的ProductRequest参数格式是 asin（字符串，逗号分隔）
# 不要混淆两者！

# ✅ 评论数据用独立 endpoint
sorftime api ProductReviewsQuery '{"asin":"B0FCS7NZ35"}' --domain 1
```

## review-analyzer-skill 分析

```bash
cd /opt/data/skills/review-analyzer-skill
source .venv/bin/activate
python3 main.py "data/{ASIN}_reviews.csv" --max-reviews 300 --creator "郑佳" --template premium-gold
```

输出在 `output/` 目录：
- `可视化洞察报告_{ASIN}.html` — 可直接部署到 Vercel
- `分析洞察报告_{ASIN}.md` — Markdown 报告
- `评论采集及打标数据_{ASIN}.csv` — 标签数据

## Vercel 部署

```bash
DEPLOY_DIR="/tmp/report-deploy"
mkdir -p "$DEPLOY_DIR"
cp "output/可视化洞察报告_{ASIN}.html" "$DEPLOY_DIR/index.html"
echo '{"version":2}' > "$DEPLOY_DIR/vercel.json"
export PATH="/opt/data/.npm-global/bin:$PATH"
TOKEN=$(echo '<base64>' | base64 -d)
npx vercel link --project <project-name> --token "$TOKEN" --yes --cwd "$DEPLOY_DIR"
npx vercel deploy --prod --yes --force --token "$TOKEN" --cwd "$DEPLOY_DIR"
```
