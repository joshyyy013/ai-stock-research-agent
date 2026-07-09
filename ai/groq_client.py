from groq import Groq


def get_groq_client(api_key):
    return Groq(api_key=api_key) if api_key else None


def generate_ai_summary(client, ticker, profile, quote, news):
    news_text = ""

    for article in news[:5]:
        news_text += f"""
Headline: {article.get("headline", "N/A")}
Summary: {article.get("summary", "N/A")}
Source: {article.get("source", "N/A")}
"""

    prompt = f"""
You are an AI stock research assistant.

Analyse {ticker} using this information.

Company: {profile.get("name", "N/A")}
Industry: {profile.get("finnhubIndustry", "N/A")}
Market Cap: {profile.get("marketCapitalization", "N/A")} million

Current Price: {quote.get("c", "N/A")}
Daily Change: {quote.get("d", "N/A")}
Daily Percent Change: {quote.get("dp", "N/A")}%

Recent news:
{news_text}

Explain:
1. What changed recently?
2. Why the stock may be moving
3. Bull case
4. Bear case
5. Key risks
6. What to research next

Do not give buy, sell, or hold advice.
"""

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {"role": "system", "content": "You explain stock research clearly."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.3,
    )

    return response.choices[0].message.content


def generate_earnings_summary(client, ticker, earnings):
    earnings_text = ""

    for event in earnings[:3]:
        earnings_text += f"""
Date: {event.get("date", "N/A")}
EPS Estimate: {event.get("epsEstimate", "N/A")}
Revenue Estimate: {event.get("revenueEstimate", "N/A")}
"""

    prompt = f"""
Analyse the upcoming earnings for {ticker}.

{earnings_text}

Explain:
1. When the next earnings event is
2. Why earnings can affect the stock price
3. What investors should watch before earnings
4. What could be a positive or negative surprise

Do not give buy, sell, or hold advice.
"""

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {"role": "system", "content": "You explain earnings events clearly."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.3,
    )

    return response.choices[0].message.content


def generate_watchlist_summary(client, watchlist_data):
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
Analyse this watchlist:

{watchlist_text}

Explain:
1. Main sector exposures
2. Concentration risks
3. Stocks that may move together
4. What to monitor next

Do not give buy, sell, or hold advice.
"""

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {"role": "system", "content": "You explain portfolio risk clearly."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.3,
    )

    return response.choices[0].message.content