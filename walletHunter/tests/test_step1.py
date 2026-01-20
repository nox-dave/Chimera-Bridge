#!/usr/bin/env python3

import sys
from wallet_profiler import WalletProfiler, KNOWN_EXCHANGE_ADDRESSES

def test_step1():
    print("Testing Step 1: Exchange Wallet Filter")
    print("=" * 60)
    
    profiler = WalletProfiler()
    
    binance_14 = "0x28c6c06298d514db089934071355e5743bf21d60"
    binance_7 = "0xbe0eb53f46cd790cd13851d5eff43d12404d33e8"
    binance_15 = "0x21a31ee1afc51d94c2efccaa2092ad1028285549"
    
    print("\n1. Testing known exchange addresses:")
    test_addresses = [
        (binance_14, "Binance 14"),
        (binance_7, "Binance 7"),
        (binance_15, "Binance 15")
    ]
    
    all_passed = True
    for address, name in test_addresses:
        is_exchange = profiler.is_likely_exchange(address)
        status = "✓ PASS" if is_exchange else "✗ FAIL"
        print(f"   {status}: {name} ({address[:10]}...) - is_exchange={is_exchange}")
        if not is_exchange:
            all_passed = False
    
    print("\n2. Testing non-exchange address:")
    normal_address = "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb"
    is_exchange = profiler.is_likely_exchange(normal_address)
    status = "✓ PASS" if not is_exchange else "✗ FAIL"
    print(f"   {status}: Normal wallet - is_exchange={is_exchange}")
    if is_exchange:
        all_passed = False
    
    print("\n3. Verifying KNOWN_EXCHANGE_ADDRESSES dictionary:")
    print(f"   Found {len(KNOWN_EXCHANGE_ADDRESSES)} known exchange addresses")
    for addr, name in list(KNOWN_EXCHANGE_ADDRESSES.items())[:5]:
        print(f"     - {name}: {addr[:10]}...")
    
    print("\n" + "=" * 60)
    if all_passed:
        print("✓ Step 1 PASSED: Exchange wallet filter is working correctly")
        return 0
    else:
        print("✗ Step 1 FAILED: Some tests did not pass")
        return 1

if __name__ == '__main__':
    sys.exit(test_step1())

