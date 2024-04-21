import pandas as pd
import numpy as np

df0 = pd.read_csv("round-3-island-data-bottle/prices_round_3_day_0.csv", sep=";")
df1 = pd.read_csv("round-3-island-data-bottle/prices_round_3_day_1.csv", sep=";")
df2 = pd.read_csv("round-3-island-data-bottle/prices_round_3_day_2.csv", sep=";")
df = pd.concat([df0, df1, df2])


df_chocolate = df[df["product"] == "CHOCOLATE"]
df_strawberries = df[df["product"] == "STRAWBERRIES"]
df_roses = df[df["product"] == "ROSES"]
df_gift_basket = df[df["product"] == "GIFT_BASKET"]

df_chocolate.reset_index(drop=True, inplace=True)
df_strawberries.reset_index(drop=True, inplace=True)
df_roses.reset_index(drop=True, inplace=True)
df_gift_basket.reset_index(drop=True, inplace=True)

arr_spread = np.array(df_gift_basket['mid_price'] - 4*df_chocolate['mid_price'] - 6*df_strawberries['mid_price'] - df_roses['mid_price'])

print("Mean spread: ", np.mean(arr_spread), "Std spread: ", np.std(arr_spread))