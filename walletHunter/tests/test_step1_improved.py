#!/usr/bin/env python3

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from src.core import WalletProfiler
from src.config import KNOWN_EXCHANGE_ADDRESSES

def test_step1_improved():
    print("Testing Step 1 (Improved): Exchange Wallet Filter")
    print("=" * 70)
    
    profiler = WalletProfiler()
    
    test_cases = [
        ("0xdfd5293d8e347dfe59e90efd55b2956a1343963d", "Binance 16", True),
        ("0x4976a4a02f38326660d17bf34b431dc6e2eb2327", "Binance 20", True),
        ("0x2b3fed49557bd88f78b898684f82fbb355305dbb", "Revolut 4", True),
        ("0x28c6c06298d514db089934071355e5743bf21d60", "Binance 14", True),
        ("0xbe0eb53f46cd790cd13851d5eff43d12404d33e8", "Binance 7", True),
        ("0x21a31ee1afc51d94c2efccaa2092ad1028285549", "Binance 15", True),
        ("0x3606f0f14828cbf4962a284a4bff93bc94b63665", "Unknown wallet", False),
        ("0xe66baa0b612003af308d78f066bbdb9a5e00ff6c", "Unknown wallet", False),
        ("0x61a258da0e6015ad2754714d001fb78322015bec", "Unknown wallet", False),
    ]
    
    print("\n1. Testing known exchange addresses (should be filtered):")
    all_passed = True
    for address, name, expected in test_cases:
        is_exchange = profiler.is_likely_exchange(address)
        status = "✓ PASS" if is_exchange == expected else "✗ FAIL"
        print(f"   {status}: {name} ({address[:10]}...) - is_exchange={is_exchange} (expected={expected})")
        if is_exchange != expected:
            all_passed = False
    
    print("\n2. Verifying KNOWN_EXCHANGE_ADDRESSES dictionary:")
    print(f"   Total exchange addresses: {len(KNOWN_EXCHANGE_ADDRESSES)}")
    
    required_addresses = {
        "0xdfd5293d8e347dfe59e90efd55b2956a1343963d": "Binance 16",
        "0x4976a4a02f38326660d17bf34b431dc6e2eb2327": "Binance 20",
        "0x2b3fed49557bd88f78b898684f82fbb355305dbb": "Revolut 4"
    }
    
    print("\n3. Verifying required addresses are in dictionary:")
    for addr, name in required_addresses.items():
        addr_lower = addr.lower()
        found = any(k.lower() == addr_lower for k in KNOWN_EXCHANGE_ADDRESSES.keys())
        status = "✓ FOUND" if found else "✗ MISSING"
        print(f"   {status}: {name} ({addr[:10]}...)")
        if not found:
            all_passed = False
    
    print("\n4. Checking for duplicates:")
    addresses_lower = [k.lower() for k in KNOWN_EXCHANGE_ADDRESSES.keys()]
    duplicates = [addr for addr in set(addresses_lower) if addresses_lower.count(addr) > 1]
    if duplicates:
        print(f"   ✗ Found {len(duplicates)} duplicate addresses")
        all_passed = False
    else:
        print("   ✓ No duplicates found")
    
    print("\n" + "=" * 70)
    if all_passed:
        print("✓ Step 1 (Improved) PASSED: All exchange addresses correctly identified")
        return 0
    else:
        print("✗ Step 1 (Improved) FAILED: Some tests did not pass")
        return 1

if __name__ == '__main__':
    sys.exit(test_step1_improved())

