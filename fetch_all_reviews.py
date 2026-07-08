#!/usr/bin/env python3
"""Fetch reviews for ASINs via Sorftime CLI (ProductReviewsQuery).
Edit the ASINS list below with your target ASINs before running."""
import subprocess, json, os, sys, time

# =============================================
# EDIT THIS LIST - add your target ASINs
# =============================================
ASINS = [
    # Example: "B0FCS7NZ35", ...
]
MAX_PAGES = 3  # ~100 reviews per page

OUTDIR = "data/voc"

def fetch_reviews(asin, pages=MAX_PAGES):
    all_reviews = []
    for pi in range(1, pages + 1):
        cmd = ["sorftime", "api", "ProductReviewsQuery",
               json.dumps({"asin": asin, "pageIndex": pi}), "--domain", "1"]
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if r.returncode:
            print(f"  Page {pi}: error - {r.stderr[:100]}")
            break
        try:
            data = json.loads(r.stdout)
            items = data.get("data", {}).get("list", [])
            if not items:
                print(f"  Page {pi}: no more items")
                break
            all_reviews.extend(items)
            print(f"  Page {pi}: {len(items)} reviews (total {len(all_reviews)})")
        except json.JSONDecodeError:
            print(f"  Page {pi}: invalid JSON")
            break
        time.sleep(0.5)
    return all_reviews

def main():
    os.makedirs(OUTDIR, exist_ok=True)
    all_reviews_dict = {}
    
    for asin in ASINS:
        print(f"\nFetching reviews for {asin}...")
        reviews = fetch_reviews(asin)
        if reviews:
            all_reviews_dict[asin] = reviews
        else:
            all_reviews_dict[asin] = []
            print(f"  ⚠️ No reviews for {asin}")
    
    path = f"{OUTDIR}/all_reviews.json"
    with open(path, "w") as f:
        json.dump(all_reviews_dict, f, ensure_ascii=False, indent=2)
    print(f"\n✅ Total: {sum(len(v) for v in all_reviews_dict.values())} reviews saved to {path}")

if __name__ == "__main__":
    main()
