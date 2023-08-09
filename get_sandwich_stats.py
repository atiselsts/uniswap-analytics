#!/usr/bin/env python

import os

YEAR = os.getenv("YEAR")
if YEAR is None or len(YEAR) == 0:
    YEAR = "2023"

POOL = os.getenv("POOL")
if POOL is None or len(POOL) == 0:
    POOL = "0x88e6a0c2ddd26feeb64f039a2c41296fcb3f5640" # USDC/ETH 0.05%
POOL = POOL.lower()

decimals = 6 # for USDC

# change this to get v2 swaps
VERSION = os.getenv("VERSION")
try:
    VERSION = int(VERSION)
except:
    VERSION = 3
if VERSION not in [2, 3]:
    print("Uniswap v2 or v3 supported")
    exit(-1)

self_dir = os.path.dirname(os.path.abspath(__file__))
data_dir = os.path.join(self_dir, "data", f"uniswap-v{VERSION}-swaps", YEAR)

not_sandwich = [
    "0x3fc91a3afd70395cd496c647d5a6cc9d4b2b7fad", # universal router
    "0xef1c6e67703c7bd7107eed8303fbe6ec2554bf6b", # old uni router
    "0x68b3465833fb72a70ecdf485e0e4c7bd8665fc45", # router 2
    "0x1111111254fb6c44bac0bed2854e76f90643097d", # 1inch
    "0xdef1c0ded9bec7f1a1670819833240f027b25eff", # 0x proxy
]

num_sandwich_tx = {}

def load_csv(filename):
    result = []
    with open(os.path.join(data_dir, filename)) as f:
        f.readline() # skip the header
        for line in f.readlines():
            fields = line.strip().split(",")
            if len(fields) == 0:
                continue
            pool = fields[2]
            if pool != POOL:
                continue
            result.append(fields)
    return result


# MEV sandwiching is defined as buy & sell in a single block
def account_for_mev(eth_buyers, eth_sellers, trades):
    sandwichers = set(eth_buyers.keys()).intersection(set(eth_sellers.keys()))
    traders = set(eth_buyers.keys()).symmetric_difference(set(eth_sellers.keys()))
    for address in sandwichers:
        if address in not_sandwich:
            flag = False
        else:
            flag = True
            num_sandwich_tx[address] = num_sandwich_tx.get(address, 0) + 1
        trades[flag] += eth_buyers.get(address, 0) + eth_sellers.get(address, 0)
    for address in traders:
        trades[False] += eth_buyers.get(address, 0) + eth_sellers.get(address, 0)

def classify_trades(trades, data):
    current_block = None # start from a fresh block
    eth_buyers = {}
    eth_sellers = {}

    # token0: USDC, token1: ETH
    for row in data:
        if VERSION == 2:
            (_, block, _, amount0_in, amount1_in, amount0_out, amount1_out, address, _) = row
            amount0_out = int(amount0_out)
            amount1_out = int(amount1_out)
            if amount0_out > 0:
                # selling ETH
                amount0 = -amount0_out
            elif amount1_out > 0:
                # buying ETH
                amount0 = int(amount0_in)
            else:
                amount0 = 0
        else:
            (_, block, _, amount0, amount1, address, _) = row
            amount0 = int(amount0)

        if current_block != block:
            current_block = block
            # account for MEV in the block
            account_for_mev(eth_buyers, eth_sellers, trades)
            # clean up state; look only at single-block MEV
            eth_buyers = {}
            eth_sellers = {}
        if amount0 < 0:
            # selling ETH, account for USDC volume, including the fee
            eth_sellers[address] = eth_sellers.get(address, 0) - amount0
        elif amount0 > 0:
            eth_buyers[address] = eth_buyers.get(address, 0) + amount0
        else:
            # ignore transactions with zero USDC output
            pass

    account_for_mev(eth_buyers, eth_sellers, trades)
    return trades


def main():
    # {True: sandwich_volume, False: other_trader_volume}
    trades = {True: 0, False: 0}
    for filename in sorted(os.listdir(data_dir)):
        if "-swaps.csv" in filename:
            data = load_csv(filename)
            classify_trades(trades, data)
    print(f"total USDC volume: {sum(trades.values()) / (10 ** decimals) * 1e-6:.0f} million")
    sandwich_proportion = trades[True] / sum(trades.values())    
    print(f"sandwich volume proportion: {100*sandwich_proportion:.2f}%")
    print("top sandwich traders by num tx:")
    sandwichers = sorted(list(num_sandwich_tx.items()), key=lambda x: x[1], reverse=True)
    for i in range(min(10, len(sandwichers))):
        print(sandwichers[i])

if __name__ == "__main__":
    main()
