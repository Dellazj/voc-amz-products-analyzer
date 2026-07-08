#!/usr/bin/env python3
"""Fetch all reviews for B07MMQ4BZH via sorftime CLI and save as CSV for review-analyzer"""
import subprocess, json, csv, os, sys, time

ASIN = "B07MMQ4BZH"
OUTPUT_CSV = f"/opt/data/skills/review-analyzer-skill/data/{ASIN}_reviews.csv"
DOMAIN = "1"
MAX_PAGES = 3  # 100 reviews per page, 3 pages = 300 reviews

def call_api(asin, page=1):
    cmd = [
        "/opt/data/.npm-global/bin/sorftime", "api", "ProductReviewsQuery",
        json.dumps({"asin": asin, "pageIndex": page}),
        "--domain", DOMAIN
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    data = json.loads(result.stdout)
    return data

print(f"Fetching reviews for {ASIN}...")
all_reviews = []

for page in range(1, MAX_PAGES + 1):
    print(f"  Page {page}...")
    data = call_api(ASIN, page)
    if data.get("Code") != 0:
        print(f"  Error: {data.get('Message')}")
        break
    items = data.get("Data", [])
    if not items:
        print(f"  No more reviews")
        break
    print(f"  Got {len(items)} reviews")
    all_reviews.extend(items)
    time.sleep(1)

print(f"Total: {len(all_reviews)} reviews")

# Filter to only this ASIN (sorftime returns all variants)
asin_reviews = [r for r in all_reviews if r.get("Asin") == ASIN]
print(f"Filtered to {ASIN}: {len(asin_reviews)} reviews")

if not asin_reviews and not all_reviews:
    print("No reviews found!")
    sys.exit(1)

# Use all reviews if filtered is empty
if not asin_reviews:
    asin_reviews = all_reviews

os.makedirs(os.path.dirname(OUTPUT_CSV), exist_ok=True)

with open(OUTPUT_CSV, "w", newline="", encoding="utf-8-sig") as f:
    writer = csv.writer(f)
    writer.writerow(["review_title", "review_body", "rating", "review_date", "reviewer_name", "verified_purchase", "helpful_count", "review_id", "asin"])

    for i, r in enumerate(asin_reviews):
        writer.writerow([
            r.get("Title", ""),
            r.get("Content", ""),
            r.get("Star", ""),
            r.get("ReviewsDate", ""),
            r.get("ConsumerName", ""),
            "Y" if r.get("IsVP") else "N",
            r.get("Helpful", 0),
            f"R{(i+1):04d}",
            ASIN
        ])

print(f"✅ CSV saved: {OUTPUT_CSV}")
with open(OUTPUT_CSV, "r", encoding="utf-8-sig") as f:
    lines = [l.strip() for l in f.readlines()[:3]]
    for l in lines:
        print(f"  {l[:120]}...")
