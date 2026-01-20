#!/usr/bin/env python3

import sys
import asyncio
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.scanners.pattern_scanner import PatternScanner


async def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Basilisk Pattern Scanner - FREE Vulnerability Detection")
    parser.add_argument("file", help="Solidity file to scan")
    parser.add_argument("--no-slither", action="store_true", help="Disable Slither analysis")
    parser.add_argument("--json", action="store_true", help="Output JSON format")
    
    args = parser.parse_args()
    
    scanner = PatternScanner()
    
    print(f"\n🔱 Basilisk Pattern Scanner")
    print(f"=" * 50)
    print(f"Scanning: {args.file}")
    
    findings = await scanner.scan_file(
        args.file,
        use_slither=not args.no_slither
    )
    
    if args.json:
        import json
        print(json.dumps([f.to_dict() for f in findings], indent=2))
    else:
        print(scanner.format_findings(findings))
        
        print(f"\n{'=' * 50}")
        print(f"📊 Summary:")
        by_severity = {}
        for f in findings:
            by_severity[f.severity.value] = by_severity.get(f.severity.value, 0) + 1
        for sev, count in sorted(by_severity.items()):
            print(f"   {sev}: {count}")


if __name__ == "__main__":
    asyncio.run(main())
