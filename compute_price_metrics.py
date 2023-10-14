#!/usr/bin/env python

#
# This script computes metrics related to asset price such as:
# 1) Volatility (sigma)
# 2) Price drift (mu)
# 3) Expected LVR
#

PAIR = "ETH-USD"
PERIOD_START = "2023-01-01"
PERIOD_END = "2023-10-01"

import yfinance as yf
import numpy as np
from math import sqrt

DAYS_IN_YEAR = 365

def get_sigma_and_mu(data):
    #print(len(data))
    data['Log Returns'] = np.log(data['Close']/data['Close'].shift())
    daily_std = data['Log Returns'].std()
    daily_drift = data['Log Returns'].mean()
    return daily_std, daily_drift

def get_lvr(sigma, mu):
    return (sigma ** 2) / 8

def main():
    data = yf.download(PAIR, start=PERIOD_START, end=PERIOD_END)
    print(data)
    num_days = len(data['Open'])
    sigma, mu = get_sigma_and_mu(data)
#    sigma *= sqrt(DAYS_IN_YEAR)
#    mu *= DAYS_IN_YEAR

    lvr = get_lvr(sigma, 0.0)
    lvr_with_mu = get_lvr(sigma, mu)

    print(f"sigma={sigma:.3f} mu={mu:.6f} lvr={lvr:.3f} lvr_with_mu={lvr_with_mu:.3f}")


if __name__ == "__main__":
    main()
