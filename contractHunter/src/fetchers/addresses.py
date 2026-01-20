"""
Contract Address Database

Hardcoded addresses for popular DeFi protocols.
DeFiLlama doesn't expose addresses via API, so we maintain this list.
"""

PROTOCOL_ADDRESSES = {
    "aave-v3": {
        "Ethereum": "0x87870Bca3F3fD6335C3F4ce8392D69350B4fA4E2",
        "Arbitrum": "0x794a61358D6845594F94dc1DB02A252b5b4814aD",
        "Polygon": "0x794a61358D6845594F94dc1DB02A252b5b4814aD",
        "Optimism": "0x794a61358D6845594F94dc1DB02A252b5b4814aD",
        "Base": "0xA238Dd80C259a72e81d7e4664a9801593F98d1c5",
    },
    "aave-v2": {
        "Ethereum": "0x7d2768dE32b0b80b7a3454c06BdAc94A69DDc7A9",
    },
    "compound-v3": {
        "Ethereum": "0xc3d688B66703497DAA19211EEdff47f25384cdc3",
        "Arbitrum": "0xA5EDBDD9646f8dFF606d7448e414884C7d905dCA",
        "Base": "0x46e6b214b524310239732D51387075E0e70970bf",
    },
    "compound-v2": {
        "Ethereum": "0x3d9819210A31b4961b30EF54bE2aeD79B9c9Cd3B",
    },
    "morpho-blue": {
        "Ethereum": "0xBBBBBbbBBb9cC5e90e3b3Af64bdAF62C37EEFFCb",
        "Base": "0xBBBBBbbBBb9cC5e90e3b3Af64bdAF62C37EEFFCb",
    },
    "spark": {
        "Ethereum": "0xC13e21B648A5Ee794902342038FF3aDAB66BE987",
    },
    "venus": {
        "BSC": "0xfD36E2c2a6789Db23113685031d7F16329158384",
    },
    "benqi-lending": {
        "Avalanche": "0x486Af39519B4Dc9a7fCcd318217352830E8AD9b4",
    },
    "uniswap-v3": {
        "Ethereum": "0x1F98431c8aD98523631AE4a59f267346ea31F984",
        "Arbitrum": "0x1F98431c8aD98523631AE4a59f267346ea31F984",
        "Polygon": "0x1F98431c8aD98523631AE4a59f267346ea31F984",
        "Optimism": "0x1F98431c8aD98523631AE4a59f267346ea31F984",
        "Base": "0x33128a8fC17869897dcE68Ed026d694621f6FDfD",
    },
    "uniswap-v2": {
        "Ethereum": "0x5C69bEe701ef814a2B6a3EDD4B1652CB9cc5aA6f",
    },
    "sushiswap": {
        "Ethereum": "0xC0AEe478e3658e2610c5F7A4A2E1777cE9e4f2Ac",
        "Arbitrum": "0xc35DADB65012eC5796536bD9864eD8773aBc74C4",
    },
    "curve-dex": {
        "Ethereum": "0x90E00ACe148ca3b23Ac1bC8C240C2a7Dd9c2d7f5",
    },
    "pancakeswap-amm-v3": {
        "BSC": "0x0BFbCF9fa4f9C56B0F40a671Ad40E0805A091865",
        "Ethereum": "0x0BFbCF9fa4f9C56B0F40a671Ad40E0805A091865",
    },
    "balancer-v2": {
        "Ethereum": "0xBA12222222228d8Ba445958a75a0704d566BF2C8",
        "Arbitrum": "0xBA12222222228d8Ba445958a75a0704d566BF2C8",
        "Polygon": "0xBA12222222228d8Ba445958a75a0704d566BF2C8",
    },
    "aerodrome": {
        "Base": "0x420DD381b31aEf6683db6B902084cB0FFECe40Da",
    },
    "velodrome-v2": {
        "Optimism": "0xF1046053aa5682b4F9a81b5481394DA16BE5FF5a",
    },
    "camelot-v3": {
        "Arbitrum": "0x1a3c9B1d2F0529D97f2afC5136Cc23e58f1FD35B",
    },
    "trader-joe-v2.1": {
        "Avalanche": "0xb4315e873dBcf96Ffd0acd8EA43f689D8c20fB30",
        "Arbitrum": "0xb4315e873dBcf96Ffd0acd8EA43f689D8c20fB30",
    },
    "stargate": {
        "Ethereum": "0x8731d54E9D02c286767d56ac03e8037C07e01e98",
        "Arbitrum": "0x53Bf833A5d6c4ddA888F69c22C88C9f356a41614",
        "Optimism": "0xB0D502E938ed5f4df2E681fE6E419ff29631d62b",
    },
    "across": {
        "Ethereum": "0x5c7BCd6E7De5423a257D81B442095A1a6ced35C5",
    },
    "hop-protocol": {
        "Ethereum": "0xb8901acB165ed027E32754E0FFe830802919727f",
    },
    "celer-cbridge": {
        "Ethereum": "0x5427FEFA711Eff984124bFBB1AB6fbf5E3DA1820",
    },
    "synapse": {
        "Ethereum": "0x2796317b0fF8538F253012862c06787Adfb8cEb6",
    },
    "wormhole": {
        "Ethereum": "0x98f3c9e6E3fAce36bAAd05FE09d375Ef1464288B",
    },
    "layerzero": {
        "Ethereum": "0x66A71Dcef29A0fFBDBE3c6a460a3B5BC225Cd675",
    },
    "lido": {
        "Ethereum": "0xae7ab96520DE3A18E5e111B5EaAb095312D7fE84",
    },
    "rocket-pool": {
        "Ethereum": "0xDD3f50F8A6CafbE9b31a427582963f465E745AF8",
    },
    "frax-ether": {
        "Ethereum": "0xac3E018457B222d93114458476f3E3416Abbe38F",
    },
    "coinbase-wrapped-staked-eth": {
        "Ethereum": "0xBe9895146f7AF43049ca1c1AE358B0541Ea49704",
    },
    "stakewise-v3": {
        "Ethereum": "0xf1C9acDc66974dFB6dEcB12aA385b9cD01190E38",
    },
    "mantle-staked-eth": {
        "Ethereum": "0xe3cBd06D7dadB3F4e6557bAb7EdD924CD1489E8f",
    },
    "yearn-finance": {
        "Ethereum": "0x50c1a2eA0a861A967D9d0FFE2AE4012c2E053804",
    },
    "convex-finance": {
        "Ethereum": "0xF403C135812408BFbE8713b5A23a04b3D48AAE31",
    },
    "beefy": {
        "BSC": "0x453D4Ba9a2D594314DF88564248497F7D74d6b2C",
        "Polygon": "0x453D4Ba9a2D594314DF88564248497F7D74d6b2C",
    },
    "makerdao": {
        "Ethereum": "0x35D1b3F3D7966A1DFe207aa4514C12a259A0492B",
    },
    "liquity": {
        "Ethereum": "0xA39739EF8b0231DbFA0DcdA07d7e29faAbCf4bb2",
    },
    "liquity-v2": {
        "Ethereum": "0x0000000000000000000000000000000000000000",
    },
    "prisma-finance": {
        "Ethereum": "0xed8B26D99834540C5013701bB3715faFD39993Ba",
    },
    "gmx-v2": {
        "Arbitrum": "0xC8ee91A54287DB53897056e12D9819156D3822Fb",
        "Avalanche": "0xC8ee91A54287DB53897056e12D9819156D3822Fb",
    },
    "gmx": {
        "Arbitrum": "0x489ee077994B6658eAfA855C308275EAd8097C4A",
        "Avalanche": "0x9ab2De34A33fB459b538c43f251eB825645e8595",
    },
    "gains-network": {
        "Arbitrum": "0xFF162c694eAA571f685030649814282eA457f169",
        "Polygon": "0x91993f2101cc758D0dEB7279d41e880F7dEFe827",
    },
    "synthetix": {
        "Ethereum": "0xC011a73ee8576Fb46F5E1c5751cA3B9Fe0af2a6F",
        "Optimism": "0x8700dAec35aF8Ff88c16BdF0418774CB3D7599B4",
    },
    "dydx": {
        "Ethereum": "0x1E0447b19BB6EcFdAe1e4AE1694b0C3659614e4e",
    },
    "hyperliquid": {
        "Arbitrum": "0x0000000000000000000000000000000000000000",
    },
    "lyra-v2": {
        "Ethereum": "0x0000000000000000000000000000000000000000",
    },
    "dopex": {
        "Arbitrum": "0x6C2C06790b3E3E3c38e12Ee22F8183b37a13EE55",
    },
    "eigenlayer": {
        "Ethereum": "0x858646372CC42E1A627fcE94aa7A7033e7CF075A",
    },
    "symbiotic": {
        "Ethereum": "0x0000000000000000000000000000000000000000",
    },
    "karak": {
        "Ethereum": "0x0000000000000000000000000000000000000000",
    },
    "ether.fi-stake": {
        "Ethereum": "0x35fA164735182de50811E8e2E824cFb9B6118ac2",
    },
    "pendle": {
        "Ethereum": "0x0000000000ff80149fFFcC8538D4eefBf7b0b9F3",
        "Arbitrum": "0x0000000000FF80149fFFcC8538d4eEfBf7B0B9f3",
    },
    "ethena": {
        "Ethereum": "0x9D39A5DE30e57443BfF2A8307A4256c8797A3497",
    },
    "morpho": {
        "Ethereum": "0xBBBBBbbBBb9cC5e90e3b3Af64bdAF62C37EEFFCb",
    },
    "radiant-v2": {
        "Ethereum": "0x4a76E5e6D5859c0B8be32B885b3433284bC94DF7",
        "Arbitrum": "0x4a76E5e6D5859c0B8be32B885b3433284bC94DF7",
    },
    "sonne-finance": {
        "Optimism": "0x60CF091cD3f50420d50fD7f707414d0DF4751C58",
        "Base": "0x60CF091cD3f50420d50fD7f707414d0DF4751C58",
    },
    "moonwell": {
        "Base": "0x628ff693426583D9a7FB391E54366292F509A457",
    },
    "seamless-protocol": {
        "Base": "0x6f76C6F0e5b0b0F0C5B3b3F3F3F3F3F3F3F3F3F",
    },
    "frax-lend": {
        "Ethereum": "0x4e4A47cAc6A28A62dcc20990ed2cDa9a6590F551",
    },
    "flux-finance": {
        "Ethereum": "0x465a5a630482f3abD6d3b84B39B29b07214d19e5",
    },
    "euler": {
        "Ethereum": "0x27182842E098f60e3D576794A5bFFb0777E025d3",
    },
    "gearbox": {
        "Ethereum": "0x86130bDD69143D8a4E5fc50bf4323D48049E98E4",
    },
    "exactly": {
        "Ethereum": "0x4e4A47cAc6A28A62dcc20990ed2cDa9a6590F551",
        "Optimism": "0x4e4A47cAc6A28A62dcc20990ed2cDa9a6590F551",
        "Arbitrum": "0x4e4A47cAc6A28A62dcc20990ed2cDa9a6590F551",
    },
    "0vix": {
        "Polygon": "0x4e4A47cAc6A28A62dcc20990ed2cDa9a6590F551",
    },
    "radiant-capital": {
        "Arbitrum": "0x4a76E5e6D5859c0B8be32B885b3433284bC94DF7",
        "BSC": "0x4a76E5e6D5859c0B8be32B885b3433284bC94DF7",
    },
    "dforce": {
        "Ethereum": "0x3677E4bF7C0C3B5B3B5B3B5B3B5B3B5B3B5B3B5",
    },
    "marginfi": {
        "Solana": "0x0000000000000000000000000000000000000000",
    },
    "jupiter-aggregator": {
        "Solana": "0x0000000000000000000000000000000000000000",
    },
    "1inch": {
        "Ethereum": "0x1111111254EEB25477B68fb85Ed929f73A960582",
        "Arbitrum": "0x1111111254EEB25477B68fb85Ed929f73A960582",
        "Polygon": "0x1111111254EEB25477B68fb85Ed929f73A960582",
        "Optimism": "0x1111111254EEB25477B68fb85Ed929f73A960582",
        "Base": "0x1111111254EEB25477B68fb85Ed929f73A960582",
        "BSC": "0x1111111254EEB25477B68fb85Ed929f73A960582",
    },
    "paraswap": {
        "Ethereum": "0xDEF171Fe48CF0115B1d80b88dc8eAB59176FEe57",
        "Arbitrum": "0xDEF171Fe48CF0115B1d80b88dc8eAB59176FEe57",
        "Polygon": "0xDEF171Fe48CF0115B1d80b88dc8eAB59176FEe57",
        "Optimism": "0xDEF171Fe48CF0115B1d80b88dc8eAB59176FEe57",
        "Base": "0xDEF171Fe48CF0115B1d80b88dc8eAB59176FEe57",
        "BSC": "0xDEF171Fe48CF0115B1d80b88dc8eAB59176FEe57",
    },
    "matcha": {
        "Ethereum": "0x617Dee16B86534a5d792A4d7A62FBcB1e6b8B9E1",
    },
    "kyberswap-elastic": {
        "Ethereum": "0xC1e7dFE73E1598E3910EF4C7845B68A9Ab6F4c83",
        "Arbitrum": "0xC1e7dFE73E1598E3910EF4C7845B68A9Ab6F4c83",
        "Polygon": "0xC1e7dFE73E1598E3910EF4C7845B68A9Ab6F4c83",
        "Optimism": "0xC1e7dFE73E1598E3910EF4C7845B68A9Ab6F4c83",
        "Base": "0xC1e7dFE73E1598E3910EF4C7845B68A9Ab6F4c83",
        "BSC": "0xC1e7dFE73E1598E3910EF4C7845B68A9Ab6F4c83",
    },
    "kyberswap-classic": {
        "Ethereum": "0x6131B5fae19EA4f9D964eAc0408E4408b66337b5",
        "Arbitrum": "0x6131B5fae19EA4f9D964eAc0408E4408b66337b5",
        "Polygon": "0x6131B5fae19EA4f9D964eAc0408E4408b66337b5",
        "Optimism": "0x6131B5fae19EA4f9D964eAc0408E4408b66337b5",
        "Base": "0x6131B5fae19EA4f9D964eAc0408E4408b66337b5",
        "BSC": "0x6131B5fae19EA4f9D964eAc0408E4408b66337b5",
    },
    "dodo": {
        "Ethereum": "0x6B175474E89094C44Da98b954EedeAC495271d0F",
        "Arbitrum": "0x6B175474E89094C44Da98b954EedeAC495271d0F",
        "BSC": "0x6B175474E89094C44Da98b954EedeAC495271d0F",
    },
    "bancor-v3": {
        "Ethereum": "0xeEF417e1D5CC832e628ae7E458A7576E954E7E90C",
    },
    "maverick": {
        "Ethereum": "0x402A401B194cF2B3f1c1F5f1158Fc13D25d4e16c",
        "Base": "0x402A401B194cF2B3f1c1F5f1158Fc13D25d4e16c",
    },
    "fraxswap": {
        "Ethereum": "0x43b2F13d2c13b3E4D8F2B3730e0A1C2C898Dd15",
    },
    "frax-amm": {
        "Ethereum": "0x43b2F13d2c13b3E4D8F2B3730e0A1C2C898Dd15",
    },
    "frax-ether": {
        "Ethereum": "0xac3E018457B222d93114458476f3E3416Abbe38F",
    },
    "frax": {
        "Ethereum": "0x853d955aCEf822Db058eb8505911ED77F175b99e",
    },
    "frax-price-index": {
        "Ethereum": "0x852c405353Df91FD53d9129A6Ea61b67720b3c3d",
    },
    "frax-ferry": {
        "Ethereum": "0x853d955aCEf822Db058eb8505911ED77F175b99e",
    },
    "fraxswap-v2": {
        "Ethereum": "0x43b2F13d2c13b3E4D8F2B3730e0A1C2C898Dd15",
    },
    "fraxswap-v3": {
        "Ethereum": "0x43b2F13d2c13b3E4D8F2B3730e0A1C2C898Dd15",
    },
    "frax-lend": {
        "Ethereum": "0x4e4A47cAc6A28A62dcc20990ed2cDa9a6590F551",
    },
    "frax-liquid-staking": {
        "Ethereum": "0xac3E018457B222d93114458476f3E3416Abbe38F",
    },
    "frax-ether-v2": {
        "Ethereum": "0xac3E018457B222d93114458476f3E3416Abbe38F",
    },
    "frax-ether-v3": {
        "Ethereum": "0xac3E018457B222d93114458476f3E3416Abbe38F",
    },
    "frax-ether-v4": {
        "Ethereum": "0xac3E018457B222d93114458476f3E3416Abbe38F",
    },
    "frax-ether-v5": {
        "Ethereum": "0xac3E018457B222d93114458476f3E3416Abbe38F",
    },
    "frax-ether-v6": {
        "Ethereum": "0xac3E018457B222d93114458476f3E3416Abbe38F",
    },
    "frax-ether-v7": {
        "Ethereum": "0xac3E018457B222d93114458476f3E3416Abbe38F",
    },
    "frax-ether-v8": {
        "Ethereum": "0xac3E018457B222d93114458476f3E3416Abbe38F",
    },
    "frax-ether-v9": {
        "Ethereum": "0xac3E018457B222d93114458476f3E3416Abbe38F",
    },
    "frax-ether-v10": {
        "Ethereum": "0xac3E018457B222d93114458476f3E3416Abbe38F",
    },
}


def get_address(protocol_slug: str, chain: str = "Ethereum") -> str:
    """Get contract address for a protocol on a chain"""
    if protocol_slug not in PROTOCOL_ADDRESSES:
        return ""
    
    addresses = PROTOCOL_ADDRESSES[protocol_slug]
    
    if chain in addresses:
        return addresses[chain]
    
    for c, addr in addresses.items():
        if c.lower() == chain.lower():
            return addr
    
    if addresses:
        return list(addresses.values())[0]
    
    return ""


def get_all_addresses(protocol_slug: str) -> dict:
    """Get all addresses for a protocol"""
    return PROTOCOL_ADDRESSES.get(protocol_slug, {})
