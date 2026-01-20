#!/usr/bin/env python3

import os
import json
import sys
from typing import Dict, List
from datetime import datetime
from .whale_organizer import process_whale_data
from .intel_profiler import build_wallet_intel, generate_intel_report
from .osint_categorizer import categorize_for_osint, OSINT_CATEGORIES
from .ipfs_osint import scan_wallet_ipfs, generate_ipfs_report

def _convert_sets_to_lists(obj):
    if isinstance(obj, set):
        return list(obj)
    elif isinstance(obj, dict):
        return {k: _convert_sets_to_lists(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [_convert_sets_to_lists(item) for item in obj]
    return obj

class ProfileSaver:
    def __init__(self, base_dir: str = "profiles"):
        self.base_dir = base_dir
        if not os.path.exists(self.base_dir):
            os.makedirs(self.base_dir)
    
    def save_whale_profile(self, wallet_data: Dict) -> str:
        address = wallet_data.get('address', '').lower()
        if not address:
            return None
        
        etherscan_api_key = os.getenv('ETHERSCAN_API_KEY')
        whale_profile = process_whale_data(wallet_data, etherscan_api_key)
        
        basic_data = {
            'balance_eth': wallet_data.get('eth_balance', 0),
            'balance_usd': wallet_data.get('total_value_usd', 0),
            'tokens': wallet_data.get('token_holdings', {}),
            'total_value_usd': wallet_data.get('total_value_usd', 0),
        }
        
        transaction_analysis = wallet_data.get('transaction_analysis')
        intel = build_wallet_intel(
            address,
            basic_data,
            etherscan_api_key,
            transaction_analysis
        )
        
        intel.risk_score = whale_profile.risk_score
        
        confidence = intel.behavior.confidence_score
        balance_usd = intel.balance_usd
        
        wallet_age = intel.wallet_age_days if intel.wallet_age_days > 0 else (whale_profile.age_days or 0)
        
        profile_data_for_osint = {
            'address': address,
            'balance_usd': balance_usd,
            'total_value_usd': balance_usd,
            'tx_count': whale_profile.tx_count,
            'wallet_age_days': wallet_age,
            'age_days': wallet_age,
            'risk_score': whale_profile.risk_score,
            'nft_activity': whale_profile.nft_activity,
            'defi_activity': whale_profile.defi_activity,
            'bridge_activity': whale_profile.bridge_activity,
            'behavior': {
                'confidence_score': confidence,
                'meme_exposure': getattr(intel.behavior, 'meme_exposure', False),
                'sophistication': getattr(intel.behavior, 'sophistication', 'Unknown'),
                'defi_protocols': getattr(intel.behavior, 'defi_protocols', []),
                'nft_platforms': getattr(intel.behavior, 'nft_platforms', []),
                'bridges_used': getattr(intel.behavior, 'bridges_used', []),
                'likely_region': getattr(intel.behavior, 'likely_region', 'Unknown'),
            }
        }
        
        osint_categories = categorize_for_osint(profile_data_for_osint)
        
        if not osint_categories:
            primary_category = "🐟_easy_targets"
        else:
            primary_category = osint_categories[0]
        
        category_dir = os.path.join(self.base_dir, primary_category)
        if not os.path.exists(category_dir):
            os.makedirs(category_dir)
        
        whale_dir = os.path.join(category_dir, address)
        if not os.path.exists(whale_dir):
            os.makedirs(whale_dir)
        
        profile_file = os.path.join(whale_dir, 'profile.json')
        summary_file = os.path.join(whale_dir, 'summary.txt')
        
        profile_data = {
            'address': address,
            'discovered_at': datetime.now().isoformat(),
            'total_value_usd': wallet_data.get('total_value_usd', 0),
            'eth_balance': wallet_data.get('eth_balance', 0),
            'eth_value_usd': wallet_data.get('eth_value_usd', 0),
            'token_holdings': wallet_data.get('token_holdings', {}),
            'category': whale_profile.category,
            'risk_score': whale_profile.risk_score,
            'tx_count': whale_profile.tx_count,
            'total_moved_eth': whale_profile.total_moved_eth,
            'defi_activity': whale_profile.defi_activity,
            'nft_activity': whale_profile.nft_activity,
            'bridge_activity': whale_profile.bridge_activity,
            'age_days': intel.wallet_age_days if intel.wallet_age_days > 0 else whale_profile.age_days,
            'first_seen': whale_profile.first_seen,
            'last_active': whale_profile.last_active,
            'etherscan_url': whale_profile.etherscan_url,
            'osint_categories': osint_categories,
            'primary_osint_category': primary_category
        }
        
        if wallet_data.get('transaction_analysis'):
            profile_data['transaction_analysis'] = wallet_data['transaction_analysis']
        
        with open(profile_file, 'w') as f:
            json.dump(profile_data, f, indent=2)
        
        summary_text = generate_intel_report(intel)
        
        ipfs_data = None
        if whale_profile.nft_activity:
            try:
                from ..core.api_clients import RPCClient
                rpc = RPCClient()
                nft_transfers = wallet_data.get('nft_transfers', [])
                if not nft_transfers:
                    etherscan_api_key = os.getenv('ETHERSCAN_API_KEY')
                    from ..core.api_clients import EtherscanClient
                    etherscan = EtherscanClient(etherscan_api_key)
                    nft_transfers = etherscan.get_nft_transfers(address, limit=20)
                
                if nft_transfers:
                    ipfs_data = scan_wallet_ipfs(address, nft_transfers, rpc, limit=10)
                    if ipfs_data:
                        profile_data['ipfs_osint'] = ipfs_data
                        
                        if ipfs_data.get('findings', {}).get('total_hashes', 0) > 0:
                            from ..core.api_clients import RPCClient
                            rpc = RPCClient()
                            ipfs_report = generate_ipfs_report(ipfs_data, profile_data, rpc)
                            summary_text += "\n\n" + ipfs_report
            except Exception as e:
                pass
        
        with open(summary_file, 'w', encoding='utf-8') as f:
            f.write(summary_text)
        
        if ipfs_data:
            ipfs_file = os.path.join(whale_dir, 'ipfs_osint.json')
            serializable_data = _convert_sets_to_lists(ipfs_data)
            with open(ipfs_file, 'w') as f:
                json.dump(serializable_data, f, indent=2)
        
        if "🎯_prime_targets" in osint_categories:
            for cat in osint_categories:
                if cat != "🎯_prime_targets" and cat != primary_category:
                    additional_dir = os.path.join(self.base_dir, cat, address)
                    if not os.path.exists(additional_dir):
                        os.makedirs(additional_dir)
                        with open(os.path.join(additional_dir, 'profile.json'), 'w') as f:
                            json.dump(profile_data, f, indent=2)
                        with open(os.path.join(additional_dir, 'summary.txt'), 'w', encoding='utf-8') as f:
                            f.write(summary_text)
        
        return whale_dir
    
    def save_whale_profiles(self, wallets: List[Dict]) -> List[str]:
        saved_dirs = []
        for wallet in wallets:
            try:
                dir_path = self.save_whale_profile(wallet)
                if dir_path:
                    saved_dirs.append(dir_path)
            except Exception as e:
                print(f"Error saving profile for {wallet.get('address', 'unknown')}: {e}", file=sys.stderr)
        return saved_dirs

