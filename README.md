# Finance Tracker

A self-hosted personal finance dashboard built with Python and Dash. Track your bank accounts, savings, investments and pensions — with interactive charts showing your net worth over time and allocation breakdown.

![Python](https://img.shields.io/badge/Python-3.9+-blue) ![Dash](https://img.shields.io/badge/Dash-Plotly-e94560) ![SQLite](https://img.shields.io/badge/Database-SQLite-green)

## Features

- Add and manage multiple account types (Current, Savings, Investment/ISA, Pension)
- Log balances with date tracking
- Net worth over time line chart
- Allocation by account type donut chart
- Editable and sortable data tables
- Delete accounts and balance entries
- Dark themed UI
- All data stored locally in SQLite — your data never leaves your machine

## Prerequisites

- Python 3.9 or higher
- pip (Python package manager)

## Setup

### 1. Clone the repository

```bash
git clone https://github.com/ChrisJ99/Finance-tracker.git
cd Finance-tracker
```

### 2. Create a virtual environment

**Windows:**
```cmd
python -m venv venv
venv\Scripts\activate
```

**Linux / macOS / ChromeOS:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install dash pandas plotly
```

### 4. Run the app

```bash
python app.py
```

### 5. Open in your browser

Go to [http://localhost:8050](http://localhost:8050)

The SQLite database (`finance.db`) is created automatically on first run.

## Project Structure

```
Finance-tracker/
├── app.py           # Main application
├── assets/          # Dash auto-loads CSS from this folder
│   └── style.css    # Application styles
├── finance.db       # SQLite database (created on first run, gitignored)
├── .gitignore
└── README.md
```

## Usage

1. **Add accounts** — give each account a name, type and institution
2. **Log balances** — select an account, pick a date and enter the balance
3. **View charts** — net worth over time and allocation breakdown update automatically
4. **Edit data** — click any editable cell in the tables to modify it, then hit Save Changes
5. **Delete data** — tick the checkboxes next to rows and hit Delete Selected

## .gitignore

Make sure your `.gitignore` includes:

```
venv/
__pycache__/
*.pyc
finance.db
```

`finance.db` contains your personal financial data and should not be committed to the repository.

## License

This project is for personal use.
