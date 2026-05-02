#!/usr/bin/env python3
"""
Chimera contract analysis — CLI entry (scripts/hunt.py).

Discover and assess DeFi protocols using DeFiLlama and local scanners.

Usage:
    # Preset assessment runs
    python scripts/hunt.py --preset fresh_whales
    python scripts/hunt.py --preset lending_risks
    python scripts/hunt.py --preset bridge_targets
    
    # Filtered run
    python scripts/hunt.py --min-tvl 500000 --unaudited --category Lending
    
    # Fast-growing protocols
    python scripts/hunt.py --growing --min-tvl 100000
    
    # List available presets
    python scripts/hunt.py --list-presets
    
    # Save results
    python scripts/hunt.py --preset easy_targets --save
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
load_dotenv()

import asyncio
import argparse
import json
from termcolor import cprint

from src.hunters.contract_hunter import ContractHunter


def print_banner():
    banner = """
    ╔══════════════════════════════════════════════════════════╗
    ║                                                          ║
    ║   🔱 CHIMERA CONTRACT ANALYSIS                           ║
    ║                                                          ║
    ║   Protocol discovery and technical risk assessment       ║
    ║                                                          ║
    ╚══════════════════════════════════════════════════════════╝
    """
    print(banner)


async def main():
    parser = argparse.ArgumentParser(
        description="Chimera contract analysis — discover and assess protocols",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --preset fresh_whales          # Scan unaudited high-TVL protocols
  %(prog)s --preset lending_risks           # Scan lending protocols
  %(prog)s --min-tvl 1000000 --unaudited    # Custom filtered run
  %(prog)s --growing                       # Find fast-growing protocols
  %(prog)s --list-presets                  # Show all presets
        """
    )
    
    parser.add_argument(
        "--preset", "-p",
        type=str,
        help="Run a preset hunt (use --list-presets to see options)"
    )
    parser.add_argument(
        "--list-presets",
        action="store_true",
        help="List all available hunt presets"
    )
    
    parser.add_argument(
        "--min-tvl",
        type=float,
        default=100_000,
        help="Minimum TVL in USD (default: 100000)"
    )
    parser.add_argument(
        "--max-tvl",
        type=float,
        help="Maximum TVL in USD"
    )
    parser.add_argument(
        "--category", "-c",
        type=str,
        help="Filter by category (e.g., Lending, DEX, Bridge)"
    )
    parser.add_argument(
        "--chain",
        type=str,
        help="Filter by chain (e.g., Ethereum, Arbitrum)"
    )
    parser.add_argument(
        "--unaudited", "-u",
        action="store_true",
        help="Only show unaudited protocols"
    )
    parser.add_argument(
        "--high-risk",
        action="store_true",
        help="Only show high-risk categories"
    )
    parser.add_argument(
        "--growing", "-g",
        action="store_true",
        help="Find fast-growing protocols"
    )
    parser.add_argument(
        "--limit", "-l",
        type=int,
        default=30,
        help="Maximum number of results (default: 30)"
    )
    
    parser.add_argument(
        "--scan",
        action="store_true",
        help="Scan discovered contracts for vulnerabilities (uses PatternScanner + Slither)"
    )
    parser.add_argument(
        "--scan-limit",
        type=int,
        default=10,
        help="Maximum contracts to scan (default: 10)"
    )
    parser.add_argument(
        "--etherscan-key",
        type=str,
        help="Etherscan API key for fetching contract source (or set ETHERSCAN_API_KEY env var)"
    )
    parser.add_argument(
        "--save", "-s",
        action="store_true",
        help="Save results to JSON file"
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output raw JSON"
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Show all results (not just top 10)"
    )
    parser.add_argument(
        "--quiet", "-q",
        action="store_true",
        help="Minimal output"
    )
    
    args = parser.parse_args()
    
    import os
    etherscan_key = args.etherscan_key or os.getenv("ETHERSCAN_API_KEY")
    hunter = ContractHunter(etherscan_api_key=etherscan_key)
    
    try:
        if args.list_presets:
            print("\n🎯 Available Hunt Presets:")
            print("=" * 50)
            for name, config in hunter.PRESETS.items():
                print(f"\n  📌 {name}")
                print(f"     {config['description']}")
                if 'min_tvl' in config:
                    print(f"     Min TVL: ${config['min_tvl']:,}")
                if 'categories' in config:
                    print(f"     Categories: {', '.join(config['categories'])}")
            print()
            return
        
        if not args.quiet and not args.json:
            print_banner()
        
        if args.scan:
            result = await hunter.hunt_and_scan(
                min_tvl=args.min_tvl,
                max_tvl=args.max_tvl,
                categories=[args.category] if args.category else None,
                chains=[args.chain] if args.chain else None,
                exclude_audited=args.unaudited,
                limit=args.limit,
                scan_limit=args.scan_limit,
                verbose=not args.quiet and not args.json
            )
        elif args.preset:
            result = await hunter.hunt_preset(
                args.preset,
                verbose=not args.quiet and not args.json
            )
        else:
            result = await hunter.hunt(
                min_tvl=args.min_tvl,
                max_tvl=args.max_tvl,
                categories=[args.category] if args.category else None,
                chains=[args.chain] if args.chain else None,
                exclude_audited=args.unaudited,
                high_risk_only=args.high_risk,
                growing=args.growing,
                limit=args.limit,
                verbose=not args.quiet and not args.json
            )
        
        if args.json:
            print(json.dumps(result.to_dict(), indent=2))
        else:
            hunter.print_results(result, show_all=args.all)
        
        hunt_json_path = None
        if args.save:
            hunt_json_path = hunter.save_results(result)
        
        if result.contracts_analyzed > 0:
            if not args.quiet and not args.json:
                print("\n📁 Saving reports...")
            paths = hunter.save_reports(result)
            if not args.quiet and not args.json:
                print(f"   Saved {len(paths['protocols'])} protocol reports")
                if paths['summary']:
                    print(f"   Summary: {paths['summary']}")
            
            if hunt_json_path:
                hunter.categorize_hunt_results(str(hunt_json_path))
            
    except ValueError as e:
        cprint(f"\n❌ Error: {e}", "red")
        sys.exit(1)
    except KeyboardInterrupt:
        cprint("\n\n⚠️  Interrupted by user", "yellow")
        sys.exit(0)
    except Exception as e:
        cprint(f"\n❌ Unexpected error: {e}", "red")
        raise
    finally:
        await hunter.close()


if __name__ == "__main__":
    asyncio.run(main())
