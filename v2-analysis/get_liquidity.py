#!/usr/bin/env python

#
# This script gets liquidity in the pool, at the start of every day
#

import os
import sys

sys.path.append("..")

from abi import v2_pool_abi
from web3 import Web3

URL = os.getenv("INFURA_URL_MAINNET")
web3 = Web3(Web3.WebsocketProvider(URL))

YEAR = os.getenv("YEAR")
if YEAR is None or len(YEAR) == 0:
    YEAR = "2023"

POOL = os.getenv("POOL")
if POOL is None or len(POOL) == 0:
    POOL = "0xb4e16d0168e52d35cacd2c6185b44281ec28c9dc" # v2 USDC/ETH
POOL = POOL.lower()

VERSION = os.getenv("VERSION")
if VERSION is None or len(VERSION) == 0:
    VERSION = 2

print(f"using pool {POOL} on Uniswap v{VERSION}, year {YEAR}")

self_dir = os.path.dirname(os.path.abspath(__file__))
data_dir = os.path.join(self_dir, "..", "data")

uni_data_dir = os.path.join(data_dir, f"uniswap-v{VERSION}-swaps", YEAR)
cex_price_dir = os.path.join(data_dir, "cex-prices")

def load_csv(filename):
    result = []
    with open(os.path.join(uni_data_dir, filename)) as f:
        f.readline() # skip the header
        for line in f.readlines():
            fields = line.strip().split(",")
            if len(fields) == 0:
                continue
#            pool = fields[2]
#            if pool != POOL:
#                continue
            result.append(fields)
            break
    return result


def load_prices(filename):
    result = {}
    with open(os.path.join(cex_price_dir, filename)) as f:
        f.readline() # skip the header
        for line in f.readlines():
            fields = line.strip().split(",")
            if len(fields) == 0:
                continue
            # save the open price
            result[fields[0]] = float(fields[1])
    return result


def main():
    if VERSION == 2:
        contract = web3.eth.contract(address=web3.to_checksum_address(POOL), abi=v2_pool_abi)

    prices_eth = load_prices("ETH-USD.csv")
    prices_btc = load_prices("BTC-USD.csv")
    if POOL == "0xb4e16d0168e52d35cacd2c6185b44281ec28c9dc":
        prices = prices_eth
    else:
        prices = prices_btc

    with open(f"reserves-v{VERSION}-{YEAR}-{POOL}.csv", "w") as outf:
        for filename in sorted(os.listdir(uni_data_dir)):
            if "-swaps.csv" in filename:
                date = filename[:10]
                tx = load_csv(filename)
                blocknum = int(tx[0][1])
                if VERSION == 2:
                    reserves = contract.functions.getReserves().call(block_identifier=blocknum)
                    if POOL == "0xb4e16d0168e52d35cacd2c6185b44281ec28c9dc":
                        # ETH
                        reserve_usdc = reserves[0]
                        reserve_volatile = reserves[1]
                        if date in prices:
                            volatile_price = prices[date]
                            total_value = reserve_usdc / 1e6 + reserve_volatile / 1e18 * eth_price
                        else:
                            # use pool's price
                            print("missing CEX price for", date)
                            total_value = 2 * reserve_usdc / 1e6
                        reserve_volatile = reserve_weth
                    else:
                        # BTC
                        reserve_volatile = reserves[0]
                        reserve_usdc = reserves[1]
                        if date in prices:
                            volatile_price = prices[date]
                            total_value = reserve_usdc / 1e6 + reserve_volatile / 1e8 * volatile_price
                        else:
                            # use pool's price
                            print("missing CEX price for", date)
                            total_value = 2 * reserve_usdc / 1e6

                    total_shares = contract.functions.totalSupply().call(block_identifier=blocknum)
                    value_per_share = total_value / total_shares
                    print(filename, reserve_usdc / 1e6)
                    outf.write(f"{reserve_usdc},{reserve_volatile},{total_value},{value_per_share},{volatile_price}\n")


if __name__ == "__main__":
    main()
