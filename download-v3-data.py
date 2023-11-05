#!/usr/bin/env python

#
# This file creates a local database of:
# - all Uniswap v3 initialize, mint, burn, swap and flash events
# and stores them in CSV files on the disk.
#
# Attention: Google BigQuery access is required!
# Only Ethereum supported for now.
# (Polygon DB also exists and could be easily queried instead.)
#

import os
from google.cloud import bigquery
import pandas as pd
from datetime import date, timedelta, datetime

DIR = os.path.join("data", f"uniswap-v3-all")

YEAR = os.getenv("YEAR")
print(YEAR)
if YEAR is None or len(YEAR) == 0:
    YEAR = "2021"
YEAR = int(YEAR)

START_DATE = date(YEAR, 1, 1)
if YEAR == 2021:
    START_DATE = date(YEAR, 5, 4)

if YEAR == date.today().year:
    END_DATE = date.today() - timedelta(days=1)
else:
    END_DATE = date(YEAR, 12, 31)

INIT_TOPIC = "0x98636036cb66a9c19a37435efc1e90142190214e8abeb821bdba3f2990dd4c95"
SWAP_TOPIC = "0xc42079f94a6350d7e6235f29174924f928cc2ac818eb64fed8004e115fbcca67"
MINT_TOPIC = "0x7a53080ba414158be7ec69b987b5fb7d07dee101fe85488f0853ae16239d0bde"
BURN_TOPIC = "0x0c396cd989a39f4459b5fa1aed6a9a8dcdbc45908acfd67e028cd568da98982c"
FLASH_TOPIC = "0xbdbdb71d7860376ba52b25a5028beea23581364a40522f6bcfb86bb1f2dca633"
COLLECT_TOPIC = "0x70935338e69775456a85ddef226c395fb668b63fa0115f5f20610b388e6ca9c0"

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
  AND (topics[SAFE_OFFSET(0)] = '{1}' OR topics[SAFE_OFFSET(0)] = '{2}' OR topics[SAFE_OFFSET(0)] = '{3}' OR topics[SAFE_OFFSET(0)] = '{4}' OR topics[SAFE_OFFSET(0)] = '{5}')
ORDER BY block_timestamp, log_index ASC
"""

QUERY_NEW = """
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
  AND (topics[SAFE_OFFSET(0)] = '{6}')
ORDER BY block_timestamp, log_index ASC
"""

COMPLEMENT = 1 << 256
MAX_INT256 = (1 << 256) // 2 - 1

def signed_int(s):
    u = int(s, 16)
    if u <= MAX_INT256:
        return u
    return u - COMPLEMENT 

def get_events(client, date):
    year = date[:4]
    filename = os.path.join(DIR, year, date + "-events.csv")
    if os.access(filename, os.R_OK):
        print(f"file {filename} already exists")
        return False

    query = QUERY.format(date, INIT_TOPIC, SWAP_TOPIC, MINT_TOPIC, BURN_TOPIC, FLASH_TOPIC, COLLECT_TOPIC)
    query_job = client.query(query)
    iterator = query_job.result(timeout=300)
    with open(filename, "w") as f:
        s = ["timestamp", "block", "pool", "tx_hash", "type", "price", "tick_lower", "tick_upper", "liquidity",  "amount0", "amount1"]
        f.write(",".join(s) + "\n")

        for row in iterator:
            timestamp = int(round(row[0].timestamp()))
            block = row[1]
            tx_hash = row[2]
            pool = row[3]
            data = row[4]
            topic = row[6][0]

            # sqrtPriceX96
            price = 0
            liquidity = 0
            tick_lower = 0
            tick_upper = 0
            amount0 = 0
            amount1 = 0

            if len(data) < 130:
                # not a Uniswap event?
                continue
            if topic == MINT_TOPIC:
                event_type = 1
                liquidity = int(data[66:130], 16)
                amount0 = int(data[130:194], 16)
                amount1 = int(data[194:258], 16)
                tick_lower = signed_int(row[6][2])
                tick_upper = signed_int(row[6][3])
            elif topic == BURN_TOPIC:
                #print("burn", row)
                event_type = 2
                liquidity = int(data[:66], 16)
                amount0 = int(data[66:130], 16)
                amount1 = int(data[130:194], 16)
                tick_lower = signed_int(row[6][2])
                tick_upper = signed_int(row[6][3])
            elif topic == SWAP_TOPIC:
                if len(data) < 322:
                    # not a Uniswap event?
                    print(tx_hash)
                    assert len(data) >= 322
                    continue
                event_type = 3
                amount0 = signed_int(data[:66])
                amount1 = signed_int(data[66:130])
                price = int(data[130:194], 16)
                liquidity = int(data[194:258], 16)
                tick_lower = signed_int(data[258:322])
                tick_upper = tick_lower
            elif topic in INIT_TOPIC:
                # print("init", row)
                event_type = 4
                price = int(data[:66], 16)
                tick_lower = signed_int(data[66:130])
                tick_upper = tick_lower
            elif topic == FLASH_TOPIC:
                event_type = 5
                if len(data) < 258:
                    # not a Uniswap event?
                    print(tx_hash)
                    assert len(data) >= 258
                    continue
                #amount0 = int(data[:66], 16)
                #amount1 = int(data[66:130], 16)
                # keep track of just the the fee amounts
                amount0 = int(data[130:194], 16)
                amount1 = int(data[194:258], 16)
            elif topic == COLLECT_TOPIC:
                event_type = 6
                tick_lower = signed_int(row[6][2])
                tick_upper = signed_int(row[6][3])
                amount0 = int(data[66:130], 16)
                amount1 = int(data[130:194], 16)

            s = [str(u) for u in [timestamp, block, pool, tx_hash, event_type, price, tick_lower, tick_upper, liquidity, amount0, amount1]]
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
