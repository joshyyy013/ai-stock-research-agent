import os
import requests
import streamlit as st
from dotenv import load_dotenv
from datetime import datetime, timedelta

load_dotenv()

API_KEY = os.getenv("FINNHUB_API_KEY")
BASE_URL = "https://finnhub.io/api/v1"

st.set_page_config(page_title="AI Stock Research Agent", layout="wide")

st.title("AI Stock Research Agent - Phase 1")
st.write("Enter a stock ticker to view price, company details, and recent news.")

ticker = st.text_input("Enter ticker symbol", value="MU").upper()


def get_quote(symbol):
    url = f"{BASE_URL}/quote"
    params = {"symbol": symbol, "token": API_KEY}
    response = requests.get(url, params=params)
    return response.json()


def get_company_profile(symbol):
    url = f"{BASE_URL}/stock/profile2"
    params = {"symbol": symbol, "token": API_KEY}
    response = requests.get(url, params=params)
    return response.json()


def get_company_news(symbol):
    today = datetime.today().date()
    week_ago = today - timedelta(days=7)

    url = f"{BASE_URL}/company-news"
    params = {
        "symbol": symbol,
        "from": week_ago,
        "to": today,
        "token": API_KEY
    }

    response = requests.get(url, params=params)
    return response.json()


if st.button("Research Stock"):
    if not API_KEY:
        st.error("API key missing. Add FINNHUB_API_KEY to your .env file.")
    else:
        quote = get_quote(ticker)
        profile = get_company_profile(ticker)
        news = get_company_news(ticker)

        st.subheader(f"{ticker} Overview")

        col1, col2, col3 = st.columns(3)

        col1.metric("Current Price", f"${quote.get('c', 'N/A')}")
        col2.metric("Previous Close", f"${quote.get('pc', 'N/A')}")
        col3.metric("Daily Change", f"{quote.get('d', 'N/A')}")

        st.subheader("Company Profile")

        st.write(f"**Company:** {profile.get('name', 'N/A')}")
        st.write(f"**Industry:** {profile.get('finnhubIndustry', 'N/A')}")
        st.write(f"**Country:** {profile.get('country', 'N/A')}")
        st.write(f"**Exchange:** {profile.get('exchange', 'N/A')}")
        st.write(f"**Market Cap:** {profile.get('marketCapitalization', 'N/A')} million")

        st.subheader("Recent News")

        if news:
            for article in news[:5]:
                st.write(f"### {article.get('headline')}")
                st.write(article.get("summary"))
                st.write(article.get("url"))
                st.divider()
        else:
            st.write("No recent news found.")