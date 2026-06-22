import os
from pathlib import Path
from datetime import datetime, timedelta

import requests
import streamlit as st
from dotenv import load_dotenv
from groq import Groq


# Load environment variables
env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=env_path)

FINNHUB_API_KEY = os.getenv("FINNHUB_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
BASE_URL = "https://finnhub.io/api/v1"

if GROQ_API_KEY:
    groq_client = Groq(api_key=GROQ_API_KEY)
else:
    groq_client = None


st.set_page_config(page_title="AI Stock Research Agent", layout="wide")

st.title("AI Stock Research Agent - Phase 2")
st.write("Research stocks using live market data, company news, and AI-generated summaries.")

ticker = st.text_input("Enter ticker symbol", value="MU").upper()


def get_quote(symbol):
    url = f"{BASE_URL}/quote"
    params = {"symbol": symbol, "token": FINNHUB_API_KEY}
    response = requests.get(url, params=params)
    return response.json()


def get_company_profile(symbol):
    url = f"{BASE_URL}/stock/profile2"
    params = {"symbol": symbol, "token": FINNHUB_API_KEY}
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
        "token": FINNHUB_API_KEY,
    }

    response = requests.get(url, params=params)
    return response.json()


def generate_ai_summary(ticker, profile, quote, news):
    news_text = ""

    for article in news[:5]:
        news_text += f"""
Headline: {article.get("headline")}
Summary: {article.get("summary")}
Source: {article.get("source")}
URL: {article.get("url")}
"""

    prompt = f"""
You are an AI stock research assistant.

Analyse {ticker} using the company profile, quote data, and recent news below.

Company profile:
{profile}

Quote:
{quote}

Recent news:
{news_text}

Return the answer in this format:

1. What changed recently?
2. Why the stock may be moving
3. Bull case
4. Bear case
5. Key risks
6. What to research next

Do not give direct financial advice.
Do not say buy, sell, or hold.
Keep it clear and beginner-friendly.
"""

    response = groq_client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {
                "role": "system",
                "content": "You explain stock research clearly and carefully.",
            },
            {"role": "user", "content": prompt},
        ],
        temperature=0.3,
    )

    return response.choices[0].message.content


if st.button("Research Stock"):
    if not FINNHUB_API_KEY:
        st.error("Finnhub API key missing. Add FINNHUB_API_KEY to your .env file.")
    else:
        with st.spinner("Fetching stock data..."):
            st.session_state.ticker = ticker
            st.session_state.quote = get_quote(ticker)
            st.session_state.profile = get_company_profile(ticker)
            st.session_state.news = get_company_news(ticker)
            st.session_state.ai_summary = None


if "quote" in st.session_state:
    ticker = st.session_state.ticker
    quote = st.session_state.quote
    profile = st.session_state.profile
    news = st.session_state.news

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

    st.subheader("AI Research Summary")

    if st.button("Generate AI Summary"):
        if not GROQ_API_KEY:
            st.error("Groq API key missing. Add GROQ_API_KEY to your .env file.")
        else:
            with st.spinner("Generating AI summary..."):
                st.session_state.ai_summary = generate_ai_summary(
                    ticker, profile, quote, news
                )

    if st.session_state.get("ai_summary"):
        st.write(st.session_state.ai_summary)