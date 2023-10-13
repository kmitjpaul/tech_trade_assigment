import dash
import pandas as pd
import plotly.express as px
from dash import dcc, html
from dash.dependencies import Input, Output

from src.constants import BINANCE_SYMBOLS_LIST
from src.influx import Repository
from src.settings import LOG_LEVEL
import numpy as np

app = dash.Dash(__name__)

app.layout = html.Div([
    html.Div([
        html.H1(
            children="Binance graph",
        ),
        html.P(
            children=(
                "Order book graph shows the relationship between the price per unit of cryptocurrency and the number of requests/offers. "
                "Price over time graph shows price bids and asks over time"
            ),
        ),
    ], style={'text-align': 'center'}),
    html.Div(
        [
            html.Div([
                html.Div([
                    dcc.Dropdown(BINANCE_SYMBOLS_LIST, 'BTCUSDT', id='symbols-dropdown'),
                    dcc.RadioItems(
                        id='radio-buttons-component',
                        options=[
                            {'label': '1 minute', 'value': '-1m'},
                            {'label': '1 hour', 'value': '-1h'},
                            {'label': '1 day', 'value': '-1d'},
                        ],
                        value='-1h',
                        inline=True,
                    ),
                ], style={'display': 'flex', 'flex-direction': 'column', 'gap': '1.5em'}),
                html.H1('Order book depth graph'),
                dcc.Graph(id='order-depth-graph'),
                html.H1('Price over time graph'),
                dcc.Graph(id='order-timeline-graph'),
                dcc.Interval(
                    id='interval-component',
                    interval=1000,
                    n_intervals=0
                ),
            ], style={'box-shadow': '#0000002b 1px 1px 10px 1px', 'padding': '2em', 'width': '45%'}),
        ], style={'display': 'flex', 'flex-direction': 'column', 'align-items': 'center'}
    )
])


@app.callback(Output('order-depth-graph', 'figure'), [
    Input('interval-component', 'n_intervals'),
    Input('radio-buttons-component', 'value'),
    Input('symbols-dropdown', 'value'),
    Input('order-depth-graph', 'relayoutData')
])
def update_depth_graph(_n_intervals: int, radio_button_value: str, symbols_dropdown_value: str, relayoutData):
    data = Repository().get_prices_and_times_by_time_range_start(radio_button_value, symbols_dropdown_value)

    df = pd.DataFrame(dict(
        price=data.prices,
        type=data.types,
    ))

    if len(df['price']):
        step_size = 100000
        bin_intervals = np.arange(min(df['price']), max(df['price']) + step_size, step_size)
        df['price_bin'] = pd.cut(df['price'], bin_intervals, include_lowest=True)

        grouped = df.groupby(['price_bin', 'type'], observed=False).agg({'price': ['mean', 'count']}).reset_index()
        grouped.columns = ['price_bin', 'type', 'averaged_unit_price', 'order_depth']
        df = grouped[grouped['order_depth'] != 0]

        fig = px.line(df, x="averaged_unit_price", y="order_depth", color='type')
    else:
        fig = px.line(df, x="price")

    return _process_figure(fig, relayoutData)


@app.callback(Output('order-timeline-graph', 'figure'), [
    Input('interval-component', 'n_intervals'),
    Input('radio-buttons-component', 'value'),
    Input('symbols-dropdown', 'value'),
    Input('order-timeline-graph', 'relayoutData')
])
def update_timeline_graph(_n_intervals: int, radio_button_value: str, symbols_dropdown_value: str, relayoutData):
    data = Repository().get_prices_and_times_by_time_range_start(radio_button_value, symbols_dropdown_value)

    df = pd.DataFrame(dict(
        price=data.prices,
        time=data.times,
        type=data.types,
    ))
    fig = px.line(df, x="time", y="price", color="type")

    return _process_figure(fig, relayoutData)


def _process_figure(fig, relayoutData):
    fig.update_xaxes(rangeslider_visible=True)

    # plotly bug when xaxis.range not in relayoutData, there is another key 'xaxis.range[0]' which causes exception
    if relayoutData:
        relayout_data = {}
        if 'xaxis.range' in relayoutData or 'autosize' in relayoutData:
            relayout_data = relayoutData
        elif 'xaxis.range[0]' in relayoutData and 'xaxis.range[1]' in relayoutData:
            relayout_data = {
                'xaxis.range': [relayoutData['xaxis.range[0]'], relayoutData['xaxis.range[1]']]
            }
        fig.update_layout(relayout_data)

    return fig


if __name__ == '__main__':
    app.run_server(debug=LOG_LEVEL == 'DEBUG', host='0.0.0.0')
