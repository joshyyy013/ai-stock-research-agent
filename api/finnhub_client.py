import requests
from datetime import datetime, timedelta

BASE_URL = "https://finnhub.io/api/v1"


def get_quote(symbol, api_key):
    return make_request(
        f"{BASE_URL}/quote",
        {
            "symbol": symbol,
            "token": api_key,
        },
    )


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

def make_request(url, params):
    try:
        response = requests.get(
            url,
            params=params,
            timeout=15,
        )
        response.raise_for_status()
        return response.json()

    except requests.exceptions.Timeout:
        raise RuntimeError("The request timed out. Please try again.")

    except requests.exceptions.HTTPError as error:
        raise RuntimeError(
            f"The data provider returned an error: {error}"
        )

    except requests.exceptions.RequestException as error:
        raise RuntimeError(
            f"Could not connect to the data provider: {error}"
        )