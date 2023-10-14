#!/usr/bin/env python

#
# This script analyzes WBTC/USDC transactions in depth.
#
# The issue is in this transaction - Roe finance exploiter
# https://etherscan.io/tx/0x927b784148b60d5233e57287671cdf67d38e3e69e5b6d0ecacc7c1aeaa98985b
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


#timestamp,block,pool,tx_hash,type,field0,field1,field2,field3

def load_csv(filename):
    result = []
    with open(os.path.join(self_dir, filename)) as f:
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

def main():
    if VERSION == 2:
        contract = web3.eth.contract(address=web3.to_checksum_address(POOL), abi=v2_pool_abi)

    tx = load_csv("jan11.csv")
    for fields in tx:
        (timestamp, block, pool, tx_hash, event_type, field0, field1, field2, field3) = fields
        event_type = int(event_type)
        if event_type in [0, 1, 2]:
            print(tx_hash, field0, field1)

if __name__ == "__main__":
    main()
