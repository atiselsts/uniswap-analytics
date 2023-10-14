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
import pandas as pd
from ing_theme_matplotlib import mpl_style
from math import sqrt

pl.rcParams["savefig.dpi"] = 200

PAIR = "ETH-USD"
PERIOD_START = "2023-01-01"
PERIOD_END = "2024-01-01"

DAYS_IN_YEAR = 365

def calculate_historical_vols(df, sessions_in_year):
    # calculate first log returns using the open
    log_returns = []
    log_returns.append(np.log(df.loc[0, 'Close'] / df.loc[0, 'Open']))
    # calculate all but first log returns using close to close
    for index in range(len(df) - 1):
        log_returns.append(np.log(df.loc[index + 1, 'Close'] / df.loc[index, 'Close']))
    df = df.assign(log_returns=log_returns)

    # log returns squared - using high and low - for Parkinson volatility
    high_low_log_returns_squared = []
    for index in range(len(df)):
        high_low_log_returns_squared.append(np.log(df.loc[index, 'High'] / df.loc[index, 'Low']) ** 2)
    df = df.assign(high_low_log_returns_squared=high_low_log_returns_squared)

    # calculate the 7-day standard deviation and vol
    if len(df) > 6:
        sd_7_day = [0] * 6
        vol_7_day = [0] * 6
        park_vol_7_day = [0] * 6
        for index in range(len(df) - 6):
            sd = np.std(df.loc[index:index + 6, 'log_returns'], ddof=1)
            sd_7_day.append(sd)
            vol_7_day.append(sd * np.sqrt(sessions_in_year))
            park_vol_7_day.append(np.sqrt(
                (1 / (4 * 7 * np.log(2)) * sum(df.loc[index:index + 6, 'high_low_log_returns_squared']))) * np.sqrt(
                sessions_in_year))
        df = df.assign(sd_7_day=sd_7_day)
        df = df.assign(vol_7_day=vol_7_day)
        df = df.assign(park_vol_7_day=park_vol_7_day)

    # calculate the 30-day standard deviation and vol
    if len(df) > 29:
        sd_30_day = [np.nan] * 29
        vol_30_day = [np.nan] * 29
        park_vol_30_day = [np.nan] * 29
        for index in range(len(df) - 29):
            sd = np.std(df.loc[index:index + 29, 'log_returns'], ddof=1)
            sd_30_day.append(sd)
            vol_30_day.append(sd * np.sqrt(sessions_in_year))
            park_vol_30_day.append(np.sqrt(
                (1 / (4 * 30 * np.log(2)) * sum(df.loc[index:index + 29, 'high_low_log_returns_squared']))) * np.sqrt(
                sessions_in_year))
        df = df.assign(sd_30_day=sd_30_day)
        df = df.assign(vol_30_day=vol_30_day)
        df = df.assign(park_vol_30_day=park_vol_30_day)

    return df


def get_sigma_and_mu(data):
    data['Log Returns'] = np.log(data['Close']/data['Close'].shift())
    daily_std = data['Log Returns'].std()
    daily_drift = data['Log Returns'].mean()
    return daily_std, daily_drift


def get_lvr(sigma, mu):
    return (sigma ** 2) / 8


def analyze(pair):
    data = yf.download(pair, start=PERIOD_START, end=PERIOD_END)
    data.to_csv(pair + ".csv")
    
    #print(data)
    num_days = len(data['Open'])
    sigma, mu = get_sigma_and_mu(data)
    sigma *= sqrt(DAYS_IN_YEAR)
    mu *= DAYS_IN_YEAR

    lvr = get_lvr(sigma, 0.0)
    lvr_with_mu = get_lvr(sigma, mu)

    price_returns = data['Close'][-1] / data['Open'][0]
    lp_returns = sqrt(price_returns)
    hold_value = (1 + price_returns) / 2
    lp_value = 1 * lp_returns
    il = (hold_value - lp_value) / hold_value

    print(f"{pair} sigma={sigma:.3f} mu={mu:.6f} lvr={lvr:.3f} lvr_with_mu={lvr_with_mu:.3f} R={price_returns:.3f} IL={il:.3f}")
    
    return 100 * data['Open'] / data['Open'][0]


def main():
    mpl_style(True)

    eth = analyze("ETH-USD")

    df = pd.read_csv('ETH-USD.csv')
    df['Date'] = pd.to_datetime(df['Date'])
    df = calculate_historical_vols(df, DAYS_IN_YEAR)
    print(df)

    df["vol_7_day"] = df["vol_7_day"] / np.sqrt(DAYS_IN_YEAR)
    df["lvr"] = (df["vol_7_day"] ** 2) / 8

    x = range(1, len(eth) + 1)

    fig, ax1 = pl.subplots()
    ax2 = ax1.twinx()

    ax1.plot(x, 100 * df["vol_7_day"], color='orange')
    ax2.plot(x, 10_000 * df["lvr"], color='red')
    pl.ylabel("Volatility $\sigma$, %")
    ax1.set_xlabel('Day in 2023')
    ax1.set_ylabel('Daily volatility $\sigma$, %', color='orange')
    ax2.set_ylabel('Daily LVR, bps', color='red')
    pl.legend()
    pl.savefig("2023-lvr-and-volatility.png", bbox_inches='tight')
    pl.close()




if __name__ == "__main__":
    main()
