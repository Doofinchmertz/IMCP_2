import pandas as pd
import talib

df = pd.read_csv('round-1-island-data-bottle/prices_round_1_day_-1.csv', sep=';')

df.drop(['day', 'bid_price_2', 'bid_volume_2', 'bid_price_3', 'bid_volume_3', 'ask_price_2', 'ask_volume_2', 'ask_price_3', 'ask_volume_3'], axis=1, inplace=True)
