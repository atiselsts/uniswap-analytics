#!/usr/bin/env python

#
# This file creates a local database of:
# - all Uniswap v2 sync events
# and stores them in CSV files on the disk.
#
# Attention: Google BigQuery access is required!
#

import os
from web3 import Web3
from google.cloud import bigquery
import pandas as pd
from datetime import date, timedelta, datetime

UNISWAP_VERSION = 2

# save in the swaps directory (because each swap creates a sync event) 
DIR = os.path.join("data", f"uniswap-v{UNISWAP_VERSION}-swaps")

YEAR = os.getenv("YEAR")
if YEAR is None or len(YEAR) == 0:
    YEAR = "2023"
YEAR = int(YEAR)

START_DATE = date(YEAR, 1, 1)
if YEAR == 2020:
    # this is the date when v2 was launched
    START_DATE = date(YEAR, 5, 5)

if YEAR == date.today().year:
    END_DATE = date.today() - timedelta(days=1)
else:
    END_DATE = date(YEAR, 12, 31)

SYNC_TOPIC = "0x1c411e9a96e071241c2f21f7726b17ae89e3cab4c78be50e062b03a9fffbbad1"

SYNC_QUERY = """
SELECT
  block_timestamp
  ,block_number
  ,transaction_hash
  ,address
  ,data
  ,log_index
FROM `bigquery-public-data.crypto_ethereum.logs`
WHERE
  DATE(block_timestamp) = '{0}'
  AND topics[SAFE_OFFSET(0)] = '{1}'
ORDER BY block_timestamp, log_index ASC
"""

def get_sync(client, date):
    year = date[:4]
    filename = os.path.join(DIR, year, date + "-sync.csv")
    if os.access(filename, os.R_OK):
        print(f"file {filename} already exists")
        return False

    query = SYNC_QUERY.format(date, SYNC_TOPIC)
    query_job = client.query(query)
    iterator = query_job.result(timeout=300)
    with open(filename, "w") as f:
        s = ["timestamp", "block", "pool", "reserve0", "reserve1", "tx_hash"]
        f.write(",".join(s) + "\n")

        for row in iterator:
            timestamp = int(round(row[0].timestamp()))
            block = row[1]
            tx_hash = row[2]
            pool = row[3]
            data = row[4]
            reserve0 = int(data[:66], 16)
            reserve1 = int(data[66:], 16)
            s = [str(u) for u in [timestamp, block, pool, reserve0, reserve1, tx_hash]]
            f.write(",".join(s) + "\n")
    return True


def main():
    os.makedirs(os.path.join(DIR, str(YEAR)), exist_ok=True)

    client = bigquery.Client()
    end_date = END_DATE
    if end_date is None:
        end_date = datetime.today() - timedelta(days=1)
    dates = pd.date_range(START_DATE, end_date, freq='d')
    dates = [d.strftime('%Y-%m-%d') for d in dates]
    for d in dates:
        print(d)
        get_sync(client, d)

if __name__ == "__main__":
    main()
    print("all done")
