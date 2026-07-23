"""
Phase 6: Interactive dashboard.
Run with: streamlit run dashboard/app.py
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs"

st.set_page_config(page_title="Shop Consumer Intelligence", layout="wide")
st.title("🛍️ Shop Consumer Intelligence: Funnel & Sentiment")
st.caption("End-to-end behavior analysis — Olist Brazilian e-commerce dataset")

tab1, tab2, tab3 = st.tabs(["Funnel", "Sentiment & Topics", "Segments"])

with tab1:
    st.header("Purchase Funnel")
    funnel_path = OUT / "funnel_stage_counts.csv"
    if funnel_path.exists():
        fc = pd.read_csv(funnel_path).iloc[0]
        stages = ["purchased", "approved", "shipped", "delivered", "reviewed"]
        fig = go.Figure(go.Funnel(y=stages, x=[fc[s] for s in stages]))
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Run scripts/02_funnel_analysis.py first.")

    delivery_path = OUT / "delivery_days_by_review_score.csv"
    if delivery_path.exists():
        st.subheader("Delivery Speed vs. Review Score")
        d = pd.read_csv(delivery_path)
        fig2 = px.bar(d, x="review_score", y="delivery_days",
                      labels={"delivery_days": "Avg delivery days"})
        st.plotly_chart(fig2, use_container_width=True)

with tab2:
    st.header("Customer Sentiment")
    sent_path = OUT / "reviews_with_sentiment.csv"
    if sent_path.exists():
        df = pd.read_csv(sent_path)
        col1, col2 = st.columns(2)
        with col1:
            fig3 = px.pie(df, names="model_sentiment", title="Sentiment distribution")
            st.plotly_chart(fig3, use_container_width=True)
        with col2:
            agree = (df.rating_sentiment == df.model_sentiment).mean()
            st.metric("Model vs. star-rating agreement", f"{agree:.1%}")
            st.caption("Divergence = reviews where text sentiment tells a different "
                       "story than the star rating alone.")

        topics_path = OUT / "negative_review_topics.csv"
        if topics_path.exists():
            st.subheader("Top complaint themes (negative reviews)")
            st.dataframe(pd.read_csv(topics_path).head(10))
    else:
        st.info("Run scripts/03_sentiment_analysis.py first.")

with tab3:
    st.header("Customer Segments (RFM)")
    seg_path = OUT / "segment_profiles.csv"
    if seg_path.exists():
        st.dataframe(pd.read_csv(seg_path))
    cross_path = OUT / "segment_sentiment_crosstab.csv"
    if cross_path.exists():
        st.subheader("Sentiment by segment")
        st.dataframe(pd.read_csv(cross_path))
    if not seg_path.exists():
        st.info("Run scripts/04_segmentation.py first.")
