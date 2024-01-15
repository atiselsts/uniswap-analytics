#!/usr/bin/env python

#
# This script computes metrics related to asset price such as:
# 1) Volatility (sigma)
# 2) Price drift (mu)
# 3) Expected LVR
#

import yfinance as yf
import numpy as np
import matplotlib.pyplot as pl
from ing_theme_matplotlib import mpl_style
from math import sqrt

pl.rcParams["savefig.dpi"] = 200

#PAIR = "ETH-USD"
PAIR = "ETH-BTC"
PERIOD_START = "2023-01-01"
#PERIOD_END = "2023-02-01"
PERIOD_END = "2024-01-01"


DAYS_IN_YEAR = 365

def get_sigma_and_mu(data):
    #print(len(data))
    data['Log Returns'] = np.log(data['Close']/data['Close'].shift())
    daily_std = data['Log Returns'].std()
    daily_drift = data['Log Returns'].mean()
    return daily_std, daily_drift

def get_lvr(sigma, mu):
    return (sigma ** 2) / 8


def analyze(pair):
    data = yf.download(pair, start=PERIOD_START, end=PERIOD_END)
    #print(data)
    num_days = len(data['Open'])
    sigma, mu = get_sigma_and_mu(data)
    sigma *= sqrt(DAYS_IN_YEAR)
    mu *= DAYS_IN_YEAR

    lvr = get_lvr(sigma, 0.0)
    lvr_with_mu = get_lvr(sigma, mu)

    print(f"{pair} sigma={sigma:.3f} mu={mu:.6f} lvr={lvr:.3f} lvr_with_mu={lvr_with_mu:.3f}")
    return 100 * data['Open'] / data['Open'][0]


def main():
    mpl_style(True)

    eth = analyze("ETH-USD")
    btc = analyze("BTC-USD")
    eth_btc = analyze("ETH-BTC")

    x = range(1, len(eth) + 1)

    pl.figure()
    pl.plot(x, btc, label="BTC/USD")
    pl.plot(x, eth_btc, label="ETH/BTC")
    pl.plot(x, eth, label="ETH/USD")
    pl.ylabel("Relative value, %")
    pl.xlabel("Day in 2023")
    pl.legend()
    pl.axhline(100, color="white") #, [x[0], x[-1]])
    pl.ylim(0, 300)
    #pl.show()
    pl.savefig("2023-price-history.png", bbox_inches='tight')
    pl.close()




if __name__ == "__main__":
    main()
