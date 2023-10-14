#!/usr/bin/env python

#
# This script estimates proportion of different volume types in a specific Uniswap pool.
#
# Types:
#  1) Sandwich bot volume
#  2) Arbitrage bot volume
#  3) Retail user volume
#  4) Unclasified volume
#
#
# Sandwich bot volume is defined as:
#  1) Same address has multiple tx in a single block, and at least one tx in each direction.
#  2) The address is not a known router or aggregator address.
#
#
# Arbitrage bot volume is defined as:
#  1) Not part of the sandwich volume
#  2) The address is related to a list of MEV bots.
#
#
# Retail user volume:
#  1) The address *is* a known router or aggregator address.
#
# Unclasified volume:
#  The address is a pool internal of the Uniswap, or otherwise classified in any other types.
#
#
# Warning: for now, always assumes that token1 is ETH! Change the code for pools where false!

import os
import matplotlib.pyplot as pl

YEAR = os.getenv("YEAR")
if YEAR is None or len(YEAR) == 0:
    YEAR = "2023"

POOL = os.getenv("POOL")
if POOL is None or len(POOL) == 0:
    POOL = "0xb4e16d0168e52d35cacd2c6185b44281ec28c9dc" # v2 USDC/ETH
POOL = POOL.lower()

DECIMALS = os.getenv("DECIMALS")
if DECIMALS is None or len(DECIMALS) == 0:
    DECIMALS = 6 # for USDC
DECIMALS = int(DECIMALS)

# only v2 supported for now
VERSION = 2

print(f"using pool {POOL} on Uniswap v{VERSION}, year {YEAR}, token0 decimals {DECIMALS}")

self_dir = os.path.dirname(os.path.abspath(__file__))
data_dir = os.path.join(self_dir, "data", f"uniswap-v{VERSION}-swaps", YEAR)


# metamask swap router
# 0x881D40237659C251811CEC9c364ef91dC08D300C (Metamask: Swap Router

trader_addresses = set([
    "0x3fc91a3afd70395cd496c647d5a6cc9d4b2b7fad", # universal router
    "0xef1c6e67703c7bd7107eed8303fbe6ec2554bf6b", # old universal router
    "0x68b3465833fb72a70ecdf485e0e4c7bd8665fc45", # SwapRouter02
    "0x7a250d5630b4cf539739df2c5dacb4c659f2488d", # UniswapV2Router02
    "0x1111111254fb6c44bac0bed2854e76f90643097d", # 1inch
    "0x1111111254eeb25477b68fb85ed929f73a960582", # 1inch
    "0x84d99aa569d93a9ca187d83734c8c4a519c4e9b1", # 1inch resolver
    "0xdef1c0ded9bec7f1a1670819833240f027b25eff", # 0x proxy
    "0xe66b31678d6c16e9ebf358268a790b763c133750", # 0x coinbase wallet proxy
    "0xdef171fe48cf0115b1d80b88dc8eab59176fee57", # paraswap
    "0x74de5d4fcbf63e00296fd95d33236b9794016631", # airswap (unverified contract)
    "0x9008d19f58aabd9ed0d60971565aa8510560ab41", # CoW protocol
    "0x22f9dcf4647084d6c31b2765f6910cd85c178c18", # 0x proxy flash
    "0x555b6ee8fab3dfdbcca9121721c435fd4c7a1fd1", # KyberSwap??? (unverified, unsure)
    "0x58df81babdf15276e761808e872a3838cbecbcf9", # BananaGun (unverified)
])

# includes all mev bots, no matter the type
arb_addresses = set([
    "0x56178a0d5f301baf6cf3e1cd53d9863437345bf9",
    "0x0087bb802d9c0e343f00510000729031ce00bf27",
    "0xc6093fd9cc143f9f058938868b2df2daf9a91d28",
    "0x57c1e0c2adf6eecdb135bcf9ec5f23b319be2c94",
    "0x2a6812a728c61b1f26ffa0749377d6bd7bf7f1f8",
    "0x7122db0ebe4eb9b434a9f2ffe6760bc03bfbd0e0", # this is from 1inch, but looks like a mev bot
    "0x53222470cdcfb8081c0e3a50fd106f0d69e63f20", # same here
    "0x1136b25047e142fa3018184793aec68fbb173ce4", # same here
    "0x92f3f71cef740ed5784874b8c70ff87ecdf33588", # same here
    "0xbfef411d9ae30c5b471d529c838f1abb7b65d67f",
    "0x3b17056cc4439c61cea41fe1c9f517af75a978f7",
    "0x00000000008c4fb1c916e0c88fd4cc402d935e7d",
    "0xa69babef1ca67a37ffaf7a485dfff3382056e78c",
    "0xc79c30ef1941002c54293a028cf252dfb0ddd2aa", # this looks like atomic arb bot
    "0x5050e08626c499411b5d0e0b5af0e83d3fd82edf",
    "0xf8b721bff6bf7095a0e10791ce8f998baa254fd0",
    "0x280027dd00ee0050d3f9d168efd6b40090009246",
    "0x6b75d8af000000e20b7a7ddf000ba900b4009a80",
    "0x51c72848c68a965f66fa7a88855f9f7784502a7f", # likely a MEV bot
    "0xe8cfad4c75a5e1caf939fd80afcf837dde340a69",
    "0x98c3d3183c4b8a650614ad179a1a98be0a8d6b8e",
    "0xd050e0a4838d74769228b49dff97241b4ef3805d",
    "0xd249942f6d417cbfdcb792b1229353b66c790726",
    "0xe8c060f8052e07423f71d445277c61ac5138a2e5",
    "0x9dd864d39fbfdf7648402746263e451cd4f36af0",
    "0x4a137fd5e7a256ef08a7de531a17d0be0cc7b6b6",
    "0x000000000035b5e5ad9019092c665357240f594e",
    "0x9878644ad744a970d3598594f1cdbb1389c17826",
    "0x0000000000dbb5048a563bcec00787ddb2152b1e",
    "0x000000000005af2ddc1a93a03e9b7014064d3b8d",
    "0x0000000099cb7fc48a935bceb9f05bbae54e8987",
    "0x00000000003b3cc22af3ae1eac0440bcee416b40",
    "0x6dce52e318338b0cc30969ada8e0c95d24c37a28",
    "0x0998b994b9ce16d8b8593323e679053e303b2ea9",
    "0x429cf888dae41d589d57f6dc685707bec755fe63",
    "0x0ef8b4525c69bfa7bdece3ab09f95bbf0944b783",
    "0x6db01031355fbf8eea0c06a5d56217ba1967f0df",
    "0x6980a47bee930a4584b09ee79ebe46484fbdbdd0",
    "0xf70a5d557976191e4dac37a425b6432773511b79",
])

internal_addresses = set([
    "0x5083b16da538c5022744526122243cf3bddb3bf2", # ALI/USDC pool
    "0x88e6a0c2ddd26feeb64f039a2c41296fcb3f5640", # v3 USDC/WETH pool
    "0xe471f93c2be15b64e9ec63bbf485446cb934e8c4", # ImgAI/WETH
    "0xa43fe16908251ee70ef74718545e4fe6c5ccec9f", # pepe/WETH
    "0x8dbee21e8586ee356130074aaa789c33159921ca", # unibot/WETH
    "0x67cea36eeb36ace126a3ca6e21405258130cf33c", # tsuka/USDC
    "0x659e36b0700d9addb259eba18fa88173656ef054", # HILO/USDC
    "0x2cc846fff0b08fb3bffad71f53a60b4b6e6d6482", # BITCOIN
    "0x0d4a11d5eeaac28ec3f61d100daf4d40471f1852", # USDT
    "0xca7c2771d248dcbe09eabe0ce57a62e18da178c0", # FLOKI/WETH
    "0xc54ba7aabe7164ca2aa092900060fe2ba6eccd8b", # EGGS/WETH
    "0x9ec9367b8c4dd45ec8e7b800b1f719251053ad60", # 0xAI/WETH
    "0x11181bd3baf5ce2a478e98361985d42625de35d1", # Asto/
    "0xe59fd78557093a0beb569369ef8f47bc48a32c75",
    "0x06cd6245156c3608ae67d690c125e86a8bc6a88c",
    "0x55d5c232d921b9eaa6b37b5845e439acd04b4dba",
    "0x5281e311734869c64ca60ef047fd87759397efe6",
    "0x684b00a5773679f88598a19976fbeb25a68e9a5f",
    "0xbe8bc29765e11894f803906ee1055a344fdf2511",
])

#known_addresses = trader_addresses + arb_addresses + internal_addresses

def load_csv(filename):
    result = []
    with open(os.path.join(data_dir, filename)) as f:
        f.readline() # skip the header
        for line in f.readlines():
            fields = line.strip().split(",")
            if len(fields) == 0:
                continue
            pool = fields[2]
            if pool != POOL:
                continue
            result.append(fields)
    return result


# MEV sandwiching is defined as buy & sell in a single block
def account_for_mev(eth_buyers, eth_sellers):
    maybe_sandwichers = set(eth_buyers.keys()).intersection(set(eth_sellers.keys()))
    other_traders = set(eth_buyers.keys()).symmetric_difference(set(eth_sellers.keys()))

    sandwich = 0
    arb = 0
    retail = 0
    other = 0

    for address in maybe_sandwichers:
        # classify based on address
        volume = eth_buyers.get(address, 0) + eth_sellers.get(address, 0)

        if address in trader_addresses:
            retail += volume
        elif address in arb_addresses:
            # print("sandwich, ", address)
            sandwich += volume
        elif address in internal_addresses:
            other += volume
        else:
            if volume > 1e9:
                print("unknown sandwicher address:", address, volume / 1e6)
            other += volume

    for address in other_traders:
        # classify based on address
        volume = eth_buyers.get(address, 0) + eth_sellers.get(address, 0)

        if address in trader_addresses:
            retail += volume
        elif address in arb_addresses:
            #print("arb, ", address, volume)
            arb += volume
        else:
            other += volume

    return sandwich, arb, retail, other


def classify_trades(data):
    current_block = None # start from a fresh block
    eth_buyers = {}
    eth_sellers = {}

    volume_sandwich = 0
    volume_arb = 0
    volume_retail = 0
    volume_other = 0

    block_volume_sandwich = {True: 0, False: 0}
    block_volume_token0_in = 0
    block_volume_token0_out = 0

    # token0: e.g. USDC, token1: ETH
    for row in data:
        if VERSION == 2:
            (_, block, _, amount0_in, amount1_in, amount0_out, amount1_out, address, _) = row
            amount0_in = int(amount0_in)
            amount0_out = int(amount0_out)

            # remove fake "volume" created due to pool imbalance, returned to the swapper due to sync() call
            if amount0_in > 0 and amount0_out > 0:
                if amount0_in > amount0_out:
                    amount0_in -= amount0_out
                    amount0_out = 0
                else:
                    amount0_out -= amount0_in
                    amount0_in = 0

        if current_block != block:
            current_block = block
            # account for MEV in the block
            sandwich, arb, retail, other = account_for_mev(eth_buyers, eth_sellers)
            volume_sandwich += sandwich
            volume_arb += arb
            volume_retail += retail
            volume_other += other

            # clean up state; look only at single-block MEV
            eth_buyers = {}
            eth_sellers = {}

        if amount0_out > 0:
            # selling ETH, account for USDC volume, including the fee
            eth_sellers[address] = eth_sellers.get(address, 0) + amount0_out
        elif amount0_in > 0:
            eth_buyers[address] = eth_buyers.get(address, 0) + amount0_in

    # process the final block
    sandwich, arb, retail, other = account_for_mev(eth_buyers, eth_sellers)
    volume_sandwich += sandwich
    volume_arb += arb
    volume_retail += retail
    volume_other += other
            
    return (volume_sandwich, volume_arb, volume_retail, volume_other)


def main():
    days = []
    all_stats = []
    
    for filename in sorted(os.listdir(data_dir)):
        if "-swaps.csv" in filename:
            data = load_csv(filename)
            days.append(filename.split("-swaps")[0])
            day_stats = classify_trades(data)
            print(day_stats)
            all_stats.append(day_stats)
#            if len(all_stats) >= 20:
#                break

    coeff    = 1e12
#    coeff    = 1e8
    sandwich = [u[0] / coeff for u in all_stats]
    arb      = [u[1] / coeff for u in all_stats]
    retail   = [u[2] / coeff for u in all_stats]
    other    = [u[3] / coeff for u in all_stats]

    C = ['darkgreen', 'orange', 'red', 'grey']

    pl.figure()
    pl.plot([], [], color ='darkgreen', label ='Retail')
    pl.plot([], [], color ='orange', label='Arbitrage')      
    pl.plot([], [], color ='red', label='Sandwich')
    pl.plot([], [], color ='grey', label='Unclassified')

    x = range(len(all_stats))
    pl.stackplot(x, retail, arb, sandwich, other, colors=C)
    pl.xlabel("Day")
    pl.ylabel("Volume, $ million")
#    pl.ylabel("Volume, BTC")
    pl.legend()
    pl.show()
    pl.close()

    # pie chart
    fig, ax = pl.subplots()
    sizes = [sum(retail), sum(arb), sum(sandwich), sum(other)]
    labels = ["Retail", "Arb", "Sandwich", "Unclassified"]
    ax.pie(sizes, labels=labels, autopct='%1.1f%%',
           pctdistance=1.25, labeldistance=.6, colors=C)
    pl.show()


    # get proportional plots
    # (don't seriously do this, this can get completely wrong visually!!!)
    sandwich = [u[0] / coeff / sum(u) for u in all_stats]
    arb      = [u[1] / coeff / sum(u) for u in all_stats]
    retail   = [u[2] / coeff / sum(u) for u in all_stats]
    other    = [u[3] / coeff / sum(u) for u in all_stats]

    pl.stackplot(x, retail, arb, sandwich, other, colors=C)
    pl.xlabel("Day")
    pl.ylabel("Volume, $ million")
    pl.legend()
    pl.show()
    pl.close()




if __name__ == "__main__":
    main()
