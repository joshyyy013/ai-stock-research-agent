import os
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

from api.finnhub_client import (
    get_quote,
    get_company_profile,
    get_company_news,
    get_earnings_calendar,
)
from api.sec_client import get_latest_filings
from ai.groq_client import (
    get_groq_client,
    generate_ai_summary,
    generate_earnings_summary,
    generate_watchlist_summary,
)
from reports.report_builder import build_research_report
from utils.helpers import parse_watchlist, format_price, format_percent


# ---------- SETUP ----------

env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=env_path)

FINNHUB_API_KEY = os.getenv("FINNHUB_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

groq_client = get_groq_client(GROQ_API_KEY)

st.set_page_config(page_title="AI Stock Research Agent", layout="wide")

st.title("AI Stock Research Agent")
st.write(
    "Research stocks using market data, company news, earnings events, "
    "SEC filings, watchlists, and AI summaries."
)


# ---------- SIDEBAR ----------

ticker = st.sidebar.text_input("Stock ticker", value="MU").upper()

st.sidebar.header("Watchlist")
watchlist_input = st.sidebar.text_input(
    "Enter tickers separated by commas",
    value="NVDA, AMD, MU, META, IVV, VEU",
)

watchlist = parse_watchlist(watchlist_input)


# ---------- SINGLE STOCK RESEARCH ----------

st.header("Single Stock Research")

if st.button("Research Stock"):
    if not FINNHUB_API_KEY:
        st.error("Finnhub API key missing. Add FINNHUB_API_KEY to your .env file.")
    else:
        with st.spinner("Fetching stock data..."):
            st.session_state.ticker = ticker
            st.session_state.quote = get_quote(ticker, FINNHUB_API_KEY)
            st.session_state.profile = get_company_profile(ticker, FINNHUB_API_KEY)
            st.session_state.news = get_company_news(ticker, FINNHUB_API_KEY)
            st.session_state.earnings = get_earnings_calendar(ticker, FINNHUB_API_KEY)
            st.session_state.sec_filings = get_latest_filings(ticker)

            st.session_state.ai_summary = None
            st.session_state.earnings_summary = None


if "quote" in st.session_state:
    ticker = st.session_state.ticker
    quote = st.session_state.quote
    profile = st.session_state.profile
    news = st.session_state.news
    earnings = st.session_state.earnings
    sec_filings = st.session_state.sec_filings

    st.subheader(f"{ticker} Overview")

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Current Price", format_price(quote.get("c")))
    col2.metric("Previous Close", format_price(quote.get("pc")))
    col3.metric("Daily Change", format_price(quote.get("d")))
    col4.metric("Daily % Change", format_percent(quote.get("dp")))

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
                st.session_state.earnings_summary = generate_earnings_summary(
                    groq_client, ticker, earnings
                )

    if st.session_state.get("earnings_summary"):
        st.write(st.session_state.earnings_summary)

    st.subheader("Latest SEC Filings")

    if sec_filings:
        for filing in sec_filings:
            st.write(f"**{filing['form']}** - {filing['filing_date']}")

            accession_no_dashes = filing["accession_number"].replace("-", "")
            cik = filing["cik"].lstrip("0")

            filing_url = (
                f"https://www.sec.gov/Archives/edgar/data/"
                f"{cik}/{accession_no_dashes}/{filing['primary_document']}"
            )

            st.link_button("📄 Open SEC Filing", filing_url)

            st.divider()
    else:
        st.write("No SEC filings found.")

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
                st.session_state.ai_summary = generate_ai_summary(
                    groq_client, ticker, profile, quote, news
                )

    if st.session_state.get("ai_summary"):
        st.write(st.session_state.ai_summary)

        report_text = build_research_report(
            ticker,
            profile,
            quote,
            st.session_state.ai_summary,
        )

        st.download_button(
            label="Download Research Report",
            data=report_text,
            file_name=f"{ticker}_research_report.txt",
            mime="text/plain",
        )


# ---------- WATCHLIST ----------

st.header("Watchlist Analysis")

if st.button("Load Watchlist"):
    if not FINNHUB_API_KEY:
        st.error("Finnhub API key missing. Add FINNHUB_API_KEY to your .env file.")
    else:
        watchlist_data = []

        with st.spinner("Loading watchlist..."):
            for symbol in watchlist:
                quote_data = get_quote(symbol, FINNHUB_API_KEY)
                profile_data = get_company_profile(symbol, FINNHUB_API_KEY)

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
                    groq_client,
                    st.session_state.watchlist_data,
                )

    if st.session_state.get("watchlist_summary"):
        st.write(st.session_state.watchlist_summary)