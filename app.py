import os
from pathlib import Path
from datetime import datetime, timedelta

import requests
import streamlit as st
from dotenv import load_dotenv
from groq import Groq


# ---------- SETUP ----------

env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=env_path)

FINNHUB_API_KEY = os.getenv("FINNHUB_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
BASE_URL = "https://finnhub.io/api/v1"

groq_client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None

st.set_page_config(page_title="AI Stock Research Agent", layout="wide")

st.title("AI Stock Research Agent")
st.write("Research stocks using market data, company news, earnings events, watchlists, and AI summaries.")


# ---------- SIDEBAR ----------

ticker = st.sidebar.text_input("Stock ticker", value="MU").upper()

st.sidebar.header("Watchlist")
watchlist_input = st.sidebar.text_input(
    "Enter tickers separated by commas",
    value="NVDA, AMD, MU, META, IVV, VEU"
)

watchlist = [
    symbol.strip().upper()
    for symbol in watchlist_input.split(",")
    if symbol.strip()
]


# ---------- API FUNCTIONS ----------

def get_quote(symbol):
    response = requests.get(
        f"{BASE_URL}/quote",
        params={"symbol": symbol, "token": FINNHUB_API_KEY},
    )
    return response.json()


def get_company_profile(symbol):
    response = requests.get(
        f"{BASE_URL}/stock/profile2",
        params={"symbol": symbol, "token": FINNHUB_API_KEY},
    )
    return response.json()


def get_company_news(symbol):
    today = datetime.today().date()
    week_ago = today - timedelta(days=7)

    response = requests.get(
        f"{BASE_URL}/company-news",
        params={
            "symbol": symbol,
            "from": week_ago,
            "to": today,
            "token": FINNHUB_API_KEY,
        },
    )
    return response.json()


def get_earnings_calendar(symbol):
    today = datetime.today().date()
    three_months_later = today + timedelta(days=90)

    response = requests.get(
        f"{BASE_URL}/calendar/earnings",
        params={
            "symbol": symbol,
            "from": today,
            "to": three_months_later,
            "token": FINNHUB_API_KEY,
        },
    )

    data = response.json()
    return data.get("earningsCalendar", [])


# ---------- AI FUNCTIONS ----------

def generate_ai_summary(ticker, profile, quote, news):
    profile_text = f"""
Company: {profile.get("name", "N/A")}
Industry: {profile.get("finnhubIndustry", "N/A")}
Country: {profile.get("country", "N/A")}
Exchange: {profile.get("exchange", "N/A")}
Market Cap: {profile.get("marketCapitalization", "N/A")} million
"""

    quote_text = f"""
Current Price: {quote.get("c", "N/A")}
Daily Change: {quote.get("d", "N/A")}
Daily Percent Change: {quote.get("dp", "N/A")}%
Previous Close: {quote.get("pc", "N/A")}
Open Price: {quote.get("o", "N/A")}
High Price: {quote.get("h", "N/A")}
Low Price: {quote.get("l", "N/A")}
"""

    news_text = ""

    for article in news[:5]:
        news_text += f"""
Headline: {article.get("headline", "N/A")}
Summary: {article.get("summary", "N/A")}
Source: {article.get("source", "N/A")}
"""

    prompt = f"""
You are an AI stock research assistant.

Analyse {ticker} using the information below.

Company:
{profile_text}

Quote:
{quote_text}

Recent news:
{news_text}

Return the answer in this format:

1. What changed recently?
2. Why the stock may be moving
3. Bull case
4. Bear case
5. Key risks
6. What to research next

Rules:
- Do not give direct financial advice.
- Do not say buy, sell, or hold.
- Keep it clear and beginner-friendly.
- Mention when information is limited.
"""

    response = groq_client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {"role": "system", "content": "You explain stock research clearly and carefully."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.3,
    )

    return response.choices[0].message.content


def generate_earnings_summary(ticker, earnings):
    earnings_text = ""

    for event in earnings[:3]:
        earnings_text += f"""
Date: {event.get("date", "N/A")}
EPS Estimate: {event.get("epsEstimate", "N/A")}
Revenue Estimate: {event.get("revenueEstimate", "N/A")}
Quarter: {event.get("quarter", "N/A")}
Year: {event.get("year", "N/A")}
"""

    prompt = f"""
You are an AI stock research assistant.

Analyse the upcoming earnings information for {ticker}:

{earnings_text}

Explain:
1. When the next earnings event is
2. Why earnings can affect the stock price
3. What investors should watch before earnings
4. What would count as a positive or negative surprise

Do not give buy, sell, or hold advice.
Keep it beginner-friendly.
"""

    response = groq_client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {"role": "system", "content": "You explain earnings events clearly."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.3,
    )

    return response.choices[0].message.content


def generate_watchlist_summary(watchlist_data):
    watchlist_text = ""

    for stock in watchlist_data:
        watchlist_text += f"""
Ticker: {stock["ticker"]}
Company: {stock["name"]}
Industry: {stock["industry"]}
Price: {stock["price"]}
Daily Change %: {stock["change_percent"]}
"""

    prompt = f"""
You are an AI portfolio research assistant.

Analyse this watchlist:

{watchlist_text}

Explain:
1. Main sector exposures
2. Concentration risks
3. Stocks that may move together
4. What the investor should monitor next

Do not give buy, sell, or hold advice.
Keep it beginner-friendly.
"""

    response = groq_client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {"role": "system", "content": "You explain portfolio risk clearly."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.3,
    )

    return response.choices[0].message.content


# ---------- SINGLE STOCK RESEARCH ----------

st.header("Single Stock Research")

if st.button("Research Stock"):
    if not FINNHUB_API_KEY:
        st.error("Finnhub API key missing. Add FINNHUB_API_KEY to your .env file.")
    else:
        with st.spinner("Fetching stock data..."):
            st.session_state.ticker = ticker
            st.session_state.quote = get_quote(ticker)
            st.session_state.profile = get_company_profile(ticker)
            st.session_state.news = get_company_news(ticker)
            st.session_state.earnings = get_earnings_calendar(ticker)

            st.session_state.ai_summary = None
            st.session_state.earnings_summary = None


if "quote" in st.session_state:
    ticker = st.session_state.ticker
    quote = st.session_state.quote
    profile = st.session_state.profile
    news = st.session_state.news
    earnings = st.session_state.earnings

    st.subheader(f"{ticker} Overview")

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Current Price", f"${quote.get('c', 'N/A')}")
    col2.metric("Previous Close", f"${quote.get('pc', 'N/A')}")
    col3.metric("Daily Change", f"{quote.get('d', 'N/A')}")
    col4.metric("Daily % Change", f"{quote.get('dp', 'N/A')}%")

    st.subheader("Company Profile")

    st.write(f"**Company:** {profile.get('name', 'N/A')}")
    st.write(f"**Industry:** {profile.get('finnhubIndustry', 'N/A')}")
    st.write(f"**Country:** {profile.get('country', 'N/A')}")
    st.write(f"**Exchange:** {profile.get('exchange', 'N/A')}")
    st.write(f"**Market Cap:** {profile.get('marketCapitalization', 'N/A')} million")

    st.subheader("Upcoming Earnings")

    if earnings:
        for event in earnings[:3]:
            st.write(f"**Date:** {event.get('date', 'N/A')}")
            st.write(f"**EPS Estimate:** {event.get('epsEstimate', 'N/A')}")
            st.write(f"**Revenue Estimate:** {event.get('revenueEstimate', 'N/A')}")
            st.divider()
    else:
        st.write("No upcoming earnings found in the next 90 days.")

    if st.button("Generate Earnings Summary"):
        if not GROQ_API_KEY:
            st.error("Groq API key missing. Add GROQ_API_KEY to your .env file.")
        elif not earnings:
            st.warning("No earnings data available to summarise.")
        else:
            with st.spinner("Analysing earnings event..."):
                st.session_state.earnings_summary = generate_earnings_summary(ticker, earnings)

    if st.session_state.get("earnings_summary"):
        st.write(st.session_state.earnings_summary)

    st.subheader("Recent News")

    if news:
        for article in news[:5]:
            st.write(f"### {article.get('headline', 'No headline')}")
            st.write(article.get("summary", "No summary available."))
            st.write(article.get("url", "No URL available."))
            st.divider()
    else:
        st.write("No recent news found.")

    st.sidebar.subheader("AI Usage Info")
    st.sidebar.metric("News Articles Analysed", len(news[:5]))

    st.subheader("AI Research Summary")

    if st.button("Generate AI Summary"):
        if not GROQ_API_KEY:
            st.error("Groq API key missing. Add GROQ_API_KEY to your .env file.")
        else:
            with st.spinner("Generating AI summary..."):
                st.session_state.ai_summary = generate_ai_summary(ticker, profile, quote, news)

    if st.session_state.get("ai_summary"):
        st.write(st.session_state.ai_summary)


# ---------- WATCHLIST ----------

st.header("Watchlist Analysis")

if st.button("Load Watchlist"):
    if not FINNHUB_API_KEY:
        st.error("Finnhub API key missing. Add FINNHUB_API_KEY to your .env file.")
    else:
        watchlist_data = []

        with st.spinner("Loading watchlist..."):
            for symbol in watchlist:
                quote_data = get_quote(symbol)
                profile_data = get_company_profile(symbol)

                stock_info = {
                    "ticker": symbol,
                    "name": profile_data.get("name", "N/A"),
                    "industry": profile_data.get("finnhubIndustry", "N/A"),
                    "price": quote_data.get("c", "N/A"),
                    "change_percent": quote_data.get("dp", "N/A"),
                }

                watchlist_data.append(stock_info)

        st.session_state.watchlist_data = watchlist_data
        st.session_state.watchlist_summary = None


if "watchlist_data" in st.session_state:
    st.subheader("Watchlist Overview")

    for stock in st.session_state.watchlist_data:
        st.write(
            f"**{stock['ticker']}** - {stock['name']} | "
            f"{stock['industry']} | "
            f"${stock['price']} | "
            f"{stock['change_percent']}%"
        )

    st.subheader("AI Watchlist Risk Summary")

    if st.button("Generate Watchlist Summary"):
        if not GROQ_API_KEY:
            st.error("Groq API key missing. Add GROQ_API_KEY to your .env file.")
        else:
            with st.spinner("Analysing watchlist..."):
                st.session_state.watchlist_summary = generate_watchlist_summary(
                    st.session_state.watchlist_data
                )

    if st.session_state.get("watchlist_summary"):
        st.write(st.session_state.watchlist_summary)