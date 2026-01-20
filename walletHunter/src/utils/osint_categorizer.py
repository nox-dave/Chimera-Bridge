#!/usr/bin/env python3

OSINT_CATEGORIES = {
    "🎰_gamblers": {
        "description": "High-risk traders, meme coins, leverage users",
        "psychology": "Impulsive, FOMO-driven, chases pumps, emotionally reactive",
        "attack_vectors": [
            "Fake alpha groups / insider info",
            "Pump & dump schemes",
            "Urgency-based phishing",
            "Too-good-to-be-true airdrops",
        ],
        "indicators": ["meme_exposure", "high_tx_frequency", "leverage_usage"],
    },
    "🆕_newcomers": {
        "description": "Fresh wallets (<60 days) with significant holdings",
        "psychology": "Inexperienced, trusting, doesn't know security best practices",
        "attack_vectors": [
            "Fake support / help offers",
            "Wallet 'security check' scams",
            "Impersonation of protocols",
            "Approval phishing",
        ],
        "indicators": ["wallet_age_days < 60", "balance > 100k", "low_defi_experience"],
    },
    "🏆_status_seekers": {
        "description": "NFT collectors, blue chip holders, social identity tied to crypto",
        "psychology": "Ego-driven, wants recognition, flexes holdings publicly",
        "attack_vectors": [
            "Fake exclusive mints / allowlists",
            "Impersonate NFT projects",
            "Social media targeting (they likely post about holdings)",
            "Fake collaborations / partnerships",
        ],
        "indicators": ["nft_activity", "blue_chip_nfts", "social_tokens"],
    },
    "💤_dormant_whales": {
        "description": "Large holders with low recent activity",
        "psychology": "Complacent, may have weak security, not paying attention",
        "attack_vectors": [
            "Old approval exploits",
            "Dust attacks to activate wallet",
            "Fake 'your wallet is compromised' urgency",
        ],
        "indicators": ["high_balance", "low_recent_activity", "old_approvals"],
    },
    "🌉_cross_chain_users": {
        "description": "Active bridge users, multi-chain presence",
        "psychology": "Tech-savvy but exposed to more attack surface",
        "attack_vectors": [
            "Fake bridge interfaces",
            "Cross-chain phishing",
            "MEV attacks on bridges",
        ],
        "indicators": ["bridge_usage >= 2", "multi_chain_activity"],
    },
    "🐟_easy_targets": {
        "description": "Low sophistication, CEX-dependent, limited DeFi exposure",
        "psychology": "Trusting, follows instructions, doesn't verify",
        "attack_vectors": [
            "Classic phishing",
            "Fake CEX support",
            "Seed phrase harvesting",
            "Fake apps / extensions",
        ],
        "indicators": ["sophistication == 'Novice'", "cex_only", "no_defi"],
    },
    "🦊_cautious_holders": {
        "description": "Security-conscious, hardware wallet likely, minimal exposure",
        "psychology": "Paranoid, slow to act, verifies everything",
        "attack_vectors": [
            "Long-term social engineering",
            "Supply chain attacks",
            "Physical security threats",
        ],
        "indicators": ["low_tx_count", "no_risky_approvals", "conservative_behavior"],
    },
    "🧠_defi_natives": {
        "description": "Advanced DeFi users, yield farmers, protocol power users",
        "psychology": "Overconfident, takes calculated risks, may overlook basics",
        "attack_vectors": [
            "Malicious contracts disguised as yield",
            "Fake governance proposals",
            "Protocol impersonation",
            "Approval exploits on new protocols",
        ],
        "indicators": ["defi_protocols >= 3", "yield_farming", "governance_participation"],
    },
    "🌙_night_traders": {
        "description": "Active during off-hours (likely different timezone or insomniac)",
        "psychology": "May be fatigued, less alert during unusual hours",
        "attack_vectors": [
            "Time-sensitive attacks during their active hours",
            "Target when they're likely tired",
        ],
        "indicators": ["peak_hours outside 9-17 local"],
    },
    "📈_momentum_chasers": {
        "description": "Buys during pumps, sells during dumps, reactive trader",
        "psychology": "Emotional, reactive, doesn't do research",
        "attack_vectors": [
            "Fake trending tokens",
            "Pump coordination",
            "FOMO-inducing fake news",
        ],
        "indicators": ["buys_on_pump", "high_slippage_tolerance", "meme_exposure"],
    },
    "🏛️_governance_voters": {
        "description": "Active in DAOs, holds governance tokens, votes on proposals",
        "psychology": "Community-minded, trusts decentralization, idealistic",
        "attack_vectors": [
            "Malicious governance proposals",
            "Fake delegation requests",
            "Impersonate DAO members",
        ],
        "indicators": ["governance_tokens", "dao_votes", "delegate_activity"],
    },
    "💎_high_value": {
        "description": "Balance > $1M, confirmed individual (not institution)",
        "psychology": "Varies - but high reward target",
        "attack_vectors": ["All of the above - worth the effort"],
        "indicators": ["balance > 1M", "confidence >= 70", "not_institution"],
    },
    "🎯_prime_targets": {
        "description": "Perfect storm: High value + Low sophistication + Vulnerable patterns",
        "psychology": "The ideal target - has money and is exploitable",
        "attack_vectors": ["Customized based on their specific vulnerabilities"],
        "indicators": ["high_value", "easy_target_traits", "active_patterns"],
    },
    "🏢_institutions": {
        "description": "Exchanges, funds, bots, multi-sigs",
        "psychology": "N/A - not individuals",
        "attack_vectors": ["None - skip these"],
        "indicators": ["tx_count > 50000", "institutional_patterns"],
    },
    "🤖_bots": {
        "description": "Automated trading, MEV bots, arbitrage",
        "psychology": "N/A - not human",
        "attack_vectors": ["None - skip these"],
        "indicators": ["consistent_timing", "programmatic_behavior"],
    },
}

def categorize_for_osint(profile_data: dict) -> list:
    categories = []
    
    behavior = profile_data.get('behavior', {})
    balance_usd = profile_data.get('balance_usd', profile_data.get('total_value_usd', 0))
    tx_count = profile_data.get('tx_count', 0)
    wallet_age = profile_data.get('wallet_age_days', profile_data.get('age_days', 0)) or 0
    confidence = behavior.get('confidence_score', profile_data.get('risk_score', 50))
    
    meme_exposure = behavior.get('meme_exposure', False)
    defi_protocols = behavior.get('defi_protocols', [])
    nft_platforms = behavior.get('nft_platforms', [])
    bridges_used = behavior.get('bridges_used', [])
    sophistication = behavior.get('sophistication', 'Unknown')
    exchange_interactions = behavior.get('exchange_interactions', [])
    
    if tx_count > 50000 and wallet_age > 30:
        return ["🏢_institutions"]
    
    if tx_count > 10000 and confidence < 40 and wallet_age > 7:
        return ["🤖_bots"]
    
    if meme_exposure or (tx_count > 500 and wallet_age < 90):
        categories.append("🎰_gamblers")
    
    if wallet_age < 60 and balance_usd > 50000:
        categories.append("🆕_newcomers")
    
    if len(nft_platforms) > 0 or profile_data.get('nft_activity', False):
        categories.append("🏆_status_seekers")
    
    if balance_usd > 500000 and tx_count < 100:
        categories.append("💤_dormant_whales")
    
    if len(bridges_used) >= 2 or profile_data.get('bridge_activity', False):
        categories.append("🌉_cross_chain_users")
    
    if sophistication in ['Novice', 'Unknown'] and len(defi_protocols) == 0 and not profile_data.get('defi_activity', False):
        categories.append("🐟_easy_targets")
    
    if tx_count < 50 and balance_usd > 100000 and not meme_exposure:
        categories.append("🦊_cautious_holders")
    
    if len(defi_protocols) >= 3 or sophistication in ['Advanced', 'Expert'] or profile_data.get('defi_activity', False):
        categories.append("🧠_defi_natives")
    
    if behavior.get('dao_participation') or behavior.get('governance_votes', 0) > 0:
        categories.append("🏛️_governance_voters")
    
    if behavior.get('buys_on_pump') or behavior.get('high_slippage'):
        categories.append("📈_momentum_chasers")
    
    if balance_usd > 1000000 and confidence >= 60:
        categories.append("💎_high_value")
    
    is_easy = "🐟_easy_targets" in categories or "🆕_newcomers" in categories
    is_valuable = balance_usd > 500000
    is_individual = confidence >= 60
    
    if is_easy and is_valuable and is_individual:
        categories.append("🎯_prime_targets")
    
    if not categories:
        if balance_usd > 100000:
            categories.append("🦊_cautious_holders")
        else:
            categories.append("🐟_easy_targets")
    
    return categories

def get_category_info(category_key: str) -> dict:
    return OSINT_CATEGORIES.get(category_key, {})

def print_category_analysis(categories: list):
    print("\n" + "=" * 60)
    print("🎯 OSINT CATEGORY ANALYSIS")
    print("=" * 60)
    
    for cat_key in categories:
        info = OSINT_CATEGORIES.get(cat_key, {})
        if info:
            print(f"\n{cat_key}")
            print(f"  {info.get('description', '')}")
            print(f"\n  Psychology: {info.get('psychology', 'Unknown')}")
            print(f"\n  Attack Vectors:")
            for vector in info.get('attack_vectors', []):
                print(f"    • {vector}")

if __name__ == "__main__":
    test_profile = {
        "balance_usd": 750000,
        "tx_count": 150,
        "wallet_age_days": 45,
        "behavior": {
            "confidence_score": 75,
            "meme_exposure": True,
            "sophistication": "Intermediate",
            "defi_protocols": ["Uniswap"],
            "nft_platforms": ["OpenSea"],
            "bridges_used": [],
        }
    }
    
    print("Test Profile:")
    print(f"  Balance: ${test_profile['balance_usd']:,}")
    print(f"  Age: {test_profile['wallet_age_days']} days")
    print(f"  Meme exposure: {test_profile['behavior']['meme_exposure']}")
    print(f"  NFT activity: {len(test_profile['behavior']['nft_platforms']) > 0}")
    
    categories = categorize_for_osint(test_profile)
    print_category_analysis(categories)

