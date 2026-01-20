import os
from typing import Dict, List, Optional
from termcolor import cprint

from ..fetchers.etherscan_fetcher import EtherscanFetcher
from ..analyzers import (
    LLMAnalyzer,
    ReentrancyAnalyzer,
    FlashLoanAnalyzer,
    AccessControlAnalyzer,
    DelegateCallAnalyzer,
    SelfDestructAnalyzer,
    SignatureReplayAnalyzer,
    FunctionSelectorAnalyzer,
    StorageCollisionAnalyzer,
    OracleManipulationAnalyzer,
    DoSAnalyzer,
    IntegerOverflowAnalyzer
)
from ..models.model_factory import ModelFactory


class ProtocolRiskScanner:
    def __init__(self, model=None, etherscan_api_key: Optional[str] = None, network: str = "mainnet"):
        self.model = model
        if not self.model:
            factory = ModelFactory()
            self.model = factory.get_model("openai", "gpt-4o-mini")
        
        self.etherscan_fetcher = EtherscanFetcher(api_key=etherscan_api_key, network=network)
        
        self.analyzers = [
            LLMAnalyzer(self.model),
            ReentrancyAnalyzer(self.model),
            FlashLoanAnalyzer(self.model),
            AccessControlAnalyzer(self.model),
            DelegateCallAnalyzer(self.model),
            SelfDestructAnalyzer(self.model),
            SignatureReplayAnalyzer(self.model),
            FunctionSelectorAnalyzer(self.model),
            StorageCollisionAnalyzer(self.model),
            OracleManipulationAnalyzer(self.model),
            DoSAnalyzer(self.model),
            IntegerOverflowAnalyzer(self.model)
        ]
    
    def scan_contract(self, address: str) -> Dict:
        cprint(f"\n🔍 Protocol Risk Scanner", "white", "on_blue")
        cprint("=" * 50, "cyan")
        cprint(f"📡 Contract Address: {address}", "cyan")
        
        contract_info = self.etherscan_fetcher.fetch_contract_source_sync(address)
        
        if not contract_info:
            return {
                "success": False,
                "error": "Failed to fetch contract source",
                "address": address
            }
        
        cprint(f"✅ Fetched: {contract_info['name']}", "green")
        cprint(f"   Compiler: {contract_info['compiler']}", "cyan")
        
        contract_code = contract_info["source"]
        
        cprint(f"\n🔬 Running vulnerability analyzers...", "cyan")
        
        findings = []
        vulnerable_patterns = []
        
        llm_analyzer = LLMAnalyzer(self.model)
        
        for analyzer in self.analyzers:
            try:
                pattern, confidence = analyzer.detect_pattern(contract_code)
                if confidence > 0.5:
                    analysis = analyzer.analyze(contract_code)
                    
                    if not analysis or not analysis.get("vulnerable"):
                        analysis = llm_analyzer.analyze(contract_code)
                        if analysis and analysis.get("vulnerable"):
                            pattern_type = pattern.replace('_', ' ').title()
                            if analysis.get("type", "").lower() not in pattern.lower():
                                analysis["type"] = f"{pattern_type} - {analysis.get('type', 'Vulnerability detected')}"
                    
                    if analysis and analysis.get("vulnerable"):
                        findings.append({
                            "analyzer": analyzer.__class__.__name__,
                            "pattern": pattern,
                            "confidence": confidence,
                            "vulnerability": analysis
                        })
                        vulnerable_patterns.append({
                            "type": analysis.get("type", "Unknown"),
                            "severity": analysis.get("severity", "Unknown"),
                            "pattern": pattern,
                            "confidence": confidence
                        })
                        cprint(f"   ⚠️  {analyzer.__class__.__name__}: {analysis.get('type', 'Unknown')} ({analysis.get('severity', 'Unknown')})", "yellow")
            except Exception as e:
                cprint(f"   ❌ {analyzer.__class__.__name__} failed: {e}", "red")
        
        if not findings:
            cprint("\n✅ No vulnerabilities detected", "green")
            return {
                "success": True,
                "vulnerable": False,
                "address": address,
                "contract_info": contract_info,
                "findings": []
            }
        
        cprint(f"\n⚠️  Found {len(findings)} vulnerability pattern(s)", "yellow")
        
        result = {
            "success": True,
            "vulnerable": True,
            "address": address,
            "contract_info": contract_info,
            "findings": findings,
            "vulnerable_patterns": vulnerable_patterns
        }
        
        at_risk_wallets = self._query_at_risk_wallets(address, vulnerable_patterns)
        result["at_risk_wallets"] = at_risk_wallets
        
        return result
    
    def _query_at_risk_wallets(self, address: str, patterns: List[Dict]) -> List[Dict]:
        cprint(f"\n🔎 Querying at-risk wallets...", "cyan")
        
        at_risk = []
        
        try:
            web3_available = self._check_web3_available()
            if not web3_available:
                cprint("   ⚠️  web3.py not available. Install with: pip install web3", "yellow")
                cprint("   💡 Returning placeholder structure for wallet detection", "yellow")
                return [{
                    "address": "0x...",
                    "balance": "N/A",
                    "note": "Install web3.py for actual wallet detection"
                }]
            
            from web3 import Web3
            
            rpc_url = os.getenv("ETH_RPC_URL", "https://eth.llamarpc.com")
            w3 = Web3(Web3.HTTPProvider(rpc_url))
            
            if not w3.is_connected():
                cprint("   ⚠️  Could not connect to Ethereum RPC", "yellow")
                return []
            
            contract_balance = w3.eth.get_balance(address)
            cprint(f"   📊 Contract balance: {w3.from_wei(contract_balance, 'ether')} ETH", "cyan")
            
            for pattern in patterns:
                if pattern["type"].lower() in ["reentrancy", "access control", "flash loan"]:
                    cprint(f"   🔍 Pattern {pattern['type']} may affect users with deposits", "yellow")
            
            at_risk.append({
                "address": address,
                "balance_wei": str(contract_balance),
                "balance_eth": str(w3.from_wei(contract_balance, 'ether')),
                "note": "Full wallet enumeration requires contract-specific analysis"
            })
        
        except ImportError:
            cprint("   ⚠️  web3.py not installed", "yellow")
        except Exception as e:
            cprint(f"   ❌ Error querying wallets: {e}", "red")
        
        return at_risk
    
    def _check_web3_available(self) -> bool:
        try:
            import web3
            return True
        except ImportError:
            return False
    
    def format_report(self, result: Dict) -> str:
        if not result.get("success"):
            return f"❌ Scan failed: {result.get('error', 'Unknown error')}"
        
        if not result.get("vulnerable"):
            return f"✅ Contract {result['address']} appears secure"
        
        report = []
        report.append(f"\n{'='*60}")
        report.append(f"🚨 VULNERABILITY REPORT")
        report.append(f"{'='*60}")
        report.append(f"Contract: {result['contract_info']['name']}")
        report.append(f"Address: {result['address']}")
        report.append(f"\n⚠️  VULNERABLE PATTERNS DETECTED:")
        
        for pattern in result.get("vulnerable_patterns", []):
            report.append(f"  • {pattern['type']} ({pattern['severity']}) - Confidence: {pattern['confidence']:.0%}")
        
        report.append(f"\n📋 DETAILED FINDINGS:")
        for finding in result.get("findings", []):
            vuln = finding.get("vulnerability", {})
            report.append(f"\n  Analyzer: {finding['analyzer']}")
            report.append(f"  Type: {vuln.get('type', 'Unknown')}")
            report.append(f"  Severity: {vuln.get('severity', 'Unknown')}")
            report.append(f"  Explanation: {vuln.get('explanation', 'N/A')}")
        
        at_risk = result.get("at_risk_wallets", [])
        if at_risk:
            report.append(f"\n💰 AT-RISK WALLETS:")
            for wallet in at_risk:
                report.append(f"  • {wallet.get('address', 'N/A')}")
                if 'balance_eth' in wallet:
                    report.append(f"    Balance: {wallet['balance_eth']} ETH")
                if 'note' in wallet:
                    report.append(f"    Note: {wallet['note']}")
        
        report.append(f"\n{'='*60}")
        
        return "\n".join(report)
