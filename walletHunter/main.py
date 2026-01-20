#!/usr/bin/env python3

import sys
import argparse
from dotenv import load_dotenv
from src.core import WalletProfiler
from src.utils import ReportGenerator, ProfileSaver

load_dotenv()

def main():
    parser = argparse.ArgumentParser(
        description='Generate OSINT profile for Ethereum wallet address',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  python main.py 0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb
  python main.py 0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb --json
  python main.py 0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb --output profile.txt
  python main.py --find-whale --min-balance 500000
        '''
    )
    
    parser.add_argument('address', nargs='?', help='Ethereum wallet address to analyze')
    parser.add_argument('--json', action='store_true', help='Output in JSON format')
    parser.add_argument('--output', '-o', help='Output file path (default: stdout)')
    parser.add_argument('--api-key', help='Etherscan API key (or set ETHERSCAN_API_KEY env var)')
    parser.add_argument('--find-whale', action='store_true', help='Find high-value wallets automatically')
    parser.add_argument('--min-balance', type=float, default=100000, help='Minimum USD balance for whale finding (default: 100000)')
    parser.add_argument('--limit', type=int, default=10, help='Number of wallets to find (default: 10)')
    
    args = parser.parse_args()
    
    profiler = WalletProfiler(api_key=args.api_key)
    
    if args.find_whale:
        wallets = profiler.find_high_value_wallets(min_balance_usd=args.min_balance, limit=args.limit)
        
        if wallets:
            saver = ProfileSaver()
            saved_dirs = saver.save_whale_profiles(wallets)
            print(f"\nSaved {len(saved_dirs)} whale profiles to:", file=sys.stderr)
            for dir_path in saved_dirs:
                print(f"  - {dir_path}", file=sys.stderr)
        
        if args.json:
            import json
            output = json.dumps(wallets, indent=2, default=str)
        else:
            lines = []
            lines.append("=" * 80)
            lines.append(f"HIGH-VALUE WALLETS (Min: ${args.min_balance:,.0f})")
            lines.append("=" * 80)
            lines.append("")
            
            for i, wallet in enumerate(wallets, 1):
                lines.append(f"{i}. {wallet['address']}")
                lines.append(f"   Total Value: ${wallet['total_value_usd']:,.2f}")
                lines.append(f"   ETH Balance: {wallet['eth_balance']:.4f} ETH")
                if wallet.get('categories'):
                    lines.append(f"   Categories: {', '.join(wallet['categories'])}")
                if wallet['token_holdings']:
                    lines.append("   Token Holdings:")
                    for token, data in wallet['token_holdings'].items():
                        lines.append(f"     - {token}: {data['balance']:.2f} (${data['value_usd']:,.2f})")
                if wallet.get('metadata'):
                    metadata = wallet['metadata']
                    if 'nft_collections' in metadata:
                        lines.append("   NFT Collections:")
                        for collection in metadata['nft_collections']:
                            lines.append(f"     - {collection['name']}: {collection['count']} NFTs")
                lines.append("")
            
            lines.append("=" * 80)
            output = "\n".join(lines)
        
        if args.output:
            with open(args.output, 'w') as f:
                f.write(output)
            print(f"Report saved to: {args.output}", file=sys.stderr)
        else:
            print(output)
        return
    
    if not args.address:
        parser.error("address is required unless using --find-whale")
    
    address = args.address.strip()
    if not address.startswith('0x') or len(address) != 42:
        print(f"Error: Invalid Ethereum address format: {address}", file=sys.stderr)
        sys.exit(1)
    
    profile = profiler.generate_profile(address)
    
    if args.json:
        report = ReportGenerator.generate_json_report(profile)
    else:
        report = ReportGenerator.generate_text_report(profile)
    
    if args.output:
        with open(args.output, 'w') as f:
            f.write(report)
        print(f"Report saved to: {args.output}", file=sys.stderr)
    else:
        print(report)

if __name__ == '__main__':
    main()

