# app.py
from dash import Dash, dcc, html, Input, Output
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.express as px

# ---------- Load & prepare data ----------
df = pd.read_csv("data/pink_morsel_sales.csv")
df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
df = df.dropna(subset=["Date"]).sort_values("Date")
df["Sales"] = pd.to_numeric(df["Sales"], errors="coerce").fillna(0.0)

# Ensure Region values are lowercase (for matching with radio options)
df["Region"] = df["Region"].astype(str).str.strip().str.lower()

# precompute list of regions (from data) to validate choices where needed
available_regions = sorted(df["Region"].dropna().unique())

PRICE_HIKE_DATE = pd.to_datetime("2021-01-15")

# ---------- Helpers ----------
def compute_before_after(dframe, date_cut=PRICE_HIKE_DATE):
    before = dframe[dframe["Date"] < date_cut]["Sales"].sum()
    after = dframe[dframe["Date"] >= date_cut]["Sales"].sum()
    pct_change = None
    if before == 0 and after == 0:
        pct_change = 0.0
    elif before == 0:
        pct_change = float("inf")
    else:
        pct_change = (after - before) / before * 100.0
    return round(before, 2), round(after, 2), pct_change

def make_summary_card(before, after, pct):
    if pct == float("inf"):
        pct_str = "∞ % (before = 0)"
    else:
        pct_str = f"{pct:.2f}%"
    delta = after - before
    delta_str = f"{delta:,.2f}"
    return dbc.Card(
        dbc.CardBody([
            html.H5("Before vs After (Price Increase)", className="card-title"),
            html.P(f"Price increase date: {PRICE_HIKE_DATE.strftime('%Y-%m-%d')}", className="card-text"),
            html.Div([
                html.Div([html.H6("Total — before"), html.P(f"{before:,.2f}")], style={"marginRight": "24px"}),
                html.Div([html.H6("Total — after"), html.P(f"{after:,.2f}")], style={"marginRight": "24px"}),
                html.Div([html.H6("Change"), html.P(pct_str)], style={})
            ], style={"display":"flex", "alignItems":"center", "gap":"24px"})
        ]),
        className="shadow-sm summary-card"
    )

# ---------- Dash App ----------
app = Dash(__name__, external_stylesheets=[dbc.themes.LITERA])
app.title = "Pink Morsel Sales Visualiser"

# Radio options required by the task (lowercase labels)
RADIO_OPTIONS = [
    {"label": "North", "value": "north"},
    {"label": "East",  "value": "east"},
    {"label": "South", "value": "south"},
    {"label": "West",  "value": "west"},
    {"label": "All",   "value": "all"},
]

app.layout = dbc.Container([
    dbc.Row([
        dbc.Col(html.H1("Pink Morsel — Sales Visualiser"), width=12)
    ], className="my-3"),
    dbc.Row([
        dbc.Col(html.P(
            "Inspect daily sales for Pink Morsel and compare totals before and after the price increase on "
            f"{PRICE_HIKE_DATE.strftime('%Y-%m-%d')}. Use the region radio selector to focus on a single region or choose All for overall totals."
        ), width=12)
    ], className="mb-3"),
    dbc.Row([
        dbc.Col(
            dbc.Card([
                dbc.CardBody([
                    html.Label("Select region (radio)", className="control-label"),
                    dcc.RadioItems(
                        id="region-radio",
                        options=RADIO_OPTIONS,
                        value="all",
                        labelStyle={"display": "inline-block", "margin-right": "12px"},
                        inputStyle={"margin-right": "6px"}
                    ),
                    html.Br(),
                    html.Label("Date range", className="control-label"),
                    dcc.DatePickerRange(
                        id="date-range",
                        min_date_allowed=df["Date"].min().date(),
                        max_date_allowed=df["Date"].max().date(),
                        start_date=df["Date"].min().date(),
                        end_date=df["Date"].max().date(),
                        display_format="YYYY-MM-DD"
                    ),
                    html.Br(), html.Br(),
                    dbc.Checklist(
                        options=[{"label": "Show 7-day moving average", "value": "ma7"}],
                        value=[],
                        id="ma-toggle",
                        switch=True
                    ),
                    html.Br(),
                    dbc.Button("Reset filters", id="reset-btn", color="secondary", size="sm")
                ])
            ]), width=4
        ),
        dbc.Col(id="summary-col", width=8)
    ], className="mb-3"),
    dbc.Row([
        dbc.Col(dcc.Graph(id="sales-line", config={"displayModeBar": True}), width=12)
    ]),
    dbc.Row([
        dbc.Col(html.P("Tip: Hover to inspect values. The dashed red line marks the price increase date."),
                width=12, className="text-muted mt-2")
    ]),
], fluid=True)


# ---------- Callbacks ----------
@app.callback(
    Output("date-range", "start_date"),
    Output("date-range", "end_date"),
    Input("reset-btn", "n_clicks"),
    prevent_initial_call=True
)
def reset_filters(n):
    return df["Date"].min().date(), df["Date"].max().date()


@app.callback(
    Output("summary-col", "children"),
    Output("sales-line", "figure"),
    Input("region-radio", "value"),
    Input("date-range", "start_date"),
    Input("date-range", "end_date"),
    Input("ma-toggle", "value")
)
def update_visual(region_value, start_date, end_date, ma_values):
    # Region handling
    if region_value is None or region_value == "all":
        dff = df.copy()
    else:
        # filter, but also be robust if region not present in dataset
        dff = df[df["Region"] == region_value]

    # apply date filter
    if start_date:
        dff = dff[dff["Date"] >= pd.to_datetime(start_date)]
    if end_date:
        dff = dff[dff["Date"] <= pd.to_datetime(end_date)]

    # aggregate daily totals
    daily = dff.groupby("Date", as_index=False)["Sales"].sum().sort_values("Date")

    # compute before/after totals within current filtered window
    before, after, pct = compute_before_after(dff, PRICE_HIKE_DATE)
    summary = make_summary_card(before, after, pct)

    # build line figure
    fig = px.line(daily, x="Date", y="Sales",
                  title="Pink Morsel — Daily Sales",
                  labels={"Sales": "Sales (currency units)", "Date": "Date"},
                  template="plotly_white",
                  markers=True)

    # optionally add 7-day moving average
    if ma_values and "ma7" in ma_values and len(daily) >= 7:
        daily["MA7"] = daily["Sales"].rolling(7).mean()
        fig.add_scatter(x=daily["Date"], y=daily["MA7"], mode="lines",
                        name="7-day MA", line=dict(width=3, dash="dot"))

    # highlight price hike date
    fig.add_vline(x=PRICE_HIKE_DATE, line_dash="dash", line_color="red", line_width=2, opacity=0.8)
    top_y = daily["Sales"].max() if not daily["Sales"].isna().all() else 0
    fig.add_annotation(x=PRICE_HIKE_DATE, y=top_y, text="Price increase\n2021-01-15",
                       showarrow=False, yshift=10, bgcolor="rgba(255,255,255,0.7)")

    fig.update_layout(margin={"l": 60, "r": 20, "t": 60, "b": 100}, hovermode="x unified")
    fig.update_xaxes(tickformat="%Y-%m-%d", tickangle=-45)

    return summary, fig


# ---------- Run ----------
if __name__ == "__main__":
    app.run(debug=True)
