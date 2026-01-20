#!/usr/bin/env python3

import os
import sys
import json
import argparse
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Callable
from dataclasses import dataclass

PROFILES_DIR = "profiles"

def load_all_profiles(profiles_dir: str = PROFILES_DIR) -> List[dict]:
    profiles = []
    
    all_dir = os.path.join(profiles_dir, "_all")
    if os.path.exists(all_dir):
        search_dirs = [all_dir]
    else:
        search_dirs = [profiles_dir]
    
    seen_addresses = set()
    
    for search_dir in search_dirs:
        for root, dirs, files in os.walk(search_dir):
            if '📦_archive' in root or '🗑️_trash' in root:
                continue
            
            if 'profile.json' in files:
                filepath = os.path.join(root, 'profile.json')
                try:
                    with open(filepath, 'r') as f:
                        data = json.load(f)
                    
                    address = data.get('address', '').lower()
                    if address and address not in seen_addresses:
                        data['_folder'] = root
                        profiles.append(data)
                        seen_addresses.add(address)
                
                except Exception as e:
                    pass
    
    return profiles

def parse_comparison(value_str: str) -> tuple:
    value_str = value_str.strip()
    
    if value_str.startswith('>='):
        op = '>='
        num_str = value_str[2:]
    elif value_str.startswith('<='):
        op = '<='
        num_str = value_str[2:]
    elif value_str.startswith('>'):
        op = '>'
        num_str = value_str[1:]
    elif value_str.startswith('<'):
        op = '<'
        num_str = value_str[1:]
    elif value_str.startswith('='):
        op = '='
        num_str = value_str[1:]
    else:
        op = '>='
        num_str = value_str
    
    num_str = num_str.strip().upper()
    multiplier = 1
    
    if num_str.endswith('M'):
        multiplier = 1_000_000
        num_str = num_str[:-1]
    elif num_str.endswith('K'):
        multiplier = 1_000
        num_str = num_str[:-1]
    elif num_str.endswith('B'):
        multiplier = 1_000_000_000
        num_str = num_str[:-1]
    
    try:
        num = float(num_str) * multiplier
    except:
        num = 0
    
    return op, num

def compare_value(actual: float, op: str, target: float) -> bool:
    if op == '>':
        return actual > target
    elif op == '>=':
        return actual >= target
    elif op == '<':
        return actual < target
    elif op == '<=':
        return actual <= target
    elif op == '=':
        return actual == target
    return False

def filter_balance(profiles: List[dict], condition: str) -> List[dict]:
    op, target = parse_comparison(condition)
    
    return [p for p in profiles if compare_value(
        p.get('balance_usd', p.get('total_value_usd', 0)), op, target
    )]

def filter_confidence(profiles: List[dict], condition: str) -> List[dict]:
    op, target = parse_comparison(condition)
    
    def get_confidence(p):
        behavior = p.get('behavior', {})
        return behavior.get('confidence_score', p.get('risk_score', 50))
    
    return [p for p in profiles if compare_value(get_confidence(p), op, target)]

def filter_category(profiles: List[dict], category: str) -> List[dict]:
    category = category.lower().strip()
    
    category_map = {
        'gamblers': '🎰_gamblers',
        'gambler': '🎰_gamblers',
        'newcomers': '🆕_newcomers',
        'newcomer': '🆕_newcomers',
        'new': '🆕_newcomers',
        'fresh': '🆕_newcomers',
        'status': '🏆_status_seekers',
        'nft': '🏆_status_seekers',
        'dormant': '💤_dormant_whales',
        'sleeping': '💤_dormant_whales',
        'cross_chain': '🌉_cross_chain_users',
        'bridge': '🌉_cross_chain_users',
        'easy': '🐟_easy_targets',
        'fish': '🐟_easy_targets',
        'noob': '🐟_easy_targets',
        'cautious': '🦊_cautious_holders',
        'careful': '🦊_cautious_holders',
        'defi': '🧠_defi_natives',
        'advanced': '🧠_defi_natives',
        'night': '🌙_night_traders',
        'momentum': '📈_momentum_chasers',
        'fomo': '📈_momentum_chasers',
        'governance': '🏛️_governance_voters',
        'dao': '🏛️_governance_voters',
        'high_value': '💎_high_value',
        'whale': '💎_high_value',
        'prime': '🎯_prime_targets',
        'target': '🎯_prime_targets',
        'institution': '🏢_institutions',
        'exchange': '🏢_institutions',
        'bot': '🤖_bots',
    }
    
    full_category = category_map.get(category, category)
    
    def has_category(p):
        cats = p.get('osint_categories', [])
        folder = p.get('_folder', '')
        return full_category in cats or full_category in folder
    
    return [p for p in profiles if has_category(p)]

def filter_region(profiles: List[dict], region: str) -> List[dict]:
    region = region.lower().strip()
    
    region_keywords = {
        'europe': ['europe', 'eu', 'utc+0', 'utc+1', 'utc+2', 'utc+3'],
        'us': ['america', 'us', 'usa', 'utc-5', 'utc-6', 'utc-7', 'utc-8'],
        'asia': ['asia', 'pacific', 'utc+8', 'utc+9', 'utc+10', 'utc+11', 'utc+12'],
    }
    
    keywords = region_keywords.get(region, [region])
    
    def matches_region(p):
        behavior = p.get('behavior', {})
        likely_region = behavior.get('likely_region', '').lower()
        timezone = behavior.get('likely_timezone', '').lower()
        
        for kw in keywords:
            if kw in likely_region or kw in timezone:
                return True
        return False
    
    return [p for p in profiles if matches_region(p)]

def filter_sophistication(profiles: List[dict], level: str) -> List[dict]:
    level = level.lower().strip()
    
    def matches_level(p):
        behavior = p.get('behavior', {})
        soph = behavior.get('sophistication', '').lower()
        return level in soph
    
    return [p for p in profiles if matches_level(p)]

def filter_has_scam_nfts(profiles: List[dict]) -> List[dict]:
    def has_scam(p):
        verdicts = p.get('verdicts', [])
        for verdict in verdicts:
            if verdict.get('severity') in ['CRITICAL', 'HIGH']:
                title = verdict.get('title', '').upper()
                if 'SCAM' in title or 'PHISHING' in title or 'ATTACK' in title:
                    return True
        
        folder = p.get('_folder', '')
        ipfs_path = os.path.join(folder, 'ipfs_osint.json')
        
        if os.path.exists(ipfs_path):
            try:
                with open(ipfs_path) as f:
                    ipfs_data = json.load(f)
                
                findings = ipfs_data.get('findings', {})
                domain_analysis = findings.get('domain_analysis', {}) or ipfs_data.get('domain_analysis', {})
                
                if isinstance(domain_analysis, dict):
                    for domain, info in domain_analysis.items():
                        if isinstance(info, dict):
                            reputation = info.get('reputation', '').lower()
                            if reputation in ['suspicious', 'scam']:
                                return True
                            scam_indicators = info.get('scam_indicators', [])
                            if scam_indicators and len(scam_indicators) > 0:
                                return True
            except:
                pass
        
        return False
    
    return [p for p in profiles if has_scam(p)]

def filter_has_ens(profiles: List[dict]) -> List[dict]:
    def has_ens(p):
        ens = p.get('ens_name') or p.get('behavior', {}).get('ens_name')
        return ens and ens != 'None'
    
    return [p for p in profiles if has_ens(p)]

def filter_no_exchange(profiles: List[dict]) -> List[dict]:
    def no_exchange(p):
        behavior = p.get('behavior', {})
        exchanges = behavior.get('exchange_interactions', [])
        return not exchanges or len(exchanges) == 0
    
    return [p for p in profiles if no_exchange(p)]

def filter_meme_exposure(profiles: List[dict]) -> List[dict]:
    def has_meme(p):
        behavior = p.get('behavior', {})
        return behavior.get('meme_exposure', False)
    
    return [p for p in profiles if has_meme(p)]

def filter_dust_target(profiles: List[dict]) -> List[dict]:
    def is_dust_target(p):
        behavior = p.get('behavior', {})
        return behavior.get('dust_attack_target', False)
    
    return [p for p in profiles if is_dust_target(p)]

def filter_rich_and_dumb(profiles: List[dict]) -> List[dict]:
    result = filter_balance(profiles, ">500k")
    result = [p for p in result if 
              p.get('behavior', {}).get('sophistication', '').lower() in ['novice', 'unknown', '']]
    return result

def filter_prime_targets(profiles: List[dict]) -> List[dict]:
    result = filter_balance(profiles, ">100k")
    result = filter_confidence(result, ">50")
    
    def is_vulnerable(p):
        cats = p.get('osint_categories', [])
        vulnerable_cats = ['🆕_newcomers', '🐟_easy_targets', '🎰_gamblers', '🏆_status_seekers']
        return any(c in cats for c in vulnerable_cats)
    
    return [p for p in result if is_vulnerable(p)]

def filter_phishing_victims(profiles: List[dict]) -> List[dict]:
    result = filter_has_scam_nfts(profiles)
    result = filter_dust_target(result) if not result else result
    return result

def filter_eu_whales(profiles: List[dict]) -> List[dict]:
    result = filter_balance(profiles, ">500k")
    result = filter_region(result, "europe")
    return result

def filter_asia_whales(profiles: List[dict]) -> List[dict]:
    result = filter_balance(profiles, ">500k")
    result = filter_region(result, "asia")
    return result

def format_results(profiles: List[dict], verbose: bool = False) -> str:
    if not profiles:
        return "No matching profiles found."
    
    profiles = sorted(profiles, key=lambda p: p.get('balance_usd', 0), reverse=True)
    
    lines = [
        f"",
        f"🎯 SEARCH RESULTS: {len(profiles)} targets found",
        f"=" * 70,
        f"",
    ]
    
    if verbose:
        for p in profiles[:20]:
            address = p.get('address', 'Unknown')
            balance = p.get('balance_usd', p.get('total_value_usd', 0))
            confidence = p.get('behavior', {}).get('confidence_score', p.get('risk_score', '?'))
            cats = p.get('osint_categories', [])
            cat_short = ', '.join(c.split('_')[1] if '_' in c else c for c in cats[:3])
            region = p.get('behavior', {}).get('likely_region', 'Unknown')
            soph = p.get('behavior', {}).get('sophistication', 'Unknown')
            
            lines.append(f"┌─ {address}")
            lines.append(f"│  Balance:      ${balance:>15,.0f}")
            lines.append(f"│  Confidence:   {confidence}%")
            lines.append(f"│  Region:       {region}")
            lines.append(f"│  Sophistication: {soph}")
            lines.append(f"│  Categories:   {cat_short}")
            lines.append(f"│  Etherscan:    https://etherscan.io/address/{address}")
            lines.append(f"└─")
            lines.append(f"")
    else:
        lines.append(f"{'Address':<44} {'Balance':>14} {'Conf':>6} {'Region':<12} {'Categories'}")
        lines.append(f"-" * 100)
        
        for p in profiles[:30]:
            address = p.get('address', 'Unknown')[:42]
            balance = p.get('balance_usd', p.get('total_value_usd', 0))
            confidence = p.get('behavior', {}).get('confidence_score', p.get('risk_score', '?'))
            cats = p.get('osint_categories', [])
            cat_short = ', '.join(c.split('_')[1][:8] if '_' in c else c[:8] for c in cats[:2])
            region = p.get('behavior', {}).get('likely_region', '?')[:10]
            
            lines.append(f"{address:<44} ${balance:>13,.0f} {confidence:>5}% {region:<12} {cat_short}")
        
        if len(profiles) > 30:
            lines.append(f"")
            lines.append(f"... and {len(profiles) - 30} more")
    
    lines.append(f"")
    lines.append(f"=" * 70)
    
    return "\n".join(lines)

def export_addresses(profiles: List[dict]) -> str:
    return "\n".join(p.get('address', '') for p in profiles if p.get('address'))

def interactive_search(profiles_dir: str = PROFILES_DIR):
    print("""
╔══════════════════════════════════════════════════════════════════════════════╗
║                         🔍 GARGOPHIAS TARGET SEARCH                          ║
╚══════════════════════════════════════════════════════════════════════════════╝

QUICK FILTERS (type and press Enter):

  rich            Balance > $1M
  dumb            Low sophistication (Novice/Unknown)
  rich+dumb       High balance + Low sophistication (PRIME TARGETS)
  
  newcomer        Fresh wallets with funds
  gambler         Meme coin players, high frequency traders
  easy            Easy targets (low sophistication)
  whale           High value holders (>$1M)
  
  europe          European timezone
  asia            Asia-Pacific timezone
  us              US/Americas timezone
  
  scam            Received scam NFT airdrops (being targeted)
  dust            Targeted by dust attacks
  meme            Has meme coin exposure
  
ADVANCED FILTERS:

  balance >500k   Custom balance filter
  conf >70        Confidence score filter
  cat gamblers    Specific category
  
COMMANDS:

  export          Export current results as address list
  clear           Clear filters
  quit            Exit

""")
    
    all_profiles = load_all_profiles(profiles_dir)
    current_results = all_profiles
    
    print(f"Loaded {len(all_profiles)} profiles.\n")
    
    while True:
        try:
            query = input("🔍 Search> ").strip().lower()
        except (KeyboardInterrupt, EOFError):
            print("\nGoodbye.")
            break
        
        if not query:
            continue
        
        if query in ['quit', 'exit', 'q']:
            print("Goodbye.")
            break
        
        if query == 'clear':
            current_results = all_profiles
            print(f"Filters cleared. {len(current_results)} profiles.")
            continue
        
        if query == 'export':
            print(export_addresses(current_results))
            continue
        
        results = all_profiles
        
        if 'rich+dumb' in query or 'rich dumb' in query:
            results = filter_rich_and_dumb(results)
        elif query == 'rich':
            results = filter_balance(results, ">1M")
        elif query == 'dumb':
            results = filter_sophistication(results, "novice")
            results += [p for p in all_profiles if p.get('behavior', {}).get('sophistication', '').lower() in ['unknown', '']]
        elif query == 'prime':
            results = filter_prime_targets(results)
        elif query in ['newcomer', 'newcomers', 'new', 'fresh']:
            results = filter_category(results, 'newcomers')
        elif query in ['gambler', 'gamblers']:
            results = filter_category(results, 'gamblers')
        elif query in ['easy', 'fish', 'noob']:
            results = filter_category(results, 'easy')
        elif query in ['whale', 'whales', 'high_value']:
            results = filter_balance(results, ">1M")
        elif query in ['europe', 'eu']:
            results = filter_region(results, 'europe')
        elif query in ['asia', 'asian', 'apac']:
            results = filter_region(results, 'asia')
        elif query in ['us', 'usa', 'america']:
            results = filter_region(results, 'us')
        elif query in ['scam', 'scammed', 'phishing']:
            results = filter_has_scam_nfts(results)
        elif query == 'dust':
            results = filter_dust_target(results)
        elif query in ['meme', 'memes']:
            results = filter_meme_exposure(results)
        elif query.startswith('balance'):
            parts = query.split(maxsplit=1)
            if len(parts) > 1:
                results = filter_balance(results, parts[1])
        elif query.startswith('conf'):
            parts = query.split(maxsplit=1)
            if len(parts) > 1:
                results = filter_confidence(results, parts[1])
        elif query.startswith('cat'):
            parts = query.split(maxsplit=1)
            if len(parts) > 1:
                results = filter_category(results, parts[1])
        else:
            print(f"Unknown filter: {query}")
            continue
        
        current_results = results
        print(format_results(results))

def main():
    parser = argparse.ArgumentParser(
        description="Search and filter whale profiles",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python target_search.py --rich --dumb
  python target_search.py --balance ">1M" --newcomer
  python target_search.py --scam-victim --region europe
  python target_search.py --category gamblers --confidence ">70"
  python target_search.py -i  # Interactive mode
        """
    )
    
    parser.add_argument("-i", "--interactive", action="store_true",
                       help="Interactive search mode")
    parser.add_argument("-v", "--verbose", action="store_true",
                       help="Verbose output with full details")
    parser.add_argument("--export", action="store_true",
                       help="Export addresses only (one per line)")
    
    parser.add_argument("--balance", type=str,
                       help="Balance filter: '>1M', '>=500k', '<100k'")
    parser.add_argument("--rich", action="store_true",
                       help="Shortcut: balance > $1M")
    
    parser.add_argument("--confidence", type=str,
                       help="Confidence filter: '>70', '>=80'")
    
    parser.add_argument("--category", type=str,
                       help="OSINT category: gamblers, newcomers, easy, etc.")
    parser.add_argument("--newcomer", action="store_true",
                       help="Shortcut: newcomers category")
    parser.add_argument("--gambler", action="store_true",
                       help="Shortcut: gamblers category")
    parser.add_argument("--easy", action="store_true",
                       help="Shortcut: easy_targets category")
    
    parser.add_argument("--dumb", action="store_true",
                       help="Shortcut: low sophistication (Novice/Unknown)")
    parser.add_argument("--sophistication", type=str,
                       help="Sophistication level: novice, intermediate, advanced")
    
    parser.add_argument("--region", type=str,
                       help="Region: europe, asia, us")
    parser.add_argument("--europe", action="store_true",
                       help="Shortcut: European timezone")
    parser.add_argument("--asia", action="store_true",
                       help="Shortcut: Asia-Pacific timezone")
    parser.add_argument("--us", action="store_true",
                       help="Shortcut: US/Americas timezone")
    
    parser.add_argument("--scam-victim", action="store_true",
                       help="Has received scam NFT airdrops")
    parser.add_argument("--dust-target", action="store_true",
                       help="Targeted by dust attacks")
    parser.add_argument("--meme", action="store_true",
                       help="Has meme coin exposure")
    parser.add_argument("--no-exchange", action="store_true",
                       help="No exchange trail detected")
    parser.add_argument("--has-ens", action="store_true",
                       help="Has ENS name")
    
    parser.add_argument("--prime", action="store_true",
                       help="Shortcut: Prime targets (high value + exploitable)")
    parser.add_argument("--rich-dumb", action="store_true",
                       help="Shortcut: Rich + Low sophistication")
    
    parser.add_argument("--profiles-dir", default=PROFILES_DIR,
                       help="Profiles directory path")
    
    args = parser.parse_args()
    
    if args.interactive:
        interactive_search(args.profiles_dir)
        return
    
    profiles = load_all_profiles(args.profiles_dir)
    
    if not profiles:
        print("No profiles found.")
        return
    
    results = profiles
    
    if args.rich_dumb or (args.rich and args.dumb):
        results = filter_rich_and_dumb(results)
    else:
        if args.prime:
            results = filter_prime_targets(results)
        
        if args.rich:
            results = filter_balance(results, ">1M")
        
        if args.balance:
            results = filter_balance(results, args.balance)
        
        if args.confidence:
            results = filter_confidence(results, args.confidence)
        
        if args.dumb:
            results = filter_sophistication(results, "novice")
            novice_addrs = {p.get('address') for p in results}
            for p in profiles:
                if p.get('address') not in novice_addrs:
                    soph = p.get('behavior', {}).get('sophistication', '').lower()
                    if soph in ['unknown', '']:
                        results.append(p)
        
        if args.sophistication:
            results = filter_sophistication(results, args.sophistication)
        
        if args.category:
            results = filter_category(results, args.category)
        
        if args.newcomer:
            results = filter_category(results, 'newcomers')
        
        if args.gambler:
            results = filter_category(results, 'gamblers')
        
        if args.easy:
            results = filter_category(results, 'easy')
        
        if args.europe:
            results = filter_region(results, 'europe')
        
        if args.asia:
            results = filter_region(results, 'asia')
        
        if args.us:
            results = filter_region(results, 'us')
        
        if args.region:
            results = filter_region(results, args.region)
        
        if args.scam_victim:
            results = filter_has_scam_nfts(results)
        
        if args.dust_target:
            results = filter_dust_target(results)
        
        if args.meme:
            results = filter_meme_exposure(results)
        
        if args.no_exchange:
            results = filter_no_exchange(results)
        
        if args.has_ens:
            results = filter_has_ens(results)
    
    if args.export:
        print(export_addresses(results))
    else:
        print(format_results(results, verbose=args.verbose))

if __name__ == "__main__":
    main()

