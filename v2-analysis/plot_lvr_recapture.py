#!/usr/bin/env python

#
# This plots the figures for the article on LVR.
#

import matplotlib.pyplot as pl
import numpy as np
from ing_theme_matplotlib import mpl_style
from math import sqrt


# Constants for the LP positions

INITIAL_PRICE = 1000

# assume $1 million of liquidity in the pool (the larger, the better for all parties)
INITIAL_VALUE = 1e6

# Constants for price simulations
SIGMA = 0.03

# assume 12 second blocks as in the mainnet
BLOCKS_PER_DAY = 86400 // 12

NUM_DAYS = 10

# assume 0.3% swap fees
SWAP_FEE_03 = 0.3 / 100

NUM_SIMULATIONS = 10000


# Constants for plotting
pl.rcParams["savefig.dpi"] = 200

############################################################

def get_liquidity(reserve_x, reserve_y):
    return sqrt(reserve_x * reserve_y)

############################################################

#
# Use geometrical Brownian motion to simulate price evolution.
#
def get_price_path(sigma_per_day, blocks_per_day=BLOCKS_PER_DAY, M=NUM_SIMULATIONS, num_days=NUM_DAYS):
    np.random.seed(123) # make it repeatable
    mu = 0.0   # assume delta neutral behavior
    T = num_days
    n = T * blocks_per_day
    # calc each time step
    dt = T/n
    # simulation using numpy arrays
    St = np.exp(
        (mu - sigma_per_day ** 2 / 2) * dt
        + sigma_per_day * np.random.normal(0, np.sqrt(dt), size=(M, n-1)).T
    )
    # include array of 1's
    St = np.vstack([np.ones(M), St])
    # multiply through by S0 and return the cumulative product of elements along a given simulation path (axis=0). 
    St = INITIAL_PRICE * St.cumprod(axis=0)
    return St

############################################################

def estimate_lvr(prices, swap_tx_cost, fee_tier):
    fee_factor_down = 1.0 - fee_tier
    fee_factor_up = 1.0 + fee_tier

    reserve_y = INITIAL_VALUE / 2
    reserve_x = reserve_y / INITIAL_PRICE
    pool_value0 = INITIAL_VALUE
    L = get_liquidity(reserve_x, reserve_y)

    # compute lvr and fees
    lvr = 0
    collected_fees = 0
    num_tx = 0

    for cex_price in prices:
        pool_price = reserve_y / reserve_x
        if cex_price > pool_price:
            to_price = cex_price * fee_factor_down
            if to_price < pool_price:
                continue
        else:
            to_price = cex_price * fee_factor_up
            if to_price > pool_price:
                continue

        to_sqrt_price = sqrt(to_price)
        delta_x = L / to_sqrt_price - reserve_x
        delta_y = L * to_sqrt_price - reserve_y
        if delta_x > 0:
            # arber sells X, LP buys X
            swap_fee = fee_tier * delta_x * cex_price
        else:
            # arber buys X, LP sells X
            swap_fee = fee_tier * delta_y

        # assume fixed gas fees
        lp_loss_vs_cex = -(delta_x * cex_price + delta_y)

        arb_gain = lp_loss_vs_cex - swap_fee - swap_tx_cost
        if arb_gain > 0:
            lvr += lp_loss_vs_cex # account without swap fees and tx fees
            reserve_x += delta_x
            reserve_y += delta_y
            collected_fees += swap_fee
            num_tx += 1

    # normalize by dividing with the initial value of the capital rather than the final value
    lvr /= pool_value0
    collected_fees /= pool_value0
    return lvr, collected_fees, num_tx


############################################################

def compute_lvr(all_prices, swap_tx_cost, fee_tier):
    print(f"compute_lvr, swap_tx_cost={swap_tx_cost}, fee_tier={100*fee_tier:.2}%")
    #fee_multiplier = 1 / (1 - swap_fee)

    all_lvr = []
    all_fees = []
    all_tx_per_block = []

    if len(all_prices.shape) > 2:
        # take the first elements from the second dimension
        all_prices = all_prices[:,0,:]

    for sim in range(all_prices.shape[1]):
        prices = all_prices[:,sim]
        lvr, collected_fees, num_tx = estimate_lvr(prices, swap_tx_cost, fee_tier)
        all_lvr.append(lvr)
        all_fees.append(collected_fees)
        all_tx_per_block.append(num_tx / len(prices))

    return np.mean(all_lvr), np.mean(all_fees), np.mean(all_tx_per_block)

############################################################

def plot_lvr_and_tx_cost():
    fig, ax = pl.subplots()
    fig.set_size_inches((6, 4))

    # reduce the number of simulations, since we iterate over each block
    num_simulations = 200

    all_prices = get_price_path(SIGMA, blocks_per_day=BLOCKS_PER_DAY, M=num_simulations)
    final_prices = all_prices[-1,:]
    returns = final_prices / INITIAL_PRICE
    year_sigma = SIGMA * sqrt(365) # convert from daily to yearly volatility
    print(f"sigma={year_sigma:.2f} mean={np.mean(final_prices):.4f} std={np.std(np.log(returns)):.4f}")

    coeff = 365 / NUM_DAYS
    lvr = (SIGMA ** 2) / 8
    lvr_per_year = 100 * lvr * 365
    print(f"predicted LVR: {lvr_per_year}% per year")

    tx_cost_bps = [0.0005, 0.001, 0.0015, 0.002]
    x = tx_cost_bps

    swap_tx_cost_dollars = [INITIAL_VALUE * u / 10000 for u in tx_cost_bps]
    print(swap_tx_cost_dollars)

    lvr_and_fees = [compute_lvr(all_prices, cost, SWAP_FEE_03) for cost in swap_tx_cost_dollars]
    pl.plot(x, [coeff * 100 * u[0] for u in lvr_and_fees], label="Losses to LVR", marker="v", color="red")
    pl.plot(x, [coeff * 100 * u[1] for u in lvr_and_fees], label="Gains from arb fees, 0.3% pool", marker="o", color="orange")

    fee_apr = [coeff * 100 * u[1] for u in lvr_and_fees]
    proc_recapture = [f"{100*u/lvr_per_year:.2f}" for u in fee_apr]
    print("percent recaptured:", proc_recapture)

    pl.xlabel("Swap tx fixed cost, bps")
    pl.ylabel("APR, %")
    pl.legend()
    pl.ylim(0, 5)

    pl.savefig("simulations_lvr_and_tx_cost.png", bbox_inches='tight')
    pl.close()


############################################################
    
def main():
    mpl_style(True)

    # check what % of LVR goes to the LP as fees, as a function of Tx cost
    plot_lvr_and_tx_cost()


if __name__ == '__main__':
    main()
    print("all done!")

# results:
#    [0.05, 0.1, 0.15, 0.2]
#    compute_lvr, swap_tx_cost=0.05, fee_tier=0.3%
#    compute_lvr, swap_tx_cost=0.1, fee_tier=0.3%
#    compute_lvr, swap_tx_cost=0.15, fee_tier=0.3%
#    compute_lvr, swap_tx_cost=0.2, fee_tier=0.3%
#    percent recaptured: ['87.41', '84.24', '82.00', '80.15']
