# uniswap-analytics

This repository is a collection of scripts for Uniswap analytics.

Currently there are:
* `get_sandwich_stats.py` - analyze MEV sandwich volume in Uniswap v2 and v3 pools.

## Data sources

The repository uses data from Google BigQuery.
The data can be downloaded and saved locally to the disk using the scripts `download-swap-data-v2.py` and `download-swap-data-v3.py`.
