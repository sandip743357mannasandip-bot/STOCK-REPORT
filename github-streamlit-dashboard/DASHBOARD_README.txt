US STOCK PAPER TRADING DASHBOARD
================================

START ON WINDOWS
1. Extract this ZIP folder somewhere convenient.
2. Double-click START_DASHBOARD.bat.
3. Wait for the browser to open. If it does not, visit http://localhost:8501
4. Keep the black terminal window open while using the dashboard.

The first launch installs Streamlit and Pandas. Internet is required for package
installation and for market/news data retrieval.

FEATURES
- Overview of paper cash, equity, positions and P&L
- Daily and opening-range scanner using the included trader-scanner script
- Yahoo Finance headlines using trader-news
- Manual simulated buy, price updates and simulated position closing
- Trade journal, win rate, cumulative P&L and CSV export
- Editable paper risk limits

IMPORTANT SAFETY
- This dashboard is PAPER-ONLY. It does not connect to a broker and cannot
  place live orders. Do not add broker API keys.
- Market data is public, unofficial and may be delayed, incomplete or rate-limited.
- Scanner matches are research candidates, not buy/sell recommendations.
- Paper trades are manually entered and are not automatically synchronized
  with real-time quotes. Update marks yourself using a verified quote.
- Your paper ledger is stored locally in trader/paper_portfolio.json.
- Your paper settings are stored in trader/config.json.
