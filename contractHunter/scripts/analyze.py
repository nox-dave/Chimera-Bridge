#!/usr/bin/env python3
import sys
import argparse
import re
from pathlib import Path
from termcolor import cprint

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.models.model_factory import ModelFactory
from src.analyzers.llm_analyzer import LLMAnalyzer
from src.scanners.protocol_risk_scanner import ProtocolRiskScanner


def is_ethereum_address(address: str) -> bool:
    return bool(re.match(r'^0x[a-fA-F0-9]{40}$', address))


def load_contract(contract_path: Path) -> str:
    if not contract_path.exists():
        cprint(f"❌ Contract not found: {contract_path}", "red")
        sys.exit(1)
    with open(contract_path, "r") as f:
        return f.read()


def analyze_local_contract(contract_path: Path, model):
    contract_code = load_contract(contract_path)
    
    cprint("\n🔍 Basilisk Contract Analyzer", "white", "on_blue")
    cprint("=" * 50, "cyan")
    cprint(f"✅ Loaded {contract_path.name}", "green")
    
    analyzer = LLMAnalyzer(model)
    analysis = analyzer.analyze(contract_code)
    
    if not analysis:
        cprint("❌ Analysis failed", "red")
        sys.exit(1)
    
    if not analysis['vulnerable']:
        cprint("✅ No vulnerability detected", "green")
        return
    
    cprint(f"\n📊 Found: {analysis['type']} ({analysis['severity']})", "yellow")
    cprint(f"   {analysis['explanation']}", "yellow")


def analyze_contract_address(address: str, model, network: str):
    scanner = ProtocolRiskScanner(model=model, network=network)
    result = scanner.scan_contract(address)
    
    if not result.get("success"):
        cprint(f"❌ Scan failed: {result.get('error', 'Unknown error')}", "red")
        sys.exit(1)
    
    report = scanner.format_report(result)
    print(report)


def main():
    parser = argparse.ArgumentParser(description="🔍 Analyze contract for vulnerabilities")
    parser.add_argument("contract", help="Contract address (0x...) or path to contract file (relative to challenges/)")
    parser.add_argument("--model", default="gpt-4o-mini", help="Model to use")
    parser.add_argument("--network", default="mainnet", help="Network for address lookup (mainnet, sepolia, etc.)")
    args = parser.parse_args()
    
    factory = ModelFactory()
    model = factory.get_model("openai", args.model)
    
    if not model:
        cprint("❌ Failed to initialize model", "red")
        sys.exit(1)
    
    if is_ethereum_address(args.contract):
        analyze_contract_address(args.contract, model, args.network)
    else:
        contract_path = project_root / "challenges" / args.contract
        analyze_local_contract(contract_path, model)


if __name__ == "__main__":
    main()
