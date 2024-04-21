import pandas as pd
import numpy as np
import statistics
import matplotlib.pyplot as plt

def black_scholes_price(S, T, r, sigma, K = 10000):
    d1 = (np.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * np.sqrt(T))
    d2 = d1 - sigma * np.sqrt(T)
    return S * statistics.NormalDist().cdf(d1) - K * np.exp(-r * T) * statistics.NormalDist().cdf(d2)

df = pd.read_csv('round-4-island-data-bottle/prices_round_4_day_1.csv', sep=';')

df_coconut = df[df['product'] == "COCONUT"]
df_coupon = df[df['product'] == "COCONUT_COUPON"]
df_coconut.reset_index(drop=True, inplace=True)
df_coupon.reset_index(drop=True, inplace=True)

df_coconut["bs_price"] = df_coconut.apply(lambda x: black_scholes_price(x['mid_price'], 249/365, 0, 0.193), axis=1)

plt.plot(df_coconut['bs_price'], label='BS Price')
plt.plot(df_coupon['mid_price'], label='Coupon price')
plt.legend()
plt.show()