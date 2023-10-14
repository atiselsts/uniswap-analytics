#!/usr/bin/env python

#
# This script analyzes transaction stats by sampling a random subset of tx
#

import os
import random

from web3 import Web3

URL = os.getenv("INFURA_URL_MAINNET")
web3 = Web3(Web3.WebsocketProvider(URL))


NUM_TX = 1000

YEAR = os.getenv("YEAR")
if YEAR is None or len(YEAR) == 0:
    YEAR = "2023"

POOL = os.getenv("POOL")
if POOL is None or len(POOL) == 0:
    POOL = "0xb4e16d0168e52d35cacd2c6185b44281ec28c9dc" # v2 USDC/ETH
POOL = POOL.lower()

DECIMALS = os.getenv("DECIMALS")
if DECIMALS is None or len(DECIMALS) == 0:
    DECIMALS = 6 # for USDC
DECIMALS = int(DECIMALS)

VERSION = os.getenv("VERSION")
if VERSION is None or len(VERSION) == 0:
    VERSION = 2

print(f"using pool {POOL} on Uniswap v{VERSION}, year {YEAR}, token0 decimals {DECIMALS}")

def load_csv(filename):
    result = []
    with open(filename) as f:
        f.readline() # skip the header
        for line in f.readlines():
            fields = line.strip().split(",")
            if len(fields) == 0:
                continue
            result.append(fields)
    return result

def tx_get_details(hash):
    receipt = web3.eth.get_transaction_receipt(hash)
    dst = receipt["to"]
    sender = receipt["from"]
    gas = receipt.gasUsed
    gas_price = receipt.effectiveGasPrice
    cost = web3.from_wei(gas * gas_price, "ether")
    print(dst, gas)
    return dst, sender, gas, gas_price, cost, hash


def main():
    random.seed(12345) # make it repeatable

    filename = f"tx-v{VERSION}-{YEAR}-{POOL}.csv"
    txs = load_csv(filename)
    tx_subset = random.sample(txs, NUM_TX)
    with open(f"tx-details-v{VERSION}-{YEAR}-{POOL}.csv", "w") as outf:   
        for tx, in tx_subset:
            result = tx_get_details(tx)
            s = ",".join([str(u) for u in result])
            outf.write(s)
            outf.write("\n")



if __name__ == "__main__":
    main()
