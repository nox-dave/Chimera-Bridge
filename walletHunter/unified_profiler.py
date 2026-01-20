#!/usr/bin/env python3

import os
import sys
import json
import time
from datetime import datetime, timezone
from typing import Dict, List, Optional
from dataclasses import dataclass

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.core.wallet_profiler import WalletProfiler
from src.core.api_clients import EtherscanClient, RPCClient
from src.core.funding_tracer import trace_funding_for_profile, generate_funding_report_from_dict
from src.core.token_risk_scanner import scan_token_risks_for_profile, generate_token_risk_report_from_dict
from src.utils.intel_profiler import build_wallet_intel, generate_intel_report
from src.utils.osint_categorizer import categorize_for_osint
from src.utils.ipfs_osint import scan_wallet_ipfs, generate_ipfs_report
from src.utils.ens_resolver import scan_wallet_ens
from src.utils.osint_verdicts import generate_all_verdicts
from src.utils.approval_scanner import scan_approvals_for_profile
from src.utils.whale_organizer import process_whale_data
from src.utils.profile_saver import ProfileSaver
from src.utils.batch_summary import generate_batch_summary, save_batch_summary

PROFILES_DIR = "profiles"

ENABLE_IPFS_BY_DEFAULT = True
IPFS_ONLY_IF_NFT_ACTIVITY = True

@dataclass
class ProfileConfig:
    include_ipfs: bool = True
    include_ens: bool = True
    include_verdicts: bool = True
    include_approvals: bool = True
    save_to_disk: bool = True
    verbose: bool = True

class UnifiedProfiler:
    def __init__(self, config: ProfileConfig = None, api_key: Optional[str] = None):
        self.config = config or ProfileConfig()
        self.api_key = api_key or os.getenv('ETHERSCAN_API_KEY')
        
        self.wallet_profiler = WalletProfiler(api_key=self.api_key)
        self.etherscan = EtherscanClient(self.api_key)
        self.rpc = RPCClient()
        self.profile_saver = ProfileSaver()
    
    def generate_full_profile(self, address: str) -> Dict:
        address = address.lower()
        
        if self.config.verbose:
            print(f"\n{'='*60}")
            print(f"🐋 Profiling: {address[:16]}...")
            print(f"{'='*60}")
        
        profile = {
            'address': address,
            'generated': datetime.now(timezone.utc).isoformat(),
            'pipeline_version': '2.0',
        }
        
        if self.config.verbose:
            print("  [1/9] Fetching wallet data...")
        
        balance = self.wallet_profiler.get_balance(address)
        eth_balance = balance.get('eth', 0)
        
        eth_price = 3000
        try:
            import requests
            api_key = self.api_key or os.getenv('ETHERSCAN_API_KEY', '')
            if api_key:
                eth_price_url = 'https://api.etherscan.io/v2/api'
                params = {
                    'chainid': 1,
                    'module': 'stats',
                    'action': 'ethprice',
                    'apikey': api_key
                }
                response = requests.get(eth_price_url, params=params, timeout=5)
                if response.status_code == 200:
                    data = response.json()
                    if data.get('status') == '1' and data.get('result'):
                        result = data.get('result', {})
                        if isinstance(result, dict) and 'ethusd' in result:
                            eth_price = float(result['ethusd'])
        except:
            pass
        
        eth_value_usd = eth_balance * eth_price
        
        token_balances = self.wallet_profiler.get_token_balances(address)
        total_token_value_usd = 0
        token_holdings = {}
        
        for token in token_balances[:20]:
            if isinstance(token, dict):
                token_balance_raw = token.get('balance', 0) or token.get('tokenBalance', 0) or token.get('TokenQuantity', 0)
                token_decimals = token.get('decimals', 18) or token.get('TokenDecimal', 18)
                
                try:
                    if isinstance(token_balance_raw, str):
                        token_balance = float(token_balance_raw) / (10 ** int(token_decimals))
                    else:
                        token_balance = float(token_balance_raw) / (10 ** int(token_decimals))
                except:
                    token_balance = 0
                
                token_value_usd = token.get('value_usd', 0) or token.get('value', 0)
                token_symbol = token.get('symbol', '') or token.get('tokenSymbol', '') or token.get('TokenSymbol', '')
                token_address = token.get('contractAddress', '') or token.get('tokenAddress', '') or token.get('TokenAddress', '')
                
                if not token_value_usd and token_balance > 0:
                    from src.config import MAJOR_TOKENS
                    if token_symbol in MAJOR_TOKENS:
                        token_price = MAJOR_TOKENS[token_symbol]['price']
                        token_value_usd = token_balance * token_price
                    elif token_address and token_address.lower() in [t['address'].lower() for t in MAJOR_TOKENS.values()]:
                        for name, info in MAJOR_TOKENS.items():
                            if info['address'].lower() == token_address.lower():
                                token_value_usd = token_balance * info['price']
                                token_symbol = name
                                break
                
                if token_value_usd and token_value_usd > 0:
                    total_token_value_usd += token_value_usd
                    token_holdings[token_symbol or 'UNKNOWN'] = {
                        'balance': token_balance,
                        'value_usd': token_value_usd
                    }
        
        total_value_usd = eth_value_usd + total_token_value_usd
        
        profile.update({
            'balance_usd': total_value_usd,
            'total_value_usd': total_value_usd,
            'eth_balance': eth_balance,
            'eth_value_usd': eth_value_usd,
            'token_holdings': token_holdings,
        })
        
        if self.config.verbose:
            print("  [2/9] Analyzing transactions...")
        
        txs = self.wallet_profiler.get_transactions(address, limit=1000)
        internal_txs = self.wallet_profiler.get_internal_transactions(address, limit=500)
        token_txs = self.wallet_profiler.get_token_transfers(address, limit=1000)
        nft_txs = self.wallet_profiler.get_nft_transfers(address, limit=500)
        
        tx_patterns = self.wallet_profiler.transaction_analyzer.analyze_patterns(txs)
        token_activity = self.wallet_profiler.transaction_analyzer.analyze_token_activity(token_txs)
        nft_activity = self.wallet_profiler.transaction_analyzer.analyze_nft_activity(nft_txs)
        
        profile['transaction_analysis'] = tx_patterns
        profile['token_activity'] = token_activity
        profile['nft_activity'] = nft_activity
        profile['tx_count'] = len(txs)
        profile['total_internal_txs'] = len(internal_txs)
        
        has_nft_activity = bool(nft_activity.get('unique_collections', 0) > 0 or nft_txs)
        
        if self.config.verbose:
            print("  [3/9] Building behavioral intelligence...")
        
        basic_data = {
            'balance_eth': eth_balance,
            'balance_usd': total_value_usd,
            'tokens': token_balances[:20],
            'total_value_usd': total_value_usd,
        }
        
        intel = build_wallet_intel(
            address,
            basic_data,
            self.api_key,
            tx_patterns
        )
        
        profile['behavior'] = {
            'confidence_score': intel.behavior.confidence_score,
            'sophistication': intel.behavior.sophistication,
            'risk_tolerance': intel.behavior.risk_tolerance,
            'trading_style': intel.behavior.trading_style,
            'likely_region': intel.behavior.likely_region,
            'likely_timezone': intel.behavior.likely_timezone,
            'meme_exposure': getattr(intel.behavior, 'meme_exposure', False),
            'defi_protocols': intel.behavior.defi_protocols,
            'nft_platforms': intel.behavior.nft_platforms,
            'bridges_used': intel.behavior.bridges_used,
            'exchange_interactions': intel.behavior.exchange_interactions,
            'frequent_counterparties': intel.behavior.frequent_counterparties,
        }
        
        profile['wallet_age_days'] = intel.wallet_age_days
        profile['age_days'] = intel.wallet_age_days
        
        if self.config.verbose:
            print("  [4/9] Tracing funding source...")
        
        funding_data = None
        try:
            import asyncio
            funding_data = asyncio.run(trace_funding_for_profile(address))
            profile['funding_trace'] = funding_data
        except Exception as e:
            if self.config.verbose:
                print(f"     ⚠️  Funding trace error: {e}")
            profile['funding_trace'] = {'error': str(e)}
        
        if self.config.verbose:
            print("  [5/9] Running IPFS OSINT scan...")
        
        ipfs_data = None
        if self.config.include_ipfs:
            if not IPFS_ONLY_IF_NFT_ACTIVITY or has_nft_activity:
                try:
                    nft_transfers = nft_txs if nft_txs else self.etherscan.get_nft_transfers(address, limit=50)
                    ipfs_data = scan_wallet_ipfs(address, nft_transfers, self.rpc, limit=20, debug=False)
                    if ipfs_data:
                        profile['ipfs_osint'] = ipfs_data
                except Exception as e:
                    if self.config.verbose:
                        print(f"     ⚠️  IPFS scan error: {e}")
                    profile['ipfs_osint'] = {'error': str(e)}
            else:
                if self.config.verbose:
                    print("     ⏭️  Skipping IPFS (no NFT activity)")
                profile['ipfs_osint'] = {'skipped': True, 'reason': 'no_nft_activity'}
        
        if self.config.verbose:
            print("  [6/9] Resolving ENS...")
        
        ens_data = None
        if self.config.include_ens:
            try:
                ens_data = scan_wallet_ens(address, self.rpc)
                if ens_data:
                    profile['ens'] = ens_data
            except Exception as e:
                if self.config.verbose:
                    print(f"     ⚠️  ENS resolution error: {e}")
                profile['ens'] = {'error': str(e)}
        
        approval_data = None
        if self.config.include_approvals:
            if self.config.verbose:
                print("  [7/9] Scanning token approvals...")
            try:
                import asyncio
                approval_data = asyncio.run(scan_approvals_for_profile(address, self.api_key))
                profile['approval_risk'] = approval_data or {
                    'scan_timestamp': datetime.now(timezone.utc).isoformat(),
                    'total_approvals': 0,
                    'unlimited_approvals': 0,
                    'high_risk_approvals': 0,
                    'total_exposure_usd': 0.0,
                    'verdicts': [],
                    'has_dangerous_approvals': False,
                }
            except Exception as e:
                if self.config.verbose:
                    print(f"     ⚠️  Approval scan error: {e}")
                profile['approval_risk'] = {'error': str(e)}
        
        if self.config.verbose:
            print("  [8/9] Scanning token risks...")
        
        token_risk_data = None
        try:
            import asyncio
            token_risk_data = asyncio.run(scan_token_risks_for_profile(address))
            profile['token_risks'] = token_risk_data
        except Exception as e:
            if self.config.verbose:
                print(f"     ⚠️  Token risk scan error: {e}")
            profile['token_risks'] = {'error': str(e)}
        
        if self.config.verbose:
            print("  [9/9] Generating verdicts and categorizing...")
        
        osint_categories = categorize_for_osint(profile)
        profile['osint_categories'] = osint_categories
        profile['primary_osint_category'] = osint_categories[0] if osint_categories else "🐟_easy_targets"
        
        if self.config.include_verdicts:
            try:
                domains = None
                if ipfs_data and not ipfs_data.get('skipped') and not ipfs_data.get('error'):
                    findings = ipfs_data.get('findings', {})
                    if findings.get('domains'):
                        if isinstance(findings['domains'], dict):
                            domains = list(findings['domains'].keys())
                        elif isinstance(findings['domains'], list):
                            domains = findings['domains']
                
                verdicts = generate_all_verdicts(profile, ipfs_data if ipfs_data and not ipfs_data.get('skipped') else None, domains, ens_data, approval_data)
                profile['verdicts'] = [{
                    'title': v.title,
                    'severity': v.severity,
                    'category': v.category,
                    'description': v.description,
                    'evidence': v.evidence,
                    'action': v.action,
                } for v in verdicts]
                
                if token_risk_data and not token_risk_data.get('error'):
                    token_risk_verdicts = token_risk_data.get('verdicts', [])
                    for verdict_dict in token_risk_verdicts:
                        profile['verdicts'].append({
                            'title': verdict_dict.get('title', ''),
                            'severity': verdict_dict.get('severity', 'INFO'),
                            'category': 'TOKEN_RISK',
                            'description': verdict_dict.get('description', ''),
                            'evidence': verdict_dict.get('evidence', []),
                            'action': verdict_dict.get('action', ''),
                        })
            except Exception as e:
                if self.config.verbose:
                    print(f"     ⚠️  Verdict generation error: {e}")
                profile['verdicts'] = []
        
        if self.config.save_to_disk:
            self._save_profile(profile, intel)
        
        if self.config.verbose:
            balance = profile.get('balance_usd', 0)
            confidence = profile.get('behavior', {}).get('confidence_score', 0)
            cats = profile.get('osint_categories', [])
            print(f"\n  ✅ Profile complete:")
            print(f"     Balance: ${balance:,.0f}")
            print(f"     Confidence: {confidence}%")
            print(f"     Categories: {', '.join(c.split('_')[1] if '_' in c else c for c in cats[:3])}")
        
        return profile
    
    def _save_profile(self, profile: Dict, intel):
        address = profile.get('address', '')
        categories = profile.get('osint_categories', [])
        
        all_dir = os.path.join(PROFILES_DIR, '_all', address)
        os.makedirs(all_dir, exist_ok=True)
        
        profile_data = {
            'address': address,
            'discovered_at': profile.get('generated', datetime.now(timezone.utc).isoformat()),
            'total_value_usd': profile.get('total_value_usd', 0),
            'eth_balance': profile.get('eth_balance', 0),
            'eth_value_usd': profile.get('eth_value_usd', 0),
            'token_holdings': profile.get('token_holdings', {}),
            'risk_score': profile.get('behavior', {}).get('confidence_score', 50),
            'tx_count': profile.get('tx_count', 0),
            'defi_activity': bool(profile.get('behavior', {}).get('defi_protocols')),
            'nft_activity': bool(profile.get('nft_activity', {}).get('unique_collections', 0) > 0),
            'bridge_activity': bool(profile.get('behavior', {}).get('bridges_used')),
            'age_days': profile.get('wallet_age_days', 0),
            'osint_categories': categories,
            'primary_osint_category': profile.get('primary_osint_category', '🐟_easy_targets'),
            'behavior': profile.get('behavior', {}),
            'transaction_analysis': profile.get('transaction_analysis', {}),
            'token_activity': profile.get('token_activity', {}),
            'nft_activity': profile.get('nft_activity', {}),
        }
        
        if profile.get('ipfs_osint'):
            profile_data['ipfs_osint'] = profile['ipfs_osint']
        
        if profile.get('ens'):
            profile_data['ens'] = profile['ens']
        
        if profile.get('approval_risk'):
            profile_data['approval_risk'] = profile['approval_risk']
        
        if profile.get('funding_trace'):
            profile_data['funding_trace'] = profile['funding_trace']
        
        if profile.get('token_risks'):
            profile_data['token_risks'] = profile['token_risks']
        
        if profile.get('verdicts'):
            profile_data['verdicts'] = profile['verdicts']
        
        with open(os.path.join(all_dir, 'profile.json'), 'w') as f:
            json.dump(profile_data, f, indent=2)
        
        summary_text = generate_intel_report(intel)
        
        if profile.get('funding_trace') and not profile['funding_trace'].get('error'):
            try:
                funding_report = generate_funding_report_from_dict(profile['funding_trace'])
                if funding_report:
                    summary_text += "\n\n" + funding_report
            except:
                pass
        
        if profile.get('token_risks') and not profile['token_risks'].get('error'):
            try:
                token_risk_report = generate_token_risk_report_from_dict(profile['token_risks'])
                if token_risk_report:
                    summary_text += "\n\n" + token_risk_report
            except:
                pass
        
        if profile.get('ipfs_osint') and not profile['ipfs_osint'].get('skipped') and not profile['ipfs_osint'].get('error'):
            try:
                ipfs_report = generate_ipfs_report(profile['ipfs_osint'], profile_data, self.rpc)
                summary_text += "\n\n" + ipfs_report
            except:
                pass
        
        if profile.get('verdicts'):
            verdicts_section = "\n\n" + "━" * 80 + "\n"
            verdicts_section += "🎯 OSINT VERDICTS\n"
            verdicts_section += "━" * 80 + "\n\n"
            
            severity_order = {'CRITICAL': 0, 'HIGH': 1, 'MEDIUM': 2, 'LOW': 3, 'INFO': 4}
            sorted_verdicts = sorted(profile['verdicts'], key=lambda v: severity_order.get(v.get('severity', 'INFO'), 99))
            
            for v in sorted_verdicts:
                severity_icon = {'CRITICAL': '🚨', 'HIGH': '⚠️', 'MEDIUM': '⚡', 'LOW': '📌', 'INFO': 'ℹ️'}.get(v.get('severity', 'INFO'), '•')
                verdicts_section += f"{severity_icon} [{v.get('severity', 'INFO')}] {v.get('title', 'Unknown')}\n"
                verdicts_section += f"   {v.get('description', '')}\n"
                if v.get('evidence'):
                    for e in v.get('evidence', [])[:3]:
                        verdicts_section += f"     • {e}\n"
                if v.get('action'):
                    verdicts_section += f"   → Action: {v.get('action', '')}\n"
                verdicts_section += "\n"
            
            summary_text += verdicts_section
        
        with open(os.path.join(all_dir, 'summary.txt'), 'w', encoding='utf-8') as f:
            f.write(summary_text)
        
        if profile.get('ipfs_osint') and not profile['ipfs_osint'].get('skipped') and not profile['ipfs_osint'].get('error'):
            ipfs_file = os.path.join(all_dir, 'ipfs_osint.json')
            serializable_data = self._convert_sets_to_lists(profile['ipfs_osint'])
            with open(ipfs_file, 'w') as f:
                json.dump(serializable_data, f, indent=2)
        
        for cat in categories:
            cat_dir = os.path.join(PROFILES_DIR, cat, address)
            os.makedirs(cat_dir, exist_ok=True)
            
            with open(os.path.join(cat_dir, 'profile.json'), 'w') as f:
                json.dump(profile_data, f, indent=2)
            
            with open(os.path.join(cat_dir, 'summary.txt'), 'w', encoding='utf-8') as f:
                f.write(summary_text)
            
            if profile.get('ipfs_osint') and not profile['ipfs_osint'].get('skipped') and not profile['ipfs_osint'].get('error'):
                ipfs_file = os.path.join(cat_dir, 'ipfs_osint.json')
                serializable_data = self._convert_sets_to_lists(profile['ipfs_osint'])
                with open(ipfs_file, 'w') as f:
                    json.dump(serializable_data, f, indent=2)
    
    def _convert_sets_to_lists(self, obj):
        if isinstance(obj, set):
            return list(obj)
        elif isinstance(obj, dict):
            return {k: self._convert_sets_to_lists(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._convert_sets_to_lists(item) for item in obj]
        return obj

def hunt_whales_unified(
    min_balance: int = 100000,
    limit: int = 10,
    include_ipfs: bool = ENABLE_IPFS_BY_DEFAULT,
    api_key: Optional[str] = None
) -> List[Dict]:
    print("╔══════════════════════════════════════════════════════════════════════════════╗")
    print("║                         🐋 UNIFIED WHALE HUNTER                              ║")
    print("╚══════════════════════════════════════════════════════════════════════════════╝")
    print()
    print(f"  Min Balance: ${min_balance:,}")
    print(f"  Limit: {limit}")
    print(f"  IPFS OSINT: {'Enabled' if include_ipfs else 'Disabled'}")
    print()
    
    print("🔍 Phase 1: Discovering whales...")
    wallet_profiler = WalletProfiler(api_key=api_key)
    discovered_wallets = wallet_profiler.find_high_value_wallets(min_balance_usd=min_balance, limit=limit)
    
    if not discovered_wallets:
        print("   No whales found matching criteria.")
        return []
    
    discovered_addresses = [w.get('address', '').lower() for w in discovered_wallets if w.get('address')]
    print(f"   Found {len(discovered_addresses)} potential targets")
    
    print(f"\n🐋 Phase 2: Generating full profiles...")
    
    config = ProfileConfig(
        include_ipfs=include_ipfs,
        include_ens=True,
        include_verdicts=True,
        save_to_disk=True,
        verbose=True,
    )
    
    profiler = UnifiedProfiler(config, api_key=api_key)
    profiles = []
    
    for i, address in enumerate(discovered_addresses, 1):
        print(f"\n[{i}/{len(discovered_addresses)}] Processing {address[:16]}...")
        
        try:
            profile = profiler.generate_full_profile(address)
            profiles.append(profile)
        except Exception as e:
            print(f"   ❌ Error: {e}")
            import traceback
            if config.verbose:
                traceback.print_exc()
            continue
        
        if i < len(discovered_addresses):
            time.sleep(1)
    
    print("\n" + "="*70)
    print("✅ HUNT COMPLETE")
    print("="*70)
    print(f"  Profiles generated: {len(profiles)}")
    
    if profiles:
        total_value = sum(p.get('balance_usd', 0) for p in profiles)
        under_attack = sum(1 for p in profiles if any('under_attack' in str(cat) for cat in p.get('osint_categories', [])))
        high_risk = sum(1 for p in profiles if '🐟' in str(p.get('primary_osint_category', '')))
        
        print(f"  Total value tracked: ${total_value:,.0f}")
        print(f"  High risk profiles: {high_risk}")
        
        print("\n" + "="*70)
        print("📊 Generating batch intelligence summary...")
        print("="*70)
        
        batch_params = {
            'min_balance': min_balance,
            'limit': limit,
            'include_ipfs': include_ipfs,
        }
        
        try:
            summary = generate_batch_summary(profiles, batch_params)
            print(summary)
            
            summary_file = save_batch_summary(profiles, batch_params)
            print(f"\n✅ Batch summary saved to: {summary_file}")
        except Exception as e:
            print(f"  ⚠️  Error generating batch summary: {e}")
            import traceback
            traceback.print_exc()
    
    return profiles

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Unified Whale Profiler")
    parser.add_argument("--hunt", action="store_true", help="Hunt for whales")
    parser.add_argument("--address", type=str, help="Profile single address")
    parser.add_argument("--min-balance", type=int, default=100000, help="Minimum balance (USD)")
    parser.add_argument("--limit", type=int, default=10, help="Max whales to discover")
    parser.add_argument("--no-ipfs", action="store_true", help="Skip IPFS scanning")
    parser.add_argument("--fast", action="store_true", help="Fast mode (skip IPFS + ENS)")
    parser.add_argument("--api-key", type=str, help="Etherscan API key")
    
    args = parser.parse_args()
    
    if args.address:
        config = ProfileConfig(
            include_ipfs=not args.no_ipfs and not args.fast,
            include_ens=not args.fast,
            verbose=True,
        )
        profiler = UnifiedProfiler(config, api_key=args.api_key)
        profiler.generate_full_profile(args.address)
        
    elif args.hunt:
        hunt_whales_unified(
            min_balance=args.min_balance,
            limit=args.limit,
            include_ipfs=not args.no_ipfs and not args.fast,
            api_key=args.api_key
        )
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
