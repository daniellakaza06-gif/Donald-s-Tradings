# Trade Intelligence Dashboard

A professional Streamlit analytics application built from the supplied **Daily Trade Sheet** Excel workbook.

## What it uses

The app parses every weekly trading worksheet and preserves the workbook's core fields: coin, capital allocated, target stop loss, profit target, actual profit/loss percentages, actual profit/loss in ZAR, daily grouping, and the workbook's profitability-model sheet.

## Features

- Executive KPI dashboard
- Daily and weekly realised P/L analysis
- Win/loss and profit-factor analytics
- Searchable trade ledger
- Risk-vs-target visualisation
- Coin-level performance leaderboard
- Profitability-model viewer
- Workbook coverage/audit page
- Workbook replacement upload
- Filtered CSV export
- Responsive dark professional UI

## Run locally

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
streamlit run streamlit_app.py
```

## Deploy with Streamlit Community Cloud

1. Push this folder to a GitHub repository.
2. In Streamlit Community Cloud, create an app from that repository.
3. Set the entrypoint to `streamlit_app.py`.
4. Deploy.

The included workbook is stored at `data/daily_trade_sheet.xlsx`, so the deployed app has data immediately. The sidebar uploader can temporarily replace it for a session.

## Repository structure

```text
trade_analytics_streamlit/
├── .streamlit/config.toml
├── data/daily_trade_sheet.xlsx
├── .gitignore
├── README.md
├── requirements.txt
└── streamlit_app.py
```

## Stack

Python · Streamlit · pandas · Plotly · openpyxl · GitHub
