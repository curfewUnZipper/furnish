import streamlit as st
import pandas as pd
import plotly.express as px
from wordcloud import WordCloud
import matplotlib.pyplot as plt
from sentiment_analysis import analyze_sentiment
from topic_analysis import top_keywords

from scraper import scrape_tweets_for_product
# Cache scraped tweets for 1 hour
@st.cache_data(ttl=3600)
def cached_scrape(product_name, limit=50):
    return scrape_tweets_for_product(product_name, limit)

# from transformers import pipeline
# @st.cache_resource
# def load_hf_model():
#     return pipeline("sentiment-analysis", model="cardiffnlp/twitter-roberta-base-sentiment-latest")
# hf_analyzer = load_hf_model()

import os
from datetime import datetime
import time 

st.set_page_config(page_title="Informed Customer", layout="wide")

#CSS
st.markdown(
    """
    <style>
    .reportview-container {
        background: linear-gradient(#f7fbfd, #ffffff);
    }
    .stApp {
        font-family: "Segoe UI", Roboto, sans-serif;
    }
    .metric-label {
        color: #6b7280;
    }
    </style>
    """, unsafe_allow_html=True
)

st.title("Sentiment Analysis of Furniture Dashboard")

# Sidebar controls
st.sidebar.header("Controls")
data_option = st.sidebar.selectbox("Data source", ["sample:combined.csv", "Upload CSV"])
engine = st.sidebar.radio("Sentiment engine", ["textblob", "huggingface"], index=0)
category = st.sidebar.selectbox("Category", ["all","sofa","bed","chair","table"])
product_filter = st.sidebar.text_input("Product name filter (substring)", "")
fetch_live = st.sidebar.button("🔍 Fetch Live Tweets for Product")

# Load data
DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
if data_option.startswith("sample"):
    df = pd.read_csv(os.path.join(DATA_DIR, "combined.csv"))
    # --- Live scraping integration ---

if fetch_live:
    query_name = product_filter or category

    if query_name == "all":
        st.info("No specific product selected — fetching tweets for all main furniture categories.")
        categories = ["sofa", "chair", "table", "bed"]
    else:
        categories = [query_name]

    all_data = []

    for cat in categories:
        with st.spinner(f"Fetching tweets for '{cat}'..."):
            try:
                live_df = cached_scrape(cat, limit=50)

                if not live_df.empty:
                    st.success(f"Fetched {len(live_df)} tweets about '{cat}'. Running sentiment analysis...")
                    live_df["sentiment_label"] = live_df["text"].apply(
                        lambda t: analyze_sentiment(t, engine=engine)["label"]
                    )
                    live_df["category"] = cat

                    # ✅ Convert dates to DD-MM-YYYY format before saving
                    if "date" in live_df.columns:
                        live_df["date"] = pd.to_datetime(live_df["date"]).dt.strftime("%d-%m-%Y")

                    all_data.append(live_df)

                    # Save per-category CSV
                    os.makedirs("data", exist_ok=True)
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    cat_filename = f"data/tweets_{cat}_{timestamp}.csv"
                    live_df.to_csv(cat_filename, index=False, encoding="utf-8")
                    st.write(f"💾 Saved category data to `{cat_filename}`")


                else:
                    st.warning(f"No tweets found for '{cat}'.")

            except Exception as e:
                st.error(f"Error fetching tweets for '{cat}': {e}")
    
        time.sleep(5)

    # Merge all fetched data into main df
    if all_data:
        combined_df = pd.concat(all_data, ignore_index=True)
        df = pd.concat([df, combined_df], ignore_index=True)

        # Save combined dataset
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        combined_filename = f"data/tweets_combined_{timestamp}.csv"
        if "date" in df.columns:
            df["date"] = pd.to_datetime(df["date"]).dt.strftime("%d-%m-%Y")

        df.to_csv(combined_filename, index=False, encoding="utf-8")
        st.success(f"✅ All fetched data saved to `{combined_filename}`")
    else:
        st.warning("No tweets found for any selected category.")


else:
    uploaded = st.sidebar.file_uploader("Upload CSV", type=["csv"])
    if uploaded is not None:
        df = pd.read_csv(uploaded)
    else:
        df = pd.read_csv(os.path.join(DATA_DIR, "combined.csv"))

# filter by category/product
if category!="all":
    df = df[df["category"]==category]
if product_filter:
    df = df[df["product_name"].str.contains(product_filter, case=False, na=False)]

st.sidebar.write("Records:", len(df))

# analyze sentiment if not present
if "sentiment_label" not in df.columns:
    df["sentiment_label"] = df["text"].apply(lambda t: analyze_sentiment(t, engine=engine)["label"])

# Overall sentiment metrics
counts = df["sentiment_label"].value_counts(normalize=True)
pos = round(100*counts.get("positive", 0),1)
neu = round(100*counts.get("neutral", 0),1)
neg = round(100*counts.get("negative", 0),1)

col1, col2, col3, col4 = st.columns([1,1,1,2])
col1.metric("Positive", f"{pos}%")
col2.metric("Neutral", f"{neu}%")
col3.metric("Negative", f"{neg}%")
col4.metric("Total mentions", len(df))

# Alert rule: if negative > 30%
if neg > 30:
    st.error("⚠️ Alert: Negative sentiment exceeds 30% — investigate top complaints.")

# Sentiment timeline (by date)
df["date"] = pd.to_datetime(df["date"], utc=True)
timeline = df.groupby(pd.Grouper(key="date", freq="7D", origin="epoch"))["sentiment_label"].apply(lambda s: (s=="negative").sum()/len(s) if len(s)>0 else 0).reset_index(name="neg_ratio")
fig_t = px.line(timeline, x="date", y="neg_ratio", title="Negative sentiment ratio over time (7-day buckets)")
st.plotly_chart(fig_t, use_container_width=True)

# Sentiment by region (choropleth) - needs ISO codes; using region column as ISO if possible
region_df = df.groupby("region")["sentiment_label"].apply(lambda s: (s=="negative").mean()).reset_index(name="neg_ratio").dropna()
print(region_df)
import pycountry

def iso2_to_iso3(code):
    try:
        return pycountry.countries.get(alpha_2=code).alpha_3
    except:
        return None

region_df["iso3"] = region_df["region"].apply(iso2_to_iso3)
region_df = region_df.dropna(subset=["iso3"])

vmin = region_df["neg_ratio"].min()
vmax = region_df["neg_ratio"].max()

if not region_df.empty:
    # if regions are ISO country codes, use choropleth
    try:
        fig_map = px.choropleth(
                                    region_df,
                                    locations="iso3",
                                    color="neg_ratio",
                                    locationmode="ISO-3",
                                    color_continuous_scale=px.colors.sequential.Reds,
                                    range_color=(vmin, vmax),  # 👈 match your actual 0.1–0.2 range
                                    title="Negative Sentiment by Region"
                                )
        fig_map.update_geos(
                                showframe=False,
                                showcoastlines=True,
                                showland=True,
                                landcolor="whitesmoke",
                                projection_type="natural earth"
                            )

        fig_map.update_layout(
                                    margin=dict(l=0, r=0, t=40, b=0),
                                    coloraxis_colorbar=dict(
                                        title="Negative Ratio",
                                        tickformat=".0%",
                                    ),
                                    paper_bgcolor="white",
                                    plot_bgcolor="white"
                                )

        st.plotly_chart(fig_map, use_container_width=True)
        # st.write(region_df[["region", "neg_ratio"]].head())
    except Exception:
        st.write("Region heatmap not available (regions must be ISO-3 country codes).")
else:
    st.write("No region data to plot.")

# Top products table (by negative percentage)
prod_df = df.groupby("product_name")["sentiment_label"].apply(lambda s: (s=="negative").mean()).reset_index(name="neg_ratio")
prod_df = prod_df.sort_values("neg_ratio", ascending=False).head(15)
st.subheader("Products with highest negative ratio")
st.dataframe(prod_df)

# Word cloud for complaints / trending words
st.subheader("Word Cloud (top terms)")
texts = df[df["sentiment_label"]=="negative"]["text"].astype(str).tolist()
if texts:
    wc = WordCloud(width=800, height=300, background_color=None, mode="RGBA").generate(" ".join(texts))
    plt.figure(figsize=(12,4))
    plt.imshow(wc, interpolation="bilinear")
    plt.axis("off")
    st.pyplot(plt)
else:
    st.write("No negative texts for word cloud.")

# Topic keywords (simple)
st.subheader("Top Keywords (all mentions)")
topk = top_keywords(df["text"].astype(str).tolist(), n=30, stopwords=set())
st.table(topk[:20])

st.markdown("---")
