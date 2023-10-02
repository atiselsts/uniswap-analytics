# uniswap-analytics

This repository is a collection of scripts for Uniswap analytics.

Currently there are:
* `get_sandwich_stats.py` - analyze MEV sandwich volume in Uniswap v2 and v3 pools.

## Data sources

The repository uses data from Google BigQuery.
The data can be downloaded and saved locally to the disk using the scripts `download-swap-data-v2.py` and `download-swap-data-v3.py`.

## Important pools

Some pools to try out:

 * v2 USDC/ETH pool ($59.5M TVL):   0xb4e16d0168e52d35cacd2c6185b44281ec28c9dc
 * v3 USDC/ETH 0.3% ($97.4M TVL):   0x8ad599c3a0ff1de082011efddc58f1908eb6e6d8
 * v3 USDC/ETH 0.05% ($272.6M TVL): 0x88e6a0c2ddd26feeb64f039a2c41296fcb3f5640
#
 * v2 WETH/BTC pool ($5.9M TVL):    0xbb2b8038a1640196fbe3e38816f3e67cba72d940
 * v3 WETH/BTC 0.3% ($211.8M TVL): 0xcbcdf9626bc03e24f779434178a73a0b4bad62ed
 * v3 WETH/BTC 0.05% ($84.8M TVL):  0x4585fe77225b41b697c938b018e2ac67ac5a20c0
