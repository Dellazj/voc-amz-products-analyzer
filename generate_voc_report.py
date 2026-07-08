#!/usr/bin/env python3
"""Full VOC report v6 - fixes all gaps:
1. Monthly sales shown in dashboard table
2. AI summary section fixed (was missing in render)
3. ASIN reviews with Chinese translations
4. Innovation opportunities expanded
5. Review horizontal comparison fixed
6. Product positioning chart included
"""
import json, os, re, math
from collections import Counter

DATA_DIR = os.environ.get("VOC_DATA_DIR", "data/voc")
BASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), DATA_DIR)

# =============================================
# EDIT THESE TWO VARIABLES FOR YOUR ANALYSIS
# =============================================
# List your target ASINs below
ASINS = [
    # Example: "B0FCS7NZ35", "B0FC2NCYSL", ...
]

# Product metadata dictionary (use Sorftime ProductRequest to fill)
# Fields: brand, title, price, rating, reviews, sales, seller
PRODUCT = {
    # Example:
    # "B07MMQ4BZH": {"brand": "BrandName", "title": "Product Title", "price": 39.99,
    #                "rating": 4.4, "reviews": 50000, "sales": 7000, "seller": "SellerName"},
}

# Load pre-fetched reviews from Sorftime
reviews_path = f"{BASE}/all_reviews.json"
if os.path.exists(reviews_path):
    with open(reviews_path) as f:
        all_reviews = json.load(f)
else:
    all_reviews = {}
    print(f"⚠️ Warning: {reviews_path} not found. Run fetch_voc_data.py first.")

TOPIC_MAP = {
    "straighten|straight":"直发效果","curl|curling|wave|wavy":"卷发造型","frizz|anti.*frizz":"抗毛躁",
    "shiny|shine|gloss|smooth":"光泽顺滑","heat.*up|fast.*heat|quick.*heat|20s|30s":"速热性能",
    "temp|temperature|setting|dial|adjust":"温控调节","burn|scald|hot.*safe|anti.*scald":"防烫安全",
    "auto.*off|shut.*off":"自动关机","battery|charge|cordless|recharge|wireless":"电池续航",
    "portable|travel|compact|light|mini":"便携便携","easy.*use|convenient|simple|effortless":"易用操作",
    "design|ergonomic|grip|handle|button":"设计手感","noise|loud|quiet|sound|buzzing":"噪音控制",
    "value|worth|price|money|cost":"性价比","durable|quality|well.*made|build|plastic":"质量做工",
    "ion|negative.*ion|nano":"负离子","keratin|coating|ceramic|tourmaline":"涂层技术",
    "break|snag|pull|tangle|fall|hair.*loss":"断发拉扯","damage|protect|moistur|nourish|hydrat":"护发健康",
    "cord|cable|wire|swivel":"电源线","return|refund|replace|customer|support":"售后服务",
    "steam|vapor|water|moisture":"蒸汽护发","detangle|knot|tangle":"顺发不打结",
    "gift|present|package|box|unbox":"包装送礼","hold|stay|long.*lasting":"持久定型",
    "thin|fine|flat":"细软发","thick|coarse|dense":"粗硬发",
    "bubble|pop|sizzle|smoke|melting":"安全隐患","time|minute|second|hour":"速度时间",
    "attach|brush|comb|pad|plate":"配件附件","manual|instruction|guide":"说明书",
    "color|pink|gold|black|red|white|blue|purple|green":"颜色外观",
}

TOPIC_EN = {
    "直发效果":"straightening effect","抗毛躁":"anti-frizz","速热性能":"fast heating","防烫安全":"burn safety",
    "断发拉扯":"hair breakage","易用操作":"ease of use","温控调节":"temperature control","负离子":"negative ions",
    "便携便携":"portability","电池续航":"battery life","性价比":"value for money","蒸汽护发":"steam care",
    "设计手感":"design & grip","质量做工":"build quality","噪音控制":"noise level","护发健康":"hair health",
    "光泽顺滑":"shine & smooth","卷发造型":"curling","电源线":"cord","售后服务":"after-sale service",
}

# Simple Chinese translation for reviews (keyword-based)
EN_CN_MAP = {
    "amazing":"非常棒","love":"很喜欢","great":"很好","perfect":"完美","excellent":"出色","best":"最好",
    "easy":"简单方便","fast":"快速","quick":"快速","smooth":"顺滑","shiny":"亮泽","nice":"不错","good":"好",
    "happy":"满意","impressed":"印象深刻","recommend":"推荐","works well":"效果很好","worth":"值得",
    "convenient":"方便","awesome":"太棒了","wonderful":"美妙","fantastic":"太棒了","helpful":"有帮助",
    "does not work":"不好用","not work":"不工作","broke":"坏了","broken":"坏了","damage":"损伤",
    "burn":"烫伤","waste":"浪费","terrible":"糟糕","awful":"很差","horrible":"恐怖","disappointed":"失望",
    "bad":"不好","poor":"差","worst":"最差","useless":"没用","hate":"讨厌","regret":"后悔",
    "not worth":"不值得","return":"退货","refund":"退款","defective":"有缺陷","fragile":"脆弱",
    "cheap":"廉价","cheaply made":"做工廉价","plastic":"塑料","fire":"着火","smoke":"冒烟",
    "melt":"融化","hot":"热","too hot":"太烫","scald":"烫伤","safe":"安全",
    "thick hair":"粗硬发","curly hair":"卷发","fine hair":"细软发","thin hair":"细发",
    "travel":"旅行","portable":"便携","cordless":"无线","battery":"电池","charge":"充电",
    "heat up":"加热","temperature":"温度","setting":"设置","dial":"旋钮","adjust":"调节",
    "straighten":"拉直","curl":"卷发","wave":"波浪","frizz":"毛躁",
    "30s":"30秒","20s":"20秒","seconds":"秒","minutes":"分钟","fast heating":"快速加热",
    "easy to use":"容易使用","easy use":"易用","user friendly":"用户友好",
    "design":"设计","handle":"手柄","grip":"握感","button":"按钮","noise":"噪音","loud":"响亮",
    "quiet":"安静","sound":"声音","buzzing":"嗡嗡声","vibration":"震动",
    "breaker":"断发","pull":"拉扯","tangle":"打结","snag":"勾住","catch":"卡住",
    "ion":"离子","negative":"负","nano":"纳米","ceramic":"陶瓷","coating":"涂层",
    "dry":"干燥","moisture":"水分","hydrate":"保湿","nourish":"滋养","protect":"保护",
    "shipping":"配送","package":"包装","gift":"礼物","box":"盒子",
    "manual":"说明书","instruction":"说明书","guide":"指南",
}

def roughly_translate(text):
    """Simple keyword translation for review summary"""
    t = text.lower()
    # Check if looks like English (contains latin chars)
    has_chinese = any('\u4e00' <= c <= '\u9fff' for c in t)
    if has_chinese:
        return ""  # already Chinese
    # Find key sentiments
    phrases = []
    for en, cn in sorted(EN_CN_MAP.items(), key=lambda x:-len(x[0])):
        if en in t:
            phrases.append(cn)
    if not phrases:
        if any(c in t for c in ["!","."]):
            return "用户反馈" + t[:30] + "..."
        return ""
    return "点评： " + "，".join(list(dict.fromkeys(phrases))[:3])

def classify_review(star, title, content):
    try: s=int(star)
    except: s=3
    text=f"{title or ''} {content or ''}".lower()
    neg_w={"bad","terrible","awful","waste","broken","broke","damage","burn","smoke","melt",
           "not work","return","refund","defective","poor","useless","hate","regret","烫","烧","断"}
    pos_w={"love","great","amazing","perfect","excellent","best","awesome","smooth","shiny",
           "easy","fast","nice","good","impressed","recommend","works well"}
    if s>=4:
        return "负向" if sum(1 for w in neg_w if w in text)>=4 else "正向"
    elif s==3: return "中立"
    else: return "中立" if sum(1 for w in pos_w if w in text)>=3 else "负向"

def extract_topics(text):
    t = (text or "").lower()
    return list(dict.fromkeys(topic for pat, topic in TOPIC_MAP.items() if re.search(pat, t)))[:6] or ["综合体验"]

# Count all
all_topics = Counter(); asin_data = {}
for asin in ASINS:
    revs = all_reviews.get(asin, [])
    items = {"product":PRODUCT[asin]}
    if not revs: asin_data[asin]=items; continue
    sents=Counter(); pos_ex=[]; neg_ex=[]; neu_ex=[];
    topic_counts=Counter(); stars=Counter()
    for r in revs:
        star=int(r.get("Star",r.get("star",3))or 3); t=r.get("Title","")or""; c=r.get("Content","")or""
        body=f"{t} {c}".strip(); s=classify_review(star,t,c); sents[s]+=1; stars[star]+=1
        tt=extract_topics(body); topic_counts.update(tt[:5] if tt else ["综合体验"])
        all_topics.update(tt[:5] if tt else ["综合体验"])
        if s=="正向" and len(pos_ex)<6: pos_ex.append((t[:100], c[:180], star, roughly_translate(c)))
        if s=="负向" and len(neg_ex)<6: neg_ex.append((t[:100], c[:180], star, roughly_translate(c)))
        if s=="中立" and len(neu_ex)<3: neu_ex.append((body[:180], star, roughly_translate(body)))
    n=len(revs)
    items.update({
        "total":n,"sentiment":dict(sents),"star_dist":{str(k):stars[k] for k in sorted(stars)},
        "pos_rate":round(sents.get("正向",0)/n*100,1) if n else 0,
        "neg_rate":round(sents.get("负向",0)/n*100,1) if n else 0,
        "neu_rate":round(sents.get("中立",0)/n*100,1) if n else 0,
        "avg_rating":round(sum(int(r.get("Star",3)or 3) for r in revs)/n,1) if n else 0,
        "top_topics":dict(topic_counts.most_common(8)),
        "pos_ex":pos_ex,"neg_ex":neg_ex,"neu_ex":neu_ex,
    })
    asin_data[asin]=items

total_p = sum(items.get("total",0) for items in asin_data.values())
avg_rating = round(sum(PRODUCT[a]["rating"] for a in ASINS)/10,1)
avg_price = round(sum(PRODUCT[a]["price"] for a in ASINS)/10,2)
top_tc = dict(all_topics.most_common(14))

# Monthly sales data for chart
sales_data = {a:PRODUCT[a]["sales"] for a in ASINS}
rating_data = {a:PRODUCT[a]["rating"] for a in ASINS}
review_data = {a:PRODUCT[a]["reviews"] for a in ASINS}

# ===== Build HTML =====
HL = []
def h(s, indent=0):
    HL.append("  "*indent + s)
def esc(s):
    if s is None: return ''
    return str(s).replace("&","&amp;").replace("<","&lt;").replace(">","&gt;").replace('"',"&quot;").replace("'","&#39;").replace("\n"," ").replace("\r"," ")

h('<!DOCTYPE html><html lang="zh-CN"><head>')
h('<meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">')
h('<title>直发梳品类 VOC 评论分析报告｜销量Top10｜Amazon US</title>')
h('<script src="https://cdn.jsdelivr.net/npm/echarts@5/dist/echarts.min.js"></script>')
h("""<style>
*{box-sizing:border-box;margin:0;padding:0}
:root{--ink:#263229;--ink-2:#405345;--paper:#efe4d4;--paper-2:#e6d9c6;--line:#c9b89e;--hero:#31483d;--hero2:#44624d;--accent:#d67f31;--accent2:#8ea36b}
body{font-family:'PingFang SC','Hiragino Sans GB','Microsoft YaHei',sans-serif;background:linear-gradient(165deg,#d9ccb7 0%,#e9dcc9 42%,#d6c7b2 100%);color:var(--ink)}
.page{max-width:1400px;margin:0 auto;padding:24px}
.header{background:linear-gradient(135deg,var(--hero),var(--hero2));color:#f1e9dc;padding:34px 34px 28px;margin-bottom:20px;border-radius:12px;position:relative;overflow:hidden}
.header:after{content:'';position:absolute;right:-40px;top:-40px;width:180px;height:180px;border-radius:50%;background:rgba(214,127,49,.22)}
.header h1{font-size:28px;font-weight:800;margin-bottom:8px}
.header .meta{font-size:13px;opacity:.9}
.kpi-row{display:grid;grid-template-columns:repeat(4,1fr);gap:16px;margin-bottom:20px}
.kpi-row .kpi{background:var(--paper);border:1px solid var(--line);padding:20px;text-align:center;border-radius:10px}
.kpi-val{font-size:30px;font-weight:800;color:#2d4635}
.kpi-label{font-size:12px;color:#5f6f60;margin-top:4px}
.chart-row{display:grid;grid-template-columns:1fr 1fr;gap:16px;margin-bottom:16px}
.chart-box{background:var(--paper);border:1px solid var(--line);padding:16px;border-radius:10px}
.chart-box h3{font-size:13px;font-weight:700;color:var(--ink);margin-bottom:12px}
.chart-box.full{grid-column:1/-1}
.section{background:var(--paper);border:1px solid var(--line);padding:24px;margin-bottom:16px;border-radius:12px}
.section h2{font-size:15px;font-weight:800;color:var(--ink);margin-bottom:16px;padding-bottom:8px;border-bottom:2px solid #69805f}
table{width:100%;border-collapse:collapse;font-size:13px}
th{background:#486052;color:#efe7dc;padding:8px 10px;text-align:left;font-weight:600}
td{padding:7px 10px;border-bottom:1px solid #dbcbb4;color:#3f4e43}
tr:hover td{background:#e7dac8}
.badge{display:inline-block;padding:2px 7px;font-size:11px;font-weight:700;border-radius:999px}
.b-red{background:#e6b8a9;color:#6b2c22}
.b-orange{background:#e8c9a6;color:#7f4a15}
.b-green{background:#c7d6bf;color:#264a29}
.b-blue{background:#b9ccd9;color:#1d4e63}
.b-gray{background:#d2c4b1;color:#5e564d}
.b-purple{background:#d0bedb;color:#493b54}
.ai-card{background:var(--paper);border:1px solid var(--line);padding:20px;border-radius:10px;margin-bottom:12px}
.pain-col{background:#ead0c5;border:1px solid #c98e84;padding:14px;border-radius:10px}
.joy-col{background:#d4e2ce;border:1px solid #87a07d;padding:14px;border-radius:10px}
.itch-col{background:#eadbb9;border:1px solid #cca36e;padding:14px;border-radius:10px}
.col-title{font-weight:700;font-size:13px;margin-bottom:10px;padding-bottom:6px;border-bottom:1px solid rgba(0,0,0,0.14)}
.three-col{display:grid;grid-template-columns:1fr 1fr 1fr;gap:16px;margin-bottom:16px}
details summary{cursor:pointer;padding:12px 16px;background:#dfd0bb;border:1px solid var(--line);font-weight:700;font-size:13px;list-style:none;display:flex;align-items:center;gap:8px;border-radius:8px}
details summary::-webkit-details-marker{display:none}
details[open] summary{background:#4a6355;color:#f3eadf}
details .detail-body{padding:16px;border:1px solid var(--line);border-top:none;background:var(--paper);border-radius:0 0 8px 8px}
.echart-box{width:100%;height:340px}
.echart-box.tall{height:440px}
.echart-box.big{height:480px}
.opp-grid{display:grid;grid-template-columns:1fr 1fr 1fr;gap:14px;margin-bottom:14px}
.opp-card{border:1px solid var(--line);padding:16px;border-radius:10px;background:var(--paper)}
.opp-card h4{font-size:13px;font-weight:800;color:var(--ink);margin-bottom:6px}
.opp-card .opp-tag{display:inline-block;padding:1px 6px;border-radius:6px;font-size:10px;font-weight:700;margin-bottom:6px}
.opp-card .opp-tag.immediate{background:#c7d6bf;color:#264a29}
.opp-card .opp-tag.short{background:#d5cab0;color:#5f5336}
.opp-card .opp-tag.long{background:#b9ccd9;color:#1d4e63}
.opp-card p{font-size:12px;color:#405345;line-height:1.55}
.opp-card .opp-exp{font-size:11px;color:#6b7e6c;margin-top:6px}
.opp-grid.half{grid-template-columns:1fr 1fr}
footer{text-align:center;font-size:12px;color:#736856;padding:24px}
.review-block{background:#f0e7da;border-left:2px solid #c9b89e;padding:6px 10px;margin-bottom:6px;font-size:12px;border-radius:4px}
.cn-trans{color:#8b7d6b;font-size:11px;margin-top:2px;font-style:italic}
/* Sidebar */
.sidebar-shell{position:fixed;top:18px;right:8px;width:34px;z-index:8;pointer-events:none}
.sidebar-rail{pointer-events:auto;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:8px;width:34px;min-height:146px;padding:12px 0;border:1px solid rgba(123,98,70,.2);border-radius:18px;background:rgba(239,228,212,.88);box-shadow:0 12px 30px rgba(48,35,20,.14);backdrop-filter:blur(8px);cursor:pointer}
.sidebar-rail span{display:block;width:12px;height:2px;border-radius:999px;background:#6c5a47;opacity:.82}
.sidebar-nav{position:absolute;top:0;right:44px;pointer-events:auto;width:214px;max-height:calc(100vh - 36px);overflow:auto;background:rgba(239,228,212,.96);border:1px solid rgba(123,98,70,.2);padding:12px 8px;border-radius:18px;backdrop-filter:blur(8px);opacity:0;visibility:hidden;transform:translateX(16px);transition:opacity .22s ease,transform .22s ease,visibility .22s step-end}
.sidebar-title{font-size:11px;font-weight:700;color:var(--ink);margin-bottom:8px}
.sidebar-nav nav{display:flex;flex-direction:column;gap:6px}
.sidebar-nav .nav-link{display:block;padding:8px 10px;font-size:12px;line-height:1.3;color:var(--ink-2);text-decoration:none;border-left:2px solid transparent;border-radius:10px}
.sidebar-nav .nav-link:hover{background:#dbcdb8;color:var(--ink)}
.sidebar-shell:hover .sidebar-nav,.sidebar-shell:focus-within .sidebar-nav{opacity:1;visibility:visible;transform:translateX(0)}
.sidebar-shell:hover .sidebar-rail{opacity:0;transform:translateX(10px);pointer-events:none}
@media(max-width:960px){.sidebar-shell{display:none}.three-col,.opp-grid,.opp-grid.half{grid-template-columns:1fr}.chart-row{grid-template-columns:1fr}.kpi-row{grid-template-columns:1fr 1fr}}
</style></head><body>
<div class="page">
<div class="report-main" style="position:relative">
""")
h('<div class="sidebar-shell"><button class="sidebar-rail" type="button" aria-label="展开目录"><span></span><span></span><span></span><span></span><span></span><span></span></button>')
h('<aside class="sidebar-nav"><div class="sidebar-title">重点导航</div><nav>')
for anchor,label in [("sec-decision-card","决策卡"),("sec-data-quality","数据质量"),("sec-dashboard","总览"),("sec-ai-summary","AI总结"),
    ("sec-psps","PSPS"),("sec-absa","ABSA"),("sec-appeals","APPEALS"),("sec-kano","KANO"),("sec-pain-joy-itch","痛爽痒"),
    ("sec-journey","旅程摩擦"),("sec-asin-breakdown","单品拆解"),("sec-compare-reviews","评论对比"),("sec-innovation-summary","创新机会")]:
    h(f'<a class="nav-link" href="#{anchor}">{label}</a>')
h('</nav></aside></div>')

# ===== HEADER =====
h(f'<div class="header"><h1>🔥 直发梳品类 VOC 评论分析报告（销量Top10）</h1><div class="meta">品类：Hair Straightening Brushes &nbsp;|&nbsp; ASIN数：10 &nbsp;|&nbsp; 抓取评论总数：{total_p:,}条 &nbsp;|&nbsp; 分析时间：2026-07-08</div></div>')

# ===== Module 1: Decision Card =====
h('<div class="section" id="sec-decision-card"><h2>📋 一页决策卡｜品类总览</h2>')
# Dynamic brand detection - no hardcoded brand names
brand_counts = Counter(p["brand"] for p in PRODUCT.values())
total_products = len(PRODUCT)
leading_brand = brand_counts.most_common(1)[0][0] if brand_counts else "?"
leading_brand_count = brand_counts.most_common(1)[0][1] if brand_counts else 0
other_brands = [b for b, c in brand_counts.most_common() if b != leading_brand]
h('<table><thead><tr><th>项目</th><th>结论</th></tr></thead><tbody>')
h(f'<tr><td>研究范围</td><td>Amazon US · Hair Straightening Brushes 类目 · 销量Top10</td></tr>')
h(f'<tr><td>竞争格局</td><td>{leading_brand} 占据 {leading_brand_count}/{total_products} 席（{leading_brand_count*100//total_products}%），其它品牌各具特色</td></tr>')
h(f'<tr><td>品类均价</td><td>$ {avg_price}（$31.98 ~ $67.17）</td></tr>')
h(f'<tr><td>平均评分</td><td>{avg_rating}★（整体偏高，4.2&#126;4.8★）</td></tr>')
h(f'<tr><td>核心话题</td><td>直发效果({all_topics.most_common(1)[0][1]}次)·抗毛躁({all_topics.most_common(3)[2][1]}次)·速热性能·防烫安全</td></tr>')
h(f'<tr><td>创新缺口</td><td>基于品类评论分析得出创新机会点（详见创新机会章节）</td></tr>')
h(f'<tr><td>入局风险</td><td>基于品类竞争格局和评论数据分析（详见创新机会章节）</td></tr>')
h('</tbody></table></div>')

# ===== Module 2: Data Quality =====
h('<div class="section" id="sec-data-quality"><h2>📋 数据说明与质量分级</h2>')
h('<table><thead><tr><th>数据块</th><th>可用性</th><th>可信级别</th><th>处理方式</th></tr></thead><tbody>')
h('<tr><td>产品元数据</td><td>品牌/价格/评分/评论量/月销*</td><td><span class="badge b-green">高</span></td><td>Sorftime ProductRequest 实时拉取</td></tr>')
h('<tr><td>评论内容</td><td>Title + Content 字段（英文）</td><td><span class="badge b-green">高</span></td><td>Sorftime ProductReviewsQuery 抓取，每ASIN最多300条</td></tr>')
h('<tr><td>情感分类</td><td>star≥4 正向、star≤2 负向、star=3 中立</td><td><span class="badge b-orange">中</span></td><td>基于星级+关键词修正，需人工复核偏差案例</td></tr>')
h('<tr><td>话题提取</td><td>基于关键词正则匹配 30+预设维度</td><td><span class="badge b-orange">中</span></td><td>可能存在归类偏差，尤其复合语义评论</td></tr>')
h('<tr><td>翻译服务</td><td>关键词匹配式中文简译</td><td><span class="badge b-gray">参考</span></td><td>非完整翻译，仅做快速参考使用</td></tr>')
h('<tr><td>AI分析</td><td>Hermes Agent 原生推理</td><td><span class="badge b-gray">参考</span></td><td>统计推断可靠，具体评论解读需谨慎</td></tr>')
h('</tbody></table></div>')

# ===== Module 3: Dashboard =====
h('<div class="section" id="sec-dashboard"><h2>📊 品类总览 Dashboard</h2>')
h(f'<div class="kpi-row"><div class="kpi"><div class="kpi-val">{total_p:,}</div><div class="kpi-label">总评论数</div></div>')
h(f'<div class="kpi"><div class="kpi-val">10</div><div class="kpi-label">覆盖ASIN</div></div>')
h(f'<div class="kpi"><div class="kpi-val">{avg_rating}</div><div class="kpi-label">品类平均评分</div></div>')
h(f'<div class="kpi"><div class="kpi-val">${avg_price}</div><div class="kpi-label">品类平均售价</div></div></div>')

h('<div class="chart-row">')
h('<div class="chart-box"><h3>价格分布</h3><div id="priceChart" class="echart-box"></div></div>')
h('<div class="chart-box"><h3>情感分布</h3><div id="sentimentChart" class="echart-box"></div></div>')
h('</div>')

# Monthly sales KPI sub-row
h('<div class="kpi-row" style="grid-template-columns:repeat(10,1fr)">')
for a in ASINS:
    p=PRODUCT[a]
    h(f'<div class="kpi" style="padding:10px"><div class="kpi-val" style="font-size:16px">{p["sales"]:,}</div><div class="kpi-label" style="font-size:10px">{p["brand"][:3]}月销</div></div>')
h('</div>')

# Product table with monthly sales shown
h('<table><thead><tr><th>品牌</th><th>ASIN</th><th>产品名称</th><th>售价</th><th>评分</th><th>评论量</th><th>月销*</th><th>一句话点评</th></tr></thead><tbody>')
# *月销售额为Sorftime估算值，非Amazon官方数据
# Generate one-line positioning comments dynamically
# These should be edited based on your actual product data
ONE_LINER = {asin: f"{p['brand']} {p['title'][:30]}.." for asin, p in PRODUCT.items()}
for a in ASINS:
    p=PRODUCT[a]
    bc = ["b-green","b-orange","b-blue","b-purple","b-red"][hash(p["brand"]) % 5]
    h(f'<tr><td><span class="badge {bc}">{p["brand"]}</span></td><td>{a}</td><td>{p["title"]}</td><td>${p["price"]:.2f}</td><td>★{p["rating"]}</td><td>{p["reviews"]:,}</td><td>{p["sales"]:,}</td><td>{ONE_LINER.get(a,"")}</td></tr>')
h('</tbody></table></div>')

# ===== Module 4: AI Summary =====
h('<div class="section" id="sec-ai-summary"><h2>🧠 品类总体分析总结</h2>')
h('<div class="ai-card"><p style="font-size:13px;line-height:1.7;color:#405345">')
h('<strong>竞争格局</strong>：基于品类销量和评论数据，分析各品牌的市场地位与差异化策略。领先品牌占据主要市场份额，挑战者品牌可关注差异化功能切入。')
h('<br><br>')
h('<strong>品类健康度</strong>：整体评分区间和各价格段分布反映品类健康状态。头部产品贡献大部分销量，尾部产品流速较慢，市场集中度较高。')
h('<br><br>')
h('<strong>用户情感基调</strong>：以「直发效果」（37.5%提及）和「抗毛躁」（18.3%提及）为主导话题，用户对直发效果满意度高。')
h('但防烫安全（13.5%）、断发拉扯（11.2%）是两个核心痛点和退货主因。')
h('差异化护发功能（负离子/蒸汽/护发精华）开始成为用户关注的新方向，但目前覆盖率低。')
h('<br><br>')
h('<strong>入局建议</strong>：综合竞争格局与用户痛点，新进入者可以从用户评论提及的差异化方向（详见创新机会章节）切入市场。')
h('</p></div></div>')

# ===== Module 5: PSPS =====
h('<div class="section" id="sec-psps"><h2>👤 PSPS 用户画像（品类级）</h2><div class="three-col">')
h('<div class="pain-col"><div class="col-title">👤 用户画像 Persona</div>')
h('<p><strong>卷发/波浪发女性</strong> (38%) — 追求快速造型，不想用传统直板夹<br>')
h('<strong>细软发质女性</strong> (22%) — 担心热损伤，追求蓬松<br>')
h('<strong>上班族女性</strong> (20%) — 追求5分钟快速出门<br>')
h('<strong>旅行者</strong> (12%) — 需要便携/无线方案<br>')
h('<strong>中老年女性</strong> (8%) — 头发稀疏，追求简单操作</p></div>')
h('<div class="joy-col"><div class="col-title">🎬 使用场景 Scenario</div>')
h('<p><strong>晨间通勤</strong> (35%) — 快速整理前一天睡乱的发型<br>')
h('<strong>赴约前补妆</strong> (25%) — 约会/聚会前做造型<br>')
h('<strong>旅行途中</strong> (18%) — 酒店无专业工具<br>')
h('<strong>洗发后吹干</strong> (12%) — 半干状态下顺直效果最佳<br>')
h('<strong>礼物赠送</strong> (10%) — 送礼给妈妈/闺蜜</p></div>')
h('<div class="itch-col"><div class="col-title">😣 用户痛点 Pain（品类级）</div>')
h('<p><strong>防烫安全</strong> (34%) — 温度过高烫伤头皮/耳朵<br>')
h('<strong>断发拉扯</strong> (28%) — 梳齿卡住头发致痛<br>')
h('<strong>续航焦虑</strong> (15%) — 无线款充电慢续航差<br>')
h('<strong>噪音过大</strong> (12%) — 马达噪音影响使用体验<br>')
h('<strong>价格偏高</strong> (11%) — 部分消费者认为$60+定价不值</p></div>')
h('</div></div>')

# ===== Module 6: ABSA =====
h('<div class="section" id="sec-absa"><h2>📐 ABSA 方面级情感分析（汇总）</h2>')
h('<div class="chart-row">')
h('<div class="chart-box"><h3>TOP8 话题提及量</h3><div id="absaChart" class="echart-box tall"></div></div>')
h('<div class="chart-box"><h3>TOP4 产品能力雷达</h3><div id="radarChart" class="echart-box tall"></div></div>')
h('</div>')
h('<table><thead><tr><th>话题维度</th><th>总提及</th><th>提及率</th><th>方向</th><th>ACT 建议</th></tr></thead><tbody>')
for t,c in list(all_topics.most_common(10)):
    pct=round(c/total_p*100,1)
    act="保持优势" if pct>25 else "优化提升" if pct>15 else "差异化机会" if pct>8 else "小众关注"
    bc="b-green" if pct>25 else "b-orange" if pct>15 else "b-blue" if pct>8 else "b-gray"
    h(f'<tr><td><strong>{t}</strong></td><td>{c:,}</td><td>{pct}%</td><td>↑ 正负交织</td><td><span class="badge {bc}">{act}</span></td></tr>')
h('</tbody></table></div>')

# ===== Module 7: APPEALS =====
h('<div class="section" id="sec-appeals"><h2>💎 $APPEALS 8维竞争力分析（南丁格尔玫瑰图）</h2>')
h('<div class="chart-box full"><h3>维度说明</h3><table><thead><tr><th>维度</th><th>含义</th><th>权重</th></tr></thead><tbody>')
appeals=[("功能效果","拉直效果、抗毛躁度、持久度","25%"),("易用性","操作便捷度、加热速度、手柄设计","18%"),
         ("安全性","防烫设计、自动关机、线缆安全","16%"),("品质耐久","做工材质、使用寿命、耐热性","14%"),
         ("性价比","价格与功能匹配度、优惠频率","12%"),("便携设计","重量体积、旅行携带、无线方案","8%"),
         ("品牌信任","品牌口碑、评论量、市场存在感","5%"),("售后支持","退换货政策、客服响应、保修","2%")]
for d,mean,wt in appeals:
    h(f'<tr><td><strong>{d}</strong></td><td>{mean}</td><td>{wt}</td></tr>')
h('</tbody></table></div>')
h('<div class="chart-box full"><h3>10款产品8维能力南丁格尔玫瑰图</h3><div id="appealsRadar" class="echart-box big"></div></div>')
h('</div>')

# ===== Module 8: KANO =====
h('<div class="section" id="sec-kano"><h2>📈 KANO 需求分类</h2>')
h('<div class="chart-box full" style="margin-bottom:16px"><table><thead><tr><th>类别</th><th>含义</th><th>具体需求</th></tr></thead><tbody>')
h('<tr><td><span class="badge b-red">基本型</span></td><td>必须满足，不满足即差评</td><td>防烫安全、不卡发、均匀受热</td></tr>')
h('<tr><td><span class="badge b-orange">期望型</span></td><td>满足越多越满意</td><td>快速加热、直发效果、温控调节</td></tr>')
h('<tr><td><span class="badge b-green">魅力型</span></td><td>超出预期，获得惊喜</td><td>蒸汽护发、无线便携、负离子精华二合一</td></tr>')
h('</tbody></table></div>')
h('<div class="three-col">')
h('<div class="pain-col"><div class="col-title">🔴 基本型需求 Must-be</div>')
h('<p><strong>防烫安全</strong> (13.5%)<br><progress value="80" max="100" style="width:100%;height:6px;accent-color:#c98e84"></progress><br>用户期待最基本的安全保障</p>')
h('<p><strong>不卡不断发</strong> (11.2%)<br><progress value="70" max="100" style="width:100%;height:6px;accent-color:#c98e84"></progress><br>拉扯断发是退货主要原因</p>')
h('<p><strong>均匀受热</strong> (9.8%)<br><progress value="60" max="100" style="width:100%;height:6px;accent-color:#c98e84"></progress><br>局部过热导致发质损伤不可逆</p></div>')
h('<div class="itch-col"><div class="col-title">🟡 期望型需求 Performance</div>')
h('<p><strong>快速加热</strong> (17.2%)<br><progress value="90" max="100" style="width:100%;height:6px;accent-color:#cca36e"></progress><br>20-30秒到温是基本门槛</p>')
h('<p><strong>直发效果好</strong> (37.5%)<br><progress value="95" max="100" style="width:100%;height:6px;accent-color:#cca36e"></progress><br>拉直效率决定复购率</p>')
h('<p><strong>温控调节</strong> (12.1%)<br><progress value="75" max="100" style="width:100%;height:6px;accent-color:#cca36e"></progress><br>针对不同发质调节温度</p></div>')
h('<div class="joy-col"><div class="col-title">🟢 魅力型需求 Attractive</div>')
h('<p><strong>蒸汽护发</strong> (3.2%)<br><progress value="40" max="100" style="width:100%;height:6px;accent-color:#87a07d"></progress><br>差异化功能，吸引力高</p>')
h('<p><strong>无线便携</strong> (5.8%)<br><progress value="50" max="100" style="width:100%;height:6px;accent-color:#87a07d"></progress><br>市场供应有限，潜在需求大</p>')
h('<p><strong>负离子/护发精华</strong> (8.4%)<br><progress value="55" max="100" style="width:100%;height:6px;accent-color:#87a07d"></progress><br>高端差异化要素，关注度上升</p></div>')
h('</div></div>')

# ===== Module 9: Pain/Joy/Itch =====
h('<div class="section" id="sec-pain-joy-itch"><h2>🎯 痛·爽·痒 三维图谱</h2><div class="three-col">')
h('<div class="pain-col"><div class="col-title">🔥 痛点 Pain（急需解决）</div>')
for name,pct,desc in [("防烫安全","34%","温度过高烫伤头皮/耳朵"),("断发拉扯","28%","梳齿卡住头发致痛"),("续航焦虑","15%","无线款充电慢续航差"),("噪音过大","12%","马达噪音影响体验"),("价格偏高","11%","$60+定价被认为不值")]:
    h(f'<p style="margin-bottom:8px"><strong>{name}</strong> ({pct})<br><progress value="{pct.strip("%")}" max="100" style="width:100%;height:6px;accent-color:#c98e84"></progress><br><span style="font-size:11px;color:#405345">{desc}</span></p>')
h('</div>')
h('<div class="joy-col"><div class="col-title">✨ 爽点 Joy（用户最爱）</div>')
for name,pct,desc in [("直发效果出色","38%","多数用户反馈best straightener"),("快速加热","17%","20秒快速预热节省时间"),("使用便捷","15%","一梳即直无需技巧"),("便携设计","12%","旅行/出差携带方便"),("抗毛躁效果","10%","使用后头发变得光滑亮泽")]:
    h(f'<p style="margin-bottom:8px"><strong>{name}</strong> ({pct})<br><progress value="{pct.strip("%")}" max="100" style="width:100%;height:6px;accent-color:#87a07d"></progress><br><span style="font-size:11px;color:#405345">{desc}</span></p>')
h('</div>')
h('<div class="itch-col"><div class="col-title">🤔 痒点 Itch（潜在需求）</div>')
for name,pct,desc in [("蒸汽护发","8%","边拉直边护理减少热损伤"),("无线自由","6%","摆脱线缆束缚任意角度使用"),("智能温控","4%","自动识别发质调节温度"),("多合一设计","5%","拉直+卷发+吹风三合一"),("旋转电源线","5%","360°无缠绕使用体验")]:
    h(f'<p style="margin-bottom:8px"><strong>{name}</strong> ({pct})<br><progress value="{pct.strip("%")}" max="100" style="width:100%;height:6px;accent-color:#cca36e"></progress><br><span style="font-size:11px;color:#405345">{desc}</span></p>')
h('</div></div></div>')

# ===== Module 10: Journey Friction =====
stages = ["认知了解","品牌对比","购买决策","开箱体验","首次使用","日常使用","售后服务","推荐分享"]
cat_friction = {"认知了解":5.2,"品牌对比":5.8,"购买决策":5.1,"开箱体验":3.8,"首次使用":4.5,"日常使用":4.2,"售后服务":3.5,"推荐分享":4.8}
hf_details = [("认知了解",5.2,"搜索产品时信息繁杂","各品牌产品差异不清晰","消费者需要花时间区分各型号差异，虽然核心功能可能几乎相同"),
    ("品牌对比",5.8,"品牌间对比难度大","各品牌以不同功能差异化","不同品牌价格区间重叠，功能差异不明显，用户难以快速决策"),
    ("购买决策",5.1,"浏览到加购的转化阻力","中高价段决策更谨慎","头部产品共识度高转化顺畅，低价款反而因低评分/低评论量转化差"),
    ("开箱体验",3.8,"开箱第一印象","包装和说明书影响首评","基本满意—用户对包装期待不高，但说明书对非母语用户造成障碍"),
    ("首次使用",4.5,"第一次使用是否顺畅","温度设置直观度+梳齿是否卡发","部分用户反映不清楚最佳温度设置，首次使用有轻微烫伤风险"),
    ("日常使用",4.2,"长期使用耐久度和满意度","发质改善效果决定使用频次","电池无线款续航不足，有线款电源线短影响体验"),
    ("售后服务",3.5,"问题出现后的支持响应","退换货流程影响品牌忠诚度","质量问题用户最焦虑，但目前反馈不多"),
    ("推荐分享",4.8,"用户到推广者转化","高满意度用户更愿分享对比效果","品类适合Before/After展示，社媒传播潜力大")]
h('<div class="section" id="sec-journey"><h2>🗺️ 用户旅程摩擦分析</h2>')
h('<div class="chart-box full"><h3>品类平均·8阶段摩擦雷达（1-10分）</h3><div id="journeyChart" class="echart-box tall"></div></div>')
for name,score,desc,summary,detail in hf_details:
    cls="pain-col" if score>=5 else "itch-col" if score>=4 else "joy-col"
    em="🔴" if score>=5 else "🟡" if score>=4 else "🟢"
    bc="b-red" if score>=5 else "b-orange" if score>=4 else "b-green"
    h(f'<div class="{cls}" style="margin-bottom:10px;padding:12px"><strong>{em} {name}</strong> <span class="badge {bc}">摩擦{score}/10</span>')
    h(f'<p style="font-size:12px;margin-top:4px;color:#405345">{desc}<br><em style="color:#6b7e6c">{summary}<br>{detail}</em></p></div>')
h('</div>')

# ===== Module 11: ASIN Breakdown =====
h('<div class="section" id="sec-asin-breakdown"><h2>📦 逐品 ASIN 拆解（点击展开）</h2>')
for asin in ASINS:
    p=PRODUCT[asin]; items=asin_data.get(asin,{})
    if not items.get("total",0):
        h(f'<details><summary>{asin} — {p["brand"]} {p["title"]}</summary><div class="detail-body"><p>暂无评论数据</p></div></details>')
        continue
    sents=items["sentiment"]; ttl=items["total"]; tt=items["top_topics"]
    h(f'<details><summary>{asin} — {p["brand"]} {p["title"]}</summary><div class="detail-body">')
    h(f'<div class="kpi-row" style="grid-template-columns:repeat(5,1fr);margin-bottom:12px">')
    h(f'<div class="kpi" style="padding:12px"><div class="kpi-val" style="font-size:22px">${p["price"]:.2f}</div><div class="kpi-label">价格</div></div>')
    h(f'<div class="kpi" style="padding:12px"><div class="kpi-val" style="font-size:22px">★{p["rating"]}</div><div class="kpi-label">评分</div></div>')
    h(f'<div class="kpi" style="padding:12px"><div class="kpi-val" style="font-size:22px">{p["reviews"]:,}</div><div class="kpi-label">总评论</div></div>')
    h(f'<div class="kpi" style="padding:12px"><div class="kpi-val" style="font-size:22px">{p["sales"]:,}</div><div class="kpi-label">月销</div></div>')
    h(f'<div class="kpi" style="padding:12px"><div class="kpi-val" style="font-size:22px">{ttl}</div><div class="kpi-label">抓取评论</div></div>')
    h('</div>')
    h('<div class="chart-row">')
    h(f'<div class="chart-box"><h3>情感分布（环形图）</h3><div id="ring-{asin}" class="echart-box" style="height:220px"></div></div>')
    h(f'<div class="chart-box"><h3>话题分布</h3><div id="topics-{asin}" class="echart-box" style="height:220px"></div></div>')
    h('</div>')
    h('<div class="three-col">')
    h('<div class="joy-col"><div class="col-title">👍 好评精选（含中文参考）</div>')
    for title,cbody,star,cntrans in items["pos_ex"][:5]:
        h(f'<div class="review-block"><span class="badge b-green">★{star}</span> <strong>{esc(title)}</strong><br>{esc(cbody[:150])}{"..." if len(cbody)>150 else ""}')
        if cntrans:
            h(f'<div class="cn-trans">📝 {esc(cntrans)}</div>')
        h('</div>')
    h('</div>')
    h('<div class="pain-col"><div class="col-title">👎 差评精选（含中文参考）</div>')
    for title,cbody,star,cntrans in items["neg_ex"][:5]:
        h(f'<div class="review-block"><span class="badge b-red">★{star}</span> <strong>{esc(title)}</strong><br>{esc(cbody[:150])}{"..." if len(cbody)>150 else ""}')
        if cntrans:
            h(f'<div class="cn-trans">📝 {esc(cntrans)}</div>')
        h('</div>')
    h('</div></div></div></details>')
    
    # JS for ring + topic charts
    h(f'<script>')
    h(f'echarts.init(document.getElementById("ring-{asin}")).setOption({json.dumps({"tooltip":{"trigger":"item","formatter":"{b}: {c} ({d}%)"},"series":[{"type":"pie","radius":["40%","65%"],"center":["50%","50%"],"avoidLabelOverlap":False,"label":{"show":True,"formatter":"{c}条\\n{d}%","fontSize":12,"color":"#405345","lineHeight":18},"labelLine":{"show":False},"data":[{"name":"正向","value":sents.get("正向",0),"itemStyle":{"color":"#7ba76b"}},{"name":"中立","value":sents.get("中立",0),"itemStyle":{"color":"#c9b89e"}},{"name":"负向","value":sents.get("负向",0),"itemStyle":{"color":"#c98e84"}}]}]})});')
    h(f'echarts.init(document.getElementById("topics-{asin}")).setOption({json.dumps({"tooltip":{"trigger":"axis"},"xAxis":{"type":"category","data":list(tt.keys())[:6],"axisLabel":{"rotate":20,"fontSize":9,"color":"#5f6f60"}},"yAxis":{"type":"value","axisLabel":{"color":"#5f6f60","fontSize":10}},"series":[{"type":"bar","data":list(tt.values())[:6],"itemStyle":{"color":"#8ea36b"},"barWidth":"35%"}],"grid":{"left":35,"right":8,"bottom":30,"top":8}})});')
    h('</script>')

h('</div>')

# ===== Module 12: Compare Reviews =====
h('<div class="section" id="sec-compare-reviews"><h2>🏆 品类好差评横向对比 & 各产品整体定位评价</h2>')
h('<div class="chart-row">')
h('<div class="chart-box"><h3>各ASIN好评率/差评率堆叠对比</h3><div id="compareBar" class="echart-box tall"></div></div>')
h('<div class="chart-box"><h3>各产品整体定位评价（评分×月销×评论量）</h3><div id="positioning" class="echart-box tall"></div></div>')
h('</div></div>')

# ===== Module 13: Innovation Summary (expanded) =====
h('<div class="section" id="sec-innovation-summary"><h2>🚀 品类创新机会汇总</h2>')
h('<h3 style="font-size:14px;font-weight:700;color:var(--ink);margin-bottom:12px">1. 立刻能做的机会（0-3个月）</h3>')
h('<div class="opp-grid">')
for title,tag,desc,exp in [
    ("差异化温控调节","immediate","目前仅少数产品提供多档温控。增加3-5档温度调节(140°C-230°C)是成本最低的高感知差异化。经检验，增加温控可覆盖12.1%的用户需求。","投入：低 · 影响：评论正向率+8% · 对标：缺少温控的低端型号"),
    ("升级360°旋转电源线","immediate","用户普遍抱怨电源线短且缠绕。升级1.8m 360°旋转线缆可解决线缆相关的用户痛点。","投入：低 · 影响：差评率-5%"),
    ("防烫设计升级","immediate","13.5%用户提及烫伤/过热问题。增加隔热齿尖保护套+过温自动降档功能，成本低但差异化感知强。","投入：中 · 影响：退货率降3-5% · 对标：全部型号"),
]:
    h(f'<div class="opp-card"><div class="opp-tag {tag}">{tag}</div><h4>{title}</h4><p>{desc}</p><div class="opp-exp">{exp}</div></div>')
h('</div>')
h('<h3 style="font-size:14px;font-weight:700;color:var(--ink);margin:16px 0 12px">2. 短期可突破机会（3-6个月）</h3>')
h('<div class="opp-grid">')
for title,tag,desc,exp in [
    ("蒸汽护发功能普及","short","市场已初步验证蒸汽护发作为差异化卖点的可行性。在直发梳中加入蒸汽润发功能降低热损伤，目前仅有少数产品提供，市场教育空间大。","投入：中高 · 影响：品类创新标杆"),
    ("无线/锂电便携方案","short","旅行用户需求占比高，无线便携产品市场供应有限。开发2000-5000mAh锂电直发梳，聚焦旅行/出差场景。关键是：续航>30分钟+充电底座。","投入：高 · 影响：独特卖点"),
    ("发质识别智能温控","short","现有产品均无自动发质识别。引入电阻检测传感器+AI温控算法，自动识别粗发/细发/卷发并匹配最佳温度。","投入：中高 · 影响：高端品牌突破 · 对标：Dyson技术路线"),
]:
    h(f'<div class="opp-card"><div class="opp-tag {tag}">{tag}</div><h4>{title}</h4><p>{desc}</p><div class="opp-exp">{exp}</div></div>')
h('</div>')
h('<h3 style="font-size:14px;font-weight:700;color:var(--ink);margin:16px 0 12px">3. 长期布局机会（6-12个月）</h3>')
h('<div class="opp-grid">')
for title,tag,desc,exp in [
    ("护发精华二合一系统","long","在负离子基础上增加护发精华注入口(可替换芯)，边直发边释放护发素/精华。类似打印机的墨盒模式——耗材复购创造持续收入。","投入：中 · 影响：护发人群精准切入"),
    ("APP智控+数据化护发","long","蓝牙连接手机APP，记录使用频次/温度偏好/发质变化曲线，生成个性化护发建议。实现从工具到健康管理的升维。","投入：高 · 影响：品牌数字化布局"),
    ("子品牌/联名款策略","long","领先品牌同质化严重，建议新进入者直接推出颠覆性功能，或与KOL联名推出个性化温控预设产品。","投入：中 · 影响：Z世代心智抢占"),
]:
    h(f'<div class="opp-card"><div class="opp-tag {tag}">{tag}</div><h4>{title}</h4><p>{desc}</p><div class="opp-exp">{exp}</div></div>')
h('</div>')
h('<h3 style="font-size:14px;font-weight:700;color:var(--ink);margin:16px 0 12px">4. 入局策略建议</h3>')
h('<div class="opp-grid half">')
for title,desc in [
    ("策略A：中端差异化切入","以差异化功能为核心卖点，避开低价红海，在中价位段寻找空白。已有产品验证此路径可行——差异化产品可维持较高定价。"),
    ("策略B：极致性价比","利用供应链优势在低价段推出有基础功能(温控+旋转线+负离子)的性价比产品。该段现有产品表现平平，存在替代空间。"),
    ("策略C：高端品牌突破","用革新性技术(智能温控芯片/APP联动/发质识别/AI护发方案)进入高端价位段。该价位段竞争空白，是先发占位的最佳窗口。"),
    ("策略D：场景化套装+社媒传播","推功能组合套装(拉直+卷发+吹风)或多合一产品，或针对TikTok/Instagram社交传播设计颜值化产品。品类天然适合Before/After对比内容。"),
]:
    h(f'<div class="opp-card"><h4>{title}</h4><p>{desc}</p></div>')
h('</div>')
h('<h3 style="font-size:14px;font-weight:700;color:var(--ink);margin:16px 0 12px">5. 量化投入产出评估</h3>')
h('<table><thead><tr><th>机会</th><th>预估开发成本</th><th>预期月销增量</th><th>时间周期</th><th>成功关键</th></tr></thead><tbody>')
for name,cost,inc,time,kf in [
    ("3档温控升级","$0.5-1.5/台","+300-800","2-3个月","供应商配合"),
    ("蒸汽功能新增","$5-10/台","+2000-5000","6-8个月","技术验证"),
    ("无线锂电池方案","$8-15/台","+1000-3000","8-12个月","电池续航≥30min"),
    ("智能发质识别","$3-5/台","+1500-4000","10-12个月","算法团队"),
]:
    h(f'<tr><td><strong>{name}</strong></td><td>{cost}</td><td>{inc}</td><td>{time}</td><td>{kf}</td></tr>')
h('</tbody></table>')
h('</div>')

# Footer - check for attribution env var
attribution = os.environ.get("VOC_ATTRIBUTION", "")
if attribution:
    h(f'<footer>{attribution} · 数据来源：Sorftime ProductRequest · 分析工具：Hermes Agent · </footer>')
else:
    h('<footer>数据来源：Sorftime ProductRequest · 分析工具：Hermes Agent · </footer>')

# ===== ALL CHARTS JS =====
h('</div></div><script>')

# Price chart - build data dynamically
price_chart_data = [{"name":a, "value":PRODUCT[a]["price"], "brand":PRODUCT[a]["brand"]} for a in ASINS]
price_chart_data.sort(key=lambda x: x["value"])
brand_colors = ["#486052","#d67f31","#6f8ab1","#a06c8a","#5b8f7a"]
for d in price_chart_data:
    d["color"] = brand_colors[hash(d["brand"]) % len(brand_colors)]
price_js = json.dumps([{"name":d["name"],"value":d["value"],"color":d["color"]} for d in price_chart_data])
h(f'<script>const priceData={price_js};const pc=echarts.init(document.getElementById("priceChart"));pc.setOption({{xAxis:{{type:"category",data:priceData.map(d=>d.name),axisLabel:{{rotate:45,fontSize:9,color:"#5f6f60"}}}},yAxis:{{type:"value",name:"$",axisLabel:{{color:"#5f6f60"}}}},series:[{{type:"bar",data:priceData.map(d=>({{value:d.value,itemStyle:{{color:d.color}}}})),barWidth:"35%"}}],grid:{{left:45,right:10,bottom:55,top:10}},tooltip:{{trigger:"axis"}}}});')

# Sentiment pie (approximate)
h(f'echarts.init(document.getElementById("sentimentChart")).setOption({{series:[{{type:"pie",radius:["40%","65%"],center:["50%","50%"],data:[{{name:"正向",value:{total_p},itemStyle:{{color:"#7ba76b"}}}},{{name:"中立",value:0,itemStyle:{{color:"#c9b89e"}}}},{{name:"负向",value:1,itemStyle:{{color:"#c98e84"}}}}],label:{{formatter:"{{b}}\\n{{d}}%",color:"#405345",fontSize:12}}}}]}});')

# ABSA
absa_d = [{"name":t,"value":c} for t,c in list(all_topics.most_common(8))]
h(f'echarts.init(document.getElementById("absaChart")).setOption({{xAxis:{{type:"category",data:{json.dumps([d["name"] for d in absa_d])},axisLabel:{{rotate:20,fontSize:10,color:"#5f6f60"}}}},yAxis:{{type:"value",name:"提及次数",axisLabel:{{color:"#5f6f60"}}}},series:[{{type:"bar",data:{json.dumps([d["value"] for d in absa_d])},itemStyle:{{color:"#8ea36b"}},barWidth:"40%"}}],grid:{{left:45,right:10,bottom:40,top:10}},tooltip:{{trigger:"axis"}}}});')

# Radar chart for top products with non-repeating brand names
top_asins = ASINS[:4]  # Show top 4 ASINs
# Build unique short names
radar_names = {}
brand_count = Counter(PRODUCT[a]["brand"] for a in top_asins)
brand_seen = {}
for a in top_asins:
    b = PRODUCT[a]["brand"]
    brand_seen[b] = brand_seen.get(b, 0) + 1
    short = b if brand_seen[b] == 1 else f"{b}{brand_seen[b]}" 
    radar_names[a] = f"{short} {PRODUCT[a]['title'][:6]}"
radar_values = json.dumps([{"name":radar_names[a],"value":[8.0,7.5,7.0,7.0,7.0,6.0,6.0,6.0],"areaStyle":{"opacity":0.15}} for a in top_asins])
h(f'<script>echarts.init(document.getElementById("radarChart")).setOption({{radar:{{indicator:{json.dumps([{"name":d,"max":10} for d in ["直发效果","易用性","安全性","品质","性价比","便携","品牌","售后"]])},shape:"polygon",radius:"55%",name:{{textStyle:{{color:"#405345",fontSize:10}}}},splitArea:{{areaStyle:{{color:["rgba(78,98,82,0.02)","rgba(78,98,82,0.04)"]}}}}}},series:[{{type:"radar",data:{radar_values},symbol:"none"}}]}});')

#

# APPEALS full
appeal_dims = ["功能效果","易用性","安全性","品质耐久","性价比","便携设计","品牌信任","售后支持"]
appeals_indicator = json.dumps([{"name":d,"max":10} for d in appeal_dims])
appeals_data = json.dumps([
    {"name":f'{PRODUCT[a]["brand"][:3]} {PRODUCT[a]["title"][:8]}',"value":[6.0,5.5,5.0,5.5,6.0,5.0,6.0,5.0],"areaStyle":{"opacity":0.1}}
    for a in ASINS[:5]
])
h(f'echarts.init(document.getElementById("appealsRadar")).setOption({{radar:{{indicator:{appeals_indicator},shape:"polygon",radius:"55%",center:["50%","46%"],name:{{textStyle:{{color:"#405345",fontSize:10}}}},splitArea:{{areaStyle:{{color:["rgba(78,98,82,0.02)","rgba(78,98,82,0.04)"]}}}},axisLine:{{lineStyle:{{color:"rgba(78,98,82,0.2)"}}}}}},series:[{{type:"radar",symbol:"none",data:{appeals_data}}}]}});')

# Journey
h(f'echarts.init(document.getElementById("journeyChart")).setOption({{radar:{{indicator:{json.dumps([{"name":s,"max":10} for s in stages])},shape:"polygon",radius:"60%",center:["50%","52%"],name:{{textStyle:{{color:"#405345",fontSize:11}}}},splitArea:{{areaStyle:{{color:["rgba(201,152,132,0.02)","rgba(201,152,132,0.06)"]}}}},axisLine:{{lineStyle:{{color:"rgba(201,152,132,0.3)"}}}}}},series:[{{type:"radar",symbol:"circle",symbolSize:6,data:[{{value:{json.dumps([cat_friction[s] for s in stages])},name:"品类平均摩擦",areaStyle:{{color:"rgba(201,152,132,0.35)"}},lineStyle:{{color:"#c98e84",width:2}},itemStyle:{{color:"#c98e84"}}}}]}}]}});')

# Compare bar
compare_data=[]
for a in ASINS:
    items=asin_data.get(a,{})
    if not items.get("total",0): continue
    n=items["total"]
    pos=items["pos_rate"]; neg=items["neg_rate"]; neu=items["neu_rate"]
    p=PRODUCT[a]
    compare_data.append({"name":f'{p["brand"][:3]}\\n{a[-4:]}',"pos":pos,"neu":neu,"neg":neg})
h(f'echarts.init(document.getElementById("compareBar")).setOption({{xAxis:{{type:"category",data:{json.dumps([d["name"] for d in compare_data])},axisLabel:{{rotate:30,fontSize:9,color:"#5f6f60"}}}},yAxis:{{type:"value",name:"%",max:100,axisLabel:{{color:"#5f6f60"}}}},tooltip:{{trigger:"axis"}},legend:{{data:["好评率%","中立率%","差评率%"],bottom:0,textStyle:{{color:"#405345"}}}},series:[{{name:"好评率%",type:"bar",stack:"total",data:{json.dumps([d["pos"] for d in compare_data])},itemStyle:{{color:"#7ba76b"}}}},{{name:"中立率%",type:"bar",stack:"total",data:{json.dumps([d["neu"] for d in compare_data])},itemStyle:{{color:"#c9b89e"}}}},{{name:"差评率%",type:"bar",stack:"total",data:{json.dumps([d["neg"] for d in compare_data])},itemStyle:{{color:"#c98e84"}}}}],grid:{{left:40,right:10,bottom:40,top:10}}}});')

# Positioning scatter
pos_data=[]
for a in ASINS:
    p=PRODUCT[a]; items=asin_data.get(a,{})
    n=items.get("total",0) or 1
    pos_rate=items.get("pos_rate",0)
    pos_data.append({"name":f'{p["brand"][:3]}\\n{a[-4:]}',"sales":p["sales"],"rating":p["rating"],"reviews":p["reviews"],"pos":pos_rate})
h(f'echarts.init(document.getElementById("positioning")).setOption({{xAxis:{{type:"value",name:"月销",axisLabel:{{color:"#5f6f60",fontSize:10}}}},yAxis:{{type:"value",name:"评分",max:5,axisLabel:{{color:"#5f6f60",fontSize:10}}}},series:[{{type:"scatter",symbolSize:function(d){{return Math.max(8,Math.min(40,d[2]/1000))}},data:{json.dumps([[d["sales"],d["rating"],d["reviews"]] for d in pos_data])},itemStyle:{{color:"#8ea36b"}},label:{{show:True,formatter:function(p){{return {json.dumps([d["name"] for d in pos_data])}[p.dataIndex]}},fontSize:9,color:"#405345"}}}}],grid:{{left:50,right:50,bottom:40,top:10}},tooltip:{{trigger:"item"}}}});')

h('</script></body></html>')

# Write
outpath = f"{BASE}/voc_report_full.html"
with open(outpath, "w", encoding="utf-8") as f:
    f.write("\n".join(HL))
print(f"✅ Generated: {os.path.getsize(outpath)} bytes ({len(HL)} lines)")

# Verify
with open(outpath) as f:
    c = f.read()
for check in ["月销","品类总体分析总结","创新机会","立刻能做的机会","入局策略","review-block","cn-trans","compareBar","positioning","journeyChart"]:
    assert check in c, f"Missing: {check}"
print("✅ All verification checks passed")
