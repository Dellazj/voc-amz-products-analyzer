#!/usr/bin/env python3
"""Fetch product data for N ASINs via Sorftime CLI (ProductRequest).
Edit the ASINS list below with your target ASINs before running."""
import subprocess, json, os, sys

# =============================================
# EDIT THIS LIST - add your target ASINs
# =============================================
ASINS = [
    # Example: "B0FCS7NZ35", "B0FC2NCYSL", ...
]
OUTDIR = "data/voc"

def sorftime_api(endpoint, payload):
    cmd = ["sorftime", "api", endpoint, json.dumps(payload), "--domain", "1"]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    if r.returncode:
        print(f"Error: {r.stderr[:200]}")
        return None
    return json.loads(r.stdout)

def main():
    os.makedirs(OUTDIR, exist_ok=True)
    
    # Step 1: Fetch product info
    print(f"Fetching {len(ASINS)} ASINs via ProductRequest...")
    result = sorftime_api("ProductRequest", {"asin": ",".join(ASINS), "trend": 2})
    if result and "data" in result:
        product_info = result["data"]
        path = f"{OUTDIR}/product_info.json"
        with open(path, "w") as f:
            json.dump(product_info, f, ensure_ascii=False, indent=2)
        print(f"✅ Saved product info ({len(product_info)} items) to {path}")
    else:
        print("⚠️ ProductRequest failed or returned no data")
    
    # Step 2: Output data for the user to review
    print(f"\nASINs to review: {', '.join(ASINS)}")
    print("Edit PRODUCT dict in generate_voc_report.py with the fetched data.")

if __name__ == "__main__":
    main()
