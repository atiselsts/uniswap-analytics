#!/usr/bin/env python

#
# This file creates a local database of:
# - all Uniswap v2 swaps
# - all new Uniswap v2 pairs
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

DIR = os.path.join("data", f"uniswap-v{UNISWAP_VERSION}-swaps")

YEAR = os.getenv("YEAR")
if YEAR is None or len(YEAR) == 0:
    YEAR = "2023"
YEAR = int(YEAR)

START_DATE = date(YEAR, 1, 1)
if YEAR == date.today().year:
    END_DATE = date.today() - timedelta(days=1)
else:
    END_DATE = date(YEAR, 12, 31)

V2_SWAP_TOPIC = "0xd78ad95fa46c994b6551d0da85fc275fe613ce37657fb8d5e3d130840159d822"
V2_CREATE_PAIR_TOPIC = "0x0d3648bd0f6ba80134a33ba9275ac585d9d315f0ad8355cddefde31afa28d0e9"
V2_FACTORY = "0x5c69bee701ef814a2b6a3edd4b1652cb9cc5aa6f"

SWAP_V2_JS_CODE = """
    let parsedEvent = {"anonymous": false, "inputs": [{"indexed": true, "internalType": "address", "name": "sender", "type": "address"}, {"indexed": false, "internalType": "uint256", "name": "amount0In", "type": "uint256"}, {"indexed": false, "internalType": "uint256", "name": "amount1In", "type": "uint256"}, {"indexed": false, "internalType": "uint256", "name": "amount0Out", "type": "uint256"}, {"indexed": false, "internalType": "uint256", "name": "amount1Out", "type": "uint256"}, {"indexed": true, "internalType": "address", "name": "to", "type": "address"}], "name": "Swap", "type": "event"}
    return abi.decodeEvent(parsedEvent, data, topics, false);
"""

SWAP_V2_QUERY = """
CREATE TEMP FUNCTION
  PARSE_LOG(data STRING, topics ARRAY<STRING>)
  RETURNS STRUCT<`sender` STRING, `amount0In` STRING, `amount1In` STRING, `amount0Out` STRING, `amount1Out` STRING, `to` STRING>
  LANGUAGE js AS \"\"\"{0}\"\"\"
OPTIONS
  ( library="https://storage.googleapis.com/ethlab-183014.appspot.com/ethjs-abi.js" );

WITH parsed_logs AS
(SELECT
    address
    ,logs.block_timestamp AS block_timestamp
    ,logs.block_number AS block_number
    ,logs.transaction_hash AS transaction_hash
    ,logs.log_index AS log_index
    ,PARSE_LOG(logs.data, logs.topics) AS parsed
FROM `bigquery-public-data.crypto_ethereum.logs` AS logs
WHERE
  DATE(block_timestamp) = '{1}'
  AND topics[SAFE_OFFSET(0)] = '{2}'
)
SELECT
    block_timestamp
    ,block_number
    ,transaction_hash
    ,address
    ,parsed.amount0In AS `amount0In`
    ,parsed.amount1In AS `amount1In`
    ,parsed.amount0Out AS `amount0Out`
    ,parsed.amount1Out AS `amount1Out`
    ,parsed.to AS `receiver`
    ,parsed.sender AS `sender`
FROM parsed_logs
ORDER BY block_timestamp, log_index ASC
"""

PAIR_JS_CODE = """
    let parsedEvent = {"anonymous": false, "inputs": [{"indexed": true, "internalType": "address", "name": "token0", "type": "address"}, {"indexed": true, "internalType": "address", "name": "token1", "type": "address"}, {"indexed": false, "internalType": "address", "name": "pair", "type": "address"}, {"indexed": false, "internalType": "uint256", "name": "", "type": "uint256"}], "name": "PairCreated", "type": "event"}
    return abi.decodeEvent(parsedEvent, data, topics, false);
"""

PAIR_QUERY = """
CREATE TEMP FUNCTION
  PARSE_LOG(data STRING, topics ARRAY<STRING>)
  RETURNS STRUCT<`token0` STRING, `token1` STRING, `pair` STRING>
  LANGUAGE js AS  \"\"\"{0}\"\"\"
OPTIONS
  ( library="https://storage.googleapis.com/ethlab-183014.appspot.com/ethjs-abi.js" );

WITH parsed_logs AS
(SELECT
    logs.block_timestamp AS block_timestamp
    ,logs.block_number AS block_number
    ,logs.transaction_hash AS transaction_hash
    ,logs.log_index AS log_index
    ,PARSE_LOG(logs.data, logs.topics) AS parsed
FROM `bigquery-public-data.crypto_ethereum.logs` AS logs
WHERE address = '{1}'
  AND DATE(block_timestamp) = '{2}'
  AND topics[SAFE_OFFSET(0)] = '{3}'
)
SELECT
    transaction_hash
    ,parsed.token0 AS `token0`
    ,parsed.token1 AS `token1`
    ,parsed.pair AS `pair`
FROM parsed_logs
ORDER BY block_timestamp, log_index ASC
"""


def get_v2_swaps(client, date):
    year = date[:4]
    filename = os.path.join(DIR, year, date + "-swaps.csv")
    if os.access(filename, os.R_OK):
        print(f"file {filename} already exists")
        return False

    query = SWAP_V2_QUERY.format(SWAP_V2_JS_CODE, date, V2_SWAP_TOPIC)
    query_job = client.query(query)
    iterator = query_job.result(timeout=300)
    with open(filename, "w") as f:
        s = ["timestamp", "block", "pool", "amount0_in", "amount1_in", "amount0_out", "amount1_out", "to", "tx_hash", "sender"]
        f.write(",".join(s) + "\n")

        for row in iterator:
            timestamp = int(round(row[0].timestamp()))
            block = row[1]
            tx_hash = row[2]
            pool = row[3]
            amount0_in = row[4]
            amount1_in = row[5]
            amount0_out = row[6]
            amount1_out = row[7]
            to = row[8]
            sender = row[9]
            s = [str(u) for u in [timestamp, block, pool, amount0_in, amount1_in,
                                  amount0_out, amount1_out, to, sender, tx_hash]]
            f.write(",".join(s) + "\n")
    return True


def get_pairs(client, date):
    year = date[:4]
    filename = os.path.join(DIR, year, date + "-pairs.csv")
    if os.access(filename, os.R_OK):
        print(f"file {filename} already exists")
        return False

    query_job = client.query(PAIR_QUERY.format(
        PAIR_JS_CODE, V2_FACTORY, date, V2_CREATE_PAIR_TOPIC))
    iterator = query_job.result(timeout=300)
    with open(filename, "w") as f:
        s = ["pair", "token0", "token1", "tx_hash"]
        f.write(",".join(s) + "\n")

        for row in iterator:
            tx_hash = row[0]
            token0 = row[1]
            token1 = row[2]
            pair = row[3]
            s = [str(u) for u in [pair, token0, token1, tx_hash]]
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
        get_pairs(client, d)
        get_v2_swaps(client, d)

if __name__ == "__main__":
    main()
    print("all done")
