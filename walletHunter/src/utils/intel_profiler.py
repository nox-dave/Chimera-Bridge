#!/usr/bin/env python3

import os
import json
import requests
from datetime import datetime
from typing import Optional, Tuple
from dataclasses import dataclass, field
from collections import Counter

EXCHANGE_LABELS = {
    "0x28c6c06298d514db089934071355e5743bf21d60": "Binance 14",
    "0xdfd5293d8e347dfe59e90efd55b2956a1343963d": "Binance 16",
    "0x21a31ee1afc51d94c2efccaa2092ad1028285549": "Binance 15",
    "0xbe0eb53f46cd790cd13851d5eff43d12404d33e8": "Binance 7",
    "0xf977814e90da44bfa03b6295a0616a897441acec": "Binance 8",
    "0x503828976d22510aad0201ac7ec88293211d23da": "Coinbase 2",
    "0x71660c4005ba85c37ccec55d0c4493e66fe775d3": "Coinbase 1",
    "0xa9d1e08c7793af67e9d92fe308d5697fb81d3e43": "Coinbase 10",
    "0x2910543af39aba0cd09dbb2d50200b3e800a63d2": "Kraken 13",
    "0x53d284357ec70ce289d6d64134dfac8e511c8a3d": "Kraken 4",
    "0x1ab4973a48dc892cd9971ece8e01dcc7688f8f23": "Bitget 6",
    "0x2b3fed49557bd88f78b898684f82fbb355305dbb": "Revolut 4",
    "0xf89d7b9c864f589bbf53a82105107622b35eaa40": "Bybit Hot Wallet",
    "0x98ec059dc3adfbdd63429454aeb0c990fba4a128": "OKX",
    "0x6cc5f688a315f3dc28a7781717a9a798a59fda7b": "OKX 2",
    "0xa7efae728d2936e78bda97dc267687568dd593f3": "OKX 3",
    "0xd24400ae8bfebb18ca49be86258a3c749cf46853": "Gemini 4",
    "0x07ee55aa48bb72dcc6e9d78256648910de513eca": "Gate.io",
}

DEFI_PROTOCOLS = {
    "0x7a250d5630b4cf539739df2c5dacb4c659f2488d": ("Uniswap V2", "DEX"),
    "0x68b3465833fb72a70ecdf485e0e4c7bd8665fc45": ("Uniswap V3", "DEX"),
    "0xe592427a0aece92de3edee1f18e0157c05861564": ("Uniswap V3", "DEX"),
    "0xef1c6e67703c7bd7107eed8303fbe6ec2554bf6b": ("Uniswap Universal Router", "DEX"),
    "0x3fc91a3afd70395cd496c647d5a6cc9d4b2b7fad": ("Uniswap Universal Router 2", "DEX"),
    "0x7d2768de32b0b80b7a3454c06bdac94a69ddc7a9": ("Aave V2", "Lending"),
    "0x87870bca3f3fd6335c3f4ce8392d69350b4fa4e2": ("Aave V3", "Lending"),
    "0x3d9819210a31b4961b30ef54be2aed79b9c9cd3b": ("Compound", "Lending"),
    "0xdef1c0ded9bec7f1a1670819833240f027b25eff": ("0x Protocol", "DEX Aggregator"),
    "0x1111111254fb6c44bac0bed2854e76f90643097d": ("1inch V4", "DEX Aggregator"),
    "0x1111111254eeb25477b68fb85ed929f73a960582": ("1inch V5", "DEX Aggregator"),
    "0x881d40237659c251811cec9c364ef91dc08d300c": ("Metamask Swap Router", "DEX Aggregator"),
    "0xd9e1ce17f2641f24ae83637ab66a2cca9c378b9f": ("SushiSwap", "DEX"),
    "0xc36442b4a4522e871399cd717abdd847ab11fe88": ("Uniswap V3 Positions NFT", "LP"),
    "0x5f98805a4e8be255a32880fdec7f6728c6568ba0": ("Liquity LUSD", "Stablecoin"),
    "0xba12222222228d8ba445958a75a0704d566bf2c8": ("Balancer Vault", "DEX"),
    "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2": ("WETH Contract", "Wrapper"),
}

NFT_PLATFORMS = {
    "0x00000000006c3852cbef3e08e8df289169ede581": "OpenSea Seaport",
    "0x0000000000000068f116a894984e2db1123eb395": "OpenSea Seaport 1.6",
    "0x00000000000000adc04c56bf30ac9d3c0aaf14dc": "Blur",
    "0x74312363e45dcaba76c59ec49a7aa8a65a67eed3": "X2Y2",
    "0x59728544b08ab483533076417fbbb2fd0b17ce3a": "LooksRare",
    "0x7be8076f4ea4a4ad08075c2508e481d6c946d12b": "OpenSea Wyvern",
    "0x7f268357a8c2552623316e2562d90e642bb538e5": "OpenSea Wyvern 2",
}

BRIDGES = {
    "0x99c9fc46f92e8a1c0dec1b1747d010903e884be1": "Optimism Bridge",
    "0x4dbd4fc535ac27206064b68ffcf827b0a60bab3f": "Arbitrum Inbox",
    "0x8315177ab297ba92a06054ce80a67ed4dbd7ed3a": "Arbitrum Gateway",
    "0x3ee18b2214aff97000d974cf647e7c347e8fa585": "Wormhole",
    "0x32400084c286cf3e17e7b677ea9583e60a000324": "zkSync Bridge",
    "0x2796317b0ff8538f253012862c06787adfb8ceb6": "Synapse Bridge",
    "0x3014ca10b91cb3d0ad85fef7a3cb95bcac9c0f79": "Hop Protocol",
    "0xa0c68c638235ee32657e8f720a23cec1bfc77c77": "Polygon Bridge",
}

MEME_TOKENS = {"shib", "doge", "pepe", "floki", "bonk", "wif", "mog", "brett"}
DEFI_TOKENS = {"uni", "aave", "comp", "mkr", "crv", "ldo", "snx", "bal", "sushi"}
POLITICAL_TOKENS = {"wlfi", "trump", "maga", "biden"}
GAMING_TOKENS = {"axs", "sand", "mana", "gala", "imx", "ilv", "enj"}
AI_TOKENS = {"fet", "agix", "ocean", "rndr", "tau"}

@dataclass
class BehavioralProfile:
    likely_real_person: bool = True
    confidence_score: int = 50
    profile_type: str = "Unknown"
    risk_tolerance: str = "Unknown"
    sophistication: str = "Unknown"
    trading_style: str = "Unknown"
    likely_timezone: str = "Unknown"
    likely_region: str = "Unknown"
    active_hours: list = field(default_factory=list)
    active_days: list = field(default_factory=list)
    token_interests: list = field(default_factory=list)
    defi_protocols: list = field(default_factory=list)
    nft_platforms: list = field(default_factory=list)
    bridges_used: list = field(default_factory=list)
    red_flags: list = field(default_factory=list)
    bullish_signals: list = field(default_factory=list)
    funding_source: str = ""
    funding_source_label: str = ""
    exchange_interactions: list = field(default_factory=list)
    frequent_counterparties: list = field(default_factory=list)
    dust_attack_target: bool = False
    round_number_transfers: int = 0
    contract_interactions: int = 0
    meme_exposure: bool = False
    defi_exposure: bool = False
    political_tokens: bool = False
    gaming_tokens: bool = False
    ai_tokens: bool = False
    stablecoin_heavy: bool = False

@dataclass 
class WalletIntel:
    address: str
    balance_eth: float = 0
    balance_usd: float = 0
    tokens: dict = field(default_factory=dict)
    total_value_usd: float = 0
    tx_count: int = 0
    first_tx_date: str = ""
    last_tx_date: str = ""
    wallet_age_days: int = 0
    total_eth_moved: float = 0
    avg_tx_value: float = 0
    behavior: BehavioralProfile = field(default_factory=BehavioralProfile)
    risk_score: int = 50
    priority: str = "medium"

def fetch_transactions(address: str, api_key: str, limit: int = 500) -> list:
    try:
        url = "https://api.etherscan.io/v2/api"
        params = {
            "chainid": 1,
            "module": "account",
            "action": "txlist",
            "address": address,
            "startblock": 0,
            "endblock": 99999999,
            "page": 1,
            "offset": min(limit, 1000),
            "sort": "desc",
            "apikey": api_key
        }
        
        print(f"    DEBUG: Fetching txns for {address[:16]}...")
        print(f"    DEBUG: API Key present: {bool(api_key)}")
        print(f"    DEBUG: API Key length: {len(api_key) if api_key else 0}")
        
        resp = requests.get(url, params=params, timeout=15)
        data = resp.json()
        
        print(f"    DEBUG: API Response status: {data.get('status')}")
        print(f"    DEBUG: API Response message: {data.get('message', 'N/A')}")
        print(f"    DEBUG: Results count: {len(data.get('result', []))}")
        
        if data.get("status") == "1":
            results = data.get("result", [])
            if isinstance(results, list):
                print(f"    DEBUG: Successfully fetched {len(results)} transactions")
                return results
            else:
                print(f"    DEBUG: Warning - result is not a list: {type(results)}")
                return []
        else:
            error_msg = data.get('message', 'Unknown error')
            print(f"    ⚠️  API Error: {error_msg}")
            if "rate limit" in error_msg.lower() or "max rate limit" in error_msg.lower():
                print(f"    ⚠️  Rate limit hit - consider adding delay or upgrading API key")
            
    except Exception as e:
        print(f"    ⚠️  Error fetching txns: {e}")
        import traceback
        print(f"    DEBUG: Traceback: {traceback.format_exc()}")
    return []

def fetch_token_transfers(address: str, api_key: str, limit: int = 200) -> list:
    try:
        url = "https://api.etherscan.io/v2/api"
        params = {
            "chainid": 1,
            "module": "account",
            "action": "tokentx",
            "address": address,
            "page": 1,
            "offset": min(limit, 1000),
            "sort": "desc",
            "apikey": api_key
        }
        
        print(f"    DEBUG: Fetching token transfers for {address[:16]}...")
        
        resp = requests.get(url, params=params, timeout=15)
        data = resp.json()
        
        print(f"    DEBUG: Token API status: {data.get('status')}, message: {data.get('message', 'N/A')}")
        print(f"    DEBUG: Token results count: {len(data.get('result', []))}")
        
        if data.get("status") == "1":
            results = data.get("result", [])
            if isinstance(results, list):
                return results
            else:
                print(f"    DEBUG: Warning - token result is not a list: {type(results)}")
                return []
        else:
            error_msg = data.get('message', 'Unknown error')
            if "rate limit" not in error_msg.lower():
                print(f"    ⚠️  Token API Error: {error_msg}")
            
    except Exception as e:
        print(f"    ⚠️  Error fetching token transfers: {e}")
    return []

def detect_dust_attacks(transactions: list, address: str) -> Tuple[bool, list]:
    address_lower = address.lower()
    dust_txns = []
    suspicious_senders = {}
    
    for tx in transactions:
        if tx.get("to", "").lower() == address_lower:
            value = int(tx.get("value", 0))
            value_eth = value / 1e18
            if 0 < value_eth < 0.0001:
                sender = tx.get("from", "").lower()
                if sender not in suspicious_senders:
                    suspicious_senders[sender] = 0
                suspicious_senders[sender] += 1
                dust_txns.append({
                    "from": sender,
                    "value_eth": value_eth,
                    "hash": tx.get("hash", "")
                })
    
    is_targeted = len(dust_txns) > 3
    return is_targeted, dust_txns

def analyze_transfer_patterns(transactions: list, address: str) -> dict:
    address_lower = address.lower()
    patterns = {
        "round_numbers": 0,
        "outgoing_count": 0,
        "incoming_count": 0,
        "largest_tx_eth": 0,
        "avg_tx_eth": 0,
        "total_moved": 0,
    }
    
    values = []
    
    for tx in transactions:
        value = int(tx.get("value", 0))
        value_eth = value / 1e18
        
        if value_eth > 0:
            values.append(value_eth)
            patterns["total_moved"] += value_eth
            if value_eth > patterns["largest_tx_eth"]:
                patterns["largest_tx_eth"] = value_eth
            if value_eth >= 1 and value_eth == int(value_eth):
                patterns["round_numbers"] += 1
            elif value_eth in [0.5, 0.1, 0.25, 1.5, 2.5, 5.5]:
                patterns["round_numbers"] += 1
        
        if tx.get("from", "").lower() == address_lower:
            patterns["outgoing_count"] += 1
        else:
            patterns["incoming_count"] += 1
    
    if values:
        patterns["avg_tx_eth"] = sum(values) / len(values)
    
    return patterns

def analyze_activity_times(transactions: list) -> Tuple[dict, dict, str, str]:
    hours = Counter()
    days = Counter()
    timestamps = []
    
    for tx in transactions:
        try:
            ts = int(tx.get("timeStamp", 0))
            if ts > 0:
                timestamps.append(ts)
                dt = datetime.utcfromtimestamp(ts)
                hours[dt.hour] += 1
                days[dt.strftime("%A")] += 1
        except:
            pass
    
    peak_hours = [h for h, _ in hours.most_common(5)]
    avg_peak = sum(peak_hours) / len(peak_hours) if peak_hours else 12
    
    if 0 <= avg_peak <= 8:
        timezone = "Asia-Pacific (UTC+8 to +12)"
        region = "Asia-Pacific"
    elif 8 < avg_peak <= 16:
        timezone = "Europe/Africa (UTC+0 to +3)"
        region = "Europe"
    else:
        timezone = "Americas (UTC-5 to -8)"
        region = "Americas"
    
    return dict(hours), dict(days), timezone, region

def analyze_token_activity(token_transfers: list, address: str) -> dict:
    address_lower = address.lower()
    analysis = {
        "tokens_traded": set(),
        "meme_exposure": False,
        "defi_exposure": False,
        "political_tokens": False,
        "gaming_tokens": False,
        "ai_tokens": False,
        "stablecoin_heavy": False,
        "token_symbols": [],
    }
    
    token_counts = Counter()
    stablecoin_count = 0
    
    for tx in token_transfers:
        symbol = tx.get("tokenSymbol", "").lower()
        token_counts[symbol] += 1
        analysis["tokens_traded"].add(symbol.upper())
        
        if symbol in MEME_TOKENS:
            analysis["meme_exposure"] = True
        if symbol in DEFI_TOKENS:
            analysis["defi_exposure"] = True
        if symbol in POLITICAL_TOKENS:
            analysis["political_tokens"] = True
        if symbol in GAMING_TOKENS:
            analysis["gaming_tokens"] = True
        if symbol in AI_TOKENS:
            analysis["ai_tokens"] = True
        if symbol in ["usdt", "usdc", "dai", "busd", "tusd"]:
            stablecoin_count += 1
    
    total_transfers = len(token_transfers)
    if total_transfers > 0 and stablecoin_count / total_transfers > 0.5:
        analysis["stablecoin_heavy"] = True
    
    analysis["token_symbols"] = [s for s, _ in token_counts.most_common(10)]
    analysis["tokens_traded"] = list(analysis["tokens_traded"])
    
    return analysis

def identify_defi_usage(transactions: list) -> list:
    protocols = set()
    for tx in transactions:
        to_addr = tx.get("to", "").lower()
        if to_addr in DEFI_PROTOCOLS:
            protocol_name, _ = DEFI_PROTOCOLS[to_addr]
            protocols.add(protocol_name)
    return list(protocols)

def identify_nft_activity(transactions: list) -> list:
    platforms = set()
    for tx in transactions:
        to_addr = tx.get("to", "").lower()
        if to_addr in NFT_PLATFORMS:
            platforms.add(NFT_PLATFORMS[to_addr])
    return list(platforms)

def identify_bridge_usage(transactions: list) -> list:
    bridges = set()
    for tx in transactions:
        to_addr = tx.get("to", "").lower()
        if to_addr in BRIDGES:
            bridges.add(BRIDGES[to_addr])
    return list(bridges)

def identify_funding_source(transactions: list, address: str) -> Tuple[str, str]:
    address_lower = address.lower()
    sorted_txns = sorted(transactions, key=lambda x: int(x.get("timeStamp", 0)))
    
    for tx in sorted_txns:
        if tx.get("to", "").lower() == address_lower:
            value = int(tx.get("value", 0))
            if value > 0:
                sender = tx.get("from", "").lower()
                label = EXCHANGE_LABELS.get(sender, "Unknown")
                return sender, label
    
    return "", ""

def identify_exchange_interactions(transactions: list) -> list:
    exchanges = set()
    for tx in transactions:
        from_addr = tx.get("from", "").lower()
        to_addr = tx.get("to", "").lower()
        if from_addr in EXCHANGE_LABELS:
            exchanges.add(EXCHANGE_LABELS[from_addr])
        if to_addr in EXCHANGE_LABELS:
            exchanges.add(EXCHANGE_LABELS[to_addr])
    return list(exchanges)

def determine_sophistication(defi_protocols: list, bridges: list, tx_count: int, contract_interactions: int) -> str:
    score = 0
    if len(defi_protocols) >= 5:
        score += 3
    elif len(defi_protocols) >= 3:
        score += 2
    elif len(defi_protocols) >= 1:
        score += 1
    if len(bridges) >= 2:
        score += 2
    elif len(bridges) >= 1:
        score += 1
    if contract_interactions > 100:
        score += 2
    elif contract_interactions > 20:
        score += 1
    if tx_count > 1000:
        score += 1
    
    if score >= 6:
        return "Expert"
    elif score >= 4:
        return "Advanced"
    elif score >= 2:
        return "Intermediate"
    else:
        return "Novice"

def determine_risk_tolerance(meme_exposure: bool, balance_usd: float, defi_protocols: list, nft_platforms: list) -> str:
    if meme_exposure and len(defi_protocols) >= 3:
        return "Degen"
    elif meme_exposure:
        return "Aggressive"
    elif len(nft_platforms) > 0 and len(defi_protocols) > 0:
        return "Moderate-Aggressive"
    elif len(defi_protocols) > 0:
        return "Moderate"
    else:
        return "Conservative"

def determine_trading_style(tx_count: int, wallet_age_days: int, nft_platforms: list, defi_protocols: list, stablecoin_heavy: bool) -> str:
    if wallet_age_days > 0:
        txns_per_day = tx_count / wallet_age_days
    else:
        txns_per_day = 0
    
    if len(nft_platforms) > 0 and txns_per_day < 1:
        return "NFT Collector"
    elif len(defi_protocols) >= 3 and txns_per_day >= 2:
        return "DeFi Farmer"
    elif txns_per_day >= 5:
        return "Active Trader"
    elif txns_per_day >= 1:
        return "Regular Trader"
    elif stablecoin_heavy:
        return "Stablecoin Holder"
    else:
        return "Long-term Holder"

def calculate_real_person_confidence(behavior: BehavioralProfile, tx_count: int, wallet_age_days: int, balance_usd: float) -> Tuple[bool, int]:
    confidence = 50
    reasons = []
    
    if behavior.dust_attack_target:
        confidence += 15
        reasons.append("Targeted by dust attacks")
    if behavior.round_number_transfers >= 3:
        confidence += 10
        reasons.append("Uses round number transfers")
    if behavior.funding_source_label and "Hot Wallet" in behavior.funding_source_label:
        confidence += 10
        reasons.append("Withdrew from CEX")
    if behavior.exchange_interactions:
        confidence += 5
        reasons.append("Exchange interactions")
    if 100 < tx_count < 5000:
        confidence += 10
        reasons.append("Reasonable tx count")
    if behavior.meme_exposure or behavior.political_tokens:
        confidence += 10
        reasons.append("Retail token activity")
    if len(behavior.nft_platforms) > 0:
        confidence += 10
        reasons.append("NFT activity")
    
    if tx_count > 50000:
        confidence -= 30
        reasons.append("⚠️ Excessive tx count")
        print(f"    DEBUG: High tx count detected ({tx_count:,}) - penalizing confidence")
    if balance_usd > 100_000_000:
        confidence -= 20
        reasons.append("⚠️ Institutional-level balance")
    if wallet_age_days < 7 and balance_usd > 1_000_000:
        confidence -= 10
        reasons.append("⚠️ Fresh wallet with large balance")
    
    confidence = max(10, min(95, confidence))
    likely_real = confidence >= 50
    
    if likely_real:
        behavior.bullish_signals = [r for r in reasons if not r.startswith("⚠️")]
    behavior.red_flags = [r for r in reasons if r.startswith("⚠️")]
    
    return likely_real, confidence

def determine_profile_type(behavior: BehavioralProfile, balance_usd: float) -> str:
    traits = []
    
    if balance_usd > 10_000_000:
        traits.append("Mega-Whale")
    elif balance_usd > 1_000_000:
        traits.append("Whale")
    elif balance_usd > 100_000:
        traits.append("Dolphin")
    else:
        traits.append("Fish")
    
    if behavior.trading_style:
        traits.append(behavior.trading_style)
    
    if behavior.political_tokens:
        traits.append("Political Token Holder")
    if behavior.meme_exposure:
        traits.append("Meme Coin Player")
    if len(behavior.bridges_used) >= 2:
        traits.append("Cross-chain User")
    
    return " | ".join(traits[:3])

def build_wallet_intel(address: str, basic_data: dict, api_key: str = None, transaction_analysis: dict = None) -> WalletIntel:
    intel = WalletIntel(
        address=address.lower(),
        balance_eth=basic_data.get("balance_eth", 0),
        balance_usd=basic_data.get("balance_usd", 0),
        tokens=basic_data.get("tokens", {}),
        total_value_usd=basic_data.get("total_value_usd", basic_data.get("balance_usd", 0)),
    )
    
    behavior = BehavioralProfile()
    
    if not api_key:
        api_key = os.getenv("ETHERSCAN_API_KEY", "")
        if not api_key:
            print(f"    DEBUG: No API key provided - skipping transaction analysis")
            print(f"    DEBUG: Set ETHERSCAN_API_KEY environment variable to enable full analysis")
    
    if api_key:
        print(f"    Building intelligence profile for {address[:16]}...")
        transactions = fetch_transactions(address, api_key, limit=500)
        token_transfers = fetch_token_transfers(address, api_key, limit=200)
        
        print(f"    DEBUG: Total transactions fetched: {len(transactions)}")
        print(f"    DEBUG: Total token transfers fetched: {len(token_transfers)}")
        
        if transactions:
            intel.tx_count = len(transactions)
            print(f"    DEBUG: Processing {intel.tx_count} transactions for analysis")
            
            timestamps = [int(tx.get("timeStamp", 0)) for tx in transactions if tx.get("timeStamp")]
            if timestamps:
                min_timestamp = min(timestamps)
                max_timestamp = max(timestamps)
                intel.first_tx_date = datetime.utcfromtimestamp(min_timestamp).strftime("%Y-%m-%d")
                intel.last_tx_date = datetime.utcfromtimestamp(max_timestamp).strftime("%Y-%m-%d")
                wallet_age_from_txs = (datetime.now() - datetime.utcfromtimestamp(min_timestamp)).days
                
                if transaction_analysis and transaction_analysis.get('first_transaction'):
                    try:
                        first_tx_str = transaction_analysis.get('first_transaction')
                        first_tx_clean = first_tx_str.replace('Z', '+00:00') if isinstance(first_tx_str, str) else str(first_tx_str)
                        first_dt = datetime.fromisoformat(first_tx_clean)
                        if first_dt.tzinfo:
                            wallet_age_from_analysis = (datetime.now(first_dt.tzinfo) - first_dt).days
                        else:
                            wallet_age_from_analysis = (datetime.now() - first_dt).days
                        
                        intel.wallet_age_days = min(wallet_age_from_txs, wallet_age_from_analysis)
                        if wallet_age_from_analysis < wallet_age_from_txs:
                            intel.first_tx_date = first_dt.strftime("%Y-%m-%d")
                    except:
                        intel.wallet_age_days = wallet_age_from_txs
                else:
                    intel.wallet_age_days = wallet_age_from_txs
            
            behavior.dust_attack_target, _ = detect_dust_attacks(transactions, address)
            
            patterns = analyze_transfer_patterns(transactions, address)
            intel.total_eth_moved = patterns["total_moved"]
            intel.avg_tx_value = patterns["avg_tx_eth"]
            behavior.round_number_transfers = patterns["round_numbers"]
            
            hours, days, timezone, region = analyze_activity_times(transactions)
            behavior.active_hours = [h for h, _ in sorted(hours.items(), key=lambda x: -x[1])[:5]]
            behavior.active_days = [d for d, _ in sorted(days.items(), key=lambda x: -x[1])[:3]]
            behavior.likely_timezone = timezone
            behavior.likely_region = region
            
            behavior.defi_protocols = identify_defi_usage(transactions)
            behavior.nft_platforms = identify_nft_activity(transactions)
            behavior.bridges_used = identify_bridge_usage(transactions)
            
            behavior.funding_source, behavior.funding_source_label = identify_funding_source(transactions, address)
            behavior.exchange_interactions = identify_exchange_interactions(transactions)
            behavior.contract_interactions = sum(1 for tx in transactions if tx.get("input", "0x") != "0x")
        
        if token_transfers:
            token_analysis = analyze_token_activity(token_transfers, address)
            behavior.token_interests = token_analysis["token_symbols"]
            behavior.meme_exposure = token_analysis["meme_exposure"]
            behavior.defi_exposure = token_analysis["defi_exposure"]
            behavior.political_tokens = token_analysis["political_tokens"]
            behavior.gaming_tokens = token_analysis["gaming_tokens"]
            behavior.ai_tokens = token_analysis["ai_tokens"]
            behavior.stablecoin_heavy = token_analysis["stablecoin_heavy"]
        
        behavior.sophistication = determine_sophistication(
            behavior.defi_protocols, behavior.bridges_used, 
            intel.tx_count, behavior.contract_interactions
        )
        
        behavior.risk_tolerance = determine_risk_tolerance(
            behavior.meme_exposure, intel.balance_usd,
            behavior.defi_protocols, behavior.nft_platforms
        )
        
        behavior.trading_style = determine_trading_style(
            intel.tx_count, intel.wallet_age_days,
            behavior.nft_platforms, behavior.defi_protocols,
            behavior.stablecoin_heavy
        )
        
        behavior.likely_real_person, behavior.confidence_score = calculate_real_person_confidence(
            behavior, intel.tx_count, intel.wallet_age_days, intel.balance_usd
        )
        
        behavior.profile_type = determine_profile_type(behavior, intel.balance_usd)
    
    elif transaction_analysis:
        intel.tx_count = transaction_analysis.get('total_transactions', 0)
        intel.total_eth_moved = transaction_analysis.get('total_value_eth', 0)
        if intel.tx_count > 0:
            intel.avg_tx_value = intel.total_eth_moved / intel.tx_count
        
        first_tx = transaction_analysis.get('first_transaction')
        last_tx = transaction_analysis.get('last_transaction')
        if first_tx:
            try:
                first_dt = datetime.fromisoformat(first_tx.replace('Z', '+00:00'))
                intel.first_tx_date = first_dt.strftime("%Y-%m-%d")
                intel.wallet_age_days = (datetime.now() - first_dt.replace(tzinfo=None)).days
            except:
                pass
        if last_tx:
            try:
                last_dt = datetime.fromisoformat(last_tx.replace('Z', '+00:00'))
                intel.last_tx_date = last_dt.strftime("%Y-%m-%d")
            except:
                pass
    
    intel.behavior = behavior
    
    intel.risk_score = behavior.confidence_score
    
    confidence = behavior.confidence_score
    balance_usd = intel.balance_usd
    
    if confidence >= 75 and balance_usd >= 100000:
        intel.priority = "high"
    elif confidence >= 60:
        intel.priority = "medium"
    elif confidence >= 50 and balance_usd >= 500000:
        intel.priority = "medium"
    else:
        intel.priority = "low"
    
    return intel

def generate_intel_report(intel: WalletIntel) -> str:
    b = intel.behavior
    lines = []
    
    lines.append("╔" + "═" * 78 + "╗")
    lines.append("║" + " 🐋 WHALE INTELLIGENCE REPORT ".center(78) + "║")
    lines.append("║" + " Gargophias OSINT Module ".center(78) + "║")
    lines.append("╚" + "═" * 78 + "╝")
    lines.append("")
    lines.append(f"Target:     {intel.address}")
    lines.append(f"Generated:  {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}")
    lines.append("")
    
    lines.append("┌" + "─" * 78 + "┐")
    lines.append("│" + " QUICK ASSESSMENT ".center(78) + "│")
    lines.append("├" + "─" * 78 + "┤")
    
    real_person_str = "✅ LIKELY REAL PERSON" if b.likely_real_person else "⚠️  POSSIBLY INSTITUTIONAL/BOT"
    lines.append(f"│  {real_person_str:<74} │")
    lines.append(f"│  Confidence: {b.confidence_score}%{' ' * 62} │")
    lines.append(f"│  Profile: {b.profile_type:<65} │")
    lines.append("└" + "─" * 78 + "┘")
    lines.append("")
    
    lines.append("━" * 80)
    lines.append("💰 FINANCIAL SUMMARY")
    lines.append("━" * 80)
    lines.append(f"  Total Portfolio Value:  ${intel.total_value_usd:>20,.2f}")
    lines.append(f"  ETH Balance:            {intel.balance_eth:>20,.4f} ETH")
    lines.append(f"  ETH Value:              ${intel.balance_usd:>20,.2f}")
    
    if intel.tokens:
        lines.append("")
        lines.append("  Token Holdings:")
        for token, data in list(intel.tokens.items())[:8]:
            if isinstance(data, dict):
                amount = data.get('amount', data.get('balance', 0))
                usd = data.get('usd', data.get('value_usd', 0))
            else:
                amount = data
                usd = data
            if usd > 0:
                lines.append(f"    • {token:<8} {amount:>18,.2f}  (${usd:>14,.2f})")
    lines.append("")
    
    lines.append("━" * 80)
    lines.append("📊 ACTIVITY METRICS")
    lines.append("━" * 80)
    lines.append(f"  Transaction Count:      {intel.tx_count:>20,}")
    lines.append(f"  Total ETH Moved:        {intel.total_eth_moved:>20,.2f} ETH")
    lines.append(f"  Avg Transaction:        {intel.avg_tx_value:>20,.4f} ETH")
    lines.append(f"  Wallet Age:             {intel.wallet_age_days:>20,} days")
    lines.append(f"  First Transaction:      {intel.first_tx_date:>20}")
    lines.append(f"  Last Transaction:       {intel.last_tx_date:>20}")
    lines.append("")
    
    lines.append("━" * 80)
    lines.append("🧠 BEHAVIORAL PROFILE")
    lines.append("━" * 80)
    lines.append(f"  Sophistication Level:   {b.sophistication:<20}")
    lines.append(f"  Risk Tolerance:         {b.risk_tolerance:<20}")
    lines.append(f"  Trading Style:          {b.trading_style:<20}")
    lines.append("")
    
    lines.append("━" * 80)
    lines.append("⏰ ACTIVITY PATTERNS")
    lines.append("━" * 80)
    
    if b.active_hours:
        hours_str = ", ".join([f"{h}:00" for h in b.active_hours[:4]])
        lines.append(f"  Peak Activity Hours:    {hours_str} UTC")
    
    if b.active_days:
        lines.append(f"  Most Active Days:       {', '.join(b.active_days[:3])}")
    
    lines.append(f"  Likely Timezone:        {b.likely_timezone}")
    lines.append(f"  Probable Region:        {b.likely_region}")
    lines.append("")
    
    lines.append("━" * 80)
    lines.append("🔧 PROTOCOL & PLATFORM USAGE")
    lines.append("━" * 80)
    
    if b.defi_protocols:
        lines.append("  DeFi Protocols:")
        for protocol in b.defi_protocols[:6]:
            lines.append(f"    ✓ {protocol}")
    else:
        lines.append("  DeFi Protocols:         None detected")
    lines.append("")
    
    if b.nft_platforms:
        lines.append("  NFT Platforms:")
        for platform in b.nft_platforms[:4]:
            lines.append(f"    ✓ {platform}")
    else:
        lines.append("  NFT Platforms:          None detected")
    lines.append("")
    
    if b.bridges_used:
        lines.append("  Cross-Chain Bridges:")
        for bridge in b.bridges_used[:4]:
            lines.append(f"    ✓ {bridge}")
    else:
        lines.append("  Bridge Usage:           None detected")
    lines.append("")
    
    if b.token_interests:
        lines.append("━" * 80)
        lines.append("🪙 TOKEN INTERESTS")
        lines.append("━" * 80)
        lines.append(f"  Active Tokens: {', '.join(b.token_interests[:10])}")
        
        flags = []
        if b.meme_exposure:
            flags.append("🐸 Meme Coins")
        if b.political_tokens:
            flags.append("🏛️ Political Tokens")
        if b.defi_exposure:
            flags.append("🏦 DeFi Tokens")
        if b.gaming_tokens:
            flags.append("🎮 Gaming Tokens")
        if b.ai_tokens:
            flags.append("🤖 AI Tokens")
        if b.stablecoin_heavy:
            flags.append("💵 Stablecoin Heavy")
        
        if flags:
            lines.append(f"  Categories: {' | '.join(flags)}")
        lines.append("")
    
    lines.append("━" * 80)
    lines.append("🏦 FUNDING & EXCHANGE RELATIONSHIPS")
    lines.append("━" * 80)
    
    if b.funding_source_label:
        lines.append(f"  Original Funding:       {b.funding_source_label}")
        lines.append(f"                          {b.funding_source[:42]}...")
    else:
        lines.append("  Original Funding:       Unknown / Contract")
    lines.append("")
    
    if b.exchange_interactions:
        lines.append("  Exchange Interactions:")
        for exchange in b.exchange_interactions[:5]:
            lines.append(f"    • {exchange}")
    else:
        lines.append("  Exchange Interactions:  None detected (DEX-only or self-custody)")
    lines.append("")
    
    lines.append("━" * 80)
    lines.append("🎯 SIGNAL ANALYSIS")
    lines.append("━" * 80)
    
    lines.append("")
    lines.append("  ✅ BULLISH SIGNALS (Real Person Indicators):")
    if b.bullish_signals:
        for signal in b.bullish_signals:
            lines.append(f"     • {signal}")
    
    additional_bullish = []
    if b.dust_attack_target:
        additional_bullish.append("Being targeted by address poisoning (scammers target real whales)")
    if b.round_number_transfers >= 3:
        additional_bullish.append(f"Uses round number transfers ({b.round_number_transfers}x) - human behavior")
    if b.political_tokens:
        additional_bullish.append("Holds political tokens - retail investor behavior")
    if b.nft_platforms:
        additional_bullish.append("NFT activity - potential social identity vector")
    if b.meme_exposure:
        additional_bullish.append("Meme coin exposure - retail speculation behavior")
    if b.funding_source_label and any(x in b.funding_source_label for x in ["Hot Wallet", "Binance", "Coinbase", "Bybit"]):
        additional_bullish.append(f"Funded from {b.funding_source_label} - withdrew from CEX")
    
    for signal in additional_bullish:
        if signal not in b.bullish_signals:
            lines.append(f"     • {signal}")
    
    if not b.bullish_signals and not additional_bullish:
        lines.append("     • No strong positive signals")
    
    lines.append("")
    lines.append("  ⚠️  RED FLAGS (Caution Indicators):")
    if b.red_flags:
        for flag in b.red_flags:
            lines.append(f"     • {flag.replace('⚠️ ', '')}")
    
    additional_red = []
    if intel.tx_count > 10000:
        additional_red.append(f"High transaction count ({intel.tx_count:,}) - possibly automated")
    if intel.wallet_age_days < 30 and intel.balance_usd > 500000:
        additional_red.append("New wallet with large balance - verify source")
    if not b.exchange_interactions and intel.balance_usd > 1000000:
        additional_red.append("No exchange interactions - unusual for large holder")
    
    for flag in additional_red:
        if flag not in [f.replace('⚠️ ', '') for f in b.red_flags]:
            lines.append(f"     • {flag}")
    
    if not b.red_flags and not additional_red:
        lines.append("     • No significant red flags detected")
    lines.append("")
    
    lines.append("━" * 80)
    lines.append("📋 OSINT ASSESSMENT")
    lines.append("━" * 80)
    
    assessment = []
    
    if b.likely_real_person and b.confidence_score >= 70:
        assessment.append(f"HIGH CONFIDENCE ({b.confidence_score}%): This wallet likely belongs to a real individual.")
    elif b.likely_real_person:
        assessment.append(f"MODERATE CONFIDENCE ({b.confidence_score}%): Likely a real person, but some uncertainty.")
    else:
        assessment.append(f"LOW CONFIDENCE ({b.confidence_score}%): May be institutional, bot, or multi-sig.")
    
    if b.likely_region != "Unknown":
        assessment.append(f"GEOGRAPHIC: Activity patterns suggest {b.likely_region} timezone ({b.likely_timezone}).")
    
    if b.sophistication == "Expert" or b.sophistication == "Advanced":
        assessment.append(f"SOPHISTICATION: {b.sophistication}-level user. Experienced with DeFi, understands gas optimization.")
    elif b.sophistication == "Intermediate":
        assessment.append(f"SOPHISTICATION: {b.sophistication} user. Familiar with DeFi basics, uses DEXs.")
    else:
        assessment.append(f"SOPHISTICATION: {b.sophistication} user. Primarily uses exchanges, limited DeFi exposure.")
    
    assessment.append(f"RISK PROFILE: {b.risk_tolerance}. {b.trading_style}.")
    
    if b.political_tokens:
        assessment.append("NOTABLE: Holds political tokens (e.g., WLFI) - likely follows US crypto politics.")
    if b.dust_attack_target:
        assessment.append("NOTABLE: Active target of address poisoning attacks - confirms wallet is monitored by scammers.")
    if len(b.bridges_used) >= 2:
        assessment.append("NOTABLE: Uses multiple bridges - may have significant holdings on other chains.")
    
    for line in assessment:
        lines.append(f"  {line}")
    lines.append("")
    
    lines.append("━" * 80)
    lines.append("🎭 PROFILE HYPOTHESIS")
    lines.append("━" * 80)
    
    profile_guess = generate_profile_guess(intel)
    for line in profile_guess:
        lines.append(f"  {line}")
    lines.append("")
    
    lines.append("━" * 80)
    lines.append("🔗 INVESTIGATION LINKS")
    lines.append("━" * 80)
    lines.append(f"  Etherscan:      https://etherscan.io/address/{intel.address}")
    lines.append(f"  Debank:         https://debank.com/profile/{intel.address}")
    lines.append(f"  Arkham Intel:   https://platform.arkhamintelligence.com/explorer/address/{intel.address}")
    lines.append(f"  Nansen:         https://pro.nansen.ai/wallet/{intel.address}")
    lines.append(f"  Zerion:         https://app.zerion.io/{intel.address}/overview")
    lines.append(f"  Zapper:         https://zapper.xyz/account/{intel.address}")
    lines.append("")
    
    lines.append("╔" + "═" * 78 + "╗")
    lines.append("║" + f" PRIORITY: {intel.priority.upper()} | CONFIDENCE: {b.confidence_score}% ".center(78) + "║")
    lines.append("╚" + "═" * 78 + "╝")
    
    return "\n".join(lines)

def generate_profile_guess(intel: WalletIntel) -> list:
    b = intel.behavior
    lines = []
    
    if b.political_tokens and b.meme_exposure:
        archetype = "Retail Speculator / Political Crypto Enthusiast"
    elif b.sophistication in ["Expert", "Advanced"] and len(b.defi_protocols) >= 3:
        archetype = "DeFi Power User / Yield Farmer"
    elif b.nft_platforms and intel.balance_usd > 500000:
        archetype = "NFT Whale / Digital Art Collector"
    elif b.stablecoin_heavy and intel.balance_usd > 1000000:
        archetype = "Conservative Whale / Stablecoin Holder"
    elif b.meme_exposure and b.risk_tolerance == "Degen":
        archetype = "Degen Trader / Meme Coin Gambler"
    elif b.exchange_interactions and not b.defi_protocols:
        archetype = "Traditional Crypto Investor"
    elif len(b.bridges_used) >= 2:
        archetype = "Multi-Chain Power User"
    elif b.political_tokens:
        archetype = "Political Crypto Enthusiast"
    else:
        archetype = "General Crypto Holder"
    
    lines.append(f"Archetype: {archetype}")
    lines.append("")
    
    narrative = []
    
    if intel.balance_usd > 10_000_000:
        narrative.append("A mega-whale with significant market influence.")
    elif intel.balance_usd > 1_000_000:
        narrative.append("A substantial holder with whale-tier capital.")
    elif intel.balance_usd > 100_000:
        narrative.append("A mid-tier holder with meaningful skin in the game.")
    
    if b.funding_source_label:
        cex = b.funding_source_label.split()[0] if b.funding_source_label else "exchange"
        narrative.append(f"Originally funded through {cex}, suggesting traditional onboarding.")
    
    if b.sophistication in ["Expert", "Advanced"]:
        narrative.append("Demonstrates advanced knowledge of DeFi protocols and on-chain mechanics.")
    elif b.sophistication == "Intermediate":
        narrative.append("Shows familiarity with DEXs and basic DeFi concepts.")
    else:
        narrative.append("Appears to rely primarily on centralized exchanges.")
    
    if b.likely_region == "Americas":
        narrative.append("Activity patterns suggest US/Americas timezone - likely American or Canadian.")
    elif b.likely_region == "Europe":
        narrative.append("Activity patterns suggest European timezone.")
    elif b.likely_region == "Asia-Pacific":
        narrative.append("Activity patterns suggest Asia-Pacific timezone.")
    
    if b.political_tokens:
        narrative.append("Interest in political tokens suggests engagement with US crypto politics.")
    if b.nft_platforms:
        narrative.append("NFT activity provides potential vector for social identity discovery.")
    if b.dust_attack_target:
        narrative.append("Being targeted by scammers confirms this is an active, monitored wallet.")
    
    lines.append("Narrative:")
    for n in narrative:
        lines.append(f"  {n}")
    
    return lines

