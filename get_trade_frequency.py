#!/usr/bin/env python

#
# This script gets:
#  1) the avg / mean / std of trades per block
#  2) the % of blocks with at least 1 trade
#  3) the avg / mean / std of trade gaps between blocks
#

import os
import numpy as np

YEAR = os.getenv("YEAR")
if YEAR is None or len(YEAR) == 0:
    YEAR = "2023"

POOL = os.getenv("POOL")
if POOL is None or len(POOL) == 0:
    POOL = "0x88e6a0c2ddd26feeb64f039a2c41296fcb3f5640" # USDC/ETH 0.05%
POOL = POOL.lower()

DECIMALS = os.getenv("DECIMALS")
if DECIMALS is None or len(DECIMALS) == 0:
    DECIMALS = 6 # for USDC
DECIMALS = int(DECIMALS)

# change this to get v2 swaps
VERSION = os.getenv("VERSION")
try:
    VERSION = int(VERSION)
except:
    VERSION = 3
if VERSION not in [2, 3]:
    print("Uniswap v2 or v3 supported")
    exit(-1)

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
            result.append(fields)
    return result

def process_day(data, block_stats, gap_stats, last_block):
    in_block = 0
    for row in data:
        if VERSION == 3:
            block = int(row[1])

        if last_block is None:
            last_block = block

        if last_block == block:
            in_block += 1
        else:
            gap = block - last_block - 1
            gap_stats.append(gap)
            while last_block < block:
                block_stats.append(in_block)
                in_block = 0
                last_block += 1
            in_block = 1

    return last_block

def main():
    block_stats = [] # trades per each block
    gap_stats = []   # num of blocks w/o trades
    last_block = None
    for filename in sorted(os.listdir(data_dir)):
        if "-swaps.csv" in filename:
            print(filename)
            data = load_csv(filename)
            last_block = process_day(data, block_stats, gap_stats, last_block)

    num_blocks = len(block_stats)
    median = sorted(block_stats)[num_blocks // 2]
    print(f"trades per block: avg={np.mean(block_stats):.2f} median={median} std={np.std(block_stats):.2f}")

    num_traded_blocks = sum([1 if u > 0 else 0 for u in block_stats])
    print(f"% of blocks with some trades: {100*num_traded_blocks/num_blocks:.2f}")

    median = sorted(gap_stats)[len(gap_stats) // 2]
    print(f"no-trade gap size between block: avg={np.mean(gap_stats):.2f} median={median} std={np.std(gap_stats):.2f}")

if __name__ == "__main__":
    main()
