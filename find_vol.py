from math import sqrt, exp, log, pi
from scipy.stats import norm
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import warnings

warnings.filterwarnings("ignore")

#   Function to calculate the values of 21 and d2 as well as the call
#   price.  To extend to puts, one could just add a function that
#   calculates the put price, or combine calls and puts into a single
#   function that takes an argument specifying which type of contract one
#   is dealing with.
def d(sigma, S, K, r, t):
    d1 = 1 / (sigma * sqrt(t)) * ( log(S/K) + (r + sigma**2/2) * t)
    d2 = d1 - sigma * sqrt(t)
    return d1, d2

def call_price(sigma, S, K, r, t, d1, d2):
    C = norm.cdf(d1) * S - norm.cdf(d2) * K * exp(-r * t)
    return C


#  Option parameters
S = 100.0
K = 105.0
t = 30.0 / 365.0
r = 0.01
C0 =2.30


#  Tolerances
def find_vol(S, K, t, r, C0):
    tol = 1e-3
    epsilon = 1

    #  Variables to log and manage number of iterations
    count = 0
    max_iter = 1000

    #  We need to provide an initial guess for the root of our function
    vol = 0.50

    while epsilon > tol:
        #  Count how many iterations and make sure while loop doesn't run away
        count += 1
        if count >= max_iter:
            print('Breaking on count')
            break

        #  Log the value previously calculated to computer percent change
        #  between iterations
        orig_vol = vol

        #  Calculate the vale of the call price
        d1, d2 = d(vol, S, K, r, t)
        function_value = call_price(vol, S, K, r, t, d1, d2) - C0

        #  Calculate vega, the derivative of the price with respect to
        #  volatility
        vega = S * norm.pdf(d1) * sqrt(t)

        #  Update for value of the volatility
        vol = -function_value / vega + vol

        #  Check the percent change between current and last iteration
        epsilon = abs( (vol - orig_vol) / orig_vol )

    return vol

volatilities = []
df = pd.read_csv('round-4-island-data-bottle/prices_round_4_day_1.csv', sep=';')
df_coconut = df[df['product'] == "COCONUT"]
df_coupon = df[df['product'] == "COCONUT_COUPON"]
df_coconut["mid_price_coconut"] = df_coconut["mid_price"]
df_coconut["prev_mid_price_coconut"] = df_coconut["mid_price_coconut"].shift(1)
df_coupon["mid_price_coupon"] = df_coupon["mid_price"]

df_coconut.reset_index(inplace=True)
df_coupon.reset_index(inplace=True)

df_both = pd.concat([df_coconut["mid_price_coconut"], df_coconut["prev_mid_price_coconut"], df_coupon["mid_price_coupon"]], axis=1)
log_returns = []
for idx, row in df_both.iterrows():
    volatilities.append(find_vol(row["mid_price_coconut"], 10000, 249/250, 0, row["mid_price_coupon"]))

print("Implied Volatility: ", np.mean(volatilities))