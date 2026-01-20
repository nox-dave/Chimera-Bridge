#!/usr/bin/env python3

from datetime import datetime
from typing import Dict, Optional
from collections import Counter

KNOWN_LABELS = {
    "0x28c6c06298d514db089934071355e5743bf21d60": "Binance 14",
    "0xdfd5293d8e347dfe59e90efd55b2956a1343963d": "Binance 16",
    "0x21a31ee1afc51d94c2efccaa2092ad1028285549": "Binance 15",
    "0x503828976d22510aad0201ac7ec88293211d23da": "Coinbase 2",
    "0x71660c4005ba85c37ccec55d0c4493e66fe775d3": "Coinbase 1",
    "0x2910543af39aba0cd09dbb2d50200b3e800a63d2": "Kraken 13",
    "0x1ab4973a48dc892cd9971ece8e01dcc7688f8f23": "Bitget 6",
    "0x7a250d5630b4cf539739df2c5dacb4c659f2488d": "Uniswap V2 Router",
    "0x68b3465833fb72a70ecdf485e0e4c7bd8665fc45": "Uniswap V3 Router",
    "0xe592427a0aece92de3edee1f18e0157c05861564": "Uniswap V3 Router 2",
    "0x7d2768de32b0b80b7a3454c06bdac94a69ddc7a9": "Aave V2 Pool",
    "0x87870bca3f3fd6335c3f4ce8392d69350b4fa4e2": "Aave V3 Pool",
    "0x3d9819210a31b4961b30ef54be2aed79b9c9cd3b": "Compound Comptroller",
    "0x00000000006c3852cbef3e08e8df289169ede581": "OpenSea Seaport",
    "0x0000000000000068f116a894984e2db1123eb395": "OpenSea Seaport 1.6",
}

def generate_enhanced_summary(
    address: str,
    whale_profile,
    profile_data: Dict,
    transaction_analysis: Optional[Dict] = None
) -> str:
    lines = []
    
    lines.append("╔" + "═" * 78 + "╗")
    lines.append("║" + f" 🐋 WHALE INTELLIGENCE REPORT ".center(78) + "║")
    lines.append("╚" + "═" * 78 + "╝")
    lines.append("")
    
    lines.append(f"Target: {address}")
    lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}")
    lines.append("")
    
    lines.append("┌" + "─" * 40 + "┐")
    lines.append(f"│ {'CLASSIFICATION':^38} │")
    lines.append("├" + "─" * 40 + "┤")
    lines.append(f"│ Category:    {whale_profile.category:<25} │")
    lines.append(f"│ Risk Score:  {whale_profile.risk_score}/100{' ':>22} │")
    lines.append(f"│ Priority:    {whale_profile.priority.upper():<25} │")
    lines.append("└" + "─" * 40 + "┘")
    lines.append("")
    
    lines.append("━" * 80)
    lines.append("💰 FINANCIAL SUMMARY")
    lines.append("━" * 80)
    lines.append(f"  Total Portfolio:     ${profile_data['total_value_usd']:>18,.2f}")
    lines.append(f"  ETH Balance:         {profile_data['eth_balance']:>18,.4f} ETH")
    
    token_holdings = profile_data.get('token_holdings', {})
    if token_holdings:
        lines.append("")
        lines.append("  Token Holdings:")
        sorted_tokens = sorted(
            token_holdings.items(),
            key=lambda x: x[1].get('value_usd', 0) if isinstance(x[1], dict) else 0,
            reverse=True
        )[:10]
        
        for token, data in sorted_tokens:
            if isinstance(data, dict):
                balance = data.get('balance', 0)
                value = data.get('value_usd', 0)
                if value > 0:
                    lines.append(f"    • {token:<10} {balance:>15,.2f}  (${value:>12,.2f})")
            elif isinstance(data, (int, float)) and data > 0:
                lines.append(f"    • {token:<10} ${data:>12,.2f}")
    lines.append("")
    
    lines.append("━" * 80)
    lines.append("📊 ACTIVITY SUMMARY")
    lines.append("━" * 80)
    lines.append(f"  Transaction Count:   {whale_profile.tx_count:>18,}")
    lines.append(f"  Total ETH Moved:     {whale_profile.total_moved_eth:>18,.4f} ETH")
    
    if whale_profile.tx_count > 0 and whale_profile.total_moved_eth > 0:
        avg_tx = whale_profile.total_moved_eth / whale_profile.tx_count
        lines.append(f"  Avg Tx Value:        {avg_tx:>18,.4f} ETH")
    
    if whale_profile.age_days is not None:
        lines.append(f"  Wallet Age:          {whale_profile.age_days:>18,} days")
    
    if whale_profile.first_seen:
        first_seen_clean = whale_profile.first_seen.split('T')[0] if 'T' in str(whale_profile.first_seen) else str(whale_profile.first_seen)
        lines.append(f"  First Transaction:   {first_seen_clean:>18}")
    
    if whale_profile.last_active:
        last_active_clean = whale_profile.last_active.split('T')[0] if 'T' in str(whale_profile.last_active) else str(whale_profile.last_active)
        lines.append(f"  Last Transaction:    {last_active_clean:>18}")
    lines.append("")
    
    lines.append("━" * 80)
    lines.append("🔍 BEHAVIORAL INTELLIGENCE")
    lines.append("━" * 80)
    
    activity_flags = []
    if whale_profile.defi_activity:
        activity_flags.append("DeFi")
    if whale_profile.nft_activity:
        activity_flags.append("NFT")
    if whale_profile.bridge_activity:
        activity_flags.append("Bridge")
    
    if activity_flags:
        lines.append("  Activity Flags:")
        for flag in activity_flags:
            lines.append(f"    ✓ {flag}")
    else:
        lines.append("  Activity Flags:       None detected")
    lines.append("")
    
    if transaction_analysis:
        most_active_hour = transaction_analysis.get('most_active_hour')
        most_active_day = transaction_analysis.get('most_active_day')
        
        if most_active_hour is not None:
            lines.append(f"  Peak Activity Hour:   {most_active_hour}:00 UTC")
            
            if 6 <= most_active_hour <= 14:
                tz_guess = "Europe/Asia"
            elif 14 <= most_active_hour <= 22:
                tz_guess = "Americas"
            else:
                tz_guess = "Asia-Pacific"
            lines.append(f"  Likely Timezone:     {tz_guess}")
        
        if most_active_day and most_active_day != 'Unknown':
            lines.append(f"  Most Active Day:      {most_active_day}")
        lines.append("")
        
        top_recipients = transaction_analysis.get('top_recipients', [])
        top_senders = transaction_analysis.get('top_senders', [])
        
        if top_senders or top_recipients:
            lines.append("━" * 80)
            lines.append("🔗 KEY RELATIONSHIPS")
            lines.append("━" * 80)
            
            if top_senders:
                lines.append("  Top Senders:")
                for addr, count in top_senders[:5]:
                    label = KNOWN_LABELS.get(addr.lower(), addr[:16] + "...")
                    lines.append(f"    • {label:<30} ({count} txns)")
            
            if top_recipients:
                lines.append("  Top Recipients:")
                for addr, count in top_recipients[:5]:
                    label = KNOWN_LABELS.get(addr.lower(), addr[:16] + "...")
                    lines.append(f"    • {label:<30} ({count} txns)")
            lines.append("")
    
    lines.append("━" * 80)
    lines.append("📋 OSINT NOTES")
    lines.append("━" * 80)
    
    notes = []
    
    if whale_profile.age_days is not None:
        if whale_profile.age_days < 30:
            notes.append("⚠️  Fresh wallet (<30 days) - May be attempting to obscure history")
        elif whale_profile.age_days > 2000:
            notes.append("💎 OG wallet (5+ years) - Early adopter, likely sophisticated")
    
    if whale_profile.bridge_activity:
        notes.append("🌉 Uses bridges - May have assets on other chains, harder to trace")
    
    if whale_profile.defi_activity:
        notes.append("🧠 DeFi activity - Sophisticated user, likely follows crypto closely")
    
    if whale_profile.nft_activity:
        notes.append("🎨 NFT activity - Potential social identity via NFT ownership")
    
    if profile_data['total_value_usd'] > 10_000_000:
        notes.append("🐋 Whale-tier balance - Movements may impact markets")
    
    if whale_profile.tx_count == 0:
        notes.append("🔒 No transaction history - New wallet or minimal activity")
    elif whale_profile.tx_count < 10:
        notes.append("🔒 Low transaction count - May be a cold storage wallet")
    
    if not notes:
        notes.append("No significant behavioral indicators detected")
    
    for note in notes:
        lines.append(f"  {note}")
    lines.append("")
    
    lines.append("━" * 80)
    lines.append("🔗 INVESTIGATION LINKS")
    lines.append("━" * 80)
    lines.append(f"  Etherscan:    https://etherscan.io/address/{address}")
    lines.append(f"  Debank:       https://debank.com/profile/{address}")
    lines.append(f"  Arkham:       https://platform.arkhamintelligence.com/explorer/address/{address}")
    lines.append(f"  Nansen:       https://pro.nansen.ai/wallet/{address}")
    lines.append(f"  Zerion:       https://app.zerion.io/{address}/overview")
    lines.append("")
    
    lines.append("╔" + "═" * 78 + "╗")
    lines.append("║" + " END OF REPORT ".center(78) + "║")
    lines.append("╚" + "═" * 78 + "╝")
    
    return "\n".join(lines)

