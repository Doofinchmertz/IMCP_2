import pandas as pd
import plotly.graph_objs as go

df = pd.read_csv('round-2-island-data-bottle/prices_round_2_day_1.csv', sep=';')

trace1 = go.Scatter(x=df['timestamp'], y=df['ORCHIDS'], mode='lines', name='prices', yaxis='y1')
trace2 = go.Scatter(x=df['timestamp'], y=df['SUNLIGHT'], mode='lines', name='sunlight', yaxis='y2')
trace3 = go.Scatter(x=df['timestamp'], y=df['HUMIDITY'], mode='lines', name='humidity', yaxis='y3')

layout = go.Layout(
    title='Variation of different parameters',
    yaxis=dict(
        title='prices',
        side='left',
        anchor='x'
    ),
    yaxis2=dict(
        title='sunlight',
        side='right',
        overlaying='y',
        anchor='x'
    ),
    yaxis3=dict(
        title='humidity',
        side='right',
        overlaying='y',
        anchor='free',
        position=0.95
    )
)

fig = go.Figure(data=[trace1, trace2, trace3], layout=layout)

fig.show()

