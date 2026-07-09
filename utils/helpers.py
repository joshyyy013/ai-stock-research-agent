def parse_watchlist(text):
    """
    Convert comma-separated ticker text into a clean list.
    Example: "NVDA, AMD, MU" -> ["NVDA", "AMD", "MU"]
    """
    if not text:
        return []

    return [
        ticker.strip().upper()
        for ticker in text.split(",")
        if ticker.strip()
    ]


def format_price(price):
    """
    Format a number as a dollar price.
    """
    try:
        return f"${float(price):,.2f}"
    except (TypeError, ValueError):
        return "N/A"


def format_percent(value):
    """
    Format a number as a percentage.
    """
    try:
        return f"{float(value):.2f}%"
    except (TypeError, ValueError):
        return "N/A"