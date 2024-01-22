#!/usr/bin/env python

#
# This script estimates the impact from having slower block times.
#

import os
import numpy as np

YEAR = os.getenv("YEAR")
if YEAR is None or len(YEAR) == 0:
    YEAR = "2023"

POOL = os.getenv("POOL")
if POOL is None or len(POOL) == 0:
    POOL = "0x8ad599c3a0ff1de082011efddc58f1908eb6e6d8" # USDC/ETH 0.3%
POOL = POOL.lower()

DECIMALS = os.getenv("DECIMALS")
if DECIMALS is None or len(DECIMALS) == 0:
    DECIMALS = 6 # for USDC
DECIMALS = int(DECIMALS)

VERSION = 3

print(f"using pool {POOL} on Uniswap v{VERSION}, year {YEAR}, token0 decimals {DECIMALS}")

self_dir = os.path.dirname(os.path.abspath(__file__))
data_dir = os.path.join(self_dir, "data", f"uniswap-v{VERSION}-all", YEAR)


def load_csv(filename):
    result = []
    with open(os.path.join(data_dir, filename)) as f:
        f.readline() # skip the header
        #timestamp,block,pool,tx_hash,type,price,tick_lower,tick_upper,liquidity,amount0,amount1
        for line in f.readlines():
            fields = line.strip().split(",")
            if len(fields) == 0:
                continue
            pool = fields[2]
            if pool != POOL:
                continue
            event_type = fields[4]
            if event_type != "3":
                continue
            block = int(fields[1])
            price = int(fields[5]) ** 2 # use price instead of sqrt price
            result.append((block, price, int(fields[-2]), int(fields[-1])))
    return result


def get_block_price(block_trades, use_last_price_in_block):
    if len(block_trades) == 0:
        return -1
    index = -1 if use_last_price_in_block else 0
    return block_trades[index][1]
    

def process_data(data, n_to_skip, use_last_price_in_block):
    batch_size = n_to_skip + 1

    volume0 = 0
    reduced_volume0 = 0

    n_blocks_with_trades = 0
    reduced_n_blocks_with_trades = 0

    n_blocks = len(data)
    reduced_n_blocks = (n_blocks + n_to_skip) // batch_size

    old_dex_price = -1

    for i in range(0, n_blocks, batch_size):
        all_empty = all([len(block_trades) == 0 for block_trades in data[i:i+batch_size]])
        if all_empty:
            continue

        prices = []
        volume0_per_subblock = []
        
        for j in range(batch_size):
            if i + j >= len(data):
                break
            trades = data[i+j]
            if len(trades) == 0:
                continue
            prices.append(get_block_price(trades, use_last_price_in_block))

            volume0_per_subblock.append(0)
            for trade in data[i+j]:
                (block, price, amount0, amount1) = trade
                volume0_per_subblock[-1] += abs(amount0)

        n_blocks_with_trades += len(volume0_per_subblock)
        volume0 += sum(volume0_per_subblock)

        have_oscillations = True
        oscillates_beyond_old = False

        if len(prices) < 2:
            have_oscillations = False
        else:
            if old_dex_price < prices[0] < prices[1] \
               or old_dex_price > prices[0] > prices[1]:
                have_oscillations = False

        if not have_oscillations:
            reduced_n_blocks_with_trades += 1

            reduced_volume0 += sum(volume0_per_subblock)
        else:
            if old_dex_price < prices[0] and old_dex_price > prices[1]:
                oscillates_beyond_old = True

            if old_dex_price > prices[0] and old_dex_price < prices[1]:
                oscillates_beyond_old = True

            if oscillates_beyond_old:
                reduced_n_blocks_with_trades += 1
                reduced_volume0 += volume0_per_subblock[-1]

        if (not have_oscillations) or oscillates_beyond_old:
            # have some trades, update the price
            old_dex_price = prices[-1]
   

    print(f"block time = {12 * batch_size} sec")
    print(f"original volume: {volume0/1e12:.0f} million USDC")
    print(f"volume with new block time: {reduced_volume0/1e12:.0f} million USDC")

    print(f"original blocks with trades: {100*n_blocks_with_trades/n_blocks:.2f} %")
    expected = batch_size * 100 * n_blocks_with_trades / n_blocks
    if expected > 100:
        expected = 100
    print(f"blocks with trades, new block time: {100*reduced_n_blocks_with_trades/reduced_n_blocks:.2f} % (if no reduction: {expected:.2f} %)")
    print("")


def main():
    all_data = []
    for filename in sorted(os.listdir(data_dir)):
        if "-events.csv" in filename:
            print(filename)
            all_data += load_csv(filename)


    n_blocks = all_data[-1][0] - all_data[0][0] + 1
    data_by_block = [[] for _ in range(n_blocks)]
    start_block = all_data[0][0]
    for row in all_data:
        block_index = row[0] - start_block
        data_by_block[block_index].append(row)    

    # if set to true, the price at the end of the block is used
    # if set to false, the price after the first trade (assumed to be arb) is used instead
    use_last_price_in_block = False

    # TODO: support larger periods to skip!
    for n_to_skip in [1]:
        print("n_to_skip=", n_to_skip)
        process_data(data_by_block, n_to_skip, use_last_price_in_block)
        process_data(data_by_block, n_to_skip, not use_last_price_in_block)


if __name__ == "__main__":
    main()
