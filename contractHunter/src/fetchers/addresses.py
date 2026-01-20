"""
Contract Address Database

Hardcoded addresses for popular DeFi protocols.
DeFiLlama doesn't expose addresses via API, so we maintain this list.

To add more protocols:
1. Find the protocol on DeFiLlama
2. Get the contract address from their docs or Etherscan
3. Add to PROTOCOL_ADDRESSES with the DeFiLlama slug as key
"""

PROTOCOL_ADDRESSES = {
    # =========================================================================
    # LIQUID STAKING / RESTAKING (High Priority)
    # =========================================================================
    "ether.fi-stake": {
        "Ethereum": "0x35fA164735182de50811E8e2E824cFb9B6118ac2",
    },
    "lido": {
        "Ethereum": "0xae7ab96520DE3A18E5e111B5EaAb095312D7fE84",
    },
    "rocket-pool": {
        "Ethereum": "0xDD3f50F8A6CafbE9b31a427582963f465E745AF8",
    },
    "eigenlayer": {
        "Ethereum": "0x858646372CC42E1A627fcE94aa7A7033e7CF075A",
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
    "obol": {
        "Ethereum": "0xAA78D336E65c18aD7a9B7B0D7e33C3bF8a65ad5F",
    },
    "swell": {
        "Ethereum": "0xf951E335afb289353dc249e82926178EaC7DEd78",
    },
    "kelp-dao": {
        "Ethereum": "0x036676389e48133B63a802f8635AD39E752D375D",
    },
    "renzo": {
        "Ethereum": "0x74a09653A083691711cF8215a6ab074BB4e99ef5",
    },
    "puffer-finance": {
        "Ethereum": "0xD9A442856C234a39a81a089C06451EBAa4306a72",
    },
    
    # =========================================================================
    # BRIDGES (High Priority - often targeted)
    # =========================================================================
    "arbitrum-bridge": {
        "Ethereum": "0x8315177aB297bA92A06054cE80a67Ed4DBd7ed3a",
    },
    "base-bridge": {
        "Ethereum": "0x49048044D57e1C92A77f79988d21Fa8fAF74E97e",
    },
    "optimism-bridge": {
        "Ethereum": "0x99C9fc46f92E8a1c0deC1b1747d010903E884bE1",
    },
    "polygon-bridge": {
        "Ethereum": "0xA0c68C638235ee32657e8f720a23ceC1bFc77C77",
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
    
    # =========================================================================
    # LENDING (High TVL)
    # =========================================================================
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
    "radiant-v2": {
        "Arbitrum": "0x2032b9A8e9F7e76768CA9271003d3e43E1616B1F",
    },
    "fluid": {
        "Ethereum": "0x52Aa899454998Be5b000Ad077a46Bbe360F4e497",
    },
    "euler": {
        "Ethereum": "0x27182842E098f60e3D576794A5bFFb0777E025d3",
    },
    "silo-finance": {
        "Ethereum": "0xd998C35B7900b344bbBe6555cc11576942Cf309d",
        "Arbitrum": "0x8658047e48CC09161f4152c79155Dac1d710Ff0a",
    },
    
    # =========================================================================
    # DEXes
    # =========================================================================
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
    "maverick": {
        "Ethereum": "0xEb6625D65a0553c9dBc64449e56abFe519bd9c9B",
    },
    
    # =========================================================================
    # YIELD / CDP
    # =========================================================================
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
    "prisma-finance": {
        "Ethereum": "0xed8B26D99834540C5013701bB3715faFD39993Ba",
    },
    "pendle": {
        "Ethereum": "0x0000000000ff80149fFFcC8538D4eefBf7b0b9F3",
        "Arbitrum": "0x0000000000FF80149fFFcC8538d4eEfBf7B0B9f3",
    },
    "ethena": {
        "Ethereum": "0x9D39A5DE30e57443BfF2A8307A4256c8797A3497",
    },
    
    # =========================================================================
    # PERPETUALS / DERIVATIVES
    # =========================================================================
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
        "Arbitrum": "0x2DF1c51E09aECF9cacB7bc98cB1742757f163dF7",
    },
    
    # =========================================================================
    # RWA (Real World Assets)
    # =========================================================================
    "tether-gold": {
        "Ethereum": "0x68749665FF8D2d112Fa859AA293F07A622782F38",
    },
    "blackrock-buidl": {
        "Ethereum": "0x7712c34205737192402172409a8F7ccef8aA2AEc",
    },
    "ondo-finance": {
        "Ethereum": "0x96F6eF951840721AdBF46Ac996b59E0235CB985C",
    },
    "centrifuge": {
        "Ethereum": "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2",
    },
    
    # =========================================================================
    # STEAKHOUSE / CURATORS
    # =========================================================================
    "steakhouse-financial": {
        "Ethereum": "0x777777c9898D384F785Ee44Acfe945efDFf5f3E0",
    },
}


def get_address(protocol_slug: str, chain: str = "Ethereum") -> str:
    """Get contract address for a protocol on a chain"""
    slug = protocol_slug.lower().strip().replace(" ", "-")
    
    if slug in PROTOCOL_ADDRESSES:
        addresses = PROTOCOL_ADDRESSES[slug]
        if chain in addresses:
            return addresses[chain]
        for c, addr in addresses.items():
            if c.lower() == chain.lower():
                return addr
        if addresses:
            return list(addresses.values())[0]
    
    slug_no_dots = slug.replace(".", "-")
    if slug_no_dots in PROTOCOL_ADDRESSES:
        addresses = PROTOCOL_ADDRESSES[slug_no_dots]
        if chain in addresses:
            return addresses[chain]
        if addresses:
            return list(addresses.values())[0]
    
    for key in PROTOCOL_ADDRESSES:
        if slug in key or key in slug:
            addresses = PROTOCOL_ADDRESSES[key]
            if chain in addresses:
                return addresses[chain]
            if addresses:
                return list(addresses.values())[0]
        if slug_no_dots in key or key in slug_no_dots:
            addresses = PROTOCOL_ADDRESSES[key]
            if chain in addresses:
                return addresses[chain]
            if addresses:
                return list(addresses.values())[0]
    
    return ""


def get_all_addresses(protocol_slug: str) -> dict:
    """Get all addresses for a protocol"""
    slug = protocol_slug.lower().strip().replace(" ", "-")
    return PROTOCOL_ADDRESSES.get(slug, {})


def list_protocols() -> list:
    """List all protocols in database"""
    return list(PROTOCOL_ADDRESSES.keys())
