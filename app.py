import dash
from dash import html, dcc, dash_table, Input, Output, State, callback, no_update
import plotly.express as px
import plotly.graph_objects as go
import sqlite3
import pandas as pd
from datetime import datetime, date

# ── Database Setup ──────────────────────────────────────────────────────────

DB_PATH = "finance.db"


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS accounts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            type TEXT NOT NULL,
            institution TEXT,
            interest_rate REAL NOT NULL DEFAULT 0
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS balances (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            account_id INTEGER NOT NULL,
            date DATE NOT NULL,
            amount REAL NOT NULL,
            FOREIGN KEY (account_id) REFERENCES accounts(id)
        )
    """)
    # Lightweight migration for existing databases created before interest_rate existed.
    account_cols = [r[1] for r in conn.execute("PRAGMA table_info(accounts)").fetchall()]
    if "interest_rate" not in account_cols:
        conn.execute("ALTER TABLE accounts ADD COLUMN interest_rate REAL NOT NULL DEFAULT 0")
    conn.commit()
    conn.close()


init_db()

# ── Account Types ───────────────────────────────────────────────────────────

ACCOUNT_TYPES = ["Current", "Savings", "Investment/ISA", "Pension"]

# ── App Setup ───────────────────────────────────────────────────────────────

app = dash.Dash(__name__, suppress_callback_exceptions=True)

app.layout = html.Div(
    style={
        "fontFamily": "'Segoe UI', Tahoma, Geneva, Verdana, sans-serif",
        "backgroundColor": "#0f1117",
        "color": "#e0e0e0",
        "minHeight": "100vh",
        "padding": "0",
        "margin": "0",
    },
    children=[
        dcc.Store(id="accounts-original-data"),
        dcc.Store(id="balances-original-data"),
        # ── Header ──
        html.Div(
            style={
                "background": "linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%)",
                "padding": "30px 40px",
                "borderBottom": "2px solid #e94560",
            },
            children=[
                html.H1(
                    "Finance Tracker",
                    style={
                        "margin": "0",
                        "fontSize": "2.2rem",
                        "fontWeight": "300",
                        "letterSpacing": "2px",
                        "color": "#e94560",
                    },
                ),
                html.P(
                    "Track your accounts, balances & net worth",
                    style={
                        "margin": "5px 0 0 0",
                        "color": "#8892b0",
                        "fontSize": "0.95rem",
                    },
                ),
            ],
        ),
        # ── Main Content ──
        html.Div(
            style={"padding": "30px 40px", "maxWidth": "1400px", "margin": "0 auto"},
            children=[
                # ── Top Row: Forms ──
                html.Div(
                    style={
                        "display": "grid",
                        "gridTemplateColumns": "1fr 1fr",
                        "gap": "30px",
                        "marginBottom": "40px",
                    },
                    children=[
                        # ── Add Account Form ──
                        html.Div(
                            style={
                                "backgroundColor": "#1a1a2e",
                                "borderRadius": "12px",
                                "padding": "25px",
                                "border": "1px solid #2a2a4a",
                            },
                            children=[
                                html.H3(
                                    "Add Account",
                                    style={
                                        "marginTop": "0",
                                        "color": "#e94560",
                                        "fontWeight": "400",
                                        "borderBottom": "1px solid #2a2a4a",
                                        "paddingBottom": "10px",
                                    },
                                ),
                                html.Label("Account Name", style={"color": "#8892b0", "fontSize": "0.85rem"}),
                                dcc.Input(
                                    id="account-name",
                                    type="text",
                                    placeholder="e.g. Barclays Current",
                                    style={
                                        "width": "100%",
                                        "padding": "10px",
                                        "marginBottom": "15px",
                                        "marginTop": "5px",
                                        "backgroundColor": "#0f1117",
                                        "border": "1px solid #2a2a4a",
                                        "borderRadius": "6px",
                                        "color": "#e0e0e0",
                                        "boxSizing": "border-box",
                                    },
                                ),
                                html.Label("Account Type", style={"color": "#8892b0", "fontSize": "0.85rem"}),
                                dcc.Dropdown(
                                    id="account-type",
                                    options=[{"label": t, "value": t} for t in ACCOUNT_TYPES],
                                    placeholder="Select type...",
                                    style={"marginBottom": "15px", "marginTop": "5px"},
                                    className="dark-dropdown",
                                ),
                                html.Label("Institution", style={"color": "#8892b0", "fontSize": "0.85rem"}),
                                dcc.Input(
                                    id="account-institution",
                                    type="text",
                                    placeholder="e.g. Barclays, Vanguard",
                                    style={
                                        "width": "100%",
                                        "padding": "10px",
                                        "marginBottom": "20px",
                                        "marginTop": "5px",
                                        "backgroundColor": "#0f1117",
                                        "border": "1px solid #2a2a4a",
                                        "borderRadius": "6px",
                                        "color": "#e0e0e0",
                                        "boxSizing": "border-box",
                                    },
                                ),
                                html.Label("Interest Rate (% APR)", style={"color": "#8892b0", "fontSize": "0.85rem"}),
                                dcc.Input(
                                    id="account-interest-rate",
                                    type="number",
                                    placeholder="e.g. 4.50",
                                    step=0.01,
                                    value=0,
                                    style={
                                        "width": "100%",
                                        "padding": "10px",
                                        "marginBottom": "20px",
                                        "marginTop": "5px",
                                        "backgroundColor": "#0f1117",
                                        "border": "1px solid #2a2a4a",
                                        "borderRadius": "6px",
                                        "color": "#e0e0e0",
                                        "boxSizing": "border-box",
                                    },
                                ),
                                html.Button(
                                    "Add Account",
                                    id="add-account-btn",
                                    n_clicks=0,
                                    style={
                                        "backgroundColor": "#e94560",
                                        "color": "white",
                                        "border": "none",
                                        "padding": "10px 25px",
                                        "borderRadius": "6px",
                                        "cursor": "pointer",
                                        "fontSize": "0.95rem",
                                        "width": "100%",
                                    },
                                ),
                                html.Div(id="account-msg", style={"marginTop": "10px", "fontSize": "0.85rem"}),
                            ],
                        ),
                        # ── Log Balance Form ──
                        html.Div(
                            style={
                                "backgroundColor": "#1a1a2e",
                                "borderRadius": "12px",
                                "padding": "25px",
                                "border": "1px solid #2a2a4a",
                            },
                            children=[
                                html.H3(
                                    "Log Balance",
                                    style={
                                        "marginTop": "0",
                                        "color": "#e94560",
                                        "fontWeight": "400",
                                        "borderBottom": "1px solid #2a2a4a",
                                        "paddingBottom": "10px",
                                    },
                                ),
                                html.Label("Account", style={"color": "#8892b0", "fontSize": "0.85rem"}),
                                dcc.Dropdown(
                                    id="balance-account",
                                    placeholder="Select account...",
                                    style={"marginBottom": "15px", "marginTop": "5px"},
                                    className="dark-dropdown",
                                ),
                                html.Label("Date", style={"color": "#8892b0", "fontSize": "0.85rem"}),
                                dcc.DatePickerSingle(
                                    id="balance-date",
                                    date=date.today(),
                                    display_format="DD/MM/YYYY",
                                    style={"marginBottom": "15px", "marginTop": "5px"},
                                ),
                                html.Label("Amount (£)", style={"color": "#8892b0", "fontSize": "0.85rem"}),
                                dcc.Input(
                                    id="balance-amount",
                                    type="number",
                                    placeholder="e.g. 5000.00",
                                    step=0.01,
                                    style={
                                        "width": "100%",
                                        "padding": "10px",
                                        "marginBottom": "20px",
                                        "marginTop": "5px",
                                        "backgroundColor": "#0f1117",
                                        "border": "1px solid #2a2a4a",
                                        "borderRadius": "6px",
                                        "color": "#e0e0e0",
                                        "boxSizing": "border-box",
                                    },
                                ),
                                html.Button(
                                    "Log Balance",
                                    id="add-balance-btn",
                                    n_clicks=0,
                                    style={
                                        "backgroundColor": "#e94560",
                                        "color": "white",
                                        "border": "none",
                                        "padding": "10px 25px",
                                        "borderRadius": "6px",
                                        "cursor": "pointer",
                                        "fontSize": "0.95rem",
                                        "width": "100%",
                                    },
                                ),
                                html.Div(id="balance-msg", style={"marginTop": "10px", "fontSize": "0.85rem"}),
                            ],
                        ),
                    ],
                ),
                # ── Summary Cards ──
                html.Div(
                    id="summary-cards",
                    style={
                        "display": "grid",
                        "gridTemplateColumns": "repeat(4, 1fr)",
                        "gap": "20px",
                        "marginBottom": "40px",
                    },
                ),
                # ── Charts Row ──
                html.Div(
                    style={
                        "display": "grid",
                        "gridTemplateColumns": "2fr 1fr",
                        "gap": "30px",
                        "marginBottom": "40px",
                    },
                    children=[
                        html.Div(
                            style={
                                "backgroundColor": "#1a1a2e",
                                "borderRadius": "12px",
                                "padding": "20px",
                                "border": "1px solid #2a2a4a",
                            },
                            children=[
                                html.H3("Net Worth Over Time", style={"marginTop": "0", "color": "#e94560", "fontWeight": "400"}),
                                dcc.Graph(id="net-worth-chart", config={"displayModeBar": False}),
                            ],
                        ),
                        html.Div(
                            style={
                                "backgroundColor": "#1a1a2e",
                                "borderRadius": "12px",
                                "padding": "20px",
                                "border": "1px solid #2a2a4a",
                            },
                            children=[
                                html.H3("Allocation by Type", style={"marginTop": "0", "color": "#e94560", "fontWeight": "400"}),
                                dcc.Graph(id="allocation-chart", config={"displayModeBar": False}),
                            ],
                        ),
                    ],
                ),
                # ── Interest Analytics ──
                html.Div(
                    style={
                        "display": "grid",
                        "gridTemplateColumns": "1fr 1fr",
                        "gap": "30px",
                        "marginBottom": "40px",
                    },
                    children=[
                        html.Div(
                            style={
                                "backgroundColor": "#1a1a2e",
                                "borderRadius": "12px",
                                "padding": "20px",
                                "border": "1px solid #2a2a4a",
                            },
                            children=[
                                html.H3("Estimated Annual Interest by Account", style={"marginTop": "0", "color": "#e94560", "fontWeight": "400"}),
                                dcc.Graph(id="interest-income-chart", config={"displayModeBar": False}),
                            ],
                        ),
                        html.Div(
                            style={
                                "backgroundColor": "#1a1a2e",
                                "borderRadius": "12px",
                                "padding": "20px",
                                "border": "1px solid #2a2a4a",
                            },
                            children=[
                                html.H3("Weighted Average Portfolio Rate", style={"marginTop": "0", "color": "#e94560", "fontWeight": "400"}),
                                dcc.Graph(id="weighted-rate-chart", config={"displayModeBar": False}),
                            ],
                        ),
                        html.Div(
                            style={
                                "backgroundColor": "#1a1a2e",
                                "borderRadius": "12px",
                                "padding": "20px",
                                "border": "1px solid #2a2a4a",
                            },
                            children=[
                                html.H3("Projected Monthly Interest Income", style={"marginTop": "0", "color": "#e94560", "fontWeight": "400"}),
                                dcc.Graph(id="monthly-interest-chart", config={"displayModeBar": False}),
                            ],
                        ),
                        html.Div(
                            style={
                                "backgroundColor": "#1a1a2e",
                                "borderRadius": "12px",
                                "padding": "20px",
                                "border": "1px solid #2a2a4a",
                            },
                            children=[
                                html.H3("Interest Contribution by Type", style={"marginTop": "0", "color": "#e94560", "fontWeight": "400"}),
                                dcc.Graph(id="interest-type-chart", config={"displayModeBar": False}),
                            ],
                        ),
                        html.Div(
                            style={
                                "backgroundColor": "#1a1a2e",
                                "borderRadius": "12px",
                                "padding": "20px",
                                "border": "1px solid #2a2a4a",
                                "gridColumn": "1 / span 2",
                            },
                            children=[
                                html.H3("Rate vs Balance", style={"marginTop": "0", "color": "#e94560", "fontWeight": "400"}),
                                dcc.Graph(id="rate-vs-balance-chart", config={"displayModeBar": False}),
                            ],
                        ),
                    ],
                ),
                # ── Accounts Table ──
                html.Div(
                    style={
                        "backgroundColor": "#1a1a2e",
                        "borderRadius": "12px",
                        "padding": "20px",
                        "border": "1px solid #2a2a4a",
                        "marginBottom": "40px",
                    },
                    children=[
                        html.Div(
                            style={"display": "flex", "justifyContent": "space-between", "alignItems": "center", "marginBottom": "10px"},
                            children=[
                                html.H3("Your Accounts", style={"marginTop": "0", "marginBottom": "0", "color": "#e94560", "fontWeight": "400"}),
                                html.Div(children=[
                                    html.Button("Undo Changes", id="undo-accounts-btn", n_clicks=0, style={
                                        "backgroundColor": "#ffd32a", "color": "#0f1117", "border": "none",
                                        "padding": "8px 18px", "borderRadius": "6px", "cursor": "pointer",
                                        "fontSize": "0.85rem", "marginRight": "10px", "display": "none",
                                    }),
                                    html.Button("Save Changes", id="save-accounts-btn", n_clicks=0, style={
                                        "backgroundColor": "#53d769", "color": "white", "border": "none",
                                        "padding": "8px 18px", "borderRadius": "6px", "cursor": "pointer",
                                        "fontSize": "0.85rem", "marginRight": "10px", "display": "none",
                                    }),
                                    html.Button("Delete Selected", id="delete-accounts-btn", n_clicks=0, style={
                                        "backgroundColor": "#ff6b6b", "color": "white", "border": "none",
                                        "padding": "8px 18px", "borderRadius": "6px", "cursor": "pointer",
                                        "fontSize": "0.85rem", "display": "none",
                                    }),
                                ]),
                            ],
                        ),
                        html.Div(id="accounts-table"),
                        html.Div(id="accounts-edit-msg", style={"marginTop": "10px", "fontSize": "0.85rem"}),
                    ],
                ),
                # ── Balance History Table ──
                html.Div(
                    style={
                        "backgroundColor": "#1a1a2e",
                        "borderRadius": "12px",
                        "padding": "20px",
                        "border": "1px solid #2a2a4a",
                    },
                    children=[
                        html.Div(
                            style={"display": "flex", "justifyContent": "space-between", "alignItems": "center", "marginBottom": "10px"},
                            children=[
                                html.H3("Balance History", style={"marginTop": "0", "marginBottom": "0", "color": "#e94560", "fontWeight": "400"}),
                                html.Div(children=[
                                    html.Button("Undo Changes", id="undo-balances-btn", n_clicks=0, style={
                                        "backgroundColor": "#ffd32a", "color": "#0f1117", "border": "none",
                                        "padding": "8px 18px", "borderRadius": "6px", "cursor": "pointer",
                                        "fontSize": "0.85rem", "marginRight": "10px", "display": "none",
                                    }),
                                    html.Button("Save Changes", id="save-balances-btn", n_clicks=0, style={
                                        "backgroundColor": "#53d769", "color": "white", "border": "none",
                                        "padding": "8px 18px", "borderRadius": "6px", "cursor": "pointer",
                                        "fontSize": "0.85rem", "marginRight": "10px", "display": "none",
                                    }),
                                    html.Button("Delete Selected", id="delete-balances-btn", n_clicks=0, style={
                                        "backgroundColor": "#ff6b6b", "color": "white", "border": "none",
                                        "padding": "8px 18px", "borderRadius": "6px", "cursor": "pointer",
                                        "fontSize": "0.85rem", "display": "none",
                                    }),
                                ]),
                            ],
                        ),
                        html.Div(id="balances-table"),
                        html.Div(id="balances-edit-msg", style={"marginTop": "10px", "fontSize": "0.85rem"}),
                    ],
                ),
            ],
        ),
    ],
)


# ── Helper: summary card ────────────────────────────────────────────────────

def make_card(title, value, color="#e94560"):
    return html.Div(
        style={
            "backgroundColor": "#1a1a2e",
            "borderRadius": "12px",
            "padding": "20px",
            "border": "1px solid #2a2a4a",
            "textAlign": "center",
        },
        children=[
            html.P(title, style={"color": "#8892b0", "margin": "0 0 8px 0", "fontSize": "0.85rem"}),
            html.H2(value, style={"color": color, "margin": "0", "fontWeight": "400"}),
        ],
    )


def make_detail_card(title, lines, color="#e94560"):
    return html.Div(
        style={
            "backgroundColor": "#1a1a2e",
            "borderRadius": "12px",
            "padding": "20px",
            "border": "1px solid #2a2a4a",
        },
        children=[
            html.P(title, style={"color": "#8892b0", "margin": "0 0 10px 0", "fontSize": "0.85rem"}),
            html.P(lines[0], style={"color": color, "margin": "0 0 6px 0", "fontSize": "1rem", "fontWeight": "500"}),
            html.P(lines[1], style={"color": "#e0e0e0", "margin": "0 0 6px 0", "fontSize": "0.9rem"}) if len(lines) > 1 else None,
            html.P(lines[2], style={"color": "#e0e0e0", "margin": "0", "fontSize": "0.9rem"}) if len(lines) > 2 else None,
        ],
    )


def _net_worth_on_or_before(nw_df, target_date):
    hist = nw_df[nw_df["date"] <= target_date]
    if hist.empty:
        return None
    return float(hist.iloc[-1]["net_worth"])


def _format_delta_pct(delta, pct):
    if delta is None or pct is None:
        return "n/a"
    delta_sign = "+" if delta >= 0 else ""
    pct_sign = "+" if pct >= 0 else ""
    return f"{delta_sign}£{delta:,.2f} ({pct_sign}{pct:.2f}%)"


# ── Callback: Add Account ───────────────────────────────────────────────────

@callback(
    Output("account-msg", "children"),
    Output("account-name", "value"),
    Output("account-type", "value"),
    Output("account-institution", "value"),
    Output("account-interest-rate", "value"),
    Input("add-account-btn", "n_clicks"),
    State("account-name", "value"),
    State("account-type", "value"),
    State("account-institution", "value"),
    State("account-interest-rate", "value"),
    prevent_initial_call=True,
)
def add_account(n, name, acc_type, institution, interest_rate):
    if not name or not acc_type:
        return (
            html.Span("Please fill in name and type.", style={"color": "#ff6b6b"}),
            dash.no_update,
            dash.no_update,
            dash.no_update,
            dash.no_update,
        )
    rate = 0 if interest_rate is None else float(interest_rate)
    conn = get_db()
    conn.execute(
        "INSERT INTO accounts (name, type, institution, interest_rate) VALUES (?, ?, ?, ?)",
        (name, acc_type, institution or "", rate),
    )
    conn.commit()
    conn.close()
    return html.Span(f"Added '{name}'!", style={"color": "#53d769"}), "", None, "", 0


# ── Callback: Add Balance ───────────────────────────────────────────────────

@callback(
    Output("balance-msg", "children"),
    Output("balance-amount", "value"),
    Input("add-balance-btn", "n_clicks"),
    State("balance-account", "value"),
    State("balance-date", "date"),
    State("balance-amount", "value"),
    prevent_initial_call=True,
)
def add_balance(n, account_id, bal_date, amount):
    if not account_id or not bal_date or amount is None:
        return html.Span("Please fill in all fields.", style={"color": "#ff6b6b"}), dash.no_update
    conn = get_db()
    conn.execute("INSERT INTO balances (account_id, date, amount) VALUES (?, ?, ?)", (account_id, bal_date, amount))
    conn.commit()
    conn.close()
    return html.Span("Balance logged!", style={"color": "#53d769"}), None


# ── Callback: Refresh everything when accounts or balances change ───────────

@callback(
    Output("balance-account", "options"),
    Output("summary-cards", "children"),
    Output("net-worth-chart", "figure"),
    Output("allocation-chart", "figure"),
    Output("interest-income-chart", "figure"),
    Output("weighted-rate-chart", "figure"),
    Output("monthly-interest-chart", "figure"),
    Output("interest-type-chart", "figure"),
    Output("rate-vs-balance-chart", "figure"),
    Output("accounts-table", "children"),
    Output("balances-table", "children"),
    Output("accounts-original-data", "data"),
    Output("balances-original-data", "data"),
    Input("account-msg", "children"),
    Input("balance-msg", "children"),
    Input("accounts-edit-msg", "children"),
    Input("balances-edit-msg", "children"),
)
def refresh_dashboard(*_):
    conn = get_db()

    # ── Accounts dropdown ──
    accounts = pd.read_sql("SELECT * FROM accounts", conn)
    if "interest_rate" not in accounts.columns:
        accounts["interest_rate"] = 0.0
    accounts["interest_rate"] = pd.to_numeric(accounts["interest_rate"], errors="coerce").fillna(0.0)
    account_options = [{"label": f"{r['name']} ({r['type']})", "value": r["id"]} for _, r in accounts.iterrows()]

    # ── Balances ──
    balances = pd.read_sql("""
        SELECT b.id, b.account_id, a.name as account, a.type, a.interest_rate, b.date, b.amount
        FROM balances b JOIN accounts a ON b.account_id = a.id
        ORDER BY b.date
    """, conn)
    conn.close()

    if not balances.empty:
        balances["date"] = pd.to_datetime(balances["date"])
        balances["interest_rate"] = pd.to_numeric(balances["interest_rate"], errors="coerce").fillna(0.0)

    # ── Pre-calculate latest snapshot + net worth/interest time series ──
    latest = pd.DataFrame()
    nw_df = pd.DataFrame(columns=["date", "net_worth"])
    interest_df = pd.DataFrame(columns=["date", "annual_interest", "monthly_interest", "weighted_rate"])
    if not balances.empty:
        latest = balances.sort_values("date").drop_duplicates("account_id", keep="last")
        all_dates = sorted(balances["date"].unique())
        nw_data = []
        interest_data = []
        for d in all_dates:
            snap = balances[balances["date"] <= d].sort_values("date").drop_duplicates("account_id", keep="last")
            total_balance = snap["amount"].sum()
            annual_interest = (snap["amount"] * (snap["interest_rate"] / 100)).sum()
            weighted_rate = (annual_interest / total_balance) * 100 if total_balance != 0 else None
            nw_data.append({"date": d, "net_worth": snap["amount"].sum()})
            interest_data.append(
                {
                    "date": d,
                    "annual_interest": annual_interest,
                    "monthly_interest": annual_interest / 12,
                    "weighted_rate": weighted_rate,
                }
            )
        nw_df = pd.DataFrame(nw_data).sort_values("date")
        interest_df = pd.DataFrame(interest_data).sort_values("date")

    # ── Summary cards ──
    chart_bg = "#1a1a2e"
    colors = ["#e94560", "#0fbcf9", "#53d769", "#ffd32a"]

    def _empty_chart(message):
        fig = go.Figure()
        fig.update_layout(
            paper_bgcolor=chart_bg,
            plot_bgcolor=chart_bg,
            font_color="#8892b0",
            annotations=[dict(text=message, showarrow=False, font=dict(size=16, color="#8892b0"))],
            xaxis=dict(visible=False),
            yaxis=dict(visible=False),
            margin=dict(l=20, r=20, t=10, b=20),
        )
        return fig

    if balances.empty:
        cards = [
            make_card("Net Worth", "£0.00"),
            make_card("Accounts", str(len(accounts)), "#0fbcf9"),
            make_card("Latest Entry", "—", "#53d769"),
            make_card("Balance Entries", "0", "#ffd32a"),
            make_detail_card("1M / 3M / 12M Change", ["1M: n/a", "3M: n/a", "12M: n/a"]),
            make_detail_card("Growth Rates", ["3M Avg MoM: n/a", "12M CAGR: n/a"]),
            make_detail_card("Drawdown", ["Max Drawdown: n/a", "Since Peak: n/a"]),
            make_detail_card("Concentration Risk", ["Largest: n/a", "Top 2 Share: n/a"]),
        ]
    else:
        net_worth = latest["amount"].sum()
        latest_date = nw_df["date"].max()
        current_nw = float(nw_df.iloc[-1]["net_worth"])

        # 1M / 3M / 12M change
        def period_change(months):
            base = _net_worth_on_or_before(nw_df, latest_date - pd.DateOffset(months=months))
            if base is None or base == 0:
                return None, None
            delta = current_nw - base
            pct = (delta / base) * 100
            return delta, pct

        chg_1m = period_change(1)
        chg_3m = period_change(3)
        chg_12m = period_change(12)

        # Rolling monthly growth and 12M CAGR
        monthly_nw = nw_df.set_index("date")["net_worth"].resample("ME").last().ffill()
        monthly_returns = monthly_nw.pct_change()
        rolling_3m_mom = monthly_returns.tail(3).mean() if len(monthly_returns.dropna()) >= 3 else None

        cagr_12m = None
        base_window = nw_df[nw_df["date"] <= (latest_date - pd.DateOffset(months=12))]
        if not base_window.empty and current_nw > 0:
            base_row = base_window.iloc[-1]
            base_value = float(base_row["net_worth"])
            base_date = base_row["date"]
            if base_value > 0:
                days = max((latest_date - base_date).days, 1)
                cagr_12m = (((current_nw / base_value) ** (365.25 / days)) - 1) * 100

        # Max drawdown and days since peak
        running_peak = nw_df["net_worth"].cummax()
        drawdown = (nw_df["net_worth"] - running_peak) / running_peak.replace(0, pd.NA)
        max_drawdown = drawdown.min() * 100 if not drawdown.dropna().empty else None
        peak_value = nw_df["net_worth"].max()
        peak_date = nw_df.loc[nw_df["net_worth"] == peak_value, "date"].max()
        days_since_peak = int((latest_date - peak_date).days) if pd.notna(peak_date) else None

        # Concentration risk (latest snapshot)
        if net_worth != 0:
            latest_sorted = latest.sort_values("amount", ascending=False)
            largest = latest_sorted.iloc[0]
            largest_share = (largest["amount"] / net_worth) * 100
            top2_share = (latest_sorted["amount"].head(2).sum() / net_worth) * 100
            largest_label = f"Largest: {largest['account']} {largest_share:.1f}%"
            top2_label = f"Top 2 Share: {top2_share:.1f}%"
        else:
            largest_label = "Largest: n/a"
            top2_label = "Top 2 Share: n/a"

        cards = [
            make_card("Net Worth", f"£{net_worth:,.2f}"),
            make_card("Accounts", str(len(accounts)), "#0fbcf9"),
            make_card("Latest Entry", latest_date.strftime("%Y-%m-%d"), "#53d769"),
            make_card("Balance Entries", str(len(balances)), "#ffd32a"),
            make_detail_card("1M / 3M / 12M Change", [
                f"1M: {_format_delta_pct(*chg_1m)}",
                f"3M: {_format_delta_pct(*chg_3m)}",
                f"12M: {_format_delta_pct(*chg_12m)}",
            ]),
            make_detail_card("Growth Rates", [
                f"3M Avg MoM: {f'{rolling_3m_mom:+.2%}' if rolling_3m_mom is not None and pd.notna(rolling_3m_mom) else 'n/a'}",
                f"12M CAGR: {f'{cagr_12m:+.2f}%' if cagr_12m is not None and pd.notna(cagr_12m) else 'n/a'}",
            ]),
            make_detail_card("Drawdown", [
                f"Max Drawdown: {f'{max_drawdown:.2f}%' if max_drawdown is not None and pd.notna(max_drawdown) else 'n/a'}",
                f"Since Peak: {f'{days_since_peak} day(s)' if days_since_peak is not None else 'n/a'}",
            ]),
            make_detail_card("Concentration Risk", [largest_label, top2_label]),
        ]

    # ── Net Worth Over Time Chart ──
    if balances.empty:
        nw_fig = go.Figure()
        nw_fig.update_layout(
            paper_bgcolor=chart_bg, plot_bgcolor=chart_bg,
            font_color="#8892b0",
            annotations=[dict(text="No data yet — log some balances!", showarrow=False, font=dict(size=16, color="#8892b0"))],
            xaxis=dict(visible=False), yaxis=dict(visible=False),
        )
    else:
        nw_fig = go.Figure()
        nw_fig.add_trace(go.Scatter(
            x=nw_df["date"], y=nw_df["net_worth"],
            mode="lines+markers",
            line=dict(color="#e94560", width=3),
            marker=dict(size=8),
            fill="tozeroy",
            fillcolor="rgba(233,69,96,0.1)",
        ))
        nw_fig.update_layout(
            paper_bgcolor=chart_bg, plot_bgcolor=chart_bg,
            font_color="#8892b0",
            margin=dict(l=20, r=20, t=10, b=20),
            xaxis=dict(gridcolor="#2a2a4a", showgrid=True),
            yaxis=dict(gridcolor="#2a2a4a", showgrid=True, tickprefix="£"),
            hovermode="x unified",
        )

    # ── Allocation Pie Chart ──
    if balances.empty:
        alloc_fig = go.Figure()
        alloc_fig.update_layout(
            paper_bgcolor=chart_bg, plot_bgcolor=chart_bg,
            font_color="#8892b0",
            annotations=[dict(text="No data yet", showarrow=False, font=dict(size=16, color="#8892b0"))],
            xaxis=dict(visible=False), yaxis=dict(visible=False),
        )
    else:
        by_type = latest.groupby("type")["amount"].sum().reset_index()
        alloc_fig = go.Figure(go.Pie(
            labels=by_type["type"], values=by_type["amount"],
            hole=0.5,
            marker=dict(colors=colors),
            textinfo="label+percent",
            textfont=dict(color="white"),
        ))
        alloc_fig.update_layout(
            paper_bgcolor=chart_bg, plot_bgcolor=chart_bg,
            font_color="#8892b0",
            margin=dict(l=20, r=20, t=10, b=20),
            showlegend=False,
        )

    # ── Interest: Estimated Annual Interest by Account ──
    if balances.empty or latest.empty:
        interest_income_fig = _empty_chart("No balance data yet")
    else:
        interest_by_account = latest.copy()
        interest_by_account["annual_interest"] = interest_by_account["amount"] * (interest_by_account["interest_rate"] / 100)
        interest_by_account = interest_by_account.sort_values("annual_interest", ascending=False)
        interest_income_fig = go.Figure()
        interest_income_fig.add_trace(go.Bar(
            x=interest_by_account["account"],
            y=interest_by_account["annual_interest"],
            marker_color="#53d769",
            hovertemplate="%{x}<br>Annual Interest: £%{y:,.2f}<extra></extra>",
        ))
        interest_income_fig.update_layout(
            paper_bgcolor=chart_bg, plot_bgcolor=chart_bg,
            font_color="#8892b0",
            margin=dict(l=20, r=20, t=10, b=20),
            xaxis=dict(gridcolor="#2a2a4a", showgrid=False),
            yaxis=dict(gridcolor="#2a2a4a", showgrid=True, tickprefix="£"),
        )

    # ── Interest: Weighted Average Portfolio Rate (time series) ──
    if interest_df.empty:
        weighted_rate_fig = _empty_chart("No balance data yet")
    else:
        weighted_rate_fig = go.Figure()
        weighted_rate_fig.add_trace(go.Scatter(
            x=interest_df["date"],
            y=interest_df["weighted_rate"],
            mode="lines+markers",
            line=dict(color="#0fbcf9", width=3),
            marker=dict(size=7),
            hovertemplate="%{x|%Y-%m-%d}<br>Weighted Rate: %{y:.2f}%<extra></extra>",
        ))
        weighted_rate_fig.update_layout(
            paper_bgcolor=chart_bg, plot_bgcolor=chart_bg,
            font_color="#8892b0",
            margin=dict(l=20, r=20, t=10, b=20),
            xaxis=dict(gridcolor="#2a2a4a", showgrid=True),
            yaxis=dict(gridcolor="#2a2a4a", showgrid=True, ticksuffix="%"),
            hovermode="x unified",
        )

    # ── Interest: Projected Monthly Interest Income (time series) ──
    if interest_df.empty:
        monthly_interest_fig = _empty_chart("No balance data yet")
    else:
        monthly_interest_fig = go.Figure()
        monthly_interest_fig.add_trace(go.Scatter(
            x=interest_df["date"],
            y=interest_df["monthly_interest"],
            mode="lines+markers",
            line=dict(color="#ffd32a", width=3),
            marker=dict(size=7),
            fill="tozeroy",
            fillcolor="rgba(255,211,42,0.15)",
            hovertemplate="%{x|%Y-%m-%d}<br>Projected Monthly Interest: £%{y:,.2f}<extra></extra>",
        ))
        monthly_interest_fig.update_layout(
            paper_bgcolor=chart_bg, plot_bgcolor=chart_bg,
            font_color="#8892b0",
            margin=dict(l=20, r=20, t=10, b=20),
            xaxis=dict(gridcolor="#2a2a4a", showgrid=True),
            yaxis=dict(gridcolor="#2a2a4a", showgrid=True, tickprefix="£"),
            hovermode="x unified",
        )

    # ── Interest: Contribution by Account Type ──
    if balances.empty or latest.empty:
        interest_type_fig = _empty_chart("No balance data yet")
    else:
        interest_by_type = latest.copy()
        interest_by_type["annual_interest"] = interest_by_type["amount"] * (interest_by_type["interest_rate"] / 100)
        by_type_interest = interest_by_type.groupby("type", as_index=False)["annual_interest"].sum().sort_values("annual_interest", ascending=False)
        bar_colors = [colors[i % len(colors)] for i in range(len(by_type_interest))]
        interest_type_fig = go.Figure(go.Bar(
            x=by_type_interest["type"],
            y=by_type_interest["annual_interest"],
            marker_color=bar_colors,
            hovertemplate="%{x}<br>Annual Interest: £%{y:,.2f}<extra></extra>",
        ))
        interest_type_fig.update_layout(
            paper_bgcolor=chart_bg, plot_bgcolor=chart_bg,
            font_color="#8892b0",
            margin=dict(l=20, r=20, t=10, b=20),
            xaxis=dict(gridcolor="#2a2a4a", showgrid=False),
            yaxis=dict(gridcolor="#2a2a4a", showgrid=True, tickprefix="£"),
        )

    # ── Interest: Rate vs Balance ──
    if balances.empty or latest.empty:
        rate_vs_balance_fig = _empty_chart("No balance data yet")
    else:
        scatter_df = latest.copy()
        scatter_df["annual_interest"] = scatter_df["amount"] * (scatter_df["interest_rate"] / 100)
        bubble_sizes = scatter_df["annual_interest"].abs()
        if bubble_sizes.max() > 0:
            sizes = (bubble_sizes / bubble_sizes.max()) * 35 + 10
        else:
            sizes = pd.Series([14] * len(scatter_df))
        rate_vs_balance_fig = go.Figure()
        rate_vs_balance_fig.add_trace(go.Scatter(
            x=scatter_df["interest_rate"],
            y=scatter_df["amount"],
            mode="markers+text",
            text=scatter_df["account"],
            textposition="top center",
            marker=dict(
                size=sizes.tolist(),
                color=scatter_df["annual_interest"],
                colorscale="Viridis",
                showscale=True,
                colorbar=dict(title="Annual Interest £"),
                line=dict(color="#0f1117", width=1),
            ),
            customdata=scatter_df[["type", "annual_interest"]],
            hovertemplate=(
                "%{text}<br>"
                "Rate: %{x:.2f}%<br>"
                "Balance: £%{y:,.2f}<br>"
                "Type: %{customdata[0]}<br>"
                "Annual Interest: £%{customdata[1]:,.2f}<extra></extra>"
            ),
        ))
        rate_vs_balance_fig.update_layout(
            paper_bgcolor=chart_bg, plot_bgcolor=chart_bg,
            font_color="#8892b0",
            margin=dict(l=20, r=20, t=10, b=20),
            xaxis=dict(title="Interest Rate (%)", gridcolor="#2a2a4a", showgrid=True),
            yaxis=dict(title="Balance (£)", gridcolor="#2a2a4a", showgrid=True, tickprefix="£"),
        )

    # ── Accounts Table ──
    if accounts.empty:
        acc_table = html.P("No accounts added yet.", style={"color": "#8892b0"})
    else:
        acc_table = dash_table.DataTable(
            id="accounts-datatable",
            data=accounts.to_dict("records"),
            columns=[
                {"name": "ID", "id": "id", "editable": False},
                {"name": "Name", "id": "name", "editable": True},
                {"name": "Type", "id": "type", "editable": True, "presentation": "dropdown"},
                {"name": "Institution", "id": "institution", "editable": True},
                {"name": "Interest Rate (% APR)", "id": "interest_rate", "editable": True, "type": "numeric", "format": {"specifier": ",.2f"}},
            ],
            editable=True,
            row_selectable="multi",
            selected_rows=[],
            sort_action="native",
            sort_mode="multi",
            dropdown={
                "type": {
                    "options": [{"label": t, "value": t} for t in ACCOUNT_TYPES],
                },
            },
            style_table={"overflowX": "auto"},
            style_header={
                "backgroundColor": "#0f1117", "color": "#e94560", "fontWeight": "500",
                "border": "1px solid #2a2a4a", "cursor": "pointer",
            },
            style_cell={
                "backgroundColor": "#1a1a2e", "color": "#e0e0e0",
                "border": "1px solid #2a2a4a", "padding": "10px", "textAlign": "left",
            },
            style_data_conditional=[
                {"if": {"row_index": "odd"}, "backgroundColor": "#161630"},
                {"if": {"state": "selected"}, "backgroundColor": "#2a1a3e", "border": "1px solid #e94560"},
                {"if": {"state": "active"}, "backgroundColor": "#0f1117", "border": "2px solid #0fbcf9", "color": "#ffffff", "cursor": "text"},
            ],
            css=[
                {"selector": ".dash-cell.focused", "rule": "color: #ffffff !important; cursor: text !important;"},
                {"selector": "input.dash-cell-value", "rule": "color: #ffffff !important; caret-color: #0fbcf9 !important; background-color: #0f1117 !important; cursor: text !important; font-size: 14px !important; min-width: 40px !important;"},
                {"selector": ".Select-value-label", "rule": "color: #e0e0e0 !important;"},
                {"selector": "tr:not(.row-selected):hover td.dash-cell", "rule": "background-color: inherit;"},
            ],
        )

    # ── Balances Table ──
    if balances.empty:
        bal_table = html.P("No balances logged yet.", style={"color": "#8892b0"})
        bal_store_data = []
    else:
        bal_display = balances[["id", "account", "type", "date", "amount"]].copy()
        bal_display["date"] = bal_display["date"].dt.strftime("%Y-%m-%d")
        bal_store_data = bal_display.to_dict("records")
        bal_table = dash_table.DataTable(
            id="balances-datatable",
            data=bal_display.to_dict("records"),
            columns=[
                {"name": "ID", "id": "id", "editable": False},
                {"name": "Account", "id": "account", "editable": False},
                {"name": "Type", "id": "type", "editable": False},
                {"name": "Date", "id": "date", "editable": True},
                {"name": "Amount (£)", "id": "amount", "editable": True, "type": "numeric", "format": {"specifier": ",.2f"}},
            ],
            editable=True,
            row_selectable="multi",
            selected_rows=[],
            sort_action="native",
            sort_mode="multi",
            style_table={"overflowX": "auto"},
            style_header={
                "backgroundColor": "#0f1117", "color": "#e94560", "fontWeight": "500",
                "border": "1px solid #2a2a4a", "cursor": "pointer",
            },
            style_cell={
                "backgroundColor": "#1a1a2e", "color": "#e0e0e0",
                "border": "1px solid #2a2a4a", "padding": "10px", "textAlign": "left",
            },
            style_data_conditional=[
                {"if": {"row_index": "odd"}, "backgroundColor": "#161630"},
                {"if": {"state": "selected"}, "backgroundColor": "#2a1a3e", "border": "1px solid #e94560"},
                {"if": {"state": "active"}, "backgroundColor": "#0f1117", "border": "2px solid #0fbcf9", "color": "#ffffff", "cursor": "text"},
            ],
            css=[
                {"selector": ".dash-cell.focused", "rule": "color: #ffffff !important; cursor: text !important;"},
                {"selector": "input.dash-cell-value", "rule": "color: #ffffff !important; caret-color: #0fbcf9 !important; background-color: #0f1117 !important; cursor: text !important; font-size: 14px !important; min-width: 40px !important;"},
                {"selector": "tr:not(.row-selected):hover td.dash-cell", "rule": "background-color: inherit;"},
            ],
            page_size=10,
        )

    acc_store_data = accounts.to_dict("records") if not accounts.empty else []
    return (
        account_options,
        cards,
        nw_fig,
        alloc_fig,
        interest_income_fig,
        weighted_rate_fig,
        monthly_interest_fig,
        interest_type_fig,
        rate_vs_balance_fig,
        acc_table,
        bal_table,
        acc_store_data,
        bal_store_data,
    )


# ── Callback: Save Account Edits ────────────────────────────────────────────

@callback(
    Output("accounts-edit-msg", "children"),
    Input("save-accounts-btn", "n_clicks"),
    State("accounts-table", "children"),
    prevent_initial_call=True,
)
def save_account_edits(n_clicks, table_children):
    if not table_children or not isinstance(table_children, dict):
        return html.Span("No data to save.", style={"color": "#ff6b6b"})
    try:
        data = table_children.get("props", {}).get("data", [])
        if not data:
            return html.Span("No data to save.", style={"color": "#ff6b6b"})
        conn = get_db()
        for row in data:
            conn.execute(
                "UPDATE accounts SET name=?, type=?, institution=?, interest_rate=? WHERE id=?",
                (
                    row["name"],
                    row["type"],
                    row.get("institution", ""),
                    0 if row.get("interest_rate") is None else float(row.get("interest_rate")),
                    row["id"],
                ),
            )
        conn.commit()
        conn.close()
        return html.Span(f"Saved {len(data)} account(s)!", style={"color": "#53d769"})
    except Exception as e:
        return html.Span(f"Error: {e}", style={"color": "#ff6b6b"})


# ── Callback: Delete Selected Accounts ──────────────────────────────────────

@callback(
    Output("accounts-edit-msg", "children", allow_duplicate=True),
    Input("delete-accounts-btn", "n_clicks"),
    State("accounts-table", "children"),
    prevent_initial_call=True,
)
def delete_accounts(n_clicks, table_children):
    if not table_children or not isinstance(table_children, dict):
        return html.Span("No data.", style={"color": "#ff6b6b"})
    try:
        props = table_children.get("props", {})
        data = props.get("data", [])
        selected = props.get("selected_rows", [])
        if not selected:
            return html.Span("Select rows to delete first (click the checkboxes).", style={"color": "#ffd32a"})
        conn = get_db()
        deleted = 0
        for idx in selected:
            if idx < len(data):
                row_id = data[idx]["id"]
                conn.execute("DELETE FROM balances WHERE account_id=?", (row_id,))
                conn.execute("DELETE FROM accounts WHERE id=?", (row_id,))
                deleted += 1
        conn.commit()
        conn.close()
        return html.Span(f"Deleted {deleted} account(s) and their balances.", style={"color": "#53d769"})
    except Exception as e:
        return html.Span(f"Error: {e}", style={"color": "#ff6b6b"})


# ── Callback: Save Balance Edits ────────────────────────────────────────────

@callback(
    Output("balances-edit-msg", "children"),
    Input("save-balances-btn", "n_clicks"),
    State("balances-table", "children"),
    prevent_initial_call=True,
)
def save_balance_edits(n_clicks, table_children):
    if not table_children or not isinstance(table_children, dict):
        return html.Span("No data to save.", style={"color": "#ff6b6b"})
    try:
        data = table_children.get("props", {}).get("data", [])
        if not data:
            return html.Span("No data to save.", style={"color": "#ff6b6b"})
        conn = get_db()
        for row in data:
            conn.execute(
                "UPDATE balances SET date=?, amount=? WHERE id=?",
                (row["date"], row["amount"], row["id"]),
            )
        conn.commit()
        conn.close()
        return html.Span(f"Saved {len(data)} balance(s)!", style={"color": "#53d769"})
    except Exception as e:
        return html.Span(f"Error: {e}", style={"color": "#ff6b6b"})


# ── Callback: Delete Selected Balances ──────────────────────────────────────

@callback(
    Output("balances-edit-msg", "children", allow_duplicate=True),
    Input("delete-balances-btn", "n_clicks"),
    State("balances-table", "children"),
    prevent_initial_call=True,
)
def delete_balances(n_clicks, table_children):
    if not table_children or not isinstance(table_children, dict):
        return html.Span("No data.", style={"color": "#ff6b6b"})
    try:
        props = table_children.get("props", {})
        data = props.get("data", [])
        selected = props.get("selected_rows", [])
        if not selected:
            return html.Span("Select rows to delete first (click the checkboxes).", style={"color": "#ffd32a"})
        conn = get_db()
        deleted = 0
        for idx in selected:
            if idx < len(data):
                row_id = data[idx]["id"]
                conn.execute("DELETE FROM balances WHERE id=?", (row_id,))
                deleted += 1
        conn.commit()
        conn.close()
        return html.Span(f"Deleted {deleted} balance(s).", style={"color": "#53d769"})
    except Exception as e:
        return html.Span(f"Error: {e}", style={"color": "#ff6b6b"})


# ── Shared button styles ─────────────────────────────────────────────────────

_UNDO_BTN_VISIBLE = {
    "backgroundColor": "#ffd32a", "color": "#0f1117", "border": "none",
    "padding": "8px 18px", "borderRadius": "6px", "cursor": "pointer",
    "fontSize": "0.85rem", "marginRight": "10px", "display": "inline-block",
}
_UNDO_BTN_HIDDEN = {**_UNDO_BTN_VISIBLE, "display": "none"}

_SAVE_BTN_VISIBLE = {
    "backgroundColor": "#53d769", "color": "white", "border": "none",
    "padding": "8px 18px", "borderRadius": "6px", "cursor": "pointer",
    "fontSize": "0.85rem", "marginRight": "10px", "display": "inline-block",
}
_SAVE_BTN_HIDDEN = {**_SAVE_BTN_VISIBLE, "display": "none"}

_DELETE_BTN_VISIBLE = {
    "backgroundColor": "#ff6b6b", "color": "white", "border": "none",
    "padding": "8px 18px", "borderRadius": "6px", "cursor": "pointer",
    "fontSize": "0.85rem", "display": "inline-block",
}
_DELETE_BTN_HIDDEN = {**_DELETE_BTN_VISIBLE, "display": "none"}


def _has_data_changes(data, original_data):
    """Compare rows ignoring display order so native sorting never counts as a change."""
    if original_data is None or data is None:
        return False
    if len(data) != len(original_data):
        return True
    key = lambda r: r.get("id", 0)
    return sorted(data, key=key) != sorted(original_data, key=key)


# ── Callback: Toggle Accounts edit buttons (Undo + Save) ─────────────────────

@callback(
    Output("undo-accounts-btn", "style"),
    Output("save-accounts-btn", "style"),
    Input("accounts-datatable", "data"),
    State("accounts-original-data", "data"),
    prevent_initial_call=True,
)
def toggle_accounts_edit_btns(data, original_data):
    has_changes = _has_data_changes(data, original_data)
    return (
        _UNDO_BTN_VISIBLE if has_changes else _UNDO_BTN_HIDDEN,
        _SAVE_BTN_VISIBLE if has_changes else _SAVE_BTN_HIDDEN,
    )


# ── Callback: Toggle Accounts Delete button ──────────────────────────────────

@callback(
    Output("delete-accounts-btn", "style"),
    Input("accounts-datatable", "selected_rows"),
    prevent_initial_call=True,
)
def toggle_delete_accounts(selected_rows):
    return _DELETE_BTN_VISIBLE if selected_rows else _DELETE_BTN_HIDDEN


# ── Callback: Undo Account Edits ─────────────────────────────────────────────
# Triggers refresh_dashboard (re-reads DB) instead of writing to datatable.data
# directly — avoids conflicting with sort_action="native" which also owns that prop.

@callback(
    Output("accounts-edit-msg", "children", allow_duplicate=True),
    Input("undo-accounts-btn", "n_clicks"),
    prevent_initial_call=True,
)
def undo_account_edits(_):
    return html.Span("Changes undone.", style={"color": "#ffd32a"})


# ── Callback: Toggle Balances edit buttons (Undo + Save) ─────────────────────

@callback(
    Output("undo-balances-btn", "style"),
    Output("save-balances-btn", "style"),
    Input("balances-datatable", "data"),
    State("balances-original-data", "data"),
    prevent_initial_call=True,
)
def toggle_balances_edit_btns(data, original_data):
    has_changes = _has_data_changes(data, original_data)
    return (
        _UNDO_BTN_VISIBLE if has_changes else _UNDO_BTN_HIDDEN,
        _SAVE_BTN_VISIBLE if has_changes else _SAVE_BTN_HIDDEN,
    )


# ── Callback: Toggle Balances Delete button ──────────────────────────────────

@callback(
    Output("delete-balances-btn", "style"),
    Input("balances-datatable", "selected_rows"),
    prevent_initial_call=True,
)
def toggle_delete_balances(selected_rows):
    return _DELETE_BTN_VISIBLE if selected_rows else _DELETE_BTN_HIDDEN


# ── Callback: Undo Balance Edits ─────────────────────────────────────────────

@callback(
    Output("balances-edit-msg", "children", allow_duplicate=True),
    Input("undo-balances-btn", "n_clicks"),
    prevent_initial_call=True,
)
def undo_balance_edits(_):
    return html.Span("Changes undone.", style={"color": "#ffd32a"})


# ── Run ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=8050)
