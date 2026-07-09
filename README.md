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