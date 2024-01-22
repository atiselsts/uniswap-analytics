#!/usr/bin/env python

#
# This script estimates proportion of different volume types in a specific Uniswap pool.
#
# Types:
#  1) Sandwich bot volume
#  2) Arbitrage bot volume
#  3) Core user volume (retail and other traders)
#  4) Unclasified volume
#
#
# Sandwich bot volume is defined as:
#  1) Same address has multiple tx in a single block, and at least one tx in each direction.
#  2) The address is not a known router or aggregator address.
#
#
# Arbitrage volume is defined as:
#  1) Not part of the sandwich volume
#  2) The address is related to a list of MEV bots.
#
#
# Core volume:
#  1) The address *is* a known router or aggregator address.
#
# Unclassified volume:
#  The address is not classified in any other types.
#
#
# Warning: for now, this code makes assumptions on the token decimals when computing the volumes.
# Change the code for pools other than WETH/USDC!

import os
import matplotlib.pyplot as pl
pl.rcParams["savefig.dpi"] = 200

YEAR = os.getenv("YEAR")
if YEAR is None or len(YEAR) == 0:
    YEAR = "2023"

# Pools:
# * v2 USDC/ETH pool ($59.5M TVL):   0xb4e16d0168e52d35cacd2c6185b44281ec28c9dc
# * v3 USDC/ETH 0.3% ($97.4M TVL):   0x8ad599c3a0ff1de082011efddc58f1908eb6e6d8
# * v3 USDC/ETH 0.05% ($272.6M TVL): 0x88e6a0c2ddd26feeb64f039a2c41296fcb3f5640
POOL = os.getenv("POOL")
if POOL is None or len(POOL) == 0:
    POOL = "0xb4e16d0168e52d35cacd2c6185b44281ec28c9dc"
POOL = POOL.lower()

VERSION = os.getenv("VERSION")
if VERSION is None or len(VERSION) == 0:
    VERSION = 2
VERSION = int(VERSION)

print(f"using pool {POOL} on Uniswap v{VERSION}, year {YEAR}")

self_dir = os.path.dirname(os.path.abspath(__file__))
data_dir = os.path.join(self_dir, "..", "data", f"uniswap-v{VERSION}-swaps", YEAR)

trader_addresses = set([
    "0xef1c6e67703c7bd7107eed8303fbe6ec2554bf6b", # Uniswap UniversalRouter
    "0x3fc91a3afd70395cd496c647d5a6cc9d4b2b7fad", # Uniswap UniversalRouterV1_2
    "0x3f6328669a86bef431dc6f9201a5b90f7975a023", # Uniswap UniversalRouterV1_3 (unofficial)
    "0xe592427a0aece92de3edee1f18e0157c05861564", # Uniswap SwapRouter
    "0x68b3465833fb72a70ecdf485e0e4c7bd8665fc45", # Uniswap SwapRouter02
    "0x7a250d5630b4cf539739df2c5dacb4c659f2488d", # UniswapV2Router02
    "0xf164fc0ec4e93095b804a4795bbe1e041497b92a", # Uniswap V2: Router (old)

    "0x1111111254fb6c44bac0bed2854e76f90643097d", # 1inch
    "0x1111111254eeb25477b68fb85ed929f73a960582", # 1inch
    "0x11111112542d85b3ef69ae05771c2dccff4faa26", # 1inch
    "0x84d99aa569d93a9ca187d83734c8c4a519c4e9b1", # 1inch resolver

    "0xdef1c0ded9bec7f1a1670819833240f027b25eff", # 0x proxy
    "0xe66b31678d6c16e9ebf358268a790b763c133750", # 0x coinbase wallet proxy
    "0xdef171fe48cf0115b1d80b88dc8eab59176fee57", # paraswap
    "0x74de5d4fcbf63e00296fd95d33236b9794016631", # airswap (unverified contract)
    "0x9008d19f58aabd9ed0d60971565aa8510560ab41", # CoW protocol
    "0x22f9dcf4647084d6c31b2765f6910cd85c178c18", # 0x proxy flash
    "0x555b6ee8fab3dfdbcca9121721c435fd4c7a1fd1", # KyberSwap??? (unverified, unsure)
    "0x58df81babdf15276e761808e872a3838cbecbcf9", # BananaGun (unverified)
    "0x3328f7f4a1d1c57c35df56bbf0c9dcafca309c49", # BananaGun Router 2
    "0xc6265979793435b496e28e61af1500c22c3ba277", # BananaGun (unverified)
    "0xf65f4ab80491fb8db2ecd1ffc63e779261bf0b36", # firebird aggregator
    "0x5b599155ade1f59f549a4a1297ddb5a4951b1b27", # KibaSwapRelayer
    "0x2ec705d306b51e486b1bc0d6ebee708e0661add1", # KibaSwap router? (unverified contract)

    "0x4fe5b965e3bd76eff36280471030ef9b0e6e2c1d", # kyberswap meta aggregator related?
    "0xd1b47490209ccb7a806e8a45d9479490c040abf4", # kyberswap meta aggregator related?
    "0xf081470f5c6fbccf48cc4e5b82dd926409dcdd67", # something to do with kyberswap?
    "0x6c77ac51c3b5dc5fa09fdee21acd83ff3a7c4436", # Swap Executor (Kyber?)

    "0x80a64c6d7f12c47b7c66c5b4e20e72bc1fcd5d9e", # Maestro Router

    "0x2c2c82e7caf5f14e4995c366d9db8cdfdf7677e3", # Shuriken Swap

    "0x6352a56caadc4f1e25cd6c75970fa768a3304e64", # OpenOcean: Exchange

    # 1inch internal stuff (some of this could be arbitrage?)
    "0x53222470cdcfb8081c0e3a50fd106f0d69e63f20",
    "0x7122db0ebe4eb9b434a9f2ffe6760bc03bfbd0e0",
    "0x1136b25047e142fa3018184793aec68fbb173ce4",
    "0x92f3f71cef740ed5784874b8c70ff87ecdf33588",
    "0xa77c88abcaa770c54a6cfbfd0c586a475537bbc1",
    "0xe37e799d5077682fa0a244d46e5649f71457bd09",
    "0x3208684f96458c540eb08f6f01b9e9afb2b7d4f0",

    "0x1d94bedcb3641ba060091ed090d28bbdccdb7f1d", # some CoW protocol stuff
    "0x23ebcd701fd92867235aeb0174b7c444b9b2b3ad", # some CoW protocol stuff

    "0xf9234cb08edb93c0d4a4d4c70cc3ffd070e78e07", # NewUniswapV2ExchangeRouter
])

#
# these next list further separate the known addresses by the protocol
#
uniswap_related_addrs = [
    "0xef1c6e67703c7bd7107eed8303fbe6ec2554bf6b", # Uniswap UniversalRouter
    "0x3fc91a3afd70395cd496c647d5a6cc9d4b2b7fad", # Uniswap UniversalRouterV1_2
    "0x3f6328669a86bef431dc6f9201a5b90f7975a023", # Uniswap UniversalRouterV1_3 (unofficial)
    "0xe592427a0aece92de3edee1f18e0157c05861564", # Uniswap SwapRouter
    "0x68b3465833fb72a70ecdf485e0e4c7bd8665fc45", # Uniswap SwapRouter02
    "0x7a250d5630b4cf539739df2c5dacb4c659f2488d", # UniswapV2Router02
    "0xf164fc0ec4e93095b804a4795bbe1e041497b92a", # Uniswap V2: Router (old)
]

oneinch_related_addrs = [
    "0x1111111254fb6c44bac0bed2854e76f90643097d", # 1inch
    "0x1111111254eeb25477b68fb85ed929f73a960582", # 1inch
    "0x11111112542d85b3ef69ae05771c2dccff4faa26", # 1inch
    "0x84d99aa569d93a9ca187d83734c8c4a519c4e9b1", # 1inch resolver

    "0x53222470cdcfb8081c0e3a50fd106f0d69e63f20",
    "0x7122db0ebe4eb9b434a9f2ffe6760bc03bfbd0e0",
    "0x1136b25047e142fa3018184793aec68fbb173ce4",
    "0x92f3f71cef740ed5784874b8c70ff87ecdf33588",
    "0xa77c88abcaa770c54a6cfbfd0c586a475537bbc1",
    "0xe37e799d5077682fa0a244d46e5649f71457bd09",
    "0x3208684f96458c540eb08f6f01b9e9afb2b7d4f0",

]

cowswap_related_addrs = [
    "0x9008d19f58aabd9ed0d60971565aa8510560ab41", # CoW protocol
    "0x1d94bedcb3641ba060091ed090d28bbdccdb7f1d", # some CoW protocol stuff
    "0x23ebcd701fd92867235aeb0174b7c444b9b2b3ad", # some CoW protocol stuff
]

other_trader_addresses = [a for a in trader_addresses if \
                          (a not in uniswap_related_addrs) \
                          and (a not in oneinch_related_addrs) \
                          and (a not in cowswap_related_addrs)]

# also:
# 0xe0C38b2a8D09aAD53f1C67734B9A95E43d5981c0 (Firebird Finance: Aggregator Router)

#
# includes all mev bots, no matter the type (trading/sandwich/arbitrage/liquidation...)
#
arb_addresses = set([
    "0x56178a0d5f301baf6cf3e1cd53d9863437345bf9",
    "0x0087bb802d9c0e343f00510000729031ce00bf27",
    "0xc6093fd9cc143f9f058938868b2df2daf9a91d28",
    "0x57c1e0c2adf6eecdb135bcf9ec5f23b319be2c94",
    "0x2a6812a728c61b1f26ffa0749377d6bd7bf7f1f8",
    "0xbfef411d9ae30c5b471d529c838f1abb7b65d67f",
    "0x3b17056cc4439c61cea41fe1c9f517af75a978f7",
    "0x00000000008c4fb1c916e0c88fd4cc402d935e7d",
    "0xa69babef1ca67a37ffaf7a485dfff3382056e78c",
    "0xc79c30ef1941002c54293a028cf252dfb0ddd2aa", # atomic arb bot
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
    "0x4a137fd5e7a256ef08a7de531a17d0be0cc7b6b6", # also strange
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
    "0xd4674001a9a66b31f3c09e3b1fec465404c83d35",
    "0xb5dc0a1c9fc1cf334e0d81d773638a277c2ead7d",
    "0x25553828f22bdd19a20e4f12f052903cb474a335",
    "0x585c3d4da9b533c7e3df8ac7356c882859298cee",
    "0x0000e0ca771e21bd00057f54a68c30d400000000",
    "0x00000000032962b51589768828ad878876299e14",
    "0xe4000004000bd8006e00720000d27d1fa000d43e",
    "0x4a5a7331da84d3834c030a9b8d4f3d687a3b788b",
    "0x76b5a83c8c8097e7723eda897537b6345789b229",
    "0x127350408e658c8a02c588d3487f11939fb20110",
    "0x50d148d0908c602a56884b8628a36470a875eeb2", # atomic arb bot?
    "0x0eae044f00b0af300500f090ea00027097d03000",
    "0x05656db19ec9ff8dfb437475b3d76ca9a29e968f",
    "0x607083af03af0c01bfccdaf956b06b2f0d4ba82b",
    "0xed77777586d73c58eb4d6bebdf9c85c2d5f56c2d",
    "0xc1374db508b7a3e0cdf061c8d8c1f7a260f231cd",
    "0xfb5185b7f8c61f815b57de679bbc857f510352f7",
    "0xccc2b577e8506eae1c0e5ee4dfc812f14dc86ac1",
    "0xd1742b3c4fbb096990c8950fa635aec75b30781a", # Seawise: Resolver
    "0xe3e53f468d5658d217412203463246af76d7db37",

    "0xbc2c6cd5013585ac720160efcb1feced30837177",
    "0xd7f3fbe8c72a961a5515203eada59750437fa762",
    "0x1c09a10047fcc944efde9226e259eddfde2c1cf0",
    "0x28e261390adaa654f29dbe268109baf06e9b4cc4", # this could be a legit router? does not look like a MEV bot
    "0x6719c6ebf80d6499ca9ce170cda72beb3f1d1a54",
    "0x493f461aead031cee2027f1b95370a692611acb9",
    "0x767c8bb1574bee5d4fe35e27e0003c89d43c5121",

    "0xbadffffffff3f678866b558e3fd0a2a4deb4dc48", # atomic arb bot

    "0x085a393044b24217b3e099654bb97f01d1563b62", # doing some flash loans
    "0x07bae765074790b76c791834ab873be27493c163",
    "0xc7dab6742619707440f44ae3b23768a18067c665",
    "0xa37a714a14a1d3d969bd2a9f10e029d02e77bfcb", # a few sandwich attacks
    "0x6d909e8b0bbb7ab996381e0a44d82d6d97fd9041", # sandwich
    "0xcb3702bc25b0f284b032e5edf1a1ebea2fe43255", # sandwich
    "0xac6a9e9ca65d4bcbea3e59c4c40128052bcc8882", # sandwich
    "0x00000000d40107239fa2b85be64b4e981e3bfdfc",
    "0x459579e5a987559bdb97bfb30ec1c572e64b5b5f",
    "0x5e51328c0583094b76f28cfd532abc3d454fcfea",
    "0x64545160d28fd0e309277c02d6d73b3923cc4bfa",
    "0x7d32c90762e22379235fc311fdb16fab399ed40a",
    "0x684f5c4c571f5a225646a060664a350772c97968",
    "0x875012b086cca9976463e18ea1d76b6c5e43e487", # sandwich
    "0x80d4230c0a68fc59cb264329d3a717fcaa472a13", # sandwich
    "0x83bc685ebd7e641f83f45cecdfe62b87afaef9c7", # probably sandwich
    "0xbf237a593a830b4720095a8807706fc7ae01e6dd",
    "0x3c0756ba2b1d702f8f63629555625b11be81546f",
    "0x9b7ee9fd51fc044e18d8ff44a1616b04b2ddea75",
    "0x93dabae1444daafd630d6b4a2d544ecfa4955579",
    "0x03c609c569993913aab877a94c8e58aec13e67cc",

    "0x9507c04b10486547584c37bcbd931b2a4fee9a41", # Jump Trading
    "0x6f1cdbbb4d53d226cf4b917bf768b94acbab6168",

    "0x2d2a7d56773ae7d5c7b9f1b57f7be05039447b4d",

    # the following list is found simply by counting zeroes, might not be reliable!
    "0x24902aa0cf0000a08c0ea0b003b0c0bf600000e0",
    "0x3b3ae790df4f312e745d270119c6052904fb6790",
    "0x00000007f7a9056880d057f611e80c419f9b20c8",
    "0x0000000000a84d1a9b0063a910315c7ffa9cd248",
    "0xfd0000000100069ad1670066004306009b487ad7",
    "0x0773edc0438b2ef18fc535b21d0ac77912c308c0",
    "0x00db464000004addd87bca92416ea100e600cb48",
    "0x0000000000007f150bd6f54c40a34d7c3d5e9f56",
    "0xa80db00007020e013fa10d0560700c0018003b8b",
    "0x5ff1de9214e2e188e1a7602002f5689a19690501",
    "0xf71530c1f043703085b42608ff9dcccc43210a8e",
    "0x0090eb43008a030065000000e70099482c00b6df",
    "0x0000000000304a767881fdccb30fceb51f6221e2",
    "0xa1006d0051a35b0000f961a8000000009ea8d2db",
    "0x7c0c078f1eb5d471579cef0ce4e089b70e1bf21e",
    "0x00000000c2cf7648c169b25ef1c217864bfa38cc",
    "0x000000c0524f353223d94fb76efab586a2ff8664",
    "0x0055ae46f700bcc53b1b00483d64000d47007200",
    "0x86ecd42504fead01409901f41cda45a0f8c54e71",
    "0x0000000000753a65f1917d8db21c8897e6af1979",
    "0x0000000f9c4e004706afdca3b2f0c8f08838eb58",
    "0x00000000000006b2ab6decbc6fc7ec6bd2fbc720",
    "0x00fc00900000002c00be4ef8f49c000211000c43",
    "0x00000000009e50a7ddb7a7b0e2ee6604fd120e49",
    "0x770e2e68000065ac970382fe3af0d500bb00a200",
    "0x00000000de337b4fff5fcbe4df67a85d0bad5d16",
    "0x5e00f600e7003200f081539ee5006eb200b49100",
    "0x5079fc00f00f30000e0c8c083801cfde000008b6",
    "0x000000000dfde7deaf24138722987c9a6991e2d4",
    "0x0000690000a5fe503ac89500eb11519c2dc00084",
    "0x660000c7feae0027f565680000005c683400e700",
    "0x7d00a2bc1370b9005eb100004da500924600a2e1",
    "0x2f00d9113515eeb40000cb7af3c700266d4eb400",
    "0x3de8eb830000f1d914294d000051000031a81d00",
    "0x0000000000450702bc4f750fd1e7ecad7054c4f1",
    "0x006a3d00df1b5c6a006b11d8000000d557622100",
    "0x00000000000747d525e898424e8774f7eb317d00",
    "0x00000000003d71e9fc20fdeb46fb86afbbee4772",
    "0x00000000f0b4b9973900fd541719cbbc1a5862d8",
    "0x0000000038355af6ffd5328a16cfd2170e59f39c",
    "0x000000000c923384110e9dca557279491e00f521",
    "0x0000cd00001700b10049dfc947103e00e1c62683",
    "0xe30062750007002400ba00c47e004a0600e500fb",
    "0x356cfd6e6d0000400000003900b415f80669009e",
    "0x120d9eed00890000bd25c59de403234039000086",
    "0x000000000000be0ab658f92dddac29d6df19a3be",
    "0x00000000ede6d8d217c60f93191c060747324bca",
    "0x25e849e019000018d8e400bf0007000888e66000",
    "0x67004e26f800c5eb050000200075f049aa0090c3",
    "0x000000000c1500d6cf5a65167f131a53c82c1033",
    "0x0035146a0000af00ef048f0000e80061a10014cb",
    "0x000000000000df8c944e775bde7af50300999283",
    "0x0000000000036414940324055c43e75f56b7d016",
    "0xc9001ac3bb95000000005aea00001b3d4ab86898",
    "0xb39bae8bc7003bf25b81a03d00006f70b900007c",
    "0xb0000000aa4f00af1200c8b2befb6300853f0069",
    "0x000000001d68ffe32f650281ff45ffcb93b055a5",
    "0x0000000000505832f1ab6459bae9198f92a8a53b",
    "0x0000900e00070d8090169000d2b090b67f0c1050",
    "0x000000004cdb5dd2343aca9228f7ed2700754d3b",
])

#
# a few of the MEV bots actually do use routers from the first list above
#
MEV_BOTS_USING_ROUTERS = [
    "0x4a137fd5e7a256ef08a7de531a17d0be0cc7b6b6",
    "0xd050e0a4838d74769228b49dff97241b4ef3805d",
    "0x56178a0d5f301baf6cf3e1cd53d9863437345bf9",

    "0xd1742b3c4fbb096990c8950fa635aec75b30781a", # Seawise: Resolver - sender is 1inch and other addresses

    "0x000000c0524f353223d94fb76efab586a2ff8664",
    "0x6980a47bee930a4584b09ee79ebe46484fbdbdd0",

    "0x085a393044b24217b3e099654bb97f01d1563b62",
    "0x86ecd42504fead01409901f41cda45a0f8c54e71",
]

# This strange address is just some guy doing some trading (until running out of gas).
# it shows up a as a sandwicher, but probably isn't.
#
# 0x11a2e73bada26f184e3d508186085c72217dc014

#
# These are among the most widely used "to" addresses, for multihop swaps
#
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

# ==================================================

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
def account_for_mev(block, eth_buyers, eth_sellers):
    maybe_sandwichers = set(eth_buyers.keys()).intersection(set(eth_sellers.keys()))
    other_traders = set(eth_buyers.keys()).symmetric_difference(set(eth_sellers.keys()))

    sandwich = 0
    arb = 0
    core = 0
    other = 0

    for address in maybe_sandwichers:
        # classify based on address
        volume = eth_buyers.get(address, 0) + eth_sellers.get(address, 0)

        if address in trader_addresses:
            core += volume
        elif address in arb_addresses:
            sandwich += volume
        elif address in internal_addresses:
            other += volume
        else:
            if volume > 1e11:
                print("unknown large sandwicher address:", address, volume / 1e6)
            other += volume

    for address in other_traders:
        # classify based on address
        volume = eth_buyers.get(address, 0) + eth_sellers.get(address, 0)

        if address in trader_addresses:
            core += volume
        elif address in arb_addresses:
            arb += volume
        else:
            other += volume

    return sandwich, arb, core, other


def classify_protocols(eth_buyers, eth_sellers):
    uniswap = 0
    oneinch = 0
    cowswap = 0
    other = 0
    for key in eth_buyers:
        if key in uniswap_related_addrs:
            uniswap += eth_buyers[key]
        elif key in oneinch_related_addrs:
            oneinch += eth_buyers[key]
        elif key in cowswap_related_addrs:
            cowswap += eth_buyers[key]
        elif key in other_trader_addresses:
            other += eth_buyers[key]

    for key in eth_sellers:
        if key in uniswap_related_addrs:
            uniswap += eth_sellers[key]
        elif key in oneinch_related_addrs:
            oneinch += eth_sellers[key]
        elif key in cowswap_related_addrs:
            cowswap += eth_sellers[key]
        elif key in other_trader_addresses:
            other += eth_sellers[key]

    return uniswap, oneinch, cowswap, other


def classify_trades(data, unknowns):
    current_block = None # start from a fresh block
    eth_buyers = {}
    eth_sellers = {}

    volume_sandwich = 0
    volume_arb = 0
    volume_core = 0
    volume_other = 0

    volume_uni = 0
    volume_1inch = 0
    volume_cowsap = 0
    volume_other_proto = 0

    # token0: e.g. USDC, token1: ETH
    for row in data:
        #
        # Extract block number and amounts
        #
        if VERSION == 2:
            (_, block, _, amount0_in, amount1_in, amount0_out, amount1_out, to, sender, tx_hash) = row
            block = int(block)

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

        elif VERSION == 3:
            (_, block, _, amount0, amount1, to, sender, tx_hash) = row
            block = int(block)

            amount0 = int(amount0)
            amount1 = int(amount1)

            # the negative amount is given to the user
            if amount0 > 0:
                amount0_in = amount0
                amount0_out = 0
            else:
                amount0_in = 0
                amount0_out = -amount0

        #
        # Decide which address to use to classify the swap.
        # In general, always prefer bots, if there is a doubt.
        #

        to_is_bot = to in arb_addresses
        sender_is_bot = sender in arb_addresses

        to_is_trader = to in trader_addresses
        sender_is_trader = sender in trader_addresses

        select_sender = False
        select_to = False

        if sender_is_bot:
            select_sender = True
            if to_is_trader:
                print("sender is bot, but to is trader:", sender, to, tx_hash)
                #assert False
        elif to_is_bot:
            select_to = True
            if sender_is_trader:
                pass
                # if to not in MEV_BOTS_USING_ROUTERS:
                #    print("sender is trader, but to is bot:", sender, to, tx_hash)
        elif sender_is_trader:
            select_sender = True
        elif to_is_trader:
            select_to = True

        if select_to:
            address = to
        elif select_sender:
            address = sender
        else:
            # neither to nor the sender matched a known address
            unknowns[sender] = unknowns.get(sender, 0) + 1
            unknowns[to] = unknowns.get(to, 0) + 1
            # by default, use the sender's address
            address = sender

        if current_block != block:
            # account for MEV in the block
            sandwich, arb, core, other = account_for_mev(current_block, eth_buyers, eth_sellers)
            current_block = block
            volume_sandwich += sandwich
            volume_arb += arb
            volume_core += core
            volume_other += other

            u, i, c, o = classify_protocols(eth_buyers, eth_sellers)
            volume_uni += u
            volume_1inch += i
            volume_cowsap += c
            volume_other_proto += o

            # clean up state; look only at single-block MEV
            eth_buyers = {}
            eth_sellers = {}

        if amount0_out > 0:
            # selling ETH, account for USDC volume, including the fee
            eth_sellers[address] = eth_sellers.get(address, 0) + amount0_out
        elif amount0_in > 0:
            eth_buyers[address] = eth_buyers.get(address, 0) + amount0_in

    # process the final block
    sandwich, arb, core, other = account_for_mev(current_block, eth_buyers, eth_sellers)
    volume_sandwich += sandwich
    volume_arb += arb
    volume_core += core
    volume_other += other

    u, i, c, o = classify_protocols(eth_buyers, eth_sellers)
    volume_uni += u
    volume_1inch += i
    volume_cowsap += c
    volume_other_proto += o

    #num_total = len(data)
    #prop_unknown = num_unknowns / num_total
    #print(100 * prop_unknown)

    return (volume_sandwich, volume_arb, volume_core, volume_other, volume_uni, volume_1inch, volume_cowsap, volume_other_proto)


def main():
    days = []
    all_stats = []

    unknowns = {}

    for filename in sorted(os.listdir(data_dir)):
        if "-swaps.csv" in filename:
            print(filename)
            data = load_csv(filename)
            days.append(filename.split("-swaps")[0])
            day_stats = classify_trades(data, unknowns)
            print(day_stats)
            all_stats.append(day_stats)

    print("unclassified traders:")
    unknowns = list(unknowns.items())
    unknowns.sort(key=lambda x: -x[1])
    for i in range(min(len(unknowns), 10)):
        print(unknowns[i])

    print("unclassified traders with many zeros in addresses:")
    for i in range(len(unknowns)):
        k, v = unknowns[i]
        if v < 10:
            break
        c = k.count("0")
        if c >= 10:
            print(f'    "{k}",')


    coeff    = 1e12
    sandwich = [u[0] / coeff for u in all_stats]
    arb      = [u[1] / coeff for u in all_stats]
    core     = [u[2] / coeff for u in all_stats]
    other    = [u[3] / coeff for u in all_stats]

    C = ['darkgreen', 'orange', 'red', 'grey']

    pl.figure()
    pl.plot([], [], color ='darkgreen', label ='Core')
    pl.plot([], [], color ='orange', label='Arbitrage')      
    pl.plot([], [], color ='red', label='Sandwich')
    pl.plot([], [], color ='grey', label='Unclassified')

    x = range(len(all_stats))
    pl.stackplot(x, core, arb, sandwich, other, colors=C)
    pl.xlabel("Day in 2023")
    pl.ylabel("Volume, $ million")
    pl.legend()
    #pl.show()
    pl.savefig(f"{YEAR}-classification-by-day-v{VERSION}.png", bbox_inches='tight')
    pl.close()

    
    uni      = [u[4] / coeff for u in all_stats]
    oneinch  = [u[5] / coeff for u in all_stats]
    cowswap  = [u[6] / coeff for u in all_stats]
    other_proto  = [u[7] / coeff for u in all_stats]

    C_protocol = ['purple', 'darkblue', 'white', "grey"]
    pl.figure()
    pl.plot([], [], color ='purple', label ='Uniswap')
    pl.plot([], [], color ='darkblue', label='1inch')
    pl.plot([], [], color ='white', label='Cowswap')
    pl.plot([], [], color ='grey', label='Other')

    x = range(len(all_stats))
    # normalize the values
    uni = [100 * u[4] / sum(u[4:]) for u in all_stats]
    oneinch = [100 * u[5] / sum(u[4:]) for u in all_stats]
    cowswap = [100 * u[6] / sum(u[4:]) for u in all_stats]
    other_proto = [100 * u[7] / sum(u[4:]) for u in all_stats]
    pl.stackplot(x, uni, oneinch, cowswap, other_proto, colors=C_protocol)
    pl.xlabel("Day in 2023")
    pl.ylabel("Volume, %")
    #pl.legend()
    #pl.show()
    pl.savefig(f"{YEAR}-protocol-classification-by-day-v{VERSION}.png", bbox_inches='tight')
    pl.close()


    # pie chart
    fig, ax = pl.subplots()
    sizes = [sum(core), sum(arb), sum(sandwich), sum(other)]
    labels = ["Core", "Arbitrage", "Sandwich", "Unclassified"]
    ax.pie(sizes, labels=labels, autopct='%1.1f%%',
           pctdistance=1.25, labeldistance=.6, colors=C)
    pl.savefig(f"{YEAR}-classification-pie-chart-v{VERSION}.png", bbox_inches='tight')
    pl.close()

    
    # get proportional plots (warning: this can get completely wrong visually!)
    sandwich = [100 * u[0] / sum(u[:4]) for u in all_stats]
    arb      = [100 * u[1] / sum(u[:4]) for u in all_stats]
    core     = [100 * u[2] / sum(u[:4]) for u in all_stats]
    other    = [100 * u[3] / sum(u[:4]) for u in all_stats]

    pl.figure()
    pl.stackplot(x, core, arb, sandwich, other, colors=C)
    pl.xlabel("Day in 2023")
    pl.ylabel("Volume, %")
    #pl.show()
    pl.savefig(f"{YEAR}-classification-stackchart-v{VERSION}.png", bbox_inches='tight')
    pl.close()


if __name__ == "__main__":
    main()
