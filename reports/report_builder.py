def build_research_report(ticker, profile, quote, ai_summary):
    return f"""
# {ticker} Stock Research Report

## Company
{profile.get('name', 'N/A')}

## Industry
{profile.get('finnhubIndustry', 'N/A')}

## Price
Current Price: ${quote.get('c', 'N/A')}
Daily Change: {quote.get('d', 'N/A')}
Daily % Change: {quote.get('dp', 'N/A')}%

## AI Research Summary
{ai_summary}
"""