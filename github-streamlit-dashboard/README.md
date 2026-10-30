# US Stocks Paper Trading Dashboard

A Streamlit dashboard for researching US-listed stocks and recording simulated trades. It is **paper-trading only**: it does not connect to a broker or place orders.

## Deploy on Streamlit Community Cloud

1. Create a new **public or private GitHub repository**.
2. Upload the **contents of this folder** to the repository root (so `app.py`, `requirements.txt`, and `trader-scanner/` are at the top level).
3. In Streamlit Community Cloud, choose **New app** and connect the repository.
4. Set the main file path to `app.py` and deploy.

## Run locally

```bash
python -m pip install -r requirements.txt
streamlit run app.py
```

## Market data limitations

- Scanner price/history data is fetched from public Yahoo Finance chart endpoints. These endpoints are unofficial, may be delayed, incomplete, rate-limited, or unavailable, and do **not** guarantee exchange real-time quotes.
- Intraday 5-minute bars may be available during a session, but the app does not provide a guaranteed real-time feed or exchange-grade execution prices.
- News is fetched from Yahoo Finance RSS and may also be delayed.
- Always check a quote with a regulated broker/data provider before relying on it. A scanner result is not a buy/sell recommendation.

## Paper account storage warning

The paper ledger and settings are written to JSON files under `trader/`. On Streamlit Community Cloud, local filesystem changes are **not guaranteed to persist** across app restarts, rebuilds, or redeployments. Export your trade journal regularly and keep a backup of any paper-account records you want to retain. Do not treat this as a permanent account database.

## Safety

- No broker integration, API keys, live orders, margin, options, or short selling.
- Simulated entries and exits are manually recorded by the user.
- Paper results do not predict future performance.
