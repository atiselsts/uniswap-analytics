#!/usr/bin/env python

#
# This script get transaction hashes from the events.
#
# Warning: for now, always assumes that one event - one tx.
# This is almost certainly true for all swaps of major coins.

import os

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
            result.append(fields[-1])
    return result


def main():
    with open(f"tx-v{VERSION}-{YEAR}-{POOL}.csv", "w") as outf:
        for filename in sorted(os.listdir(data_dir)):
            if "-swaps.csv" in filename:
                txs = load_csv(filename)
                for tx in txs:
                    outf.write(tx)
                    outf.write('\n')




if __name__ == "__main__":
    main()
