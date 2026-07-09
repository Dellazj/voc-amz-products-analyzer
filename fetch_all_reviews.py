#!/usr/bin/env python3
"""Fetch reviews for ASINs via Sorftime CLI (ProductReviewsQuery).
Filters by target ASIN (excludes variant ASINs mixed in by Sorftime)."""
import subprocess, json, os, sys, time, argparse

OUTDIR = "data/voc"

def fetch_reviews(asin, max_pages=3, max_reviews=300):
    """Fetch reviews, filtering to keep only those matching `asin`.
    Stops early when max_reviews or max_pages is reached."""
    all_reviews = []
    for pi in range(1, max_pages + 1):
        if len(all_reviews) >= max_reviews:
            print(f"  Reached {max_reviews} reviews, stopping")
            break
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
            # Filter: only keep reviews belonging to this ASIN (exclude variants)
            filtered = [i for i in items if i.get("Asin", "").upper() == asin.upper()]
            skipped = len(items) - len(filtered)
            all_reviews.extend(filtered)
            print(f"  Page {pi}: {len(items)} raw → {len(filtered)} kept (skipped {skipped} variants), total {len(all_reviews)}")
        except json.JSONDecodeError as e:
            print(f"  Page {pi}: JSON parse error (try terminal redirect method)")
            break
        time.sleep(0.5)
    # Trim to exact max_reviews limit
    return all_reviews[:max_reviews]

def main():
    parser = argparse.ArgumentParser(description="Fetch Amazon reviews via Sorftime API")
    parser.add_argument("--asins", type=str, help="Comma-separated ASIN list")
    parser.add_argument("--max-per-asin", type=int, default=300,
                        choices=[100, 200, 300, 500, 0],
                        help="Max reviews per ASIN (0 = unlimited, default: 300)")
    parser.add_argument("--pages", type=int, default=3, help="Max pages to fetch")
    args = parser.parse_args()
    
    if args.asins:
        asins = [a.strip() for a in args.asins.split(",") if a.strip()]
    else:
        asins = ASINS  # fallback to module-level list
    
    if not asins:
        print("❌ No ASINs provided. Pass --asins ASIN1,ASIN2 or edit ASINS list.")
        sys.exit(1)
    
    # max_reviews=0 means unlimited
    max_reviews = args.max_per_asin
    if max_reviews == 0:
        max_reviews = 9999
    
    os.makedirs(OUTDIR, exist_ok=True)
    all_reviews_dict = {}
    
    for asin in asins:
        print(f"\n{'='*50}")
        print(f"Fetching reviews for {asin} (max {max_reviews}, {args.pages} pages)...")
        print(f"{'='*50}")
        reviews = fetch_reviews(asin, max_pages=args.pages, max_reviews=max_reviews)
        all_reviews_dict[asin] = reviews
        if not reviews:
            print(f"  ⚠️ No reviews kept for {asin}")
    
    path = f"{OUTDIR}/all_reviews.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(all_reviews_dict, f, ensure_ascii=False, indent=2)
    total = sum(len(v) for v in all_reviews_dict.values())
    print(f"\n✅ Total: {total} reviews saved to {path}")
    for asin, revs in all_reviews_dict.items():
        print(f"   {asin}: {len(revs)} reviews")

if __name__ == "__main__":
    # === Module-level ASIN list (fallback if --asins not passed) ===
    ASINS = [
        # Example: "B0FCS7NZ35", ...
    ]
    main()
