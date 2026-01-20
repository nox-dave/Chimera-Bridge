#!/usr/bin/env python3

from typing import List, Dict
from dataclasses import dataclass, field
from .pattern_engine import PatternEngine

@dataclass
class Verdict:
    title: str
    severity: str
    category: str
    description: str
    evidence: List[str] = field(default_factory=list)
    action: str = ""

SEVERITY_ICONS = {
    "CRITICAL": "🚨",
    "HIGH": "⚠️",
    "MEDIUM": "⚡",
    "LOW": "📌",
    "INFO": "ℹ️",
}

def analyze_domain_for_verdicts(domain: str, context: dict = None) -> List[Verdict]:
    verdicts = []
    context = context or {}
    
    domain_lower = domain.lower()
    
    scam_keywords = {
        'lucky': 'Lottery/giveaway scam bait',
        'free': 'Free money scam bait',
        'claim': 'Claim/redeem phishing',
        'airdrop': 'Fake airdrop',
        'reward': 'Fake rewards',
        'bonus': 'Fake bonus',
        'gift': 'Fake gift',
        'win': 'Fake winner scam',
        'prize': 'Fake prize',
        'verified': 'Fake verification',
        'secure': 'False security claim',
        'official': 'Impersonation attempt',
    }
    
    token_names = {
        'usdc': 'USDC stablecoin',
        'usdt': 'USDT/Tether stablecoin', 
        'eth': 'Ethereum',
        'btc': 'Bitcoin',
        'bnb': 'Binance Coin',
        'uni': 'Uniswap',
        'aave': 'Aave',
        'link': 'Chainlink',
        'matic': 'Polygon',
        'sol': 'Solana',
    }
    
    protocol_names = {
        'uniswap': 'Uniswap DEX',
        'opensea': 'OpenSea NFT marketplace',
        'metamask': 'MetaMask wallet',
        'coinbase': 'Coinbase exchange',
        'binance': 'Binance exchange',
        'ledger': 'Ledger hardware wallet',
        'trezor': 'Trezor hardware wallet',
        'pancake': 'PancakeSwap',
        'sushi': 'SushiSwap',
    }
    
    nft_collections = {
        'azuki': 'Azuki NFT collection',
        'boredape': 'Bored Ape Yacht Club',
        'bayc': 'Bored Ape Yacht Club',
        'bbyc': 'Bored Ape Yacht Club',
        'imaginaryones': 'Imaginary Ones',
        'louisvuitton': 'Louis Vuitton',
        'phantom': 'Phantom wallet',
        'apiens': 'Apiens NFT',
        'youtopia': 'Youtopia NFT',
    }
    
    suspicious_tlds = ['.xyz', '.top', '.win', '.click', '.link', '.info', '.site', '.online', '.icu']
    
    evidence = []
    is_scam = False
    impersonating = None
    
    for keyword, meaning in scam_keywords.items():
        if keyword in domain_lower:
            evidence.append(f"Contains '{keyword}' - {meaning}")
            is_scam = True
    
    for token, name in token_names.items():
        if token in domain_lower:
            impersonating = name
            evidence.append(f"Impersonating {name}")
    
    for protocol, name in protocol_names.items():
        if protocol in domain_lower:
            impersonating = name
            evidence.append(f"Impersonating {name}")
    
    for collection, name in nft_collections.items():
        if collection in domain_lower:
            impersonating = name
            evidence.append(f"Impersonating {name} NFT collection")
    
    for tld in suspicious_tlds:
        if domain_lower.endswith(tld):
            evidence.append(f"Suspicious TLD: {tld}")
            is_scam = True
            break
    
    if is_scam and impersonating:
        verdicts.append(Verdict(
            title="SCAM NFT AIRDROP DETECTED",
            severity="CRITICAL",
            category="THREAT",
            description=f"This wallet received an NFT from a scam domain impersonating {impersonating}. "
                       f"The domain '{domain}' is designed to phish users.",
            evidence=evidence,
            action="Do not interact with this NFT or visit the domain"
        ))
    elif is_scam:
        verdicts.append(Verdict(
            title="SUSPICIOUS NFT AIRDROP",
            severity="HIGH",
            category="THREAT",
            description=f"This wallet received an NFT from suspicious domain '{domain}'. "
                       f"Likely a phishing or scam attempt.",
            evidence=evidence,
            action="Investigate domain before any interaction"
        ))
    elif impersonating:
        verdicts.append(Verdict(
            title="POTENTIAL IMPERSONATION",
            severity="MEDIUM",
            category="THREAT",
            description=f"Domain '{domain}' may be impersonating {impersonating}.",
            evidence=evidence,
            action="Verify authenticity before trusting"
        ))
    
    return verdicts

def analyze_wallet_for_verdicts(profile_data: dict) -> List[Verdict]:
    verdicts = []
    
    osint_categories = profile_data.get('osint_categories', [])
    if "🏢_institutions" in osint_categories:
        return verdicts
    
    engine = PatternEngine()
    pattern_verdicts = engine.get_verdicts(profile_data)
    
    verdict_titles = {v.title for v in pattern_verdicts}
    
    for verdict in pattern_verdicts:
        if verdict.category == "FILTER":
            continue
        verdicts.append(verdict)
    
    return verdicts

def analyze_scam_campaign_patterns(ipfs_data: dict, profile_data: dict = None) -> List[Verdict]:
    verdicts = []
    findings = ipfs_data.get('findings', {})
    
    domains = findings.get('domains', [])
    domain_analysis = findings.get('domain_analysis', {})
    metadata_urls = findings.get('metadata_urls', [])
    
    suspicious_domains = []
    http_urls = []
    official_keyword_domains = []
    dead_domains = []
    
    for domain in domains:
        analysis = domain_analysis.get(domain, {})
        reputation = analysis.get('reputation', 'unknown')
        scam_indicators = analysis.get('scam_indicators', [])
        
        if reputation == 'suspicious' or scam_indicators:
            suspicious_domains.append(domain)
        
        if 'official' in domain.lower():
            official_keyword_domains.append(domain)
    
    for meta in metadata_urls:
        uri = meta.get('uri', '')
        if uri.startswith('http://'):
            http_urls.append(uri)
            try:
                from urllib.parse import urlparse
                parsed = urlparse(uri)
                domain = parsed.netloc or (uri.split('/')[2] if len(uri.split('/')) > 2 else '')
                if domain and domain not in dead_domains:
                    dead_domains.append(domain)
            except:
                domain = uri.split('/')[2] if len(uri.split('/')) > 2 else ''
                if domain and domain not in dead_domains:
                    dead_domains.append(domain)
    
    suspicious_count = len(suspicious_domains)
    
    if suspicious_count >= 5:
        severity = "CRITICAL" if suspicious_count >= 9 else "HIGH"
        verdicts.append(Verdict(
            title="CARPET BOMBING SCAM CAMPAIGN",
            severity=severity,
            category="THREAT",
            description=f"Wallet is being carpet bombed with {suspicious_count} different scam NFT campaigns. "
                       f"Attackers have identified this wallet and are coordinating multiple phishing attempts. "
                       f"This pattern indicates the wallet is on a 'fresh whale' list being sold to scammers.",
            evidence=[
                f"{suspicious_count} suspicious domains detected",
                f"Multiple coordinated phishing campaigns",
                "Wallet is on attacker radar",
                "Likely on a 'fresh whale' list being sold"
            ] + [f"Domain: {d}" for d in suspicious_domains[:5]],
            action="High-priority target - multiple attacker groups know about this wallet"
        ))
    
    if len(official_keyword_domains) >= 3:
        verdicts.append(Verdict(
            title="IMPERSONATION PATTERN DETECTED",
            severity="HIGH",
            category="THREAT",
            description=f"Multiple domains ({len(official_keyword_domains)}) use the 'official' keyword to build false trust. "
                       f"This is a coordinated impersonation campaign targeting this wallet.",
            evidence=[
                f"{len(official_keyword_domains)} domains using 'official' keyword",
                "Pattern indicates coordinated attack",
                "Designed to build false trust"
            ] + [f"Domain: {d}" for d in official_keyword_domains[:5]],
            action="All domains using 'official' are likely scams - do not trust"
        ))
    
    if http_urls:
        http_count = len(http_urls)
        verdicts.append(Verdict(
            title="HTTP PROTOCOL USAGE",
            severity="MEDIUM",
            category="THREAT",
            description=f"Found {http_count} metadata URLs using HTTP instead of HTTPS. "
                       f"Legitimate NFT projects use HTTPS. HTTP indicates lazy scammers or intentional security bypass.",
            evidence=[
                f"{http_count} HTTP URLs detected",
                "Legitimate projects use HTTPS",
                "HTTP = scam indicator or lazy attacker"
            ] + [f"URL: {url[:60]}..." for url in http_urls[:3]],
            action="HTTP URLs are highly suspicious - likely scam infrastructure"
        ))
    
    if profile_data:
        balance_usd = profile_data.get('balance_usd', profile_data.get('total_value_usd', 0)) or 0
        wallet_age_days = profile_data.get('wallet_age_days', profile_data.get('age_days', 0)) or 0
        
        if wallet_age_days <= 7 and balance_usd > 500000 and suspicious_count >= 3:
            verdicts.append(Verdict(
                title="ON FRESH WHALE LIST",
                severity="CRITICAL",
                category="THREAT",
                description=f"Brand new wallet ({wallet_age_days} days old) with ${balance_usd:,.0f} is being targeted by "
                           f"{suspicious_count} different scam campaigns. This indicates the wallet address is on a 'fresh whale' "
                           f"list being sold to multiple attacker groups. Attackers know this wallet exists and have its address.",
                evidence=[
                    f"Wallet age: {wallet_age_days} days",
                    f"Balance: ${balance_usd:,.0f}",
                    f"{suspicious_count} scam campaigns detected",
                    "Multiple attacker groups targeting same wallet",
                    "Address likely leaked from exchange or tracked via mempool"
                ],
                action="This wallet is being actively monitored by scammers - high-value target"
            ))
    
    return verdicts

def analyze_ipfs_for_verdicts(ipfs_data: dict, profile_data: dict = None) -> List[Verdict]:
    verdicts = []
    
    findings = ipfs_data.get('findings', {})
    
    usernames = findings.get('usernames', [])
    emails = findings.get('emails', [])
    social_links = findings.get('social_links', [])
    
    verdicts.extend(analyze_scam_campaign_patterns(ipfs_data, profile_data))
    
    if emails:
        verdicts.append(Verdict(
            title="EMAIL ADDRESS LEAKED",
            severity="HIGH",
            category="INTEL",
            description="Email address found in NFT metadata. Direct pivot to real identity.",
            evidence=[f"Email: {email}" for email in emails[:3]],
            action="Cross-reference with breach databases, social media"
        ))
    
    if usernames:
        verdicts.append(Verdict(
            title="USERNAME DISCOVERED",
            severity="MEDIUM",
            category="INTEL",
            description="Username found in NFT metadata. Can be used for cross-platform OSINT.",
            evidence=[f"Username: {u}" for u in usernames[:5]],
            action="Search across social platforms"
        ))
    
    if social_links:
        verdicts.append(Verdict(
            title="SOCIAL MEDIA LINKED",
            severity="HIGH",
            category="INTEL",
            description="Social media profiles found in NFT metadata. Direct identity connection.",
            evidence=[f"Link: {link}" for link in social_links[:3]],
            action="Profile target via social media"
        ))
    
    creators = findings.get('creators', [])
    if creators:
        verdicts.append(Verdict(
            title="NFT CREATOR IDENTIFIED",
            severity="LOW",
            category="INTEL",
            description="Creator wallet addresses found. Can trace NFT origin.",
            evidence=[f"Creator: {c[:20]}..." if len(c) > 20 else f"Creator: {c}" for c in creators[:3]],
            action="Analyze creator wallet for additional intel"
        ))
    
    return verdicts

def analyze_ens_for_verdicts(ens_data: dict) -> List[Verdict]:
    verdicts = []
    
    if not ens_data or not ens_data.get('has_ens'):
        return verdicts
    
    ens_name = ens_data.get('ens_name', '')
    social_links = ens_data.get('social_links', {})
    text_records = ens_data.get('text_records', {})
    
    if social_links:
        has_twitter = bool(social_links.get('twitter'))
        has_discord = bool(social_links.get('discord'))
        has_github = bool(social_links.get('github'))
        
        if has_twitter or has_discord:
            platforms = []
            if has_twitter:
                platforms.append(f"Twitter: {social_links['twitter']}")
            if has_discord:
                platforms.append(f"Discord: {social_links['discord']}")
            if has_github:
                platforms.append(f"GitHub: {social_links['github']}")
            
            verdicts.append(Verdict(
                title="SOCIAL IDENTITY LINKED",
                severity="HIGH",
                category="INTEL",
                description=f"Wallet has ENS name '{ens_name}' with verified social media links. "
                           f"Direct identity pivot point for OSINT operations.",
                evidence=[
                    f"ENS: {ens_name}",
                ] + platforms,
                action="Profile target via social media for additional OSINT"
            ))
    
    if text_records.get('email'):
        verdicts.append(Verdict(
            title="EMAIL IN ENS RECORD",
            severity="MEDIUM",
            category="INTEL",
            description=f"Email address found in ENS text records for '{ens_name}'.",
            evidence=[
                f"ENS: {ens_name}",
                f"Email: {text_records['email']}"
            ],
            action="Cross-reference with breach databases, social media"
        ))
    
    if text_records.get('url'):
        verdicts.append(Verdict(
            title="PERSONAL WEBSITE LINKED",
            severity="LOW",
            category="INTEL",
            description=f"Personal website found in ENS records for '{ens_name}'.",
            evidence=[
                f"ENS: {ens_name}",
                f"Website: {text_records['url']}"
            ],
            action="Analyze website for additional identity information"
        ))
    
    return verdicts

def format_verdicts_for_report(verdicts: List[Verdict]) -> str:
    if not verdicts:
        return ""
    
    lines = [
        "",
        "━" * 80,
        "🎯 OSINT VERDICTS",
        "━" * 80,
        ""
    ]
    
    by_severity = {"CRITICAL": [], "HIGH": [], "MEDIUM": [], "LOW": [], "INFO": []}
    for v in verdicts:
        by_severity.get(v.severity, by_severity["INFO"]).append(v)
    
    for severity in ["CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"]:
        severity_verdicts = by_severity[severity]
        if not severity_verdicts:
            continue
        
        for v in severity_verdicts:
            icon = SEVERITY_ICONS.get(v.severity, "•")
            lines.append(f"{icon} [{v.severity}] {v.title}")
            lines.append(f"   {v.description}")
            
            if v.evidence:
                lines.append("   Evidence:")
                for e in v.evidence[:4]:
                    lines.append(f"     • {e}")
            
            if v.action:
                lines.append(f"   → Action: {v.action}")
            
            lines.append("")
    
    return "\n".join(lines)

def analyze_approvals_for_verdicts(approval_data: dict) -> List[Verdict]:
    verdicts = []
    
    if not approval_data or not approval_data.get('verdicts'):
        return verdicts
    
    approval_verdicts = approval_data.get('verdicts', [])
    
    for av in approval_verdicts:
        verdicts.append(Verdict(
            title=av.get('title', 'TOKEN APPROVAL RISK'),
            severity=av.get('severity', 'MEDIUM'),
            category='THREAT',
            description=av.get('description', ''),
            evidence=av.get('evidence', []),
            action=av.get('action', 'Review and revoke if necessary')
        ))
    
    return verdicts

def generate_all_verdicts(profile_data: dict, ipfs_data: dict = None, domains: List[str] = None, ens_data: dict = None, approval_data: dict = None) -> List[Verdict]:
    all_verdicts = []
    
    all_verdicts.extend(analyze_wallet_for_verdicts(profile_data))
    
    if ipfs_data:
        all_verdicts.extend(analyze_ipfs_for_verdicts(ipfs_data, profile_data))
    
    if domains:
        for domain in domains:
            all_verdicts.extend(analyze_domain_for_verdicts(domain))
    
    if ens_data:
        all_verdicts.extend(analyze_ens_for_verdicts(ens_data))
    
    if approval_data:
        all_verdicts.extend(analyze_approvals_for_verdicts(approval_data))
    
    severity_order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3, "INFO": 4}
    all_verdicts.sort(key=lambda v: severity_order.get(v.severity, 5))
    
    return all_verdicts

