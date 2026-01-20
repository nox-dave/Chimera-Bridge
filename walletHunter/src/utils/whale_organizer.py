#!/usr/bin/env python3

import json
import os
import requests
import time
from datetime import datetime
from dataclasses import dataclass, asdict
from typing import Optional, Dict, List

KNOWN_EXCHANGES = {
    "0x28c6c06298d514db089934071355e5743bf21d60",
    "0xdfd5293d8e347dfe59e90efd55b2956a1343963d",
    "0x4976a4a02f38326660d17bf34b431dc6e2eb2327",
    "0xbe0eb53f46cd790cd13851d5eff43d12404d33e8",
    "0x21a31ee1afc51d94c2efccaa2092ad1028285549",
    "0xf977814e90da44bfa03b6295a0616a897441acec",
    "0x5a52e96bacdabb82fd05763e25335261b270efcb",
    "0x3606f0f14828cbf4962a284a4bff93bc94b63665",
    "0x71660c4005ba85c37ccec55d0c4493e66fe775d3",
    "0x503828976d22510aad0201ac7ec88293211d23da",
    "0xa9d1e08c7793af67e9d92fe308d5697fb81d3e43",
    "0x1ab4973a48dc892cd9971ece8e01dcc7688f8f23",
    "0x2b3fed49557bd88f78b898684f82fbb355305dbb",
    "0x2910543af39aba0cd09dbb2d50200b3e800a63d2",
    "0x53d284357ec70ce289d6d64134dfac8e511c8a3d",
    "0x98ec059dc3adfbdd63429454aeb0c990fba4a128",
    "0x6cc5f688a315f3dc28a7781717a9a798a59fda7b",
    "0xcffad3200574698b78f32232aa9d63eabd290703",
    "0x56eddb7aa87536c09ccc2793473599fd21a8b17f",
    "0xf30ba13e4b04ce5dc4d254ae5fa95477800f0eb0",
}

@dataclass
class WhaleProfile:
    address: str
    balance_eth: float
    balance_usd: float
    total_moved_eth: float = 0
    tx_count: int = 0
    
    category: str = "unknown"
    risk_score: int = 0
    priority: str = "medium"
    
    label: Optional[str] = None
    first_seen: Optional[str] = None
    last_active: Optional[str] = None
    age_days: Optional[int] = None
    
    tokens: Optional[dict] = None
    
    defi_activity: bool = False
    nft_activity: bool = False
    bridge_activity: bool = False
    
    etherscan_url: str = ""
    
    def __post_init__(self):
        if not self.etherscan_url:
            self.etherscan_url = f"https://etherscan.io/address/{self.address}"

def get_tx_count_from_etherscan(address: str, api_key: str = None) -> Optional[int]:
    try:
        url = "https://api.etherscan.io/v2/api"
        params = {
            "chainid": 1,
            "module": "proxy",
            "action": "eth_getTransactionCount",
            "address": address,
            "tag": "latest",
        }
        if api_key:
            params["apikey"] = api_key
        
        resp = requests.get(url, params=params, timeout=5)
        result = resp.json().get("result")
        if result:
            return int(result, 16)
    except:
        pass
    return None

def calculate_risk_score(profile: WhaleProfile) -> tuple[int, str]:
    score = 50
    
    if profile.address.lower() in KNOWN_EXCHANGES:
        return (10, "filtered")
    
    bal = profile.balance_usd
    
    if bal > 100_000_000:
        score -= 15
    elif bal > 50_000_000:
        score -= 5
    elif 1_000_000 < bal < 50_000_000:
        score += 15
    elif 100_000 < bal < 1_000_000:
        score += 10
    
    tx = profile.tx_count
    
    if tx > 100000:
        score -= 35
    elif tx > 50000:
        score -= 25
    elif tx > 10000:
        score -= 15
    elif tx > 1000:
        score -= 5
    elif 100 < tx < 1000:
        score += 5
    elif tx < 100 and tx > 0:
        score += 10
    
    if profile.defi_activity:
        score += 10
    
    if profile.nft_activity:
        score += 15
    
    if profile.bridge_activity:
        score += 10
    
    if profile.age_days:
        if profile.age_days < 7:
            score += 25
        elif profile.age_days < 30:
            score += 15
        elif profile.age_days > 2000:
            score += 10
    
    score = max(0, min(100, score))
    
    if score >= 65:
        priority = "high"
    elif score >= 40:
        priority = "medium"
    else:
        priority = "low"
    
    return (score, priority)

def categorize_whale(profile: WhaleProfile) -> str:
    if profile.address.lower() in KNOWN_EXCHANGES:
        return "known_exchange"
    
    if profile.tx_count > 50000:
        return "likely_exchange"
    
    if profile.balance_usd > 100_000_000 and profile.tx_count < 10000:
        return "likely_fund"
    
    if profile.age_days and profile.age_days < 30:
        return "fresh_wallet"
    
    if profile.nft_activity:
        return "nft_collector"
    
    if profile.defi_activity:
        return "defi_user"
    
    if profile.balance_usd < 50_000_000 and profile.tx_count < 10000:
        return "likely_individual"
    
    return "unclassified"

def get_priority_folder(profile: WhaleProfile) -> str:
    if profile.priority == "filtered" or profile.category in ["known_exchange", "likely_exchange"]:
        return 'filtered'
    elif profile.priority == "high":
        return 'high_priority'
    elif profile.priority == "medium":
        return 'medium_priority'
    else:
        return 'low_priority'

def process_whale_data(wallet_data: Dict, etherscan_api_key: str = None) -> WhaleProfile:
    address = wallet_data.get('address', '').lower()
    balance_eth = wallet_data.get('eth_balance', 0)
    balance_usd = wallet_data.get('total_value_usd', 0)
    
    tx_count = wallet_data.get('tx_count', 0)
    if not tx_count:
        tx_patterns = wallet_data.get('transaction_analysis') or {}
        tx_count = tx_patterns.get('total_transactions', 0) if tx_patterns else 0
    
    if not tx_count and etherscan_api_key:
        tx_count = get_tx_count_from_etherscan(address, etherscan_api_key) or 0
        if tx_count:
            time.sleep(0.2)
    
    total_moved_eth = wallet_data.get('total_moved', 0)
    if not total_moved_eth:
        tx_patterns = wallet_data.get('transaction_analysis') or {}
        total_moved_eth = tx_patterns.get('total_value_eth', 0) if tx_patterns else 0
    
    first_seen = None
    last_active = None
    age_days = None
    
    tx_patterns = wallet_data.get('transaction_analysis') or {}
    if tx_patterns:
        first_seen = tx_patterns.get('first_transaction')
        last_active = tx_patterns.get('last_transaction')
        
        if first_seen:
            try:
                first_seen_clean = first_seen.replace('Z', '+00:00') if isinstance(first_seen, str) else str(first_seen)
                first_dt = datetime.fromisoformat(first_seen_clean)
                if first_dt.tzinfo:
                    now = datetime.now(first_dt.tzinfo)
                    age_days = (now - first_dt).days
                else:
                    now = datetime.now()
                    age_days = (now - first_dt).days
            except (ValueError, AttributeError, TypeError):
                pass
    
    token_holdings = wallet_data.get('token_holdings', {})
    
    defi_activity = wallet_data.get('defi_activity', False) or 'defi' in wallet_data.get('categories', [])
    nft_activity = wallet_data.get('nft_activity', False) or 'nft' in wallet_data.get('categories', []) or bool(wallet_data.get('nft_activity', {}))
    bridge_activity = wallet_data.get('bridge_activity', False) or 'bridge' in wallet_data.get('categories', [])
    
    profile = WhaleProfile(
        address=address,
        balance_eth=balance_eth,
        balance_usd=balance_usd,
        total_moved_eth=total_moved_eth,
        tx_count=tx_count,
        first_seen=first_seen,
        last_active=last_active,
        age_days=age_days,
        tokens=token_holdings,
        defi_activity=defi_activity,
        nft_activity=nft_activity,
        bridge_activity=bridge_activity,
        label=wallet_data.get('label')
    )
    
    profile.category = categorize_whale(profile)
    profile.risk_score, profile.priority = calculate_risk_score(profile)
    
    return profile

def organize_results(profiles: List[WhaleProfile], etherscan_api_key: str = None) -> dict:
    if etherscan_api_key:
        missing_tx = [p for p in profiles if p.tx_count == 0]
        if missing_tx:
            for i, p in enumerate(missing_tx):
                tx_count = get_tx_count_from_etherscan(p.address, etherscan_api_key)
                if tx_count:
                    p.tx_count = tx_count
                if (i + 1) % 5 == 0:
                    pass
                time.sleep(0.2)
    
    for p in profiles:
        p.category = categorize_whale(p)
        p.risk_score, p.priority = calculate_risk_score(p)
    
    profiles.sort(key=lambda x: x.risk_score, reverse=True)
    
    categorized = {
        'high_priority': [],
        'medium_priority': [],
        'low_priority': [],
        'filtered': [],
    }
    
    for p in profiles:
        if p.priority == "filtered" or p.category in ["known_exchange", "likely_exchange"]:
            categorized['filtered'].append(p)
        elif p.priority == "high":
            categorized['high_priority'].append(p)
        elif p.priority == "medium":
            categorized['medium_priority'].append(p)
        else:
            categorized['low_priority'].append(p)
    
    return categorized
