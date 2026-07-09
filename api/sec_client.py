import requests

HEADERS = {
    "User-Agent": "Joshua Kumar ai-stock-research-agent contact@example.com"
}


def get_company_cik(ticker):
    url = "https://www.sec.gov/files/company_tickers.json"
    response = requests.get(url, headers=HEADERS)
    data = response.json()

    ticker = ticker.upper()

    for company in data.values():
        if company["ticker"].upper() == ticker:
            return str(company["cik_str"]).zfill(10)

    return None


def get_latest_filings(ticker):
    cik = get_company_cik(ticker)

    if not cik:
        return []

    url = f"https://data.sec.gov/submissions/CIK{cik}.json"
    response = requests.get(url, headers=HEADERS)
    data = response.json()

    filings = data["filings"]["recent"]

    results = []

    for i in range(len(filings["form"])):
        if filings["form"][i] in ["10-K", "10-Q"]:
            results.append({
                "form": filings["form"][i],
                "filing_date": filings["filingDate"][i],
                "accession_number": filings["accessionNumber"][i],
                "primary_document": filings["primaryDocument"][i],
                "cik": cik,
            })

    return results[:5]