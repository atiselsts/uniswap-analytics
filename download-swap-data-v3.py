#!/usr/bin/env python

#
# This file creates a local database of:
# - all Uniswap v3 swaps
# - all new Uniswap v3 pools
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

UNISWAP_VERSION = 3

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

# to match gauntlet
START_DATE = date(2023, 1, 1)
END_DATE = date(2023, 12, 31)

V3_SWAP_TOPIC = "0xc42079f94a6350d7e6235f29174924f928cc2ac818eb64fed8004e115fbcca67"
V3_CREATE_POOL_TOPIC = "0x783cca1c0412dd0d695e784568c96da2e9c22ff989357a2e8b1d9b2b4e6b7118"
V3_FACTORY = "0x1f98431c8ad98523631ae4a59f267346ea31f984"


SWAP_V3_JS_CODE = """
    let parsedEvent = {"anonymous": false, "inputs": [{"indexed": true, "internalType": "address", "name": "sender", "type": "address"}, {"indexed": true, "internalType": "address", "name": "recipient", "type": "address"}, {"indexed": false, "internalType": "int256", "name": "amount0", "type": "int256"}, {"indexed": false, "internalType": "int256", "name": "amount1", "type": "int256"}], "name": "Swap", "type": "event"}
    return abi.decodeEvent(parsedEvent, data, topics, false);
"""

SWAP_V3_QUERY = """
CREATE TEMP FUNCTION
  PARSE_LOG(data STRING, topics ARRAY<STRING>)
  RETURNS STRUCT<`sender` STRING, `recipient` STRING, `amount0` STRING, `amount1` STRING>
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
    ,parsed.amount0 AS `amount0`
    ,parsed.amount1 AS `amount1`
    ,parsed.recipient AS `recipient`
    ,parsed.sender AS `sender`
FROM parsed_logs
ORDER BY block_timestamp, log_index ASC
"""


POOL_JS_CODE = """
    let parsedEvent = {"anonymous": false, "inputs": [{"indexed": true, "internalType": "address", "name": "token0", "type": "address"}, {"indexed": true, "internalType": "address", "name": "token1", "type": "address"}, {"indexed": true, "internalType": "uint24", "name": "fee", "type": "uint24"}, {"indexed": false, "internalType": "int24", "name": "tickSpacing", "type": "int24"}, {"indexed": false, "internalType": "address", "name": "pool", "type": "address"}], "name": "PoolCreated", "type": "event"}
    return abi.decodeEvent(parsedEvent, data, topics, false);
"""

POOL_QUERY = """
CREATE TEMP FUNCTION
  PARSE_LOG(data STRING, topics ARRAY<STRING>)
  RETURNS STRUCT<`token0` STRING, `token1` STRING, `fee` STRING, `pool` STRING>
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
    ,parsed.pool AS `pool`
    ,parsed.fee AS `fee`
FROM parsed_logs
ORDER BY block_timestamp, log_index ASC
"""


def get_v3_swaps(client, date):
    year = date[:4]
    filename = os.path.join(DIR, year, date + "-swaps.csv")
    if os.access(filename, os.R_OK):
        print(f"file {filename} already exists")
        return False

    query = SWAP_V3_QUERY.format(SWAP_V3_JS_CODE, date, V3_SWAP_TOPIC)
    query_job = client.query(query)
    iterator = query_job.result(timeout=300)
    with open(filename, "w") as f:
        s = ["timestamp", "block", "pool", "amount0", "amount1", "to", "sender", "tx_hash"]
        f.write(",".join(s) + "\n")

        for row in iterator:
            timestamp = int(round(row[0].timestamp()))
            block = row[1]
            tx_hash = row[2]
            pool = row[3]
            amount0 = row[4]
            amount1 = row[5]
            to = row[6]
            sender = row[7]
            s = [str(u) for u in [timestamp, block, pool, amount0, amount1, to, sender, tx_hash]]
            f.write(",".join(s) + "\n")
    return True


def get_pools(client, date):
    year = date[:4]
    filename = os.path.join(DIR, year, date + "-pools.csv")
    if os.access(filename, os.R_OK):
        print(f"file {filename} already exists")
        return False

    query_job = client.query(POOL_QUERY.format(
        POOL_JS_CODE, V3_FACTORY, date, V3_CREATE_POOL_TOPIC))
    iterator = query_job.result(timeout=300)
    with open(filename, "w") as f:
        s = ["pool", "token0", "token1", "fee", "tx_hash"]
        f.write(",".join(s) + "\n")

        for row in iterator:
            tx_hash = row[0]
            token0 = row[1]
            token1 = row[2]
            pool = row[3]
            fee = row[4]
            s = [str(u) for u in [pool, token0, token1, fee, tx_hash]]
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
        get_pools(client, d)
        get_v3_swaps(client, d)


if __name__ == "__main__":
    main()
    print("all done")
