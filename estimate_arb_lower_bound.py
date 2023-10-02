#!/usr/bin/env python

#
# This script estimates upper bound of toxic arbitrage volume proportion in a specific Uniswap pool.
# "Toxic" arbitrage is defined as external-source driven arbibtrage, as it's likely to reslt in negative markout.
#
# Non-toxic arb example:
#   - random swapper swaps token0 -> token1
#   - arber swaps token1 -> token0 to bring the price back to the start
#
# Toxic arb example:
#   - price changes on a CEX, token0 gets more expensive
#   - arber swaps token1 -> token0, buying token0 at a stale price
#
#
# The upper bound of toxic arbitrage volume in a block is defined as the volume required
# to move the start price of a block towards end of the block.
#
# For instance:
#  - Swaps in Block #1:
#    some token0 -> 10 token1
#
#  - Swaps in Block #2:
#    10 token1 -> some token0
#
#  - Swaps in Block #3:
#    4 token1 -> some token0
#    some token0 -> 5 token1
#    10 token1 -> some token0
#
# Result:
#  ceil(ArbVol_block#1) = 10
#  ceil(ArbVol_block#2) = 10
#  ceil(ArbVol_block#3) = 4 - 5 + 10 = 9 
#
# The "true" amount of toxic arbitrage volume can never be greater than this, but can be smaller than this,
# because some of the perceived arbitragers will in fact be normal traders swapping.
#
#
# Warning: for now, always assumes that token1 is ETH! Change the code for pools where false!

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

# only v2 supported for now
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
            result.append(fields)
    return result


def classify_trades(trades, data):
    current_block = None # start from a fresh block

    block_volume_token0_in = 0
    block_volume_token0_out = 0

    total_volume_token0 = 0
    maybe_arb_volume_token0 = 0

    # token0: e.g. USDC, token1: ETH
    for row in data:
        if VERSION == 2:
            (_, block, _, amount0_in, amount1_in, amount0_out, amount1_out, address, _) = row
            amount0_in = int(amount0_in)
            amount0_out = int(amount0_out)

            # remove fake "volume" created due to pool imbalance, returned to the swapper due to sync() call
            if amount0_in > 0 and amount0_out > 0:
                if amount0_in > amount0_out:
                    amount0_in -= amount0_out
                    amount0_out = 0
                else:
                    amount0_out -= amount0_in
                    amount0_in = 0

        if current_block != block:
            current_block = block
            total_volume_token0 += block_volume_token0_in + block_volume_token0_out
            maybe_arb_volume_token0 += abs(block_volume_token0_in - block_volume_token0_out) 
            block_volume_token0_in = 0
            block_volume_token0_out = 0

        block_volume_token0_in += amount0_in
        block_volume_token0_out += amount0_out


    total_volume_token0 += block_volume_token0_in + block_volume_token0_out
    maybe_arb_volume_token0 += abs(block_volume_token0_in - block_volume_token0_out) 

    return (total_volume_token0, maybe_arb_volume_token0)


def main():
    # {True: sandwich_volume, False: other_trader_volume}
    trades = {True: 0, False: 0}
    days_tracked = 0
    total = 0
    maybe_arb = 0
    for filename in sorted(os.listdir(data_dir)):
        if "-swaps.csv" in filename:
            data = load_csv(filename)
            day_total, day_maybe_arb = classify_trades(trades, data)
            total += day_total
            maybe_arb += day_maybe_arb
            days_tracked += 1

    print(f"{days_tracked} days tracked")
    if total / (10 ** DECIMALS) > 1_000_000:
        print(f"total token0 volume: {total / (10 ** DECIMALS) * 1e-6:.2f} million")
        print(f"maybe arbitrage token0 volume: {maybe_arb / (10 ** DECIMALS) * 1e-6:.2f} million")
    else:
        print(f"total token0 volume: {total / (10 ** DECIMALS)}")
        print(f"maybe arbitrage token0 volume: {maybe_arb / (10 ** DECIMALS)}")
    maybe_arb_proportion = maybe_arb / total
    print(f"maybe arbitrage volume proportion: {100*maybe_arb_proportion:.2f}%")

if __name__ == "__main__":
    main()
