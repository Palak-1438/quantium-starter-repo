# app.py
from dash import Dash, dcc, html, Input, Output
import pandas as pd
import plotly.express as px

# --- Load and prepare data ---
df = pd.read_csv("data/pink_morsel_sales.csv")

# Ensure Date is datetime and sort
df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
df = df.dropna(subset=["Date"]).sort_values("Date")

# Basic aggregation: if multiple sales per date-region exist, sum them for plotting
# (keeps Region support if you want to filter)
agg_all = df.groupby(["Date"], as_index=False)["Sales"].sum()
regions = sorted(df["Region"].dropna().unique())

# --- App ---
app = Dash(__name__)
app.title = "Pink Morsel Sales Visualiser"

app.layout = html.Div(
    style={"fontFamily": "Arial, sans-serif", "maxWidth": "1000px", "margin": "auto", "padding": "20px"},
    children=[
        html.H1("Pink Morsel — Sales Over Time", style={"textAlign": "center"}),
        html.P(
            "Visualisation to inspect the effect of the price increase on 15 Jan 2021. "
            "Use the region filter to inspect individual regions or view overall sales.",
            style={"textAlign": "center", "color": "#555"}
        ),

        html.Div(
            style={"display": "flex", "gap": "16px", "alignItems": "center", "justifyContent": "center", "marginBottom": "10px"},
            children=[
                html.Label("Filter by region:", style={"marginRight": "8px"}),
                dcc.Dropdown(
                    id="region-filter",
                    options=[{"label": r, "value": r} for r in regions],
                    value=regions,  # default: all regions selected
                    multi=True,
                    placeholder="Select region(s)",
                    style={"minWidth": "300px"}
                )
            ]
        ),

        dcc.Graph(id="sales-line", config={"displayModeBar": True, "modeBarButtonsToAdd": ["drawline"]}),

        html.Div(
            style={"textAlign": "center", "marginTop": "12px", "color": "#333"},
            children=[
                html.Span("Price increase date: "),
                html.Strong("2021-01-15")
            ]
        )
    ],
)


@app.callback(
    Output("sales-line", "figure"),
    Input("region-filter", "value")
)
def update_line(selected_regions):
    # If selected_regions is a single string, convert to list
    if selected_regions is None:
        selected_regions = []
    if isinstance(selected_regions, str):
        selected_regions = [selected_regions]

    # Filter original df by region(s)
    if selected_regions:
        dff = df[df["Region"].isin(selected_regions)]
    else:
        dff = df.copy()

    # Aggregate sales by date
    dff = dff.groupby("Date", as_index=False)["Sales"].sum().sort_values("Date")

    # Create figure
    fig = px.line(
        dff,
        x="Date",
        y="Sales",
        title="Pink Morsel Sales (Daily)",
        labels={"Date": "Date", "Sales": "Sales (currency units)"},
        template="plotly_white",
        markers=True
    )

    # Make the x-axis tickformat friendly
    fig.update_xaxes(tickformat="%Y-%m-%d", tickangle= -45, dtick="M1")

    # Add vertical line to mark price increase date
    fig.add_vline(
        x=pd.to_datetime("2021-01-15"),
        line_dash="dash",
        line_color="red",
        line_width=2,
        annotation_text="Price increase (2021-01-15)",
        annotation_position="top right",
        opacity=0.8
    )

    # Slight layout tweaks
    fig.update_layout(
        margin={"l": 60, "r": 20, "t": 60, "b": 100},
        hovermode="x unified"
    )

    return fig


if __name__ == "__main__":
    app.run(debug=True)

