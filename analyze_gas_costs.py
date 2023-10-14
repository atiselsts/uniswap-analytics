#!/usr/bin/env python

#
# This script analyzes transaction stats by sampling a random subset of tx
#

import os
import random
import matplotlib.pyplot as pl
import numpy as np

POOLS = [
    (2, "0xb4e16d0168e52d35cacd2c6185b44281ec28c9dc", "v2 USDC/ETH", 0.003),
    (3, "0x8ad599c3a0ff1de082011efddc58f1908eb6e6d8", "v3 USDC/ETH 0.3%", 0.0033),
    (3, "0x88e6a0c2ddd26feeb64f039a2c41296fcb3f5640","v3 USDC/ETH 0.05%", 0.0033),
]

YEAR = os.getenv("YEAR")
if YEAR is None or len(YEAR) == 0:
    YEAR = "2023"


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


def main():
    random.seed(12345) # make it repeatable

    labels = [u[2] for u in POOLS]
    gas_usages = []
    gas_prices = []

    for (version, pool, name, _) in POOLS:
        filename = f"tx-details-v{version}-{YEAR}-{pool}.csv"
        txs = load_csv(filename)
        gas_usages.append([int(u[2]) for u in txs])
        gas_prices.append([int(u[3])/1e9 for u in txs])

    pl.figure(figsize=(6, 4))
    for gas, lab in zip(gas_usages, labels):
        x = range(len(gas))
        pl.plot(x, sorted(gas), label=lab)

    pl.ylim(0, 1_000_000)
    pl.ylabel("Gas usage")
    pl.xlabel("Transactions")
    pl.legend()
    pl.savefig("gas-usages.pdf", bbox_inches='tight')
    pl.close()


    pl.figure(figsize=(6, 4))
    for gas, lab in zip(gas_usages, labels):
        n = len(gas)
        gas = sorted(gas)[:n//10]
        x = range(len(gas))
        pl.plot(x, sorted(gas), label=lab)

    #pl.ylim(0, 1_000_000)
    pl.ylabel("Gas usage")
    pl.xlabel("Transactions")
    pl.legend()
    pl.savefig("gas-usages-limited.pdf", bbox_inches='tight')
    pl.close()



    pl.figure(figsize=(6, 4))
    for price, lab in zip(gas_prices, labels):
        x = range(len(price))
        pl.plot(x, sorted(price), label=lab)

    pl.yscale("log")
    pl.ylabel("Gas price, gwei")
    pl.xlabel("Transactions")
    pl.legend()
    pl.savefig("gas-prices.pdf", bbox_inches='tight')
    pl.close()


    pl.figure(figsize=(6, 4))
    for price, lab in zip(gas_prices, labels):
        x = range(len(price))
        pl.plot(x, sorted(price), label=lab)

    pl.ylim(0, 150)
    pl.ylabel("Gas price, gwei")
    pl.xlabel("Transactions")
    pl.legend()
    pl.savefig("gas-prices-limited.pdf", bbox_inches='tight')
    pl.close()


    for i in range(len(POOLS)):
        gas = gas_usages[i]
        n = len(gas)
        med_gas = sorted(gas)[n // 2]
        q1_gas = sorted(gas)[n // 4]
        q3_gas = sorted(gas)[n * 3 // 4]

        gas_prices_excluding_outliers = sorted(gas_prices[i])[n//10:][:-n//10]
        avg_price = np.mean(gas_prices_excluding_outliers)

        swap_cost = med_gas * avg_price / 1e9
        print(f"pool {POOLS[i][2]} gas={q1_gas}/{med_gas}/{q3_gas} gas_price={avg_price:.1f} cost={swap_cost:.6f} ETH")


    all_swap_costs_bps = []
    for (version, pool, name, swap_cost_eth) in POOLS:
        filename = f"reserves-v{version}-{YEAR}-{pool}.csv"
        reserves = load_csv(filename)
        pool_reserves_in_eth = [2 * int(u[1]) / 1e18 for u in reserves]

        swap_costs_bps = [swap_cost_eth / u * 10_000 for u in pool_reserves_in_eth]
        all_swap_costs_bps.append(swap_costs_bps)
        break

    pl.figure(figsize=(6, 4))
    for swap_costs, lab in zip(all_swap_costs_bps, labels):
        x = range(len(swap_costs))
        pl.plot(x, swap_costs, label=lab)

    pl.ylim(0, 0.0015)
    pl.ylabel("Simple arb swap tx cost, bps")
    pl.xlabel(f"Day in {YEAR}")
    pl.legend()
    pl.savefig("tx-costs-bps.pdf", bbox_inches='tight')
    pl.close()


if __name__ == "__main__":
    main()
