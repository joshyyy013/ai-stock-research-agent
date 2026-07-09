## Setup

Clone the repository

```bash
git clone https://github.com/joshyyy013/ai-stock-research-agent.git
```

Install dependencies

```bash
pip install -r requirements.txt
```

Copy the example environment file

```bash
cp .env.example .env
```

Add your own API keys to `.env`

```
FINNHUB_API_KEY=...
GROQ_API_KEY=...
```

Run the application

```bash
streamlit run app.py
```

## Features
- Stock quote lookup
- Company profile lookup
- Recent news display
- AI stock research summary
- Earnings calendar analysis
- Watchlist risk summary
- Downloadable research reports

## Tech Stack
- Python
- Streamlit
- Finnhub API
- Groq API
- Llama 3.1
- dotenv

## Project Structure
- `app.py` - Streamlit interface
- `api/` - Finnhub API functions
- `ai/` - LLM summary generation
- `reports/` - downloadable report builder
- `utils/` - helper functions