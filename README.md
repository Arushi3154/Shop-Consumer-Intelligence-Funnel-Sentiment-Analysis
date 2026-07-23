# Shop Consumer Intelligence: Funnel & Sentiment Analysis

**Business question:** Where do customers drop off in the purchase journey, and what are they
telling us — in their own words — about why?

This project fuses **quantitative funnel analysis** (lead → order → delivery → repeat purchase)
with **qualitative sentiment/topic analysis** of review text, on the same customer base, so
findings connect: e.g. *"Customers who mention 'late delivery' in reviews are 2.3x less likely
to make a repeat purchase within 90 days."*

Dataset: [Olist Brazilian E-Commerce](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce)
(100k orders, 2016–2018) + [Olist Marketing Funnel dataset](https://www.kaggle.com/datasets/olistbr/marketing-funnel-olist)
(MQL → SQL → deal closed).

---

## Roadmap

| Phase | What | Output |
|---|---|---|
| 1. Setup | Download data, load into Postgres/DuckDB, build star schema | `sql/schema.sql` |
| 2. Funnel analysis | Stage-by-stage conversion, drop-off, time-to-convert, cohort retention | `scripts/02_funnel_analysis.py` |
| 3. Sentiment analysis | VADER baseline → DistilBERT model, topic extraction (BERTopic) on reviews | `scripts/03_sentiment_analysis.py` |
| 4. Behavioral segmentation | RFM + clustering, cross-tab with sentiment | `scripts/04_segmentation.py` |
| 5. Synthesis | Join funnel drop-off with sentiment drivers, quantify impact | `scripts/05_synthesis.py` |
| 6. Dashboard | Interactive funnel + sentiment dashboard | `dashboard/app.py` (Streamlit) |
| 7. Storytelling | One-pager insight doc + polished README + deployed link | `outputs/insights.md` |

## Folder structure
```
consumer-intelligence-funnel/
├── data/raw/            <- put downloaded Olist CSVs here
├── data/processed/      <- cleaned parquet/csv outputs from scripts
├── sql/                 <- schema + funnel SQL queries
├── scripts/             <- numbered pipeline scripts, run in order
├── dashboard/           <- Streamlit app
└── outputs/             <- charts, insight doc, final deliverables
```

## How to run
```bash
pip install -r requirements.txt
# 1. Download the two Kaggle datasets into data/raw/
python scripts/01_data_prep.py
python scripts/02_funnel_analysis.py
python scripts/03_sentiment_analysis.py
python scripts/04_segmentation.py
python scripts/05_synthesis.py
streamlit run dashboard/app.py
```

## Resume line (draft, will refine once you have real numbers)
*"Built an end-to-end consumer intelligence pipeline on 100K+ e-commerce orders — combined SQL-based
funnel analysis with transformer-based sentiment/topic modeling on customer reviews to identify
[X]% of repeat-purchase drop-off attributable to delivery experience; deployed interactive
Streamlit dashboard."*
