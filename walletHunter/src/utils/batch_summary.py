#!/usr/bin/env python3

import os
import json
from datetime import datetime, timezone
from typing import Dict, List, Optional
from collections import defaultdict, Counter

def generate_batch_summary(profiles: List[Dict], batch_params: Dict) -> str:
    if not profiles:
        return "No profiles to summarize."
    
    timestamp = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
    batch_size = len(profiles)
    min_balance = batch_params.get('min_balance', 0)
    limit = batch_params.get('limit', 0)
    
    total_value = sum(p.get('balance_usd', 0) or p.get('total_value_usd', 0) for p in profiles)
    avg_value = total_value / batch_size if batch_size > 0 else 0
    avg_confidence = sum(p.get('behavior', {}).get('confidence_score', 0) for p in profiles) / batch_size if batch_size > 0 else 0
    
    wallets_under_attack = []
    scam_domains = set()
    
    for profile in profiles:
        verdicts = profile.get('verdicts', [])
        for verdict in verdicts:
            if verdict.get('severity') in ['CRITICAL', 'HIGH']:
                title = verdict.get('title', '').upper()
                if 'SCAM' in title or 'PHISHING' in title or 'ATTACK' in title:
                    wallets_under_attack.append(profile.get('address', ''))
                    evidence = verdict.get('evidence', [])
                    for ev in evidence:
                        if 'http' in ev.lower() or '.com' in ev.lower() or '.xyz' in ev.lower() or '.top' in ev.lower():
                            parts = ev.split()
                            for part in parts:
                                if any(tld in part.lower() for tld in ['.com', '.xyz', '.top', '.win', '.click', '.io']):
                                    domain = part.split('/')[0] if '/' in part else part
                                    if '.' in domain:
                                        scam_domains.add(domain.lower())
        
        ipfs_data = profile.get('ipfs_osint', {})
        if ipfs_data and not ipfs_data.get('skipped') and not ipfs_data.get('error'):
            findings = ipfs_data.get('findings', {})
            if findings.get('domains'):
                if isinstance(findings['domains'], dict):
                    for domain, info in findings['domains'].items():
                        if info.get('reputation') == 'suspicious' or info.get('reputation') == 'scam':
                            scam_domains.add(domain.lower())
                elif isinstance(findings['domains'], list):
                    for domain in findings['domains']:
                        scam_domains.add(domain.lower())
    
    wallets_under_attack = list(set(wallets_under_attack))
    
    high_value_low_soph = []
    no_exchange_trail = []
    dangerous_approvals = []
    total_approval_exposure = 0.0
    
    for profile in profiles:
        balance = profile.get('balance_usd', 0) or profile.get('total_value_usd', 0)
        sophistication = profile.get('behavior', {}).get('sophistication', 'Unknown')
        exchange_interactions = profile.get('behavior', {}).get('exchange_interactions', [])
        
        if balance > 500000 and sophistication in ['Novice', 'Unknown']:
            high_value_low_soph.append(profile)
        
        if balance > 100000 and not exchange_interactions:
            no_exchange_trail.append(profile)
        
        approval_risk = profile.get('approval_risk', {})
        if approval_risk and not approval_risk.get('error'):
            high_risk = approval_risk.get('high_risk_approvals', 0)
            exposure = approval_risk.get('total_exposure_usd', 0)
            if high_risk > 0 or exposure > 0:
                dangerous_approvals.append({
                    'address': profile.get('address', ''),
                    'high_risk_count': high_risk,
                    'exposure_usd': exposure,
                    'unlimited_approvals': approval_risk.get('unlimited_approvals', 0),
                })
                total_approval_exposure += exposure
    
    top_targets = sorted(
        profiles,
        key=lambda p: (
            p.get('behavior', {}).get('confidence_score', 0),
            p.get('balance_usd', 0) or p.get('total_value_usd', 0)
        ),
        reverse=True
    )[:10]
    
    confidence_dist = {'High (70%+)': 0, 'Medium (40-69%)': 0, 'Low (<40%)': 0}
    sophistication_dist = {'Intermediate': 0, 'Novice': 0, 'Unknown': 0}
    region_dist = Counter()
    category_dist = Counter()
    
    for profile in profiles:
        conf = profile.get('behavior', {}).get('confidence_score', 0)
        if conf >= 70:
            confidence_dist['High (70%+)'] += 1
        elif conf >= 40:
            confidence_dist['Medium (40-69%)'] += 1
        else:
            confidence_dist['Low (<40%)'] += 1
        
        soph = profile.get('behavior', {}).get('sophistication', 'Unknown')
        if soph in sophistication_dist:
            sophistication_dist[soph] += 1
        else:
            sophistication_dist['Unknown'] += 1
        
        region = profile.get('behavior', {}).get('likely_region', 'Unknown')
        region_dist[region] += 1
        
        categories = profile.get('osint_categories', [])
        for cat in categories:
            cat_name = cat.split('_')[1] if '_' in cat else cat
            category_dist[cat_name] += 1
    
    summary = []
    summary.append("╔══════════════════════════════════════════════════════════════════════════════╗")
    summary.append("║                         📊 BATCH INTELLIGENCE SUMMARY                        ║")
    summary.append("║                        Wallet intelligence — batch review                    ║")
    summary.append("╚══════════════════════════════════════════════════════════════════════════════╝")
    summary.append("")
    summary.append(f"  Generated:    {timestamp} UTC")
    summary.append(f"  Batch Size:   {batch_size} profiles")
    summary.append(f"  Parameters:   min_balance=${min_balance:,}, limit={limit}")
    summary.append("")
    
    summary.append("━" * 80)
    summary.append("📋 EXECUTIVE SUMMARY")
    summary.append("━" * 80)
    summary.append("")
    
    if wallets_under_attack:
        summary.append(f"  🚨 {len(wallets_under_attack)} of {batch_size} wallets are under active attack by scammers")
    else:
        summary.append(f"  ✅ No active attacks detected in this batch")
    summary.append("")
    
    summary.append("  ┌─────────────────────────────────────────────────────────────────────────┐")
    summary.append(f"  │  Total Value Tracked:     ${total_value:>20,.0f}                        │")
    summary.append(f"  │  Average Wallet Value:    ${avg_value:>20,.0f}                        │")
    summary.append(f"  │  Real Person Confidence:  {avg_confidence:>15.0f}% avg                      │")
    summary.append(f"  │  Wallets Under Attack:    {len(wallets_under_attack):>15}                        │")
    summary.append(f"  │  Scam Domains Detected:   {len(scam_domains):>15}                        │")
    summary.append("  └─────────────────────────────────────────────────────────────────────────┘")
    summary.append("")
    
    summary.append("━" * 80)
    summary.append("🎯 KEY FINDINGS")
    summary.append("━" * 80)
    summary.append("")
    
    if wallets_under_attack:
        summary.append(f"  🚨 [THREAT] Concentrated scam-airdrop activity detected")
        summary.append(f"     {len(wallets_under_attack)} addresses show repeated scam-token or airdrop noise")
        summary.append("     → Prioritize victim-side documentation and authorized notification")
        summary.append("")
    
    if high_value_low_soph:
        summary.append(f"  💎 [TRIAGE] High balance with low sophistication indicators")
        summary.append(f"     {len(high_value_low_soph)} addresses over $500k notional with novice-style patterns")
        summary.append("     → Suitable for priority technical review and victim-protection outreach where authorized")
        summary.append("")
    
    if no_exchange_trail:
        summary.append(f"  🔍 [ANOMALY] Large Holders Without Exchange Trail")
        summary.append(f"     {len(no_exchange_trail)} wallets with >$100k but no CEX interactions")
        summary.append("     → May be privacy-conscious, OTC buyers, or suspicious origin")
        summary.append("")
    
    if dangerous_approvals:
        summary.append(f"  💀 [VULNERABILITY] Wallets with Dangerous Approvals")
        summary.append(f"     {len(dangerous_approvals)} wallets have ${total_approval_exposure:,.0f} in unlimited/high-risk approvals")
        summary.append("     → These wallets can be drained without further interaction")
        summary.append("")
    
    summary.append("━" * 80)
    summary.append("🏆 TOP ADDRESSES (Ranked for triage)")
    summary.append("━" * 80)
    summary.append("")
    summary.append("  #   Address                                           Balance   Conf Flags")
    summary.append("  --- -------------------------------------------- ------------ ------ --------------------")
    
    for i, profile in enumerate(top_targets[:10], 1):
        addr = profile.get('address', '')
        balance = profile.get('balance_usd', 0) or profile.get('total_value_usd', 0)
        conf = profile.get('behavior', {}).get('confidence_score', 0)
        
        flags = []
        if addr in wallets_under_attack:
            flags.append("🚨ATTACKED")
        if balance > 500000:
            flags.append("💎HIGH+")
        sophistication = profile.get('behavior', {}).get('sophistication', 'Unknown')
        if sophistication in ['Novice', 'Unknown']:
            flags.append("🐟NOVICE")
        
        flags_str = " ".join(flags) if flags else ""
        summary.append(f"  {i:<3} {addr[:42]:<42} ${balance:>12,.0f} {conf:>5.0f}% {flags_str}")
    
    summary.append("")
    
    if wallets_under_attack or scam_domains:
        summary.append("━" * 80)
        summary.append("⚠️  ACTIVE THREAT LANDSCAPE")
        summary.append("━" * 80)
        summary.append("")
        
        if wallets_under_attack:
            summary.append(f"  Wallets Under Active Attack: {len(wallets_under_attack)}")
            for addr in wallets_under_attack[:5]:
                profile = next((p for p in profiles if p.get('address') == addr), None)
                if profile:
                    balance = profile.get('balance_usd', 0) or profile.get('total_value_usd', 0)
                    nft_count = 0
                    verdicts = profile.get('verdicts', [])
                    for v in verdicts:
                        if 'SCAM' in v.get('title', '').upper() or 'NFT' in v.get('title', '').upper():
                            nft_count += 1
                    summary.append(f"    • {addr[:20]}... (${balance:,.0f}) - {nft_count} scam NFTs received")
            if len(wallets_under_attack) > 5:
                summary.append(f"    ... and {len(wallets_under_attack) - 5} more")
            summary.append("")
        
        if scam_domains:
            summary.append(f"  Scam Domains Detected: {len(scam_domains)}")
            for domain in sorted(list(scam_domains))[:10]:
                summary.append(f"    • {domain}")
            if len(scam_domains) > 10:
                summary.append(f"    ... and {len(scam_domains) - 10} more")
            summary.append("")
    
    summary.append("━" * 80)
    summary.append("📊 DISTRIBUTION BREAKDOWN")
    summary.append("━" * 80)
    summary.append("")
    
    summary.append("  By Confidence:                    By Sophistication:")
    high_conf = confidence_dist.get('High (70%+)', 0)
    med_conf = confidence_dist.get('Medium (40-69%)', 0)
    low_conf = confidence_dist.get('Low (<40%)', 0)
    inter_soph = sophistication_dist.get('Intermediate', 0)
    nov_soph = sophistication_dist.get('Novice', 0)
    unk_soph = sophistication_dist.get('Unknown', 0)
    
    summary.append(f"    High (70%+):      {high_conf:<3}            Intermediate:   {inter_soph:<3}")
    summary.append(f"    Medium (40-69%):  {med_conf:<3}            Novice      :   {nov_soph:<3}")
    summary.append(f"    Low (<40%):       {low_conf:<3}            Unknown     :   {unk_soph:<3}")
    summary.append("")
    
    if region_dist:
        summary.append("  By Region:")
        for region, count in region_dist.most_common(5):
            bar_length = int((count / batch_size) * 20) if batch_size > 0 else 0
            bar = "█" * bar_length + "░" * (20 - bar_length)
            pct = (count / batch_size * 100) if batch_size > 0 else 0
            summary.append(f"    {region:<15} {bar}   {count} ({pct:.0f}%)")
        summary.append("")
    
    if category_dist:
        summary.append("  By Category:")
        for cat, count in category_dist.most_common(10):
            summary.append(f"    {cat:<20} {count:>3} ({count/batch_size*100:.0f}%)" if batch_size > 0 else f"    {cat:<20} {count:>3}")
        summary.append("")
    
    summary.append("━" * 80)
    summary.append("💡 RECOMMENDATIONS")
    summary.append("━" * 80)
    summary.append("")
    
    if wallets_under_attack:
        summary.append(f"  • 🚨 URGENT: {len(wallets_under_attack)} addresses show heavy scam-airdrop load. Document for case files; coordinate victim notification only under lawful authority.")
        summary.append("")
    
    if high_value_low_soph:
        summary.append(f"  • 💎 HIGH-VALUE: {len(high_value_low_soph)} addresses combine large notionals with low sophistication indicators — prioritize for supervised review and optional outreach where policy allows.")
        summary.append("")
    
    if scam_domains:
        summary.append(f"  • 🛡️ THREAT INTEL: {len(scam_domains)} scam domains detected. Consider reporting to domain registrars or adding to blocklists.")
        summary.append("")
    
    summary.append("━" * 80)
    summary.append("")
    summary.append("  Next Steps:")
    summary.append("    1. Run 'target_search.py --scam-victim' to list likely scam-airdrop recipients")
    summary.append("    2. Run 'priority_triage.py' to score and organize profiles")
    summary.append("    3. Review priority queue in 'profiles/🎯_actionable/'")
    summary.append("")
    summary.append("━" * 80)
    summary.append("")
    
    summary.append("╔══════════════════════════════════════════════════════════════════════════════╗")
    summary.append("║                            END OF BATCH SUMMARY                              ║")
    summary.append("╚══════════════════════════════════════════════════════════════════════════════╝")
    
    return "\n".join(summary)

def save_batch_summary(profiles: List[Dict], batch_params: Dict, base_dir: str = "batch_intelligence") -> str:
    os.makedirs(base_dir, exist_ok=True)
    
    timestamp = datetime.now(timezone.utc)
    timestamp_str = timestamp.strftime('%Y%m%d_%H%M%S')
    
    batch_dir = os.path.join(base_dir, f"batch_{timestamp_str}")
    os.makedirs(batch_dir, exist_ok=True)
    
    summary_text = generate_batch_summary(profiles, batch_params)
    
    summary_file = os.path.join(batch_dir, "batch_summary.txt")
    with open(summary_file, 'w', encoding='utf-8') as f:
        f.write(summary_text)
    
    batch_data = {
        'generated_at': timestamp.isoformat(),
        'batch_size': len(profiles),
        'parameters': batch_params,
        'total_value_usd': sum(p.get('balance_usd', 0) or p.get('total_value_usd', 0) for p in profiles),
        'profiles': [
            {
                'address': p.get('address', ''),
                'balance_usd': p.get('balance_usd', 0) or p.get('total_value_usd', 0),
                'confidence': p.get('behavior', {}).get('confidence_score', 0),
                'sophistication': p.get('behavior', {}).get('sophistication', 'Unknown'),
                'categories': p.get('osint_categories', []),
            }
            for p in profiles
        ]
    }
    
    batch_json = os.path.join(batch_dir, "batch_data.json")
    with open(batch_json, 'w', encoding='utf-8') as f:
        json.dump(batch_data, f, indent=2)
    
    return summary_file
