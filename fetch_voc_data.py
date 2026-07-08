#!/usr/bin/env python3
"""Fetch product info & reviews for 10 ASINs via Sorftime CLI, save as JSON"""
import subprocess, json, sys, os, time, re

ASINS = ["B07MMQ4BZH","B0DCK8P752","B0BL34CGLM","B0FJDK6BMT","B0FT2PQY7R",
         "B091KHSV2X","B07RLTPSLB","B0C2C9TC42","B0F3CXQVT3","B0GZZRGJTN"]

OUTPUT_DIR = "/opt/data/skills/review-analyzer-skill/data/voc"
os.makedirs(OUTPUT_DIR, exist_ok=True)

def sf_api(endpoint, params, domain=1):
    """Call sorftime CLI API and parse JSON response"""
    param_str = json.dumps(params, ensure_ascii=False)
    cmd = f'sorftime api {endpoint} \'{param_str}\' --domain {domain}'
    env = os.environ.copy()
    env["PATH"] = f"/opt/data/.npm-global/bin:{env['PATH']}"
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True, env=env, timeout=60)
    output = r.stdout
    # Extract JSON from response
    json_start = output.find('{')
    if json_start == -1:
        return {"error": f"No JSON in response: {output[:200]}"}
    # Clean control chars
    raw = output[json_start:]
    return json.loads(raw)

def extract_json_from_response(response, key=None):
    """Parse sorftime JSON response"""
    if isinstance(response, dict) and response.get("Code") == 0:
        data = response.get("Data")
        if key and isinstance(data, dict):
            return data.get(key, data)
        return data
    return response

# ====== Phase 1: Fetch all reviews for each ASIN ======
print("=" * 60)
print("Phase 1: Fetching reviews for 10 ASINs...")

all_reviews = {}
for asin in ASINS:
    print(f"  Fetching {asin}...")
    all_comments = []
    page = 1
    while page <= 3:  # 最多3页 × 100 = 300条
        try:
            resp = sf_api("ProductReviewsQuery", {"asin": asin, "pageIndex": page})
            if resp.get("Code") != 0:
                if page == 1:
                    print(f"    {asin}: page 1 failed - {resp.get('Message','')}")
                break
            comments = resp.get("Data", [])
            if not comments:
                break
            all_comments.extend(comments)
            if len(comments) < 100:
                break  # last page
            page += 1
            time.sleep(0.5)
        except Exception as e:
            print(f"    {asin}: Error on page {page}: {e}")
            break
    all_reviews[asin] = all_comments
    print(f"    Got {len(all_comments)} reviews")

# Save raw reviews
with open(f"{OUTPUT_DIR}/all_reviews.json", "w", encoding="utf-8") as f:
    json.dump(all_reviews, f, ensure_ascii=False, indent=2)
print(f"Saved reviews to {OUTPUT_DIR}/all_reviews.json")

# ====== Phase 2: Get product info ======
print("\nPhase 2: Fetching product info...")
product_info = {}

for asin in ASINS:
    try:
        resp = sf_api("ProductRequest", {"asinList": [asin]})
        data = resp.get("Data", [])
        if data and isinstance(data, list) and len(data) > 0:
            item = data[0]
            product_info[asin] = {
                "title": item.get("Title", ""),
                "price": item.get("Price", ""),
                "rating": item.get("Score", ""),
                "reviews_count": item.get("ReviewsCount", 0),
                "bought_last_month": item.get("BoughtLastMonth", 0),
                "main_img": item.get("MainImg", ""),
                "brand": item.get("Brand", "")
            }
            print(f"  {asin}: ${item.get('Price','?')} | ★{item.get('Score','?')} | {item.get('BoughtLastMonth',0)}/mth")
        else:
            print(f"  {asin}: NO DATA")
            product_info[asin] = {"error": "No data"}
    except Exception as e:
        print(f"  {asin}: Error - {e}")
        product_info[asin] = {"error": str(e)}
    time.sleep(0.3)

with open(f"{OUTPUT_DIR}/product_info.json", "w", encoding="utf-8") as f:
    json.dump(product_info, f, ensure_ascii=False, indent=2)

print(f"Saved product info to {OUTPUT_DIR}/product_info.json")

# ====== Summary ======
print("\n" + "=" * 60)
print("SUMMARY:")
total_reviews = sum(len(v) for v in all_reviews.values())
print(f"Total reviews collected: {total_reviews}")
for asin in ASINS:
    pi = product_info.get(asin, {})
    title = pi.get("title", "?")[:50]
    price = pi.get("price", "?")
    rating = pi.get("rating", "?")
    reviews_count = pi.get("reviews_count", "?")
    bought = pi.get("bought_last_month", "?")
    rev_count = len(all_reviews.get(asin, []))
    print(f"  {asin} | ${price} | ★{rating} | {reviews_count} rev | {bought}/mth | Got {rev_count} reviews | {title}")
