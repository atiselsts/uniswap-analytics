#!/usr/bin/env python

#
# This file creates a local database of:
# - all Uniswap v2 sync, swap, burn and mint events
# and stores them in CSV files on the disk.
#
# Attention: Google BigQuery access is required!
# Only Ethereum supported for now.
# (Polygon DB also exists and could be easily queried instead.)
#

import os
from web3 import Web3
from google.cloud import bigquery
import pandas as pd
from datetime import date, timedelta, datetime

DIR = os.path.join("data", f"uniswap-v2-all")

YEAR = os.getenv("YEAR")
if YEAR is None or len(YEAR) == 0:
    YEAR = "2020"
YEAR = int(YEAR)

START_DATE = date(YEAR, 1, 1)
if YEAR == 2020:
    START_DATE = date(YEAR, 5, 5)

if YEAR == date.today().year:
    END_DATE = date.today() - timedelta(days=1)
else:
    END_DATE = date(YEAR, 12, 31)

SYNC_TOPIC = "0x1c411e9a96e071241c2f21f7726b17ae89e3cab4c78be50e062b03a9fffbbad1"
SWAP_TOPIC = "0xd78ad95fa46c994b6551d0da85fc275fe613ce37657fb8d5e3d130840159d822"
MINT_TOPIC = "0x4c209b5fc8ad50758f13e2e1088ba56a560dff690a1c6fef26394f4c03821c4f"
BURN_TOPIC = "0xdccd412f0b1252819cb1fd330b93224ca42612892bb3f4f789976e6d81936496"

QUERY = """
SELECT
  block_timestamp
  ,block_number
  ,transaction_hash
  ,address
  ,data
  ,log_index
  ,topics
FROM `bigquery-public-data.crypto_ethereum.logs`
WHERE
  DATE(block_timestamp) = '{0}'
  AND (topics[SAFE_OFFSET(0)] = '{1}' OR topics[SAFE_OFFSET(0)] = '{2}' OR topics[SAFE_OFFSET(0)] = '{3}' OR topics[SAFE_OFFSET(0)] = '{4}')
ORDER BY block_timestamp, log_index ASC
"""

def get_events(client, date):
    year = date[:4]
    filename = os.path.join(DIR, year, date + "-events.csv")
    if os.access(filename, os.R_OK):
        print(f"file {filename} already exists")
        return False

    query = QUERY.format(date, SYNC_TOPIC, SWAP_TOPIC, MINT_TOPIC, BURN_TOPIC)
    query_job = client.query(query)
    iterator = query_job.result(timeout=300)
    with open(filename, "w") as f:
        s = ["timestamp", "block", "pool", "tx_hash", "type", "field0", "field1", "field2", "field3"]
        f.write(",".join(s) + "\n")

        for row in iterator:
            timestamp = int(round(row[0].timestamp()))
            block = row[1]
            tx_hash = row[2]
            pool = row[3]
            data = row[4]
            topic = row[6][0]
            field2 = 0
            field3 = 0
            if len(data) < 130:
                # not a Uniswap event?
                continue
            if topic in SYNC_TOPIC:
                event_type = 0
                field0 = int(data[:66], 16)
                field1 = int(data[66:130], 16)
            elif topic == MINT_TOPIC:
                event_type = 1
                field0 = int(data[:66], 16)
                field1 = int(data[66:130], 16)
            elif topic == BURN_TOPIC:
                event_type = 2
                field0 = int(data[:66], 16)
                field1 = int(data[66:130], 16)
            elif topic == SWAP_TOPIC:
                if len(data) < 258:
                    # not a Uniswap event?
                    continue
                event_type = 3
                field0 = int(data[:66], 16)
                field1 = int(data[66:130], 16)
                field2 = int(data[130:194], 16)
                field3 = int(data[194:258], 16)

            s = [str(u) for u in [timestamp, block, pool, tx_hash, event_type, field0, field1, field2, field3]]
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
        get_events(client, d)


if __name__ == "__main__":
    main()
    print("all done")
