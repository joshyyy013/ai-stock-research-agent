import requests
from datetime import datetime, timedelta

BASE_URL = "https://finnhub.io/api/v1"


def get_quote(symbol, api_key):
    response = requests.get(
        f"{BASE_URL}/quote",
        params={"symbol": symbol, "token": api_key},
    )
    return response.json()


def get_company_profile(symbol, api_key):
    response = requests.get(
        f"{BASE_URL}/stock/profile2",
        params={"symbol": symbol, "token": api_key},
    )
    return response.json()


def get_company_news(symbol, api_key):
    today = datetime.today().date()
    week_ago = today - timedelta(days=7)

    response = requests.get(
        f"{BASE_URL}/company-news",
        params={
            "symbol": symbol,
            "from": week_ago,
            "to": today,
            "token": api_key,
        },
    )
    return response.json()


def get_earnings_calendar(symbol, api_key):
    today = datetime.today().date()
    three_months_later = today + timedelta(days=90)

    response = requests.get(
        f"{BASE_URL}/calendar/earnings",
        params={
            "symbol": symbol,
            "from": today,
            "to": three_months_later,
            "token": api_key,
        },
    )

    data = response.json()
    return data.get("earningsCalendar", [])