import pandas as pd
import talib

import plotly.graph_objects as go

df = pd.read_csv('round-1-island-data-bottle/prices_round_1_day_-2.csv', sep=';')
df = df[df['product'] == 'STARFRUIT']

df['ema'] = talib.EMA(df['mid_price'], timeperiod=10)

fig = go.Figure()
fig.add_trace(go.Scatter(x=df.index, y=df['ask_price_1'], name='Best Ask Price 1'))
fig.add_trace(go.Scatter(x=df.index, y=df['bid_price_1'], name='Best Bid Price 1'))
fig.add_trace(go.Scatter(x=df.index, y=df['ema'], name='EMA of Middle Price'))

fig.show()
