#!/usr/bin/env python3

import os
import json
import sys
from pathlib import Path
from .ipfs_osint import scan_wallet_ipfs, generate_ipfs_report
from ..core.api_clients import EtherscanClient, RPCClient

def _convert_sets_to_lists(obj):
    if isinstance(obj, set):
        return list(obj)
    elif isinstance(obj, dict):
        return {k: _convert_sets_to_lists(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [_convert_sets_to_lists(item) for item in obj]
    return obj

def scan_profile_ipfs(profile_path: str):
    try:
        with open(profile_path, 'r') as f:
            profile = json.load(f)
        
        address = profile.get('address', '')
        if not address:
            return None
        
        etherscan_api_key = os.getenv('ETHERSCAN_API_KEY')
        etherscan = EtherscanClient(etherscan_api_key)
        rpc = RPCClient()
        
        nft_transfers = etherscan.get_nft_transfers(address, limit=50)
        
        if not nft_transfers:
            return None
        
        ipfs_data = scan_wallet_ipfs(address, nft_transfers, rpc, limit=20)
        
        findings = ipfs_data.get('findings', {}) if ipfs_data else {}
        has_intelligence = (
            findings.get('total_hashes', 0) > 0 or
            findings.get('domains') or
            findings.get('linked_urls') or
            findings.get('usernames') or
            findings.get('emails') or
            findings.get('social_links')
        )
        
        if ipfs_data and has_intelligence:
            profile_dir = os.path.dirname(profile_path)
            ipfs_file = os.path.join(profile_dir, 'ipfs_osint.json')
            
            serializable_data = _convert_sets_to_lists(ipfs_data)
            with open(ipfs_file, 'w') as f:
                json.dump(serializable_data, f, indent=2)
            
            summary_file = os.path.join(profile_dir, 'summary.txt')
            if os.path.exists(summary_file):
                with open(summary_file, 'r', encoding='utf-8') as f:
                    summary = f.read()
                
                if 'IPFS & DOMAIN OSINT ANALYSIS' not in summary:
                    ipfs_report = generate_ipfs_report(ipfs_data, profile, rpc)
                    with open(summary_file, 'a', encoding='utf-8') as f:
                        f.write("\n\n" + ipfs_report)
            
            return ipfs_data
        
        return None
    except Exception as e:
        print(f"Error scanning {profile_path}: {e}")
        return None

def scan_all_profiles(profiles_dir: str = "profiles"):
    scanned = 0
    found = 0
    
    for root, dirs, files in os.walk(profiles_dir):
        if '🗑️_trash' in root or '📦_archive' in root:
            continue
        
        for file in files:
            if file == 'profile.json':
                profile_path = os.path.join(root, file)
                result = scan_profile_ipfs(profile_path)
                scanned += 1
                if result:
                    found += 1
                    address = result.get('address', '')[:16]
                    hashes = result.get('findings', {}).get('total_hashes', 0)
                    print(f"  [{scanned}] {address}... - {hashes} IPFS hashes found")
    
    print(f"\nScanned {scanned} profiles, found IPFS data in {found}")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="IPFS OSINT Scanner")
    parser.add_argument("--address", help="Single address to scan")
    parser.add_argument("--all", action="store_true", help="Scan all profiles")
    parser.add_argument("--profiles-dir", default="profiles", help="Profiles directory")
    
    args = parser.parse_args()
    
    if args.address:
        from ..core.api_clients import EtherscanClient, RPCClient
        from .ipfs_osint import scan_wallet_ipfs, generate_ipfs_report
        
        etherscan_api_key = os.getenv('ETHERSCAN_API_KEY')
        etherscan = EtherscanClient(etherscan_api_key)
        rpc = RPCClient()
        
        nft_transfers = etherscan.get_nft_transfers(args.address, limit=50)
        if nft_transfers:
            ipfs_data = scan_wallet_ipfs(args.address, nft_transfers, rpc, limit=20)
            if ipfs_data:
                print(generate_ipfs_report(ipfs_data, None, rpc))
        else:
            print("No NFT transfers found")
    
    elif args.all:
        scan_all_profiles(args.profiles_dir)
    
    else:
        parser.print_help()

