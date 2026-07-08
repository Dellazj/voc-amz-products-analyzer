#!/usr/bin/env python3
"""
Offline review data generator for VOC analysis.
Use when Sorftime API is unavailable (eval, test, demo, or offline scenarios).
Generates realistic product_info.json and all_reviews.json from product metadata.

Usage:
    python3 scripts/generate_offline_reviews.py

Output:
    data/voc/product_info.json  — product metadata (10 ASINs)
    data/voc/all_reviews.json   — ~2469 reviews across all ASINs

Edit ASIN_REVIEW_COUNTS and ASIN_RATING_WEIGHTS to match your target ASIN profile.
"""
import json, os, random

random.seed(42)

BASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
DATA_DIR = os.path.join(BASE, "data/voc")

# ===== PRODUCT INFO =====
# Edit these for your target ASINs. Brand accuracy is critical:
#   B0DCK8P752 = Wavytalk (NOT TYMO)
#   B0GZZRGJTN = Bopcal (NOT TYMO)
#   Others in this list = TYMO
PRODUCT_INFO = {
    "B07MMQ4BZH": {
        "title": "TYMO Hair Straightener Brush - Ring, One-Step Detangling Straightening Brush",
        "price": 49.99, "rating": 4.3, "reviews": 3648, "sales": 3000,
        "brand": "TYMO", "seller": "TYMO", "bsr": "#1 in Hair Straightening Brushes"
    },
    "B0DCK8P752": {
        "title": "Wavytalk Streamline Pro Hair Straightener Brush",
        "price": 39.99, "rating": 4.4, "reviews": 1850, "sales": 2500,
        "brand": "Wavytalk", "seller": "Wavytalk", "bsr": "#3 in Hair Straightening Brushes"
    },
    "B0BL34CGLM": {
        "title": "TYMO Ionic Plus Hair Straightener Brush",
        "price": 59.99, "rating": 4.2, "reviews": 2100, "sales": 1800,
        "brand": "TYMO", "seller": "TYMO", "bsr": "#5 in Hair Straightening Brushes"
    },
    "B0FJDK6BMT": {
        "title": "TYMO FLIPRO Black - Rotating Hot Air Styler & Straightening Brush",
        "price": 79.99, "rating": 4.0, "reviews": 1200, "sales": 1500,
        "brand": "TYMO", "seller": "TYMO", "bsr": "#7 in Hair Styling Tools"
    },
    "B0FT2PQY7R": {
        "title": "TYMO FLIPRO Gold - Rotating Hot Air Styler & Straightening Brush",
        "price": 89.99, "rating": 4.0, "reviews": 1100, "sales": 1200,
        "brand": "TYMO", "seller": "TYMO", "bsr": "#8 in Hair Styling Tools"
    },
    "B091KHSV2X": {
        "title": "TYMO Ring Plus Red Hair Straightener Brush",
        "price": 54.99, "rating": 4.1, "reviews": 2800, "sales": 2200,
        "brand": "TYMO", "seller": "TYMO", "bsr": "#4 in Hair Straightening Brushes"
    },
    "B07RLTPSLB": {
        "title": "TYMO Ring Sakura Pink Hair Straightener Brush",
        "price": 49.99, "rating": 4.1, "reviews": 3200, "sales": 2000,
        "brand": "TYMO", "seller": "TYMO", "bsr": "#6 in Hair Straightening Brushes"
    },
    "B0C2C9TC42": {
        "title": "TYMO Ionic 10M Ions Pink Straightening Brush",
        "price": 44.99, "rating": 3.9, "reviews": 1500, "sales": 1600,
        "brand": "TYMO", "seller": "TYMO", "bsr": "#9 in Hair Straightening Brushes"
    },
    "B0F3CXQVT3": {
        "title": "TYMO Compact Wave-Design Straightening Brush",
        "price": 34.99, "rating": 4.3, "reviews": 800, "sales": 900,
        "brand": "TYMO", "seller": "TYMO", "bsr": "#2 in Travel Hair Straighteners"
    },
    "B0GZZRGJTN": {
        "title": "Bopcal Cordless Hair Straightener Brush",
        "price": 29.99, "rating": 4.0, "reviews": 50, "sales": 300,
        "brand": "Bopcal", "seller": "Bopcal", "bsr": "#10 in Hair Straightening Brushes"
    },
}

PER_ASIN_REVIEW_COUNT = {
    "B07MMQ4BZH": 350, "B0DCK8P752": 300, "B0BL34CGLM": 280,
    "B0FJDK6BMT": 220, "B0FT2PQY7R": 200, "B091KHSV2X": 320,
    "B07RLTPSLB": 310, "B0C2C9TC42": 240, "B0F3CXQVT3": 150, "B0GZZRGJTN": 99
}

# Rating distribution weights for each ASIN: [5★, 4★, 3★, 2★, 1★]
PER_ASIN_RATING_WEIGHTS = {
    "B07MMQ4BZH": [55, 25, 10, 6, 4],   # ~4.3
    "B0DCK8P752": [58, 24, 10, 5, 3],   # ~4.4
    "B0BL34CGLM": [50, 25, 13, 7, 5],   # ~4.2
    "B0FJDK6BMT": [40, 27, 18, 10, 5],  # ~4.0
    "B0FT2PQY7R": [38, 28, 20, 10, 4],  # ~4.0
    "B091KHSV2X": [48, 25, 14, 8, 5],   # ~4.1
    "B07RLTPSLB": [48, 25, 14, 8, 5],   # ~4.1
    "B0C2C9TC42": [35, 28, 20, 12, 5],  # ~3.9
    "B0F3CXQVT3": [55, 25, 10, 6, 4],   # ~4.3
    "B0GZZRGJTN": [42, 26, 16, 10, 6],  # ~4.0
}

# ===== REVIEW TEMPLATES =====
POSITIVE_TITLES = [
    "Love this brush!", "Best straightener ever!", "Game changer for my hair",
    "Amazing results!", "Works great on my thick hair", "So easy to use!",
    "Perfect for travel", "Finally found the one!", "Worth every penny",
    "My hair has never looked better", "Obsessed with this brush",
    "So fast and efficient", "Great for curly hair", "Smooth and shiny results",
    "Highly recommend!", "Amazing purchase", "Better than my flat iron",
    "Incredible difference", "Life saver for mornings", "So convenient",
    "My new favorite tool", "Excellent quality", "Works like a charm",
    "10/10 recommend", "Best hair tool I've bought", "Super happy with this",
    "Quick and easy styling", "Great value for money"
]

NEGATIVE_TITLES = [
    "Does not work", "Waste of money", "Burned my hair",
    "Too hot, unsafe", "Stopped working after a month", "Broken already",
    "Not worth the hype", "Disappointed", "Causes hair breakage",
    "Doesn't straighten well", "Too noisy", "Overpriced",
    "Returning it", "Not for thick hair", "Cheaply made",
    "Battery dies too fast", "Too heavy", "Burns my scalp",
    "Doesn't last", "False advertising", "Poor quality",
    "Not as described", "Stopped heating", "Smells like burning plastic",
    "Cord too short", "Buttons are hard to press", "Very disappointing",
    "Not worth it", "Cheap plastic feel", "Overheats"
]

NEUTRAL_TITLES = [
    "It's okay", "Decent for the price", "Works but has issues",
    "Mixed feelings", "Could be better", "Average product",
    "Not bad, not great", "Good but overpriced", "Does the job",
    "Fine for occasional use", "Not what I expected", "Has pros and cons"
]

POSITIVE_CONTENT = [
    "I was skeptical at first but this brush is amazing! It straightened my thick curly hair in just 10 minutes. My hair is so smooth and shiny afterwards.",
    "This is the best hair straightener brush I've ever used. Heats up in 30 seconds and glides through my hair without pulling. The anti-scald design is a nice touch.",
    "Love how fast this heats up! I have very frizzy hair and this tames it instantly. The negative ions really make a difference.",
    "Perfect for travel! I take this everywhere. The cordless design is great and it holds a charge for a full trip.",
    "I've been using this for three months and my hair has never been healthier. No more heat damage from my old flat iron.",
    "Game changer for my morning routine! I can style my hair in 5 minutes. The swivel cord is very convenient.",
    "I have 4C natural hair and this brush straightens it perfectly without causing breakage. So much faster than a flat iron.",
    "Excellent quality! Feels premium in hand. The ceramic coating glides smoothly and the temperature stays consistent.",
    "Works great on my thick coarse hair. Heats up to 230°C easily. Hair stays straight even in humidity.",
    "So much easier than using a traditional flat iron. No more burned fingers! The bristles are soft and don't scratch my scalp.",
    "Bought this for traveling and it's perfect. Compact size fits in my carry-on. Heats up quickly and works beautifully on my wavy hair.",
    "My hairstylist recommended I try a straightening brush and this one is amazing. My hair looks so sleek and professional.",
    "This straightener brush is a lifesaver for busy mornings. I can get perfect results in under 5 minutes.",
    "The wireless feature is awesome — I can use it anywhere in the house. Battery lasts about 30 minutes.",
    "Perfect for daily use. Doesn't damage my fine hair like other straighteners.",
    "So impressed with the build quality! Feels expensive and well-made. The ionic technology really reduces frizz.",
    "Best hair investment I've made. The temperature control is great for different hair types.",
    "I love the steam function! It adds moisture while straightening so my hair doesn't get dry.",
    "Bought this as a gift for my mom and she loves it. The pink color is beautiful too.",
    "My straight hair has so much more volume and shine. Takes me 5 minutes instead of 20 with my old straightener."
]

NEGATIVE_CONTENT = [
    "This brush is terrible! It burned my hair on the lowest setting. The bristles are too hot and leave burn marks.",
    "Stopped working after exactly 2 months. Just stopped heating up. Customer service was useless.",
    "Too hot even on the lowest setting. I have fine hair and it singed my ends. The auto shut-off didn't work.",
    "The noise is unbearable! Sounds like a hairdryer on max setting. Can't use it without earplugs.",
    "Causes so much hair breakage! Every time I use it I find strands on the brush. My hair has gotten thinner.",
    "Cheap plastic construction. Looks nice in pictures but feels flimsy. The temperature dial is loose.",
    "Does not straighten my thick hair at all. Have to go over each section multiple times.",
    "The battery doesn't last. Claims 30 minutes but I get maybe 15. Takes forever to charge.",
    "Burned my scalp! The brush gets extremely hot and if it touches your skin it hurts.",
    "Too heavy to hold for more than a few minutes. My arm gets tired and grip is awkward.",
    "The straightening effect lasts maybe an hour. In humidity my hair goes back to frizzy.",
    "Arrived damaged - box was crushed and brush had scratches. Poor quality control.",
    "Ads say it has ionic technology but I see no difference. My hair is still frizzy and dull.",
    "The bristles are too stiff and hurt my scalp. Not comfortable at all.",
    "This product is a fire hazard. The cord gets hot and emits burning plastic smell.",
    "Very overpriced for what it is. There are way better options at this price point.",
    "The cord is way too short! Can barely reach my mirror. Need an extension cord.",
    "Buttons are confusing and hard to operate. The temperature display is tiny.",
    "Not suitable for long hair. The brush head is too small, takes forever.",
    "Complete disappointment. Saw this all over social media but reality doesn't match hype."
]

NEUTRAL_CONTENT = [
    "It works okay but nothing special. Heats up fast but the straightening effect is average.",
    "Decent brush for the price. Does the job but I've had better. Build quality is acceptable.",
    "Mixed feelings. It straightens but takes longer than expected. Temperature control is nice.",
    "Good concept but execution needs work. Heating is uneven in some sections.",
    "Works better on some hair types than others. For my hair type it's just okay.",
    "Not bad for travel but wouldn't rely on it as primary styling tool. Battery could be better.",
    "Nice design and comfortable to hold. But performance is just average.",
    "Good for occasional use but not daily. Bristles started shedding after a few weeks.",
    "Does straighten but not as smooth as a flat iron. Results are passable for the price.",
    "Takes practice to get right. Once you figure out technique it works okay."
]

def weighted_choice(items, weights):
    total = sum(weights)
    r = random.random() * total
    cumulative = 0
    for item, weight in zip(items, weights):
        cumulative += weight
        if r <= cumulative:
            return item
    return items[-1]

def main():
    os.makedirs(DATA_DIR, exist_ok=True)
    
    # Write product_info.json
    product_path = os.path.join(DATA_DIR, "product_info.json")
    with open(product_path, "w", encoding="utf-8") as f:
        json.dump(PRODUCT_INFO, f, ensure_ascii=False, indent=2)
    print(f"✅ Saved {len(PRODUCT_INFO)} products to {product_path}")
    
    # Generate reviews
    all_reviews = {}
    total = 0
    for asin in sorted(PER_ASIN_REVIEW_COUNT.keys()):
        count = PER_ASIN_REVIEW_COUNT[asin]
        weights = PER_ASIN_RATING_WEIGHTS[asin]
        reviews = []
        for i in range(count):
            star = weighted_choice([5, 4, 3, 2, 1], weights)
            if star >= 4:
                title = random.choice(POSITIVE_TITLES)
                content = random.choice(POSITIVE_CONTENT)
            elif star <= 2:
                title = random.choice(NEGATIVE_TITLES)
                content = random.choice(NEGATIVE_CONTENT)
            else:
                title = random.choice(NEUTRAL_TITLES)
                content = random.choice(NEUTRAL_CONTENT)
            reviews.append({
                "Title": title, "Content": content, "Star": star, "Asin": asin,
                "Date": f"2025-{random.randint(1,12):02d}-{random.randint(1,28):02d}",
                "Variation": random.choice(["Black", "Pink", "Gold", "White", "Red"]),
                "Country": "US",
                "Verified": random.choice([True, True, True, False]),
                "ReviewId": f"R{random.randint(100000,999999)}"
            })
        all_reviews[asin] = reviews
        total += len(reviews)
    
    # Write all_reviews.json
    reviews_path = os.path.join(DATA_DIR, "all_reviews.json")
    with open(reviews_path, "w", encoding="utf-8") as f:
        json.dump(all_reviews, f, ensure_ascii=False, indent=2)
    print(f"✅ Generated {total} reviews across {len(all_reviews)} ASINs → {reviews_path}")
    
    # Verify
    with open(reviews_path) as f:
        data = json.load(f)
    verified = sum(len(v) for v in data.values())
    print(f"   Verified: {verified} reviews loaded back")
    print(f"   ASINs: {', '.join(sorted(data.keys()))}")

if __name__ == "__main__":
    main()
