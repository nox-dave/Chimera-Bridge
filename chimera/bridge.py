#!/usr/bin/env python3
"""
Chimera Bridge - Connect vulnerable contracts to exposed wallets

Flow:
1. Load hunt results from contractHunter
2. For each vulnerable contract:
   - Query Etherscan for wallet interactions
   - Filter out exchanges/contracts
   - Estimate exposure amounts
3. Feed wallets to walletHunter for profiling
4. Generate exposure report
"""

import os
import sys
import json
import asyncio
import httpx
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Set
from dataclasses import dataclass, field, asdict


@dataclass
class ExposedWallet:
    """Wallet with exposure to vulnerable contract"""
    address: str
    interaction_count: int = 0
    last_interaction: str = ""
    estimated_exposure_usd: float = 0.0
    interaction_type: str = "unknown"
    profile: Optional[Dict] = None


@dataclass
class ContractExposure:
    """Exposure report for a single vulnerable contract"""
    contract_address: str
    contract_name: str
    chain: str
    category: str
    tvl: float
    vulnerability_count: int
    highest_severity: str
    exposed_wallets: List[ExposedWallet] = field(default_factory=list)
    total_wallets: int = 0
    total_exposure_usd: float = 0.0
    high_value_wallets: int = 0
    scan_timestamp: str = ""


@dataclass 
class BridgeResult:
    """Complete bridge analysis result"""
    contracts_analyzed: int = 0
    total_wallets_found: int = 0
    total_exposure_usd: float = 0.0
    exposures: List[ContractExposure] = field(default_factory=list)
    timestamp: str = ""


KNOWN_EXCHANGES = {
    "0x28c6c06298d514db089934071355e5743bf21d60",
    "0x21a31ee1afc51d94c2efccaa2092ad1028285549",
    "0xdfd5293d8e347dfe59e90efd55b2956a1343963d",
    "0x71660c4005ba85c37ccec55d0c4493e66fe775d3",
    "0x503828976d22510aad0201ac7ec88293211d23da",
    "0xddfabcdc4d8ffc6d5beaf154f18b778f892a0740",
    "0x2910543af39aba0cd09dbb2d50200b3e800a63d2",
    "0x6cc5f688a315f3dc28a7781717a9a798a59fda7b",
    "0xf89d7b9c864f589bbf53a82105107622b35eaa40",
}

CONTRACT_PATTERNS = [
    "0x0000000000000000000000000000000000000000",
    "0x000000000000000000000000000000000000dead",
]


class ChimeraBridge:
    """Bridge between contractHunter and walletHunter"""
    
    def __init__(
        self,
        etherscan_api_key: str = None,
        contract_hunter_dir: str = "contractHunter",
        wallet_hunter_dir: str = "walletHunter",
        output_dir: str = "chimera/reports",
    ):
        self.etherscan_api_key = (
            etherscan_api_key or 
            os.getenv("ETHERSCAN_API_KEY") or
            os.getenv("ETHERSCAN_KEY") or
            ""
        )
        
        if not self.etherscan_api_key:
            env_paths = [
                Path(".env"),
                Path("../.env"),
                Path(contract_hunter_dir) / ".env",
                Path(wallet_hunter_dir) / ".env",
                Path.home() / ".env",
            ]
            for env_path in env_paths:
                if env_path.exists():
                    try:
                        with open(env_path) as f:
                            for line in f:
                                if line.startswith("ETHERSCAN"):
                                    key = line.split("=", 1)[1].strip().strip('"').strip("'")
                                    if key:
                                        self.etherscan_api_key = key
                                        break
                    except:
                        pass
                if self.etherscan_api_key:
                    break
        
        self.contract_hunter_dir = Path(contract_hunter_dir)
        self.wallet_hunter_dir = Path(wallet_hunter_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.chain_apis = {
            "ethereum": ("https://api.etherscan.io/v2/api", 1),
            "polygon": ("https://api.etherscan.io/v2/api", 137),
            "arbitrum": ("https://api.etherscan.io/v2/api", 42161),
            "optimism": ("https://api.etherscan.io/v2/api", 10),
            "base": ("https://api.etherscan.io/v2/api", 8453),
        }
        
        self.wallet_profiler = None
        
        if self.etherscan_api_key:
            print(f"[+] Etherscan API key loaded")
        else:
            print(f"[!] Warning: No Etherscan API key found")
        
    async def _init_wallet_profiler(self):
        """Initialize walletHunter profiler if available"""
        if self.wallet_profiler is not None:
            return
            
        try:
            sys.path.insert(0, str(self.wallet_hunter_dir))
            from unified_profiler import UnifiedProfiler
            self.wallet_profiler = UnifiedProfiler()
            print("[+] walletHunter profiler initialized")
        except ImportError as e:
            print(f"[!] walletHunter not available: {e}")
            print("    Wallet profiling will be skipped")
            self.wallet_profiler = None
    
    async def get_contract_interactions(
        self,
        contract_address: str,
        chain: str = "ethereum",
        max_transactions: int = 1000,
    ) -> List[Dict]:
        """
        Get wallets that interacted with a contract.
        
        Returns list of unique wallet addresses with interaction info.
        """
        if not contract_address or contract_address.strip() == "":
            return []
        
        api_url, chain_id = self.chain_apis.get(chain.lower(), self.chain_apis["ethereum"])
        
        if not self.etherscan_api_key:
            print("[!] No Etherscan API key - cannot query interactions")
            return []
        
        interactions = []
        seen_addresses: Set[str] = set()
        
        async with httpx.AsyncClient(timeout=30) as client:
            params = {
                "chainid": chain_id,
                "module": "account",
                "action": "txlist",
                "address": contract_address,
                "startblock": 0,
                "endblock": 99999999,
                "page": 1,
                "offset": max_transactions,
                "sort": "desc",
                "apikey": self.etherscan_api_key,
            }
            
            try:
                response = await client.get(api_url, params=params)
                data = response.json()
                
                if data.get("status") == "1" and data.get("result"):
                    for tx in data["result"]:
                        from_addr = tx.get("from", "").lower()
                        to_addr = tx.get("to", "").lower()
                        
                        wallet = from_addr if to_addr.lower() == contract_address.lower() else to_addr
                        
                        if wallet and wallet not in seen_addresses:
                            if not self._is_excluded_address(wallet):
                                seen_addresses.add(wallet)
                                interactions.append({
                                    "address": wallet,
                                    "tx_hash": tx.get("hash"),
                                    "timestamp": tx.get("timeStamp"),
                                    "value": tx.get("value", "0"),
                                    "method": tx.get("functionName", "").split("(")[0] if tx.get("functionName") else "transfer",
                                })
            except Exception as e:
                print(f"[!] Error fetching transactions: {e}")
        
        print(f"    Found {len(interactions)} unique wallet interactions")
        return interactions
    
    def _is_excluded_address(self, address: str) -> bool:
        """Check if address should be excluded (exchange, contract, etc.)"""
        addr_lower = address.lower()
        
        if addr_lower in KNOWN_EXCHANGES:
            return True
            
        for pattern in CONTRACT_PATTERNS:
            if addr_lower == pattern.lower():
                return True
        
        return False
    
    async def estimate_exposure(
        self,
        wallet_address: str,
        contract_address: str,
        chain: str = "ethereum",
    ) -> float:
        """
        Estimate wallet's exposure to a contract.
        
        This is a simplified estimation - real exposure would require:
        - Querying token balances
        - Checking LP positions
        - Reading contract state
        """
        return 0.0
    
    async def analyze_contract(
        self,
        contract_address: str,
        contract_name: str,
        chain: str,
        category: str,
        tvl: float,
        vulnerabilities: List[Dict],
        max_wallets: int = 20,
        profile_wallets: bool = False,
    ) -> ContractExposure:
        """
        Analyze a single vulnerable contract for exposed wallets.
        """
        print(f"\n🔗 Bridging: {contract_name}")
        print(f"   Contract: {contract_address[:20] if contract_address else 'N/A'}...")
        print(f"   Chain: {chain}")
        
        severities = [v.get("severity", "").upper() for v in vulnerabilities]
        severity_order = ["CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"]
        highest = "INFO"
        for sev in severity_order:
            if sev in severities:
                highest = sev
                break
        
        interactions = await self.get_contract_interactions(
            contract_address, chain, max_transactions=500
        )
        
        exposed_wallets = []
        
        for interaction in interactions[:max_wallets]:
            wallet = ExposedWallet(
                address=interaction["address"],
                interaction_count=1,
                last_interaction=interaction.get("timestamp", ""),
                interaction_type=interaction.get("method", "unknown"),
            )
            
            wallet.estimated_exposure_usd = await self.estimate_exposure(
                interaction["address"], contract_address, chain
            )
            
            if profile_wallets and self.wallet_profiler and len(exposed_wallets) < 5:
                try:
                    print(f"    Profiling {interaction['address'][:12]}...")
                    loop = asyncio.get_event_loop()
                    profile = await asyncio.wait_for(
                        loop.run_in_executor(
                            None,
                            self.wallet_profiler.generate_full_profile,
                            interaction["address"]
                        ),
                        timeout=30.0
                    )
                    wallet.profile = profile
                    
                    if profile and profile.get("balance_usd"):
                        wallet.estimated_exposure_usd = profile["balance_usd"]
                except asyncio.TimeoutError:
                    print(f"    [!] Timeout profiling {interaction['address'][:12]}...")
                except Exception:
                    pass
            
            exposed_wallets.append(wallet)
        
        total_exposure = sum(w.estimated_exposure_usd for w in exposed_wallets)
        high_value = sum(1 for w in exposed_wallets if w.estimated_exposure_usd >= 100000)
        
        exposure = ContractExposure(
            contract_address=contract_address or "",
            contract_name=contract_name,
            chain=chain,
            category=category,
            tvl=tvl,
            vulnerability_count=len(vulnerabilities),
            highest_severity=highest,
            exposed_wallets=exposed_wallets,
            total_wallets=len(interactions),
            total_exposure_usd=total_exposure,
            high_value_wallets=high_value,
            scan_timestamp=datetime.now().isoformat(),
        )
        
        print(f"   ✅ Found {len(interactions)} wallets ({high_value} high-value)")
        
        return exposure
    
    async def bridge_from_hunt_results(
        self,
        hunt_results_path: str,
        max_contracts: int = 10,
        max_wallets_per_contract: int = 50,
        profile_wallets: bool = False,
        min_severity: str = "HIGH",
        verbose: bool = True,
    ) -> BridgeResult:
        """
        Bridge hunt results to wallet exposure analysis.
        
        Args:
            hunt_results_path: Path to hunt_*.json from contractHunter
            max_contracts: Maximum contracts to analyze
            max_wallets_per_contract: Max wallets to fetch per contract
            profile_wallets: Whether to run full walletHunter profiling
            min_severity: Minimum vulnerability severity to include
            verbose: Print progress output
        """
        if verbose:
            print("\n" + "=" * 60)
            print("🔗 CHIMERA BRIDGE - Contract → Wallet Analysis")
            print("=" * 60)
        
        with open(hunt_results_path, 'r') as f:
            hunt_data = json.load(f)
        
        targets = hunt_data.get("targets", [])
        if verbose:
            print(f"\n📂 Loaded {len(targets)} targets from hunt results")
        
        severity_order = ["CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"]
        min_sev_idx = severity_order.index(min_severity.upper()) if min_severity.upper() in severity_order else 1
        
        vulnerable_contracts = []
        for target in targets:
            vulns = target.get("vulnerabilities", [])
            scan_results = target.get("scan_results", {})
            if isinstance(scan_results, dict):
                vulns.extend(scan_results.get("findings", []))
            
            verdicts = target.get("verdicts", [])
            for verdict in verdicts:
                if isinstance(verdict, dict):
                    sev = verdict.get("severity", "").upper()
                    if sev in severity_order:
                        vulns.append({
                            "severity": sev,
                            "title": verdict.get("title", ""),
                            "description": verdict.get("description", ""),
                        })
            
            if not vulns:
                continue
                
            has_qualifying_vuln = False
            for v in vulns:
                sev = v.get("severity", "").upper()
                if sev in severity_order[:min_sev_idx + 1]:
                    has_qualifying_vuln = True
                    break
            
            if has_qualifying_vuln and target.get("address"):
                vulnerable_contracts.append(target)
        
        if verbose:
            print(f"   {len(vulnerable_contracts)} contracts with {min_severity}+ vulnerabilities")
        
        if profile_wallets:
            await self._init_wallet_profiler()
        
        exposures = []
        
        for i, contract in enumerate(vulnerable_contracts[:max_contracts], 1):
            if verbose:
                print(f"\n[{i}/{min(len(vulnerable_contracts), max_contracts)}] ", end="")
            
            vulns = contract.get("vulnerabilities", [])
            scan_results = contract.get("scan_results", {})
            if isinstance(scan_results, dict):
                vulns.extend(scan_results.get("findings", []))
            
            verdicts = contract.get("verdicts", [])
            for verdict in verdicts:
                if isinstance(verdict, dict):
                    sev = verdict.get("severity", "").upper()
                    if sev in severity_order:
                        vulns.append({
                            "severity": sev,
                            "title": verdict.get("title", ""),
                            "description": verdict.get("description", ""),
                        })
            
            contract_name = contract.get("protocol") or contract.get("protocol_name") or contract.get("name", "Unknown")
            
            exposure = await self.analyze_contract(
                contract_address=contract.get("address", ""),
                contract_name=contract_name,
                chain=contract.get("chain", "Ethereum"),
                category=contract.get("category", "Unknown"),
                tvl=contract.get("tvl", 0) or 0,
                vulnerabilities=vulns,
                max_wallets=max_wallets_per_contract,
                profile_wallets=profile_wallets,
            )
            
            exposures.append(exposure)
        
        result = BridgeResult(
            contracts_analyzed=len(exposures),
            total_wallets_found=sum(e.total_wallets for e in exposures),
            total_exposure_usd=sum(e.total_exposure_usd for e in exposures),
            exposures=exposures,
            timestamp=datetime.now().isoformat(),
        )
        
        if verbose:
            self._print_summary(result)
        
        self._save_results(result, hunt_results_path)
        
        return result
    
    def _print_summary(self, result: BridgeResult):
        """Print bridge analysis summary"""
        print("\n" + "=" * 60)
        print("📊 BRIDGE ANALYSIS COMPLETE")
        print("=" * 60)
        
        print(f"\n{'Contracts Analyzed:':<25} {result.contracts_analyzed}")
        print(f"{'Total Wallets Found:':<25} {result.total_wallets_found}")
        print(f"{'Total Exposure (USD):':<25} ${result.total_exposure_usd:,.0f}")
        
        if result.exposures:
            print("\n🎯 Exposure by Contract:")
            print("-" * 60)
            
            for exp in sorted(result.exposures, key=lambda x: x.total_wallets, reverse=True):
                sev_emoji = {"CRITICAL": "🚨", "HIGH": "⚠️", "MEDIUM": "⚡", "LOW": "📌"}.get(exp.highest_severity, "ℹ️")
                print(f"\n   {exp.contract_name}")
                print(f"   {sev_emoji} {exp.vulnerability_count} vulns ({exp.highest_severity})")
                print(f"   👥 {exp.total_wallets} wallets interacted")
                if exp.high_value_wallets > 0:
                    print(f"   💰 {exp.high_value_wallets} high-value wallets (>$100k)")
    
    def _save_results(self, result: BridgeResult, source_path: str):
        """Save bridge results to JSON"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        output = {
            "timestamp": result.timestamp,
            "source_hunt": source_path,
            "contracts_analyzed": result.contracts_analyzed,
            "total_wallets_found": result.total_wallets_found,
            "total_exposure_usd": result.total_exposure_usd,
            "exposures": [],
        }
        
        for exp in result.exposures:
            exp_dict = {
                "contract_address": exp.contract_address,
                "contract_name": exp.contract_name,
                "chain": exp.chain,
                "category": exp.category,
                "tvl": exp.tvl,
                "vulnerability_count": exp.vulnerability_count,
                "highest_severity": exp.highest_severity,
                "total_wallets": exp.total_wallets,
                "total_exposure_usd": exp.total_exposure_usd,
                "high_value_wallets": exp.high_value_wallets,
                "exposed_wallets": [
                    {
                        "address": w.address,
                        "interaction_count": w.interaction_count,
                        "interaction_type": w.interaction_type,
                        "estimated_exposure_usd": w.estimated_exposure_usd,
                    }
                    for w in exp.exposed_wallets[:20]
                ],
            }
            output["exposures"].append(exp_dict)
        
        output_path = self.output_dir / f"bridge_{timestamp}.json"
        with open(output_path, 'w') as f:
            json.dump(output, f, indent=2)
        print(f"\n💾 Results saved to: {output_path}")
        
        md_path = self.output_dir / f"bridge_{timestamp}.md"
        self._generate_markdown_report(result, md_path)
        print(f"📄 Report saved to: {md_path}")
        
        return output_path
    
    def _generate_markdown_report(self, result: BridgeResult, output_path: Path):
        """Generate markdown exposure report"""
        lines = []
        
        lines.append("# 🔗 Chimera Bridge - Exposure Report")
        lines.append("")
        lines.append(f"> Generated: {result.timestamp}")
        lines.append("")
        
        lines.append("## Overview")
        lines.append("")
        lines.append("| Metric | Value |")
        lines.append("|--------|-------|")
        lines.append(f"| Contracts Analyzed | {result.contracts_analyzed} |")
        lines.append(f"| Total Wallets Found | {result.total_wallets_found} |")
        lines.append(f"| Total Exposure | ${result.total_exposure_usd:,.0f} |")
        lines.append("")
        
        lines.append("## Exposure by Contract")
        lines.append("")
        lines.append("| Contract | Category | Severity | Wallets | High-Value |")
        lines.append("|----------|----------|----------|---------|------------|")
        
        for exp in sorted(result.exposures, key=lambda x: x.total_wallets, reverse=True):
            sev_emoji = {"CRITICAL": "🚨", "HIGH": "⚠️", "MEDIUM": "⚡"}.get(exp.highest_severity, "📌")
            lines.append(f"| {exp.contract_name} | {exp.category} | {sev_emoji} {exp.highest_severity} | {exp.total_wallets} | {exp.high_value_wallets} |")
        
        lines.append("")
        
        lines.append("## Contract Details")
        lines.append("")
        
        for exp in result.exposures:
            lines.append(f"### {exp.contract_name}")
            lines.append("")
            lines.append(f"- **Address**: `{exp.contract_address}`")
            lines.append(f"- **Chain**: {exp.chain}")
            lines.append(f"- **TVL**: ${exp.tvl:,.0f}")
            lines.append(f"- **Vulnerabilities**: {exp.vulnerability_count} ({exp.highest_severity})")
            lines.append(f"- **Wallets Exposed**: {exp.total_wallets}")
            lines.append("")
            
            if exp.exposed_wallets:
                lines.append("**Top Exposed Wallets:**")
                lines.append("")
                lines.append("| Address | Interaction Type | Exposure |")
                lines.append("|---------|-----------------|----------|")
                
                for wallet in exp.exposed_wallets[:10]:
                    addr_short = f"{wallet.address[:10]}...{wallet.address[-6:]}"
                    exposure = f"${wallet.estimated_exposure_usd:,.0f}" if wallet.estimated_exposure_usd else "Unknown"
                    lines.append(f"| `{addr_short}` | {wallet.interaction_type} | {exposure} |")
                
                lines.append("")
        
        lines.append("---")
        lines.append("*Generated by Chimera Bridge*")
        
        with open(output_path, 'w') as f:
            f.write("\n".join(lines))
    
    def generate_exposure_summary(self, exposures: List[ContractExposure]) -> str:
        """
        Generate a text summary of exposures.
        
        Args:
            exposures: List of ContractExposure objects
            
        Returns:
            Formatted summary string
        """
        lines = []
        
        lines.append("=" * 60)
        lines.append("🔗 CHIMERA BRIDGE - EXPOSURE SUMMARY")
        lines.append("=" * 60)
        lines.append("")
        
        total_wallets = sum(e.total_wallets for e in exposures)
        total_exposure = sum(e.total_exposure_usd for e in exposures)
        high_value = sum(e.high_value_wallets for e in exposures)
        
        lines.append(f"{'Contracts Analyzed:':<25} {len(exposures)}")
        lines.append(f"{'Total Wallets Found:':<25} {total_wallets}")
        lines.append(f"{'High-Value Wallets:':<25} {high_value}")
        lines.append(f"{'Total Exposure (USD):':<25} ${total_exposure:,.0f}")
        lines.append("")
        
        lines.append("EXPOSURE BY CONTRACT:")
        lines.append("-" * 60)
        
        for exp in sorted(exposures, key=lambda x: x.total_wallets, reverse=True):
            sev_emoji = {
                "CRITICAL": "🚨",
                "HIGH": "⚠️", 
                "MEDIUM": "⚡",
                "LOW": "📌"
            }.get(exp.highest_severity, "ℹ️")
            
            lines.append(f"\n{exp.contract_name}")
            lines.append(f"   Address: {exp.contract_address[:20]}...")
            lines.append(f"   {sev_emoji} {exp.vulnerability_count} vulnerabilities ({exp.highest_severity})")
            lines.append(f"   👥 {exp.total_wallets} wallets interacted")
            
            if exp.high_value_wallets > 0:
                lines.append(f"   💰 {exp.high_value_wallets} high-value wallets (>$100k)")
            
            if exp.exposed_wallets:
                lines.append(f"   Top wallets:")
                for wallet in exp.exposed_wallets[:5]:
                    addr_short = f"{wallet.address[:10]}...{wallet.address[-6:]}"
                    lines.append(f"      • {addr_short} ({wallet.interaction_type})")
        
        lines.append("")
        lines.append("=" * 60)
        
        return "\n".join(lines)


async def main():
    """CLI entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Chimera Bridge - Contract to Wallet Analysis")
    parser.add_argument("--hunt-results", "-r", required=True, help="Path to hunt_*.json")
    parser.add_argument("--max-contracts", "-c", type=int, default=10, help="Max contracts to analyze")
    parser.add_argument("--max-wallets", "-w", type=int, default=50, help="Max wallets per contract")
    parser.add_argument("--profile", "-p", action="store_true", help="Run full walletHunter profiling")
    parser.add_argument("--min-severity", "-s", default="HIGH", help="Minimum severity (CRITICAL, HIGH, MEDIUM, LOW)")
    parser.add_argument("--output", "-o", default="chimera/reports", help="Output directory")
    
    args = parser.parse_args()
    
    bridge = ChimeraBridge(output_dir=args.output)
    
    await bridge.bridge_from_hunt_results(
        hunt_results_path=args.hunt_results,
        max_contracts=args.max_contracts,
        max_wallets_per_contract=args.max_wallets,
        profile_wallets=args.profile,
        min_severity=args.min_severity,
    )


if __name__ == "__main__":
    asyncio.run(main())


ContractWalletBridge = ChimeraBridge
