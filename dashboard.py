import streamlit as st
import pandas as pd
import requests
import os

# Configuration
API_URL = os.getenv("API_URL", "http://localhost:8000/api")

st.set_page_config(page_title="Stock Sentiment Dashboard", layout="wide")

st.title("📈 Stock Market Sentiment Agent")
st.markdown("This dashboard displays sentiment analysis on financial news and RSS feeds powered by a custom ML agent running on OCI.")

# Sidebar for controls
st.sidebar.header("Controls")

# 1. Fetching Summary
st.sidebar.subheader("Sentiment Summary")
ticker_input = st.sidebar.text_input("Enter Ticker or Sector (e.g., TSLA, AAPL, Macro)", value="TSLA").upper()

if st.sidebar.button("Get Summary"):
    with st.spinner("Fetching data..."):
        try:
            resp = requests.get(f"{API_URL}/sentiment/{ticker_input}")
            if resp.status_code == 200:
                data = resp.json()

                col1, col2, col3 = st.columns(3)
                col1.metric("Average Sentiment Score", f"{data['average_score']:.2f}")
                col2.metric("Total Articles Analyzed", data['total_articles'])

                # Sentiment Breakdown
                st.subheader(f"Sentiment Breakdown for {ticker_input}")
                st.bar_chart({
                    "Positive": [data["positive_count"]],
                    "Neutral": [data["neutral_count"]],
                    "Negative": [data["negative_count"]]
                })
            else:
                st.sidebar.error(f"Error: {resp.json().get('detail', 'Not found')}")
        except Exception as e:
            st.sidebar.error(f"Failed to connect to API: {e}")

# 2. Trigger Ingestion
st.sidebar.subheader("Manual Controls")
if st.sidebar.button("Trigger Ingestion"):
    try:
        resp = requests.post(f"{API_URL}/ingest")
        if resp.status_code == 200:
            st.sidebar.success("Ingestion started in background.")
        else:
            st.sidebar.error("Failed to start ingestion.")
    except Exception as e:
        st.sidebar.error(f"API Connection Error: {e}")

st.divider()

# 3. Recent Articles List
st.subheader("Recent Articles")
col1, col2 = st.columns([1, 1])
with col1:
    filter_ticker = st.text_input("Filter by Ticker/Sector (Leave blank for all)", value=ticker_input)
with col2:
    limit = st.slider("Number of articles to show", min_value=10, max_value=100, value=20)

try:
    url = f"{API_URL}/articles?limit={limit}"
    if filter_ticker:
        url += f"&ticker={filter_ticker}"

    articles_resp = requests.get(url)
    if articles_resp.status_code == 200:
        articles = articles_resp.json()
        if articles:
            df = pd.DataFrame(articles)
            # Reorder and format columns
            df = df[['published_at', 'source', 'ticker', 'title', 'sentiment_label', 'sentiment_score', 'url']]

            # Styling for sentiment
            def highlight_sentiment(val):
                if val == 'positive':
                    return 'color: green'
                elif val == 'negative':
                    return 'color: red'
                return 'color: gray'

            st.dataframe(
                df.style.map(highlight_sentiment, subset=['sentiment_label']),
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info("No articles found.")
    else:
        st.error("Failed to fetch articles.")
except Exception as e:
    st.error(f"Failed to connect to API: {e}")
