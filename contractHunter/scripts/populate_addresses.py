#!/usr/bin/env python3
"""
Auto-populate protocol addresses from DeFiLlama

Fetches addresses for top protocols and updates the address database.
"""

import sys
import asyncio
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.fetchers.defillama_client import DeFiLlamaClient
from src.fetchers.addresses import PROTOCOL_ADDRESSES, get_address


async def fetch_protocol_address(protocol_slug: str, defillama: DeFiLlamaClient) -> dict:
    """Fetch addresses for a protocol from DeFiLlama"""
    try:
        detail = await defillama.get_protocol_detail(protocol_slug)
        if not detail or not detail.contracts:
            return {}
        
        addresses = {}
        for chain, addr in detail.contracts.items():
            if addr and isinstance(addr, str) and addr.startswith("0x") and len(addr) == 42:
                chain_name = chain.replace("_", " ").title()
                if chain_name == "Main":
                    chain_name = "Ethereum"
                addresses[chain_name] = addr
        
        return addresses
    except Exception as e:
        print(f"  [!] Error fetching {protocol_slug}: {e}")
        return {}


async def populate_addresses(min_tvl: float = 100_000, limit: int = 100, verbose: bool = True):
    """Populate address database with top protocols from DeFiLlama"""
    
    defillama = DeFiLlamaClient()
    
    if verbose:
        print(f"[+] Fetching top {limit} protocols (min TVL: ${min_tvl:,.0f})...")
    
    protocols = await defillama.get_protocols()
    
    filtered = [p for p in protocols if (p.tvl or 0) >= min_tvl]
    filtered.sort(key=lambda x: x.tvl or 0, reverse=True)
    filtered = filtered[:limit]
    
    if verbose:
        print(f"[+] Found {len(filtered)} protocols, fetching addresses...")
    
    new_addresses = {}
    updated_count = 0
    added_count = 0
    
    for i, protocol in enumerate(filtered, 1):
        if verbose and i % 10 == 0:
            print(f"  Progress: {i}/{len(filtered)}")
        
        addresses = await fetch_protocol_address(protocol.slug, defillama)
        
        if addresses:
            existing = PROTOCOL_ADDRESSES.get(protocol.slug, {})
            
            merged = {**existing, **addresses}
            
            if merged != existing:
                new_addresses[protocol.slug] = merged
                if protocol.slug in PROTOCOL_ADDRESSES:
                    updated_count += 1
                else:
                    added_count += 1
    
    if verbose:
        print(f"\n[+] Summary:")
        print(f"    Added: {added_count} new protocols")
        print(f"    Updated: {updated_count} existing protocols")
        print(f"    Total in database: {len(PROTOCOL_ADDRESSES) + added_count}")
    
    return new_addresses


def update_addresses_file(new_addresses: dict, addresses_file: Path):
    """Update the addresses.py file with new addresses"""
    
    from src.fetchers.addresses import PROTOCOL_ADDRESSES
    
    updated = {**PROTOCOL_ADDRESSES, **new_addresses}
    
    with open(addresses_file, 'r') as f:
        lines = f.readlines()
    
    start_idx = None
    end_idx = None
    
    for i, line in enumerate(lines):
        if "PROTOCOL_ADDRESSES = {" in line:
            start_idx = i
        if start_idx is not None and line.strip() == "}" and i > start_idx:
            end_idx = i
            break
    
    if start_idx is None or end_idx is None:
        print("[!] Could not find PROTOCOL_ADDRESSES block in file")
        return False
    
    formatted = format_addresses_dict(updated)
    
    new_lines = lines[:start_idx+1] + [formatted + "\n"] + lines[end_idx:]
    
    with open(addresses_file, 'w') as f:
        f.writelines(new_lines)
    
    return True


def format_addresses_dict(addresses: dict) -> str:
    """Format addresses dictionary as Python code"""
    lines = []
    for slug, chains in sorted(addresses.items()):
        lines.append(f'    "{slug}": {{')
        for chain, addr in sorted(chains.items()):
            lines.append(f'        "{chain}": "{addr}",')
        lines.append("    },")
    
    return "\n".join(lines)


async def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Populate protocol addresses from DeFiLlama")
    parser.add_argument("--min-tvl", type=float, default=100_000, help="Minimum TVL to include")
    parser.add_argument("--limit", type=int, default=100, help="Max protocols to fetch")
    parser.add_argument("--update-file", action="store_true", help="Update addresses.py file")
    parser.add_argument("--output", type=str, help="Output JSON file instead of updating addresses.py")
    parser.add_argument("-v", "--verbose", action="store_true", default=True)
    
    args = parser.parse_args()
    
    new_addresses = await populate_addresses(
        min_tvl=args.min_tvl,
        limit=args.limit,
        verbose=args.verbose
    )
    
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(new_addresses, f, indent=2)
        print(f"\n[+] Saved to {args.output}")
    elif args.update_file:
        addresses_file = Path(__file__).parent.parent / "src" / "fetchers" / "addresses.py"
        if update_addresses_file(new_addresses, addresses_file):
            print(f"\n[+] Updated {addresses_file}")
        else:
            print("\n[!] Failed to update addresses.py")
    else:
        print("\n[+] Use --update-file to update addresses.py or --output to save JSON")


if __name__ == "__main__":
    asyncio.run(main())
