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
from api.sec_client import (
    get_latest_filings,
    build_filing_url,
    get_filing_text,
)
from ai.groq_client import (
    get_groq_client,
    generate_ai_summary,
    generate_earnings_summary,
    generate_watchlist_summary,
    generate_filing_summary,
)
from reports.report_builder import build_research_report
from utils.helpers import (
    parse_watchlist,
    format_price,
    format_percent,
    validate_ticker,
)


# =========================================================
# ENVIRONMENT AND APP SETUP
# =========================================================

env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=env_path)

FINNHUB_API_KEY = os.getenv("FINNHUB_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

groq_client = get_groq_client(GROQ_API_KEY)

st.set_page_config(
    page_title="AI Stock Research Agent",
    page_icon="📈",
    layout="wide",
)

st.title("📈 AI Stock Research Agent")

st.write(
    "Research stocks using market data, company news, earnings events, "
    "SEC filings, watchlist analysis, and AI-generated summaries."
)

st.caption(
    "This application is for research and educational purposes only. "
    "It does not provide financial advice."
)


# =========================================================
# CACHED DATA FUNCTIONS
# =========================================================

@st.cache_data(ttl=300)
def load_quote(symbol):
    return get_quote(symbol, FINNHUB_API_KEY)


@st.cache_data(ttl=3600)
def load_company_profile(symbol):
    return get_company_profile(symbol, FINNHUB_API_KEY)


@st.cache_data(ttl=1800)
def load_company_news(symbol):
    return get_company_news(symbol, FINNHUB_API_KEY)


@st.cache_data(ttl=3600)
def load_earnings_calendar(symbol):
    return get_earnings_calendar(symbol, FINNHUB_API_KEY)


@st.cache_data(ttl=3600)
def load_sec_filings(symbol):
    return get_latest_filings(symbol)


@st.cache_data(ttl=3600, show_spinner=False)
def load_filing_text(filing):
    return get_filing_text(filing)


# =========================================================
# HELPER FUNCTIONS
# =========================================================

def valid_stock_response(quote, profile):
    """Check that Finnhub returned usable stock information."""

    company_name = profile.get("name")
    current_price = quote.get("c")

    if not company_name:
        return False

    if current_price in [None, 0, "0", "N/A"]:
        return False

    return True


def reset_single_stock_summaries():
    """Clear summaries when the user researches another stock."""

    st.session_state.ai_summary = None
    st.session_state.earnings_summary = None
    st.session_state.filing_summaries = {}


def display_api_error(error):
    """Show a readable API error message."""

    message = str(error)

    if "429" in message or "rate limit" in message.lower():
        st.error(
            "The data provider's rate limit was reached. "
            "Wait briefly and try again."
        )
    elif "timeout" in message.lower():
        st.error("The request timed out. Please try again.")
    else:
        st.error(f"Could not retrieve the requested data: {message}")


def display_ai_error(error, feature_name="AI summary"):
    """Show a readable Groq error message."""

    message = str(error)

    if "413" in message or "request too large" in message.lower():
        st.error(
            f"The information sent for the {feature_name} was too large "
            "for the current Groq limit."
        )
    elif "rate_limit" in message.lower() or "429" in message:
        st.error(
            "The Groq rate limit was reached. "
            "Wait briefly before trying again."
        )
    else:
        st.error(f"Could not generate the {feature_name}: {message}")


# =========================================================
# SIDEBAR
# =========================================================

st.sidebar.header("Stock Research")

ticker_input = st.sidebar.text_input(
    "Stock ticker",
    value="MU",
    help="Examples: MU, NVDA, AMD, META, MSFT",
)

ticker = ticker_input.strip().upper()

st.sidebar.divider()

st.sidebar.header("Watchlist")

watchlist_input = st.sidebar.text_input(
    "Enter tickers separated by commas",
    value="NVDA, AMD, MU, META, MSFT",
)

watchlist = parse_watchlist(watchlist_input)

st.sidebar.divider()

if FINNHUB_API_KEY:
    st.sidebar.success("Finnhub API configured")
else:
    st.sidebar.error("Finnhub API key missing")

if GROQ_API_KEY:
    st.sidebar.success("Groq API configured")
else:
    st.sidebar.warning("Groq API key missing")


# =========================================================
# SINGLE STOCK RESEARCH
# =========================================================

st.header("Single Stock Research")

if st.button("Research Stock", type="primary"):
    if not ticker:
        st.warning("Enter a stock ticker.")

    elif not validate_ticker(ticker):
        st.warning(
            "Enter a valid ticker using letters, numbers, periods, or hyphens."
        )

    elif not FINNHUB_API_KEY:
        st.error(
            "Finnhub API key missing. "
            "Add FINNHUB_API_KEY to your .env file."
        )

    else:
        try:
            with st.spinner(f"Researching {ticker}..."):
                quote = load_quote(ticker)
                profile = load_company_profile(ticker)
                news = load_company_news(ticker)
                earnings = load_earnings_calendar(ticker)
                sec_filings = load_sec_filings(ticker)

            if not valid_stock_response(quote, profile):
                st.error(
                    f"No valid stock data was found for {ticker}. "
                    "Check the ticker and try again."
                )
            else:
                st.session_state.ticker = ticker
                st.session_state.quote = quote
                st.session_state.profile = profile
                st.session_state.news = news
                st.session_state.earnings = earnings
                st.session_state.sec_filings = sec_filings

                reset_single_stock_summaries()

        except Exception as error:
            display_api_error(error)


# =========================================================
# DISPLAY SINGLE STOCK RESULTS
# =========================================================

if "quote" in st.session_state:
    researched_ticker = st.session_state.ticker
    quote = st.session_state.quote
    profile = st.session_state.profile
    news = st.session_state.news
    earnings = st.session_state.earnings
    sec_filings = st.session_state.sec_filings

    st.subheader(f"{researched_ticker} Overview")

    col1, col2, col3, col4 = st.columns(4)

    col1.metric(
        "Current Price",
        format_price(quote.get("c")),
    )

    col2.metric(
        "Previous Close",
        format_price(quote.get("pc")),
    )

    col3.metric(
        "Daily Change",
        format_price(quote.get("d")),
    )

    col4.metric(
        "Daily Change %",
        format_percent(quote.get("dp")),
    )

    market_col1, market_col2, market_col3 = st.columns(3)

    market_col1.metric(
        "Open",
        format_price(quote.get("o")),
    )

    market_col2.metric(
        "Daily High",
        format_price(quote.get("h")),
    )

    market_col3.metric(
        "Daily Low",
        format_price(quote.get("l")),
    )

    st.divider()

    # -----------------------------------------------------
    # COMPANY PROFILE
    # -----------------------------------------------------

    st.subheader("Company Profile")

    profile_col1, profile_col2 = st.columns(2)

    with profile_col1:
        st.write(f"**Company:** {profile.get('name', 'N/A')}")
        st.write(
            f"**Industry:** "
            f"{profile.get('finnhubIndustry', 'N/A')}"
        )
        st.write(f"**Country:** {profile.get('country', 'N/A')}")

    with profile_col2:
        st.write(f"**Exchange:** {profile.get('exchange', 'N/A')}")
        st.write(
            f"**Market Capitalisation:** "
            f"{profile.get('marketCapitalization', 'N/A')} million"
        )

        website = profile.get("weburl")

        if website:
            st.link_button("Company Website", website)

    st.divider()

    # -----------------------------------------------------
    # EARNINGS
    # -----------------------------------------------------

    st.subheader("Upcoming Earnings")

    if earnings:
        for event_index, event in enumerate(earnings[:3]):
            with st.container(border=True):
                st.write(
                    f"**Date:** {event.get('date', 'N/A')}"
                )
                st.write(
                    f"**Quarter:** Q{event.get('quarter', 'N/A')} "
                    f"{event.get('year', 'N/A')}"
                )
                st.write(
                    f"**EPS estimate:** "
                    f"{event.get('epsEstimate', 'N/A')}"
                )
                st.write(
                    f"**Revenue estimate:** "
                    f"{event.get('revenueEstimate', 'N/A')}"
                )
    else:
        st.info("No upcoming earnings found in the next 90 days.")

    if st.button("Generate Earnings Summary"):
        if not GROQ_API_KEY:
            st.error(
                "Groq API key missing. "
                "Add GROQ_API_KEY to your .env file."
            )

        elif not earnings:
            st.warning("No earnings data is available to summarise.")

        else:
            try:
                with st.spinner("Analysing the earnings event..."):
                    st.session_state.earnings_summary = (
                        generate_earnings_summary(
                            groq_client,
                            researched_ticker,
                            earnings,
                        )
                    )

            except Exception as error:
                display_ai_error(error, "earnings summary")

    if st.session_state.get("earnings_summary"):
        with st.container(border=True):
            st.markdown(st.session_state.earnings_summary)

    st.divider()

    # -----------------------------------------------------
    # SEC FILINGS
    # -----------------------------------------------------

    st.subheader("Latest SEC Filings")

    if sec_filings:
        if "filing_summaries" not in st.session_state:
            st.session_state.filing_summaries = {}

        for filing_index, filing in enumerate(sec_filings):
            filing_key = (
                f"{filing.get('accession_number', filing_index)}"
            )

            with st.container(border=True):
                filing_col1, filing_col2 = st.columns([3, 1])

                with filing_col1:
                    st.write(
                        f"### {filing.get('form', 'SEC Filing')}"
                    )
                    st.write(
                        f"Filed on "
                        f"{filing.get('filing_date', 'N/A')}"
                    )

                filing_url = build_filing_url(filing)

                with filing_col2:
                    st.link_button(
                        "Open Filing",
                        filing_url,
                        key=f"open_filing_{filing_key}",
                        use_container_width=True,
                    )

                if st.button(
                    "Generate AI Filing Summary",
                    key=f"summarise_filing_{filing_key}",
                ):
                    if not GROQ_API_KEY:
                        st.error(
                            "Groq API key missing. "
                            "Add GROQ_API_KEY to your .env file."
                        )

                    else:
                        try:
                            with st.spinner(
                                "Reading and analysing the filing..."
                            ):
                                filing_text = load_filing_text(filing)

                                filing_summary = generate_filing_summary(
                                    groq_client,
                                    researched_ticker,
                                    filing,
                                    filing_text,
                                )

                                st.session_state.filing_summaries[
                                    filing_key
                                ] = filing_summary

                        except Exception as error:
                            display_ai_error(
                                error,
                                "SEC filing summary",
                            )

                if filing_key in st.session_state.filing_summaries:
                    st.markdown(
                        st.session_state.filing_summaries[filing_key]
                    )

    else:
        st.info(
            "No recent 10-K or 10-Q filings were found. "
            "SEC filings may not be available for non-US companies or ETFs."
        )

    st.divider()

    # -----------------------------------------------------
    # RECENT NEWS
    # -----------------------------------------------------

    st.subheader("Recent News")

    if news:
        for article in news[:5]:
            with st.container(border=True):
                headline = article.get(
                    "headline",
                    "No headline available",
                )

                st.write(f"### {headline}")

                source = article.get("source", "Unknown source")
                st.caption(f"Source: {source}")

                summary = article.get(
                    "summary",
                    "No summary available.",
                )

                st.write(summary)

                article_url = article.get("url")

                if article_url:
                    st.link_button(
                        "Read Article",
                        article_url,
                        key=(
                            f"news_"
                            f"{article.get('id', article_url)}"
                        ),
                    )
    else:
        st.info("No recent company news was found.")

    st.sidebar.subheader("Current Research")

    st.sidebar.metric(
        "News Articles Found",
        len(news[:5]) if news else 0,
    )

    st.sidebar.metric(
        "SEC Filings Found",
        len(sec_filings) if sec_filings else 0,
    )

    st.divider()

    # -----------------------------------------------------
    # MAIN AI RESEARCH SUMMARY
    # -----------------------------------------------------

    st.subheader("AI Research Summary")

    if st.button("Generate AI Research Summary"):
        if not GROQ_API_KEY:
            st.error(
                "Groq API key missing. "
                "Add GROQ_API_KEY to your .env file."
            )

        else:
            try:
                with st.spinner("Generating AI research summary..."):
                    st.session_state.ai_summary = generate_ai_summary(
                        groq_client,
                        researched_ticker,
                        profile,
                        quote,
                        news,
                    )

            except Exception as error:
                display_ai_error(error, "stock research summary")

    if st.session_state.get("ai_summary"):
        with st.container(border=True):
            st.markdown(st.session_state.ai_summary)

        report_text = build_research_report(
            researched_ticker,
            profile,
            quote,
            st.session_state.ai_summary,
        )

        st.download_button(
            label="Download Research Report",
            data=report_text,
            file_name=(
                f"{researched_ticker}_research_report.txt"
            ),
            mime="text/plain",
        )


# =========================================================
# WATCHLIST ANALYSIS
# =========================================================

st.divider()
st.header("Watchlist Analysis")

if st.button("Load Watchlist"):
    if not watchlist:
        st.warning("Enter at least one ticker in the watchlist.")

    elif not FINNHUB_API_KEY:
        st.error(
            "Finnhub API key missing. "
            "Add FINNHUB_API_KEY to your .env file."
        )

    else:
        invalid_tickers = [
            symbol
            for symbol in watchlist
            if not validate_ticker(symbol)
        ]

        if invalid_tickers:
            st.warning(
                "These watchlist entries are invalid: "
                + ", ".join(invalid_tickers)
            )

        else:
            watchlist_data = []
            failed_symbols = []

            progress_bar = st.progress(0)

            for index, symbol in enumerate(watchlist):
                try:
                    quote_data = load_quote(symbol)
                    profile_data = load_company_profile(symbol)

                    if valid_stock_response(
                        quote_data,
                        profile_data,
                    ):
                        watchlist_data.append(
                            {
                                "ticker": symbol,
                                "name": profile_data.get(
                                    "name",
                                    "N/A",
                                ),
                                "industry": profile_data.get(
                                    "finnhubIndustry",
                                    "N/A",
                                ),
                                "price": quote_data.get(
                                    "c",
                                    "N/A",
                                ),
                                "change_percent": quote_data.get(
                                    "dp",
                                    "N/A",
                                ),
                            }
                        )
                    else:
                        failed_symbols.append(symbol)

                except Exception:
                    failed_symbols.append(symbol)

                progress_bar.progress(
                    (index + 1) / len(watchlist)
                )

            progress_bar.empty()

            st.session_state.watchlist_data = watchlist_data
            st.session_state.watchlist_summary = None

            if failed_symbols:
                st.warning(
                    "No valid data was found for: "
                    + ", ".join(failed_symbols)
                )


if "watchlist_data" in st.session_state:
    watchlist_data = st.session_state.watchlist_data

    if watchlist_data:
        st.subheader("Watchlist Overview")

        header_col1, header_col2, header_col3, header_col4 = (
            st.columns([1, 3, 2, 2])
        )

        header_col1.write("**Ticker**")
        header_col2.write("**Company**")
        header_col3.write("**Price**")
        header_col4.write("**Daily Change**")

        for stock in watchlist_data:
            row_col1, row_col2, row_col3, row_col4 = (
                st.columns([1, 3, 2, 2])
            )

            row_col1.write(f"**{stock['ticker']}**")
            row_col2.write(stock["name"])
            row_col3.write(format_price(stock["price"]))
            row_col4.write(
                format_percent(stock["change_percent"])
            )

            st.caption(stock["industry"])

        st.subheader("AI Watchlist Risk Summary")

        if st.button("Generate Watchlist Summary"):
            if not GROQ_API_KEY:
                st.error(
                    "Groq API key missing. "
                    "Add GROQ_API_KEY to your .env file."
                )

            else:
                try:
                    with st.spinner(
                        "Analysing watchlist exposure..."
                    ):
                        st.session_state.watchlist_summary = (
                            generate_watchlist_summary(
                                groq_client,
                                watchlist_data,
                            )
                        )

                except Exception as error:
                    display_ai_error(
                        error,
                        "watchlist risk summary",
                    )

        if st.session_state.get("watchlist_summary"):
            with st.container(border=True):
                st.markdown(
                    st.session_state.watchlist_summary
                )

    else:
        st.info("No valid watchlist companies were loaded.")