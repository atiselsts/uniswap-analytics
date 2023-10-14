#!/usr/bin/env python

#
# This script gets liquidity in the pool, at the start of every day
#
# Warning: it assumes the pool is USDC/WETH
#

import os

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
data_dir = os.path.join(self_dir, "data", f"uniswap-v{VERSION}-swaps", YEAR)

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
            break
    return result


def main():
    if VERSION == 2:
        contract = web3.eth.contract(address=web3.to_checksum_address(POOL), abi=v2_pool_abi)

    with open(f"reserves-v{VERSION}-{YEAR}-{POOL}.csv", "w") as outf:
        for filename in sorted(os.listdir(data_dir)):
            if "-swaps.csv" in filename:
                tx = load_csv(filename)
                blocknum = int(tx[0][1])
                if VERSION == 2:
                    reserves = contract.functions.getReserves().call(block_identifier=blocknum)
                    reserve_usdc = reserves[0]
                    reserve_weth = reserves[1]
                    print(filename, reserve_usdc / 1e6, reserve_weth / 1e18)
                    outf.write(f"{reserve_usdc},{reserve_weth}\n")



if __name__ == "__main__":
    main()
