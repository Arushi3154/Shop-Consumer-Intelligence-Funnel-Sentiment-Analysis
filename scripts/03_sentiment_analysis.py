"""
Phase 3: Sentiment & topic analysis on review text.
Baseline: VADER (fast, rule-based, good for the resume line "built a baseline model").
Upgrade: HuggingFace DistilBERT sentiment pipeline (the resume-worthy version).
Topics: BERTopic to cluster complaint themes (delivery, quality, wrong item, etc.)

Note: Olist reviews are in Portuguese. Two options:
  A) Translate to English first (deep-translator / googletrans) then run English models.
  B) Use a multilingual/Portuguese-native model, e.g.
     'nlptown/bert-base-multilingual-uncased-sentiment' or
     'neuralmind/bert-base-portuguese-cased' fine-tuned variants.
Option B is faster and more defensible for a portfolio project — no translation-noise excuse needed.
"""
import duckdb
import pandas as pd
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "data" / "processed" / "warehouse.duckdb"
OUT = ROOT / "outputs"
OUT.mkdir(exist_ok=True)

con = duckdb.connect(str(DB_PATH))
reviews = con.execute("""
    SELECT order_id, customer_id, review_score, review_comment_message
    FROM fact_orders
    WHERE review_comment_message IS NOT NULL AND TRIM(review_comment_message) != ''
""").df()
con.close()
print(f"Loaded {len(reviews):,} written reviews.")

# ---- Baseline: rating-derived sentiment label (sanity check / weak label) ----
def rating_to_label(score):
    if score >= 4:
        return "positive"
    elif score == 3:
        return "neutral"
    else:
        return "negative"

reviews["rating_sentiment"] = reviews["review_score"].apply(rating_to_label)

# ---- Model-based sentiment (multilingual BERT, handles Portuguese natively) ----
from transformers import pipeline

print("Loading multilingual sentiment model (first run downloads weights)...")
sentiment_pipe = pipeline(
    "sentiment-analysis",
    model="nlptown/bert-base-multilingual-uncased-sentiment",  # returns 1-5 star prediction
    truncation=True,
)

# Run in batches for speed
texts = reviews["review_comment_message"].astype(str).tolist()
BATCH = 64
results = []
for i in range(0, len(texts), BATCH):
    batch = texts[i:i + BATCH]
    results.extend(sentiment_pipe(batch))
    if i % (BATCH * 20) == 0:
        print(f"  processed {i}/{len(texts)}")

reviews["model_stars"] = [int(r["label"][0]) for r in results]
reviews["model_confidence"] = [r["score"] for r in results]
reviews["model_sentiment"] = reviews["model_stars"].apply(rating_to_label)

reviews.to_csv(OUT / "reviews_with_sentiment.csv", index=False)
print(f"Saved sentiment-labeled reviews to outputs/reviews_with_sentiment.csv")

# ---- Agreement check: does model sentiment match star rating? ----
agreement = (reviews["rating_sentiment"] == reviews["model_sentiment"]).mean()
print(f"Model-vs-rating agreement: {agreement:.1%}  "
      f"(useful for your writeup — model catches cases where text sentiment "
      f"diverges from the star given, e.g. sarcastic 5-star reviews with complaints)")

# ---- Topic modeling on negative reviews (what are people actually complaining about) ----
try:
    from bertopic import BERTopic
    negative_texts = reviews.loc[reviews.model_sentiment == "negative", "review_comment_message"].tolist()
    if len(negative_texts) > 50:
        print(f"Running BERTopic on {len(negative_texts)} negative reviews...")
        topic_model = BERTopic(language="multilingual", verbose=True)
        topics, probs = topic_model.fit_transform(negative_texts)
        topic_info = topic_model.get_topic_info()
        topic_info.to_csv(OUT / "negative_review_topics.csv", index=False)
        print("Saved topic breakdown to outputs/negative_review_topics.csv")
    else:
        print("Not enough negative reviews for topic modeling yet.")
except ImportError:
    print("BERTopic not installed — run `pip install bertopic` to enable topic modeling.")

print("\nPhase 3 complete.")
