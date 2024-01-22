#!/usr/bin/env python

#
# This script downloads BTC and ETH price data from yfinance, for offline use. 
#

import yfinance as yf
import pandas as pd
import os

DIR = os.path.join("data", f"cex-prices")

PERIOD_START = "2020-01-01"
PERIOD_END = "2024-01-01"

def download(symbol):
    pair = symbol + "-USD" 
    data = yf.download(pair, start=PERIOD_START, end=PERIOD_END)
    print(data)
    filename = os.path.join(DIR, pair + ".csv")
    data.to_csv(filename)

def main():
    download("ETH")
    download("BTC")




if __name__ == "__main__":
    main()
