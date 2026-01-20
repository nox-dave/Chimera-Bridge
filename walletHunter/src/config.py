KNOWN_EXCHANGE_ADDRESSES = {
    "0x28c6c06298d514db089934071355e5743bf21d60": "Binance 14",
    "0xbe0eb53f46cd790cd13851d5eff43d12404d33e8": "Binance 7",
    "0x21a31ee1afc51d94c2efccaa2092ad1028285549": "Binance 15",
    "0x47ac0fb4f2d84898e4d9e7b4dab3c24507a6d503": "Binance 8",
    "0xdfd5293d8e347dfe59e90efd55b2956a1343963d": "Binance 16",
    "0x0681d8db095565fe8a346fa0277bffde9c0edbbf": "Binance 17",
    "0xfe9e8709d3215310075d67e3ed32a380ccf451c8": "Binance 18",
    "0x4e9ce36e442e55ecd9025b9a6e0d88485d628a67": "Binance 19",
    "0x4976a4a02f38326660d17bf34b431dc6e2eb2327": "Binance 20",
    "0x564286362092d8e7936f0549571a803b203aaced": "Binance 16 (old)",
    "0xacd03d601e5bb1b275bb94076ff46ed9d753435a": "Binance 20 (old)",
    "0x2b3fed49557bd88f78b898684f82fbb355305dbb": "Revolut 4",
    "0xd551234ae421e3bcba99a0da6d736074f22192ff": "Binance 2",
    "0x3f5ce5fbfe3e9af3971dd833d26ba9b5c936f0be": "Binance 3",
    "0x85b931a32a0725be14285b66f1a22178c672d69b": "Binance 4",
    "0x708396f17127c42383e3b9014072679b2f60b82f": "Binance 5",
    "0x8894e0a0c962cb723c1976a4421c95949be2d4e3": "Binance 10",
    "0xe2fc31f816a9b94326492132018c3aecc4a93ae1": "Binance 11",
    "0x3c783c21a0383057d128bae431894a5c19f9cf06": "Binance 12",
    "0x71660c4005ba85c37ccec55d0c4493e66fe775d3": "Coinbase 2",
    "0x503828976d22510aad0201ac7ec88293211d23da": "Coinbase 3",
    "0xddfabcdc4d8ffc6d5beaf154f18b778f892a0740": "Coinbase 4",
    "0x0a869d79a7052c7f1b55a8ebabbea3420f0d1e13": "Kraken 2",
    "0xe853c56864a2ebe4576a807d26fdc4a0ada51919": "Kraken 3",
    "0x267be1c1d684f78cb4f6a176c4911b741e4ffdc0": "Kraken 4",
    "0x0d0707963952f2fba59dd06f2b425ace40b492fe": "Gate.io 1",
    "0xc80afd311c9626528de66d86814770361fe92416": "Paribu: Hot Wallet"
}

KNOWN_MIXERS = {
    '0xa160cdab225685da1d56aa342ad8841c3b53f291',
    '0x12d66f87a04a9e220743712ce6d9bb1b5616b8fc5',
    '0x47ce0c6ed5b0ce3d3a51fdb1c52dc66a7c3c2936',
    '0x910cbd523d972eb0a6f4cae4618ad62622b39dbf'
}

BURN_ADDRESSES = {
    '0x000000000000000000000000000000000000dead',
    '0x0000000000000000000000000000000000000000',
}

MAJOR_TOKENS = {
    'USDT': {'address': '0xdac17f958d2ee523a2206206994597c13d831ec7', 'decimals': 6, 'price': 1.0},
    'USDC': {'address': '0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48', 'decimals': 6, 'price': 1.0},
    'WETH': {'address': '0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2', 'decimals': 18, 'price': 2000.0},
    'DAI': {'address': '0x6b175474e89094c44da98b954eedeac495271d0f', 'decimals': 18, 'price': 1.0},
    'WBTC': {'address': '0x2260fac5e5542a773aa44fbcfedf7c193bc2c599', 'decimals': 8, 'price': 40000.0}
}

SEED_WHALES = [
    '0x47ac0fb4f2d84898e4d9e7b4dab3c24507a6d503',
    '0xbe0eb53f46cd790cd13851d5eff43d12404d33e8',
    '0x8315177ab297ba92a06054ce80a67ed4dbd7ed3a',
    '0x28c6c06298d514db089934071355e5743bf21d60',
    '0x21a31ee1afc51d94c2efccaa2092ad1028285549'
]

EXCHANGE_TX_COUNT_THRESHOLD = 10000

DEFI_PROTOCOLS = {
    'Aave': {
        'lending_pool': '0x7d2768dE32b0b80b7a3454c06BdAc94A69DDc7A9',
        'aTokens': [
            '0x028171bCA77440897B824Ca71D1c56caC55b68A3',
            '0xBcca60bB61934080951369a648Fb03DF4F96263C',
            '0x3Ed3B47Dd13EC9a98b44e6204A523E766B225811'
        ]
    },
    'Compound': {
        'comptroller': '0x3d9819210A31b4961b30EF54bE2aeD79B9c9Cd3B',
        'cTokens': [
            '0x4Ddc2D193948926D02f9B1fE9e1daa0718270ED5',
            '0x39AA39c021dfbaE8faC545936693aC917d5E7563',
            '0x5d3a536E4D6DbD6114cc1Ead35777bAB948E3643'
        ]
    },
    'MakerDAO': {
        'cdp_manager': '0x5ef30b9986345249c32f892902cae46b59226c06',
        'dai_token': '0x6b175474e89094c44da98b954eedeac495271d0f'
    }
}

BLUE_CHIP_NFTS = {
    'BAYC': '0xbc4ca0eda7647a8ab7c2061c2e118a18a936f13d',
    'CryptoPunks': '0xb47e3cd837ddf8e4c57f05d70ab865de6e193bbb',
    'Azuki': '0xed5af388653567af2f388e6224dc7c4b3241c544',
    'MAYC': '0x60e4d786628fea6478f785a6d7e704777c86a7c6',
    'PudgyPenguins': '0xbd3531da5cf5857e7cfaa92426877b022e612cf8',
    'Doodles': '0x8a90cab2b38dba80c64b7734e58ee1db3b3ac603'
}

GOVERNANCE_TOKENS = {
    'UNI': {'address': '0x1f9840a85d5af5bf1d1762f925bdaddc4201f984', 'decimals': 18, 'governor': '0x408ed6354d4973f66138c91495f2f2fcbd8724c3'},
    'AAVE': {'address': '0x7fc66500c84a76ad7e9c93437bfc5ac33e2ddae9', 'decimals': 18, 'governor': '0xec568fffba86c094cfab1a9ef18f912043c2d875'},
    'COMP': {'address': '0xc00e94cb662c3520282e6f5717214004a7f26888', 'decimals': 18, 'governor': '0xc0da02939e1441f497fd74f78ce7decb17b66529'},
    'MKR': {'address': '0x9f8f72aa9304c8b593d555f12ef6589cc3a579a2', 'decimals': 18, 'governor': '0x0a3f6849f78076aefadf113f5bed87720274ddc0'}
}

EARLY_BLOCKS = {
    'genesis': 0,
    'early_2015': 1,
    'late_2015': 200000,
    'early_2016': 2000000,
    'late_2016': 3000000,
    'early_2017': 3500000,
    'late_2017': 4500000
}

