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
            institution TEXT
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
                                    html.Button("Save Changes", id="save-accounts-btn", n_clicks=0, style={
                                        "backgroundColor": "#53d769", "color": "white", "border": "none",
                                        "padding": "8px 18px", "borderRadius": "6px", "cursor": "pointer",
                                        "fontSize": "0.85rem", "marginRight": "10px",
                                    }),
                                    html.Button("Delete Selected", id="delete-accounts-btn", n_clicks=0, style={
                                        "backgroundColor": "#ff6b6b", "color": "white", "border": "none",
                                        "padding": "8px 18px", "borderRadius": "6px", "cursor": "pointer",
                                        "fontSize": "0.85rem",
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
                                    html.Button("Save Changes", id="save-balances-btn", n_clicks=0, style={
                                        "backgroundColor": "#53d769", "color": "white", "border": "none",
                                        "padding": "8px 18px", "borderRadius": "6px", "cursor": "pointer",
                                        "fontSize": "0.85rem", "marginRight": "10px",
                                    }),
                                    html.Button("Delete Selected", id="delete-balances-btn", n_clicks=0, style={
                                        "backgroundColor": "#ff6b6b", "color": "white", "border": "none",
                                        "padding": "8px 18px", "borderRadius": "6px", "cursor": "pointer",
                                        "fontSize": "0.85rem",
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


# ── Callback: Add Account ───────────────────────────────────────────────────

@callback(
    Output("account-msg", "children"),
    Output("account-name", "value"),
    Output("account-type", "value"),
    Output("account-institution", "value"),
    Input("add-account-btn", "n_clicks"),
    State("account-name", "value"),
    State("account-type", "value"),
    State("account-institution", "value"),
    prevent_initial_call=True,
)
def add_account(n, name, acc_type, institution):
    if not name or not acc_type:
        return html.Span("Please fill in name and type.", style={"color": "#ff6b6b"}), dash.no_update, dash.no_update, dash.no_update
    conn = get_db()
    conn.execute("INSERT INTO accounts (name, type, institution) VALUES (?, ?, ?)", (name, acc_type, institution or ""))
    conn.commit()
    conn.close()
    return html.Span(f"Added '{name}'!", style={"color": "#53d769"}), "", None, ""


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
    Output("accounts-table", "children"),
    Output("balances-table", "children"),
    Input("account-msg", "children"),
    Input("balance-msg", "children"),
    Input("accounts-edit-msg", "children"),
    Input("balances-edit-msg", "children"),
)
def refresh_dashboard(*_):
    conn = get_db()

    # ── Accounts dropdown ──
    accounts = pd.read_sql("SELECT * FROM accounts", conn)
    account_options = [{"label": f"{r['name']} ({r['type']})", "value": r["id"]} for _, r in accounts.iterrows()]

    # ── Balances ──
    balances = pd.read_sql("""
        SELECT b.id, a.name as account, a.type, b.date, b.amount
        FROM balances b JOIN accounts a ON b.account_id = a.id
        ORDER BY b.date
    """, conn)
    conn.close()

    # ── Summary cards ──
    chart_bg = "#1a1a2e"
    colors = ["#e94560", "#0fbcf9", "#53d769", "#ffd32a"]

    if balances.empty:
        cards = [
            make_card("Net Worth", "£0.00"),
            make_card("Accounts", str(len(accounts)), "#0fbcf9"),
            make_card("Latest Entry", "—", "#53d769"),
            make_card("Balance Entries", "0", "#ffd32a"),
        ]
    else:
        latest = balances.sort_values("date").drop_duplicates("account", keep="last")
        net_worth = latest["amount"].sum()
        cards = [
            make_card("Net Worth", f"£{net_worth:,.2f}"),
            make_card("Accounts", str(len(accounts)), "#0fbcf9"),
            make_card("Latest Entry", balances["date"].max(), "#53d769"),
            make_card("Balance Entries", str(len(balances)), "#ffd32a"),
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
        balances["date"] = pd.to_datetime(balances["date"])
        # Get all unique dates, calculate net worth at each date using most recent balance per account
        all_dates = sorted(balances["date"].unique())
        nw_data = []
        for d in all_dates:
            snap = balances[balances["date"] <= d].sort_values("date").drop_duplicates("account", keep="last")
            nw_data.append({"date": d, "net_worth": snap["amount"].sum()})
        nw_df = pd.DataFrame(nw_data)

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
        latest = balances.sort_values("date").drop_duplicates("account", keep="last")
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
                {"selector": "input.dash-cell-value", "rule": "color: #ffffff !important; caret-color: #0fbcf9 !important; background-color: #0f1117 !important; cursor: text !important; font-size: 14px !important;"},
            ],
        )

    # ── Balances Table ──
    if balances.empty:
        bal_table = html.P("No balances logged yet.", style={"color": "#8892b0"})
    else:
        bal_display = balances[["id", "account", "type", "date", "amount"]].copy()
        bal_display["date"] = bal_display["date"].dt.strftime("%Y-%m-%d")
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
                {"selector": "input.dash-cell-value", "rule": "color: #ffffff !important; caret-color: #0fbcf9 !important; background-color: #0f1117 !important; cursor: text !important; font-size: 14px !important;"},
            ],
            page_size=10,
        )

    return account_options, cards, nw_fig, alloc_fig, acc_table, bal_table


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
                "UPDATE accounts SET name=?, type=?, institution=? WHERE id=?",
                (row["name"], row["type"], row.get("institution", ""), row["id"]),
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


# ── Run ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=8050)
