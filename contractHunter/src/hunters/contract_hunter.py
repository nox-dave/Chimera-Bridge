"""
Contract analysis engine — protocol discovery and technical risk assessment.

Flow:
1. Discover protocols via DeFiLlama (by TVL, category, audit status)
2. Fetch contract addresses
3. Analyze each contract for vulnerabilities
4. Validate findings to filter false positives
5. Generate verdicts and prioritize
6. Export batches for Chimera contract–wallet correlation when needed

Usage:
    hunter = ContractHunter()
    
    # Hunt with filters
    results = await hunter.hunt(
        min_tvl=100_000,
        categories=["Lending", "DEX"],
        exclude_audited=True,
        limit=20
    )
    
    # Run preset hunts
    results = await hunter.hunt_preset("fresh_whales")
"""

import asyncio
import sys
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from datetime import datetime
from pathlib import Path
import json

_current_file = Path(__file__).resolve()
_src_dir = _current_file.parent.parent
_root_dir = _src_dir.parent
_chimera_root = _root_dir.parent if _root_dir.name == "contractHunter" else _root_dir
_default_contracts_dir = _chimera_root / "Contracts"

for path in [str(_src_dir), str(_root_dir)]:
    if path not in sys.path:
        sys.path.insert(0, path)

try:
    from fetchers.defillama_client import DeFiLlamaClient, Protocol
except ImportError:
    try:
        from src.fetchers.defillama_client import DeFiLlamaClient, Protocol
    except ImportError:
        from ..fetchers.defillama_client import DeFiLlamaClient, Protocol

try:
    from fetchers.etherscan_fetcher import EtherscanClient, ContractSource, normalize_chain_name
except ImportError:
    try:
        from src.fetchers.etherscan_fetcher import EtherscanClient, ContractSource, normalize_chain_name
    except ImportError:
        try:
            from ..fetchers.etherscan_fetcher import EtherscanClient, ContractSource, normalize_chain_name
        except ImportError:
            EtherscanClient = None
            ContractSource = None
            normalize_chain_name = lambda x: "ethereum"

SCANNER_AVAILABLE = False
PatternScanner = None
Finding = None

try:
    from scanners.pattern_scanner import PatternScanner, Finding
    SCANNER_AVAILABLE = True
except ImportError:
    try:
        from src.scanners.pattern_scanner import PatternScanner, Finding
        SCANNER_AVAILABLE = True
    except ImportError:
        try:
            from ..scanners.pattern_scanner import PatternScanner, Finding
            SCANNER_AVAILABLE = True
        except ImportError:
            pass

VALIDATOR_AVAILABLE = False
FindingValidator = None

try:
    from scanners.finding_validator import FindingValidator
    VALIDATOR_AVAILABLE = True
except ImportError:
    try:
        from src.scanners.finding_validator import FindingValidator
        VALIDATOR_AVAILABLE = True
    except ImportError:
        try:
            from ..scanners.finding_validator import FindingValidator
            VALIDATOR_AVAILABLE = True
        except ImportError:
            pass

ADDRESS_DB_AVAILABLE = False
get_address = lambda slug, chain: ""
PROTOCOL_ADDRESSES = {}

try:
    from fetchers.addresses import get_address, PROTOCOL_ADDRESSES
    ADDRESS_DB_AVAILABLE = True
except ImportError:
    try:
        from src.fetchers.addresses import get_address, PROTOCOL_ADDRESSES
        ADDRESS_DB_AVAILABLE = True
    except ImportError:
        try:
            from ..fetchers.addresses import get_address, PROTOCOL_ADDRESSES
            ADDRESS_DB_AVAILABLE = True
        except ImportError:
            pass

REPORTS_AVAILABLE = False
ReportGenerator = None
ProtocolReport = None

try:
    from reports.report_generator import ReportGenerator, ProtocolReport
    REPORTS_AVAILABLE = True
except ImportError:
    try:
        from src.reports.report_generator import ReportGenerator, ProtocolReport
        REPORTS_AVAILABLE = True
    except ImportError:
        try:
            from ..reports.report_generator import ReportGenerator, ProtocolReport
            REPORTS_AVAILABLE = True
        except ImportError:
            pass

CATEGORIZER_AVAILABLE = False
ContractCategorizer = None

try:
    from utils.contract_categorizer import ContractCategorizer
    CATEGORIZER_AVAILABLE = True
except ImportError:
    try:
        from src.utils.contract_categorizer import ContractCategorizer
        CATEGORIZER_AVAILABLE = True
    except ImportError:
        try:
            from ..utils.contract_categorizer import ContractCategorizer
            CATEGORIZER_AVAILABLE = True
        except ImportError:
            pass


@dataclass
class ContractTarget:
    """A contract target for analysis"""
    address: str
    chain: str
    protocol_name: str
    protocol_slug: str
    tvl: float
    category: str
    is_audited: bool
    source_fetched: bool = False
    source_code: Optional[str] = None
    analysis_complete: bool = False
    vulnerabilities: List[Dict] = field(default_factory=list)
    verdicts: List[Dict] = field(default_factory=list)
    priority_score: int = 0
    validation_stats: Optional[Dict] = None


@dataclass
class HuntResult:
    """Results from a contract hunt"""
    timestamp: datetime
    parameters: Dict[str, Any]
    protocols_discovered: int
    contracts_found: int
    contracts_analyzed: int
    vulnerabilities_found: int
    targets: List[ContractTarget]
    high_priority: List[ContractTarget]
    validation_summary: Optional[Dict] = None
    
    def to_dict(self) -> Dict:
        return {
            "timestamp": self.timestamp.isoformat(),
            "parameters": self.parameters,
            "protocols_discovered": self.protocols_discovered,
            "contracts_found": self.contracts_found,
            "contracts_analyzed": self.contracts_analyzed,
            "vulnerabilities_found": self.vulnerabilities_found,
            "targets": [
                {
                    "address": t.address,
                    "chain": t.chain,
                    "protocol": t.protocol_name,
                    "tvl": t.tvl,
                    "category": t.category,
                    "audited": t.is_audited,
                    "vulnerabilities": t.vulnerabilities,
                    "verdicts": t.verdicts,
                    "priority_score": t.priority_score,
                    "validation_stats": t.validation_stats
                }
                for t in self.targets
            ],
            "high_priority_count": len(self.high_priority)
        }
        if self.validation_summary:
            result["validation_summary"] = self.validation_summary
        return result


class ContractHunter:
    """
    Contract Hunter - Discovery engine for vulnerable protocols
    
    Mirrors Gargophias's unified_profiler.py hunting flow.
    
    NEW: Includes FindingValidator to automatically filter false positives
    from PatternScanner/Slither results.
    """
    
    PRESETS = {
        "fresh_whales": {
            "description": "New high-TVL unaudited protocols",
            "min_tvl": 500_000,
            "max_tvl": 50_000_000,
            "exclude_audited": True,
            "high_risk_only": True,
            "limit": 30
        },
        "bridge_targets": {
            "description": "Cross-chain bridges (high-value targets)",
            "min_tvl": 1_000_000,
            "categories": ["Bridge", "Cross Chain"],
            "limit": 20
        },
        "lending_risks": {
            "description": "Lending protocols (flash loan vectors)",
            "min_tvl": 500_000,
            "categories": ["Lending", "CDP"],
            "limit": 30
        },
        "dex_targets": {
            "description": "DEXes (price manipulation vectors)",
            "min_tvl": 500_000,
            "categories": ["DEX"],
            "limit": 30
        },
        "yield_farms": {
            "description": "Yield aggregators (complex attack surface)",
            "min_tvl": 200_000,
            "categories": ["Yield", "Yield Aggregator", "Farm", "Leveraged Farming"],
            "limit": 40
        },
        "easy_targets": {
            "description": "Low-TVL unaudited protocols",
            "min_tvl": 50_000,
            "max_tvl": 500_000,
            "exclude_audited": True,
            "limit": 50
        },
        "growing_fast": {
            "description": "Protocols with rapid TVL growth",
            "min_tvl": 100_000,
            "growing": True,
            "growth_threshold": 20.0,
            "limit": 30
        },
        "full_scan": {
            "description": "All protocols meeting minimum criteria",
            "min_tvl": 100_000,
            "limit": 100
        }
    }
    
    def __init__(self, output_dir: Optional[str] = None, etherscan_api_key: Optional[str] = None):
        self.defillama = DeFiLlamaClient()
        if output_dir is None:
            self.output_dir = _default_contracts_dir
        else:
            self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.etherscan = None
        if EtherscanClient:
            self.etherscan = EtherscanClient(api_key=etherscan_api_key)
            print("[+] Etherscan client initialized")
        else:
            print("[!] EtherscanClient not available - source fetching disabled")
        
        self.scanner = None
        if SCANNER_AVAILABLE and PatternScanner:
            self.scanner = PatternScanner()
            print("[+] PatternScanner initialized (Slither + Pattern Matching)")
        else:
            print("[!] PatternScanner not available - vulnerability scanning disabled")
        
        self.validator = None
        if VALIDATOR_AVAILABLE and FindingValidator:
            self.validator = FindingValidator()
            print("[+] FindingValidator initialized (False Positive Filter)")
        else:
            print("[!] FindingValidator not available - all findings will be reported")
        
        (self.output_dir / "_all").mkdir(exist_ok=True)
        (self.output_dir / "🎯_critical").mkdir(exist_ok=True)
        (self.output_dir / "🎯_high").mkdir(exist_ok=True)
        (self.output_dir / "📦_archive").mkdir(exist_ok=True)
    
    async def close(self):
        """Clean up resources"""
        if hasattr(self.defillama, 'close'):
            await self.defillama.close()
        if self.etherscan and hasattr(self.etherscan, 'close'):
            await self.etherscan.close()
    
    async def hunt(
        self,
        min_tvl: float = 100_000,
        max_tvl: Optional[float] = None,
        categories: Optional[List[str]] = None,
        chains: Optional[List[str]] = None,
        exclude_audited: bool = False,
        high_risk_only: bool = False,
        growing: bool = False,
        growth_threshold: float = 10.0,
        limit: int = 50,
        analyze: bool = False,
        scan_vulnerabilities: bool = False,
        etherscan_api_key: Optional[str] = None,
        verbose: bool = True
    ) -> HuntResult:
        """
        Hunt for vulnerable contracts
        
        Args:
            min_tvl: Minimum TVL in USD
            max_tvl: Maximum TVL in USD
            categories: Filter by DeFi categories
            chains: Filter by blockchain
            exclude_audited: Only unaudited protocols
            high_risk_only: Only high-risk categories
            growing: Find fast-growing protocols
            growth_threshold: Min 7-day growth %
            limit: Maximum results
            analyze: (deprecated) use scan_vulnerabilities
            scan_vulnerabilities: Run pattern scanner on fetched contracts
            etherscan_api_key: API key for fetching contract source
            verbose: Print progress
        """
        parameters = {
            "min_tvl": min_tvl,
            "max_tvl": max_tvl,
            "categories": categories,
            "chains": chains,
            "exclude_audited": exclude_audited,
            "high_risk_only": high_risk_only,
            "growing": growing,
            "limit": limit,
            "scan_vulnerabilities": scan_vulnerabilities
        }
        
        if verbose:
            print("\n🔱 Chimera contract analysis")
            print("=" * 50)
            print(f"\n[1/5] Discovering protocols...")
        
        if growing:
            protocols = await self.defillama.find_fresh_protocols(
                min_tvl=min_tvl,
                growth_threshold=growth_threshold,
                limit=limit
            )
        else:
            protocols = await self.defillama.find_targets(
                min_tvl=min_tvl,
                max_tvl=max_tvl,
                categories=categories,
                chains=chains,
                exclude_audited=exclude_audited,
                high_risk_only=high_risk_only,
                limit=limit
            )
        
        if verbose:
            print(f"    Found {len(protocols)} protocols matching criteria")
        
        if verbose:
            print(f"\n[2/5] Fetching contract addresses (auto-discovering missing addresses)...")
        
        discovered_addresses = {}
        targets = []
        for i, protocol in enumerate(protocols):
            address = ""
            chain = protocol.chain or (protocol.chains[0] if protocol.chains else "Ethereum")
            
            if chain in ["Multi-Chain", "multi-chain", ""]:
                chain = "Ethereum"
            
            if ADDRESS_DB_AVAILABLE:
                address = get_address(protocol.slug, chain)
                if address and address == "0x0000000000000000000000000000000000000000":
                    address = ""
            
            if not address:
                try:
                    detail = await self.defillama.get_protocol_detail(protocol.slug)
                    if detail and detail.contracts:
                        all_addresses = {}
                        for contract_name, addr in detail.contracts.items():
                            if addr and isinstance(addr, str) and addr.startswith("0x") and len(addr) == 42:
                                if addr != "0x0000000000000000000000000000000000000000":
                                    chain_name = contract_name.replace("_", " ").title()
                                    if chain_name.lower() == "main":
                                        chain_name = chain
                                    all_addresses[chain_name] = addr
                        
                        if all_addresses:
                            discovered_addresses[protocol.slug] = all_addresses
                            if "main" in detail.contracts or chain in all_addresses:
                                address = all_addresses.get(chain) or all_addresses.get("main") or list(all_addresses.values())[0]
                            else:
                                address = list(all_addresses.values())[0]
                                chain = list(all_addresses.keys())[0]
                except Exception as e:
                    if verbose:
                        pass
            
            if not address and protocol.chains and len(protocol.chains) > 1:
                for alt_chain in protocol.chains[:3]:
                    if alt_chain == chain or alt_chain in ["Multi-Chain", "multi-chain", ""]:
                        continue
                    try:
                        if ADDRESS_DB_AVAILABLE:
                            alt_address = get_address(protocol.slug, alt_chain)
                            if alt_address and alt_address != "0x0000000000000000000000000000000000000000":
                                address = alt_address
                                chain = alt_chain
                                break
                    except:
                        pass
            
            if address and protocol.slug in discovered_addresses and ADDRESS_DB_AVAILABLE:
                PROTOCOL_ADDRESSES[protocol.slug] = discovered_addresses[protocol.slug]
            
            target = ContractTarget(
                address=address,
                chain=chain,
                protocol_name=protocol.name,
                protocol_slug=protocol.slug,
                tvl=protocol.tvl or 0,
                category=protocol.category or "",
                is_audited=protocol.is_audited
            )
            targets.append(target)
            
            if verbose and (i + 1) % 10 == 0:
                found = sum(1 for t in targets if t.address)
                print(f"    Processed {i+1}/{len(protocols)}, found {found} addresses")
        
        if verbose:
            found = sum(1 for t in targets if t.address)
            print(f"    Created {len(targets)} targets ({found} with addresses)")
        
        if verbose:
            print(f"\n[3/5] Generating verdicts...")
        
        for target in targets:
            target.verdicts = self._generate_verdicts(target)
            target.priority_score = self._calculate_priority(target)
        
        if verbose:
            print(f"\n[4/5] Prioritizing targets...")
        
        targets.sort(key=lambda x: x.priority_score, reverse=True)
        
        vulnerabilities_found = 0
        if scan_vulnerabilities and self.scanner:
            if verbose:
                print(f"\n[5/5] Scanning for vulnerabilities...")
            
            if etherscan_api_key:
                if not self.etherscan:
                    try:
                        from fetchers.etherscan_fetcher import EtherscanClient
                    except ImportError:
                        try:
                            from src.fetchers.etherscan_fetcher import EtherscanClient
                        except ImportError:
                            from ..fetchers.etherscan_fetcher import EtherscanClient
                    
                    fetcher = EtherscanClient(api_key=etherscan_api_key)
                else:
                    fetcher = self.etherscan
                
                scan_count = min(20, len(targets))
                for i, target in enumerate(targets[:scan_count]):
                    if verbose:
                        print(f"   [{i+1}/{scan_count}] Scanning {target.protocol_name}...")
                    
                    if target.address:
                        try:
                            network = normalize_chain_name(target.chain)
                            source = await fetcher.get_contract_source(target.address, network)
                            if source:
                                target.source_code = source.source_code
                                target.source_fetched = True
                                
                                findings = await self.scanner.scan(source.source_code, target.protocol_name)
                                
                                if self.validator and findings:
                                    findings_dicts = [f.to_dict() for f in findings]
                                    validation_result = self.validator.validate_findings(
                                        findings_dicts,
                                        source.source_code
                                    )
                                    
                                    validated_findings = []
                                    for vf in validation_result.confirmed + validation_result.needs_review:
                                        finding_dict = vf.original_finding.copy()
                                        finding_dict['_validation'] = {
                                            'status': vf.status.value,
                                            'reason': vf.reason
                                        }
                                        validated_findings.append(finding_dict)
                                    
                                    target.vulnerabilities = validated_findings
                                    target.validation_stats = {
                                        "original_count": len(findings),
                                        "validated_count": len(validated_findings),
                                        "eliminated": len(validation_result.false_positives) + len(validation_result.likely_false_positives),
                                        "elimination_rate": validation_result.elimination_rate
                                    }
                                    
                                    vulnerabilities_found += len(validated_findings)
                                    
                                    if verbose and target.validation_stats["eliminated"] > 0:
                                        print(f"      🔍 Validated: {len(findings)} → {len(validated_findings)} (filtered {target.validation_stats['eliminated']} false positives)")
                                else:
                                    target.vulnerabilities = [f.to_dict() for f in findings]
                                    vulnerabilities_found += len(findings)
                                
                                target.analysis_complete = True
                                
                                critical_high = sum(1 for f in target.vulnerabilities if f.get('severity') in ["Critical", "High"])
                                if critical_high > 0:
                                    target.priority_score = min(100, target.priority_score + critical_high * 5)
                                
                                if critical_high > 0:
                                    target.verdicts.insert(0, {
                                        "title": "CRITICAL VULNERABILITIES FOUND" if any(f.get('severity') == "Critical" for f in target.vulnerabilities) else "HIGH VULNERABILITIES FOUND",
                                        "severity": "CRITICAL" if any(f.get('severity') == "Critical" for f in target.vulnerabilities) else "HIGH",
                                        "category": "SECURITY",
                                        "description": f"Found {len(target.vulnerabilities)} validated vulnerabilities ({critical_high} critical/high)",
                                    })
                                
                                if verbose and target.vulnerabilities:
                                    print(f"      Found {len(target.vulnerabilities)} validated issues")
                        except Exception as e:
                            if verbose:
                                print(f"      [!] Error: {e}")
            else:
                if verbose:
                    print("   [!] No Etherscan API key - skipping vulnerability scan")
                    print("   [!] Pass etherscan_api_key parameter to enable")
        
        high_priority = [t for t in targets if t.priority_score >= 60]
        
        if verbose:
            print(f"\n{'=' * 50}")
            print(f"📊 Hunt Complete!")
            print(f"   Protocols discovered: {len(protocols)}")
            print(f"   High priority targets: {len(high_priority)}")
            total_tvl = sum((t.tvl or 0) for t in targets)
            print(f"   Total TVL at risk: ${total_tvl:,.0f}")
            if scan_vulnerabilities:
                print(f"   Vulnerabilities found: {vulnerabilities_found}")
        
        result = HuntResult(
            timestamp=datetime.now(),
            parameters=parameters,
            protocols_discovered=len(protocols),
            contracts_found=len(targets),
            contracts_analyzed=sum(1 for t in targets if t.analysis_complete),
            vulnerabilities_found=vulnerabilities_found,
            targets=targets,
            high_priority=high_priority
        )
        
        return result
    
    def save_reports(
        self,
        hunt_result: 'HuntResult',
        output_dir: Optional[str] = None
    ) -> Dict[str, Path]:
        """
        Save hunt results as organized reports and directories.
        
        Args:
            hunt_result: HuntResult from hunt()
            output_dir: Override output directory
            
        Returns:
            Dict with paths to generated files
        """
        if not REPORTS_AVAILABLE:
            print("[!] ReportGenerator not available")
            return {}
        
        out_dir = output_dir or str(self.output_dir)
        generator = ReportGenerator(out_dir)
        
        paths = {"protocols": [], "summary": None}
        protocols_scanned = []
        
        for target in hunt_result.targets:
            if target.analysis_complete:
                report = ProtocolReport(
                    protocol_name=target.protocol_name,
                    protocol_slug=target.protocol_slug,
                    address=target.address,
                    chain=target.chain,
                    category=target.category,
                    tvl=target.tvl or 0,
                    is_audited=target.is_audited,
                    priority_score=target.priority_score,
                    verdicts=target.verdicts,
                    vulnerabilities=target.vulnerabilities or [],
                    source_code=target.source_code,
                )
                
                path = generator.save_protocol_report(report)
                paths["protocols"].append(path)
                protocols_scanned.append(report)
                print(f"   📁 Saved: {path}")
        
        if protocols_scanned:
            hunt_dict = {
                "protocols_discovered": hunt_result.protocols_discovered,
                "contracts_found": hunt_result.contracts_found,
            }
            summary_path = generator.generate_hunt_summary(hunt_dict, protocols_scanned)
            paths["summary"] = summary_path
            print(f"   📊 Summary: {summary_path}")
        
        return paths
    
    def categorize_hunt_results(self, hunt_results_path: str) -> Dict[str, List[str]]:
        """
        Categorize contracts from hunt results into archetypes.
        
        Args:
            hunt_results_path: Path to hunt_*.json file
            
        Returns:
            Dict mapping contract slugs to their categories
        """
        if not CATEGORIZER_AVAILABLE:
            return {}
        
        try:
            categorizer = ContractCategorizer(str(self.output_dir))
            return categorizer.categorize_from_hunt_results(hunt_results_path)
        except Exception as e:
            print(f"    [!] Categorization failed: {e}")
            return {}
    
    async def hunt_preset(self, preset_name: str, verbose: bool = True) -> HuntResult:
        """
        Run a preset hunt
        
        Args:
            preset_name: One of the PRESETS keys
            verbose: Print progress
        """
        if preset_name not in self.PRESETS:
            available = ", ".join(self.PRESETS.keys())
            raise ValueError(f"Unknown preset: {preset_name}. Available: {available}")
        
        preset = self.PRESETS[preset_name]
        
        if verbose:
            print(f"\n🎯 Running preset: {preset_name}")
            print(f"   {preset['description']}")
        
        return await self.hunt(
            min_tvl=preset.get("min_tvl", 100_000),
            max_tvl=preset.get("max_tvl"),
            categories=preset.get("categories"),
            chains=preset.get("chains"),
            exclude_audited=preset.get("exclude_audited", False),
            high_risk_only=preset.get("high_risk_only", False),
            growing=preset.get("growing", False),
            growth_threshold=preset.get("growth_threshold", 10.0),
            limit=preset.get("limit", 50),
            verbose=verbose
        )
    
    def _generate_verdicts(self, target: ContractTarget) -> List[Dict]:
        """Generate verdicts for a target (mirrors Gargophias verdict system)"""
        verdicts = []
        
        tvl = target.tvl if target.tvl is not None else 0
        
        if not target.is_audited:
            if tvl > 1_000_000:
                verdicts.append({
                    "title": "UNAUDITED HIGH-TVL PROTOCOL",
                    "severity": "CRITICAL",
                    "category": "TRUST",
                    "description": f"Protocol has ${tvl:,.0f} TVL without documented audit",
                    "evidence": ["No audit links found", f"TVL: ${tvl:,.0f}"],
                    "action": "Priority target for vulnerability analysis"
                })
            else:
                verdicts.append({
                    "title": "UNAUDITED PROTOCOL",
                    "severity": "HIGH",
                    "category": "TRUST",
                    "description": "Protocol has no documented security audit",
                    "evidence": ["No audit links in DeFiLlama"],
                    "action": "Review for common vulnerabilities"
                })
        
        high_risk_categories = {
            "Bridge": ("BRIDGE PROTOCOL", "CRITICAL", "Bridge exploits historically cause massive losses"),
            "Cross Chain": ("CROSS-CHAIN PROTOCOL", "CRITICAL", "Complex attack surface across chains"),
            "Lending": ("LENDING PROTOCOL", "HIGH", "Flash loan and liquidation attack vectors"),
            "Leveraged Farming": ("LEVERAGED PROTOCOL", "HIGH", "Complex leverage mechanics"),
            "Yield Aggregator": ("YIELD AGGREGATOR", "HIGH", "Composability risks from multiple protocols"),
        }
        
        if target.category in high_risk_categories:
            title, severity, desc = high_risk_categories[target.category]
            verdicts.append({
                "title": title,
                "severity": severity,
                "category": "EXPOSURE",
                "description": desc,
                "evidence": [f"Category: {target.category}"],
                "action": "Analyze for category-specific vulnerabilities"
            })
        
        if tvl > 10_000_000:
            verdicts.append({
                "title": "VERY HIGH TVL TARGET",
                "severity": "INFO",
                "category": "INTEL",
                "description": f"Protocol holds over $10M in TVL",
                "evidence": [f"TVL: ${tvl:,.0f}"],
                "action": "High-value target if vulnerable"
            })
        
        return verdicts
    
    def _calculate_priority(self, target: ContractTarget) -> int:
        """
        Calculate priority score (0-100) for a target
        
        Mirrors Gargophias's scoring system:
        - Severity score (0-40): Based on verdicts
        - Exposure score (0-30): Based on TVL
        - Exploitability score (0-20): Based on category
        - Freshness score (0-10): Based on data recency
        """
        score = 0
        
        tvl = target.tvl if target.tvl is not None else 0
        
        severity_weights = {"CRITICAL": 40, "HIGH": 30, "MEDIUM": 20, "LOW": 10, "INFO": 5}
        max_severity = 0
        for verdict in target.verdicts:
            weight = severity_weights.get(verdict.get("severity", ""), 0)
            if weight > max_severity:
                max_severity = weight
        score += max_severity
        
        if tvl > 10_000_000:
            score += 30
        elif tvl > 1_000_000:
            score += 25
        elif tvl > 500_000:
            score += 20
        elif tvl > 100_000:
            score += 15
        else:
            score += 10
        
        high_exploit_categories = ["Bridge", "Cross Chain", "Lending", "Leveraged Farming"]
        medium_exploit_categories = ["DEX", "Yield Aggregator", "CDP"]
        
        if target.category in high_exploit_categories:
            score += 20
        elif target.category in medium_exploit_categories:
            score += 15
        else:
            score += 10
        
        if target.is_audited:
            score -= 20
        
        return max(0, min(100, score))
    
    def save_results(self, result: HuntResult, filename: Optional[str] = None):
        """Save hunt results to file"""
        if filename is None:
            filename = f"hunt_{result.timestamp.strftime('%Y%m%d_%H%M%S')}.json"
        
        output_path = self.output_dir / filename
        
        with open(output_path, 'w') as f:
            json.dump(result.to_dict(), f, indent=2)
        
        print(f"\n💾 Results saved to: {output_path}")
        return output_path
    
    def format_target_summary(self, target: ContractTarget) -> str:
        """Format a target for display"""
        audit_icon = "✅" if target.is_audited else "❌"
        tvl = target.tvl if target.tvl is not None else 0
        tvl_str = f"${tvl:,.0f}"
        
        lines = [
            f"📊 {target.protocol_name}",
            f"   Category: {target.category or 'Unknown'}",
            f"   Chain: {target.chain or 'Unknown'}",
            f"   TVL: {tvl_str}",
            f"   Audit: {audit_icon}",
            f"   Priority Score: {target.priority_score}/100"
        ]
        
        if target.verdicts:
            lines.append("   Verdicts:")
            for v in target.verdicts[:3]:
                severity_icons = {
                    "CRITICAL": "🚨",
                    "HIGH": "⚠️",
                    "MEDIUM": "⚡",
                    "LOW": "📌",
                    "INFO": "ℹ️"
                }
                icon = severity_icons.get(v.get("severity", ""), "•")
                lines.append(f"      {icon} {v.get('title', 'Unknown')}")
        
        if target.vulnerabilities:
            lines.append(f"   🔍 Vulnerabilities Found: {len(target.vulnerabilities)}")
            for vuln in target.vulnerabilities[:3]:
                sev = vuln.get('severity', 'Unknown')
                title = vuln.get('title', 'Unknown')
                validation = vuln.get('_validation', {})
                status = validation.get('status', '')
                status_icon = "✅" if status == "CONFIRMED" else "🔍" if status == "NEEDS_REVIEW" else ""
                lines.append(f"      • [{sev}] {title} {status_icon}")
        
        if target.validation_stats:
            stats = target.validation_stats
            lines.append(f"   📊 Validation: {stats['original_count']} raw → {stats['validated_count']} validated ({stats['elimination_rate']:.0f}% filtered)")
        
        return "\n".join(lines)
    
    async def scan_contract_source(
        self,
        source_code: str,
        contract_name: Optional[str] = None
    ) -> List[Dict]:
        """
        Scan contract source code for vulnerabilities using PatternScanner
        
        Args:
            source_code: Solidity source code
            contract_name: Optional name for reporting
            
        Returns:
            List of vulnerability findings as dicts
        """
        if not self.scanner:
            print("[!] Scanner not available")
            return []
        
        findings = await self.scanner.scan(source_code, contract_name)
        findings_dicts = [f.to_dict() for f in findings]
        
        if self.validator and findings_dicts:
            validation_result = self.validator.validate_findings(findings_dicts, source_code)
            
            validated = []
            for vf in validation_result.confirmed + validation_result.needs_review:
                finding_dict = vf.original_finding.copy()
                finding_dict['_validation'] = {
                    'status': vf.status.value,
                    'reason': vf.reason
                }
                validated.append(finding_dict)
            
            return validated
        
        return findings_dicts
    
    async def scan_contract_file(self, file_path: str) -> List[Dict]:
        """
        Scan a Solidity file for vulnerabilities
        
        Args:
            file_path: Path to .sol file
            
        Returns:
            List of vulnerability findings as dicts
        """
        if not self.scanner:
            print("[!] Scanner not available")
            return []
        
        findings = await self.scanner.scan_file(file_path)
        findings_dicts = [f.to_dict() for f in findings]
        
        if self.validator and findings_dicts:
            try:
                with open(file_path, 'r') as f:
                    source_code = f.read()
                
                validation_result = self.validator.validate_findings(findings_dicts, source_code)
                
                validated = []
                for vf in validation_result.confirmed + validation_result.needs_review:
                    finding_dict = vf.original_finding.copy()
                    finding_dict['_validation'] = {
                        'status': vf.status.value,
                        'reason': vf.reason
                    }
                    validated.append(finding_dict)
                
                return validated
            except Exception:
                pass
        
        return findings_dicts
    
    async def fetch_and_scan_contract(
        self,
        address: str,
        chain: str = "ethereum",
        save_source: bool = True
    ) -> Dict[str, Any]:
        """
        Fetch contract source from Etherscan and scan for vulnerabilities
        
        Args:
            address: Contract address
            chain: Chain name (ethereum, polygon, arbitrum, etc.)
            save_source: Whether to save source code to disk
            
        Returns:
            Dict with source info and vulnerability findings
        """
        result = {
            "address": address,
            "chain": chain,
            "source_fetched": False,
            "contract_name": None,
            "source_code": None,
            "vulnerabilities": [],
            "scan_completed": False,
            "error": None,
            "validation": None
        }
        
        network = normalize_chain_name(chain)
        
        if not self.etherscan:
            result["error"] = "Etherscan client not available"
            return result
        
        print(f"[1/2] Fetching source for {address[:10]}... on {network}")
        
        source = await self.etherscan.get_contract_source(address, network)
        
        if not source:
            result["error"] = "Contract not verified or fetch failed"
            return result
        
        result["source_fetched"] = True
        result["contract_name"] = source.name
        result["source_code"] = source.source_code
        result["compiler_version"] = source.compiler_version
        result["is_proxy"] = source.is_proxy
        
        if source.is_proxy and source.implementation:
            print(f"    → Proxy detected, fetching implementation: {source.implementation[:10]}...")
            impl_source = await self.etherscan.get_contract_source(source.implementation, network)
            if impl_source:
                result["implementation_address"] = source.implementation
                result["implementation_name"] = impl_source.name
                source = impl_source
        
        if save_source:
            source_dir = self.output_dir / "_all" / address[:16]
            source_dir.mkdir(parents=True, exist_ok=True)
            
            source_file = source_dir / f"{source.name}.sol"
            source_file.write_text(source.source_code)
            result["source_file"] = str(source_file)
        
        if not self.scanner:
            result["error"] = "Scanner not available"
            return result
        
        print(f"[2/2] Scanning {source.name} for vulnerabilities...")
        
        findings = await self.scanner.scan(source.source_code, source.name)
        
        if self.validator and findings:
            findings_dicts = [f.to_dict() for f in findings]
            validation_result = self.validator.validate_findings(
                findings_dicts,
                source.source_code
            )
            
            validated_findings = []
            for vf in validation_result.confirmed + validation_result.needs_review:
                finding_dict = vf.original_finding.copy()
                finding_dict['_validation'] = {
                    'status': vf.status.value,
                    'reason': vf.reason
                }
                validated_findings.append(finding_dict)
            
            result["vulnerabilities"] = validated_findings
            result["validation"] = {
                "original_count": len(findings),
                "validated_count": len(validated_findings),
                "eliminated": len(validation_result.false_positives) + len(validation_result.likely_false_positives),
                "elimination_rate": validation_result.elimination_rate
            }
            
            if result["validation"]["eliminated"] > 0:
                print(f"    🔍 Validated: {len(findings)} → {len(validated_findings)} findings (filtered {result['validation']['eliminated']} false positives)")
            
            result["vulnerability_count"] = len(validated_findings)
            
            severity_counts = {}
            for f in validated_findings:
                sev = f.get('severity', 'Unknown')
                severity_counts[sev] = severity_counts.get(sev, 0) + 1
            result["severity_counts"] = severity_counts
        else:
            result["vulnerabilities"] = [f.to_dict() for f in findings]
            result["vulnerability_count"] = len(findings)
            
            severity_counts = {}
            for f in findings:
                sev = f.severity.value
                severity_counts[sev] = severity_counts.get(sev, 0) + 1
            result["severity_counts"] = severity_counts
        
        result["scan_completed"] = True
        
        if severity_counts.get("Critical", 0) > 0:
            result["risk_level"] = "CRITICAL"
        elif severity_counts.get("High", 0) > 0:
            result["risk_level"] = "HIGH"
        elif severity_counts.get("Medium", 0) > 0:
            result["risk_level"] = "MEDIUM"
        elif severity_counts.get("Low", 0) > 0:
            result["risk_level"] = "LOW"
        else:
            result["risk_level"] = "NONE"
        
        return result
    
    async def hunt_and_scan(
        self,
        min_tvl: float = 100_000,
        max_tvl: Optional[float] = None,
        categories: Optional[List[str]] = None,
        chains: Optional[List[str]] = None,
        exclude_audited: bool = False,
        limit: int = 20,
        scan_limit: int = 10,
        verbose: bool = True
    ) -> HuntResult:
        """
        Hunt for protocols AND scan their contracts for vulnerabilities
        
        This is the full pipeline:
        1. Discover protocols from DeFiLlama
        2. For top targets, fetch contract source from Etherscan
        3. Scan each contract with PatternScanner + Slither
        4. VALIDATE findings to filter false positives  ← NEW
        5. Generate comprehensive results
        
        Args:
            min_tvl: Minimum TVL filter
            max_tvl: Maximum TVL filter
            categories: Category filter
            chains: Chain filter (also used for Etherscan)
            exclude_audited: Only unaudited protocols
            limit: Max protocols to discover
            scan_limit: Max contracts to actually scan (subset of limit)
            verbose: Print progress
            
        Returns:
            HuntResult with vulnerability findings
        """
        if verbose:
            print("\n🔱 Chimera contract analysis + scanner")
            print("=" * 50)
        
        result = await self.hunt(
            min_tvl=min_tvl,
            max_tvl=max_tvl,
            categories=categories,
            chains=chains,
            exclude_audited=exclude_audited,
            limit=limit,
            verbose=verbose
        )
        
        if not result.targets:
            if verbose:
                print("\n❌ No targets found to scan")
            return result
        
        if verbose:
            print(f"\n[5/5] Scanning top {scan_limit} targets for vulnerabilities...")
            print("-" * 50)
        
        targets_to_scan = result.high_priority[:scan_limit] if result.high_priority else result.targets[:scan_limit]
        
        scanned_count = 0
        vuln_count = 0
        total_eliminated = 0
        total_original = 0
        
        for i, target in enumerate(targets_to_scan):
            if verbose:
                print(f"\n[{i+1}/{len(targets_to_scan)}] {target.protocol_name}")
            
            if not target.address:
                if verbose:
                    print(f"    ⏭️ No contract address available (DeFiLlama doesn't provide addresses for all protocols)")
                continue
            
            chain = target.chain or "ethereum"
            
            scan_result = await self.fetch_and_scan_contract(
                address=target.address,
                chain=chain,
                save_source=True
            )
            
            if scan_result["scan_completed"]:
                scanned_count += 1
                target.source_fetched = True
                target.source_code = scan_result.get("source_code")
                target.vulnerabilities = scan_result.get("vulnerabilities", [])
                target.analysis_complete = True
                
                if scan_result.get("validation"):
                    target.validation_stats = scan_result["validation"]
                    total_original += scan_result["validation"]["original_count"]
                    total_eliminated += scan_result["validation"]["eliminated"]
                
                vuln_count += scan_result.get("vulnerability_count", 0)
                
                if scan_result.get("risk_level") == "CRITICAL":
                    target.verdicts.insert(0, {
                        "title": "CRITICAL VULNERABILITIES FOUND",
                        "severity": "CRITICAL",
                        "category": "VULNERABILITY",
                        "description": f"Scanner found {scan_result.get('severity_counts', {}).get('Critical', 0)} critical issues",
                        "evidence": [v.get("title") for v in target.vulnerabilities[:3]],
                        "action": "Immediate review required"
                    })
                    target.priority_score = min(100, target.priority_score + 20)
                
                if verbose:
                    risk = scan_result.get("risk_level", "UNKNOWN")
                    count = scan_result.get("vulnerability_count", 0)
                    print(f"    ✅ Scanned: {count} findings ({risk} risk)")
            else:
                if verbose:
                    error = scan_result.get("error", "Unknown error")
                    print(f"    ❌ Failed: {error}")
        
        result.contracts_analyzed = scanned_count
        result.vulnerabilities_found = vuln_count
        
        if total_original > 0:
            result.validation_summary = {
                "total_original_findings": total_original,
                "total_validated_findings": vuln_count,
                "total_eliminated": total_eliminated,
                "global_elimination_rate": (total_eliminated / total_original * 100) if total_original > 0 else 0
            }
        
        result.targets.sort(key=lambda x: x.priority_score, reverse=True)
        result.high_priority = [t for t in result.targets if t.priority_score >= 60]
        
        if verbose:
            print(f"\n{'=' * 50}")
            print(f"📊 Scan Complete!")
            print(f"   Contracts scanned: {scanned_count}")
            print(f"   Vulnerabilities found: {vuln_count}")
            if result.validation_summary:
                print(f"   🔍 Validation: {total_original} raw → {vuln_count} validated ({result.validation_summary['global_elimination_rate']:.1f}% filtered)")
        
        return result
    
    def print_results(self, result: HuntResult, show_all: bool = False):
        """Print hunt results in a formatted way"""
        print("\n" + "=" * 60)
        print("🔱 HUNT RESULTS")
        print("=" * 60)
        
        print(f"\n📊 Summary:")
        print(f"   Protocols discovered: {result.protocols_discovered}")
        print(f"   High priority targets: {len(result.high_priority)}")
        
        total_tvl = sum((t.tvl or 0) for t in result.targets)
        print(f"   Total TVL tracked: ${total_tvl:,.0f}")
        
        unaudited = sum(1 for t in result.targets if not t.is_audited)
        print(f"   Unaudited protocols: {unaudited}")
        
        if result.validation_summary:
            vs = result.validation_summary
            print(f"\n🔍 Validation Summary:")
            print(f"   Raw findings: {vs['total_original_findings']}")
            print(f"   After validation: {vs['total_validated_findings']}")
            print(f"   False positives filtered: {vs['total_eliminated']} ({vs['global_elimination_rate']:.1f}%)")
        
        if result.high_priority:
            print(f"\n🎯 High Priority Targets (score >= 60):")
            print("-" * 50)
            
            targets_to_show = result.high_priority if show_all else result.high_priority[:10]
            for i, target in enumerate(targets_to_show, 1):
                print(f"\n[{i}] {self.format_target_summary(target)}")
            
            if not show_all and len(result.high_priority) > 10:
                print(f"\n   ... and {len(result.high_priority) - 10} more high priority targets")
        
        print(f"\n📈 Category Breakdown:")
        categories = {}
        for t in result.targets:
            cat = t.category or "Unknown"
            categories[cat] = categories.get(cat, 0) + 1
        
        for cat, count in sorted(categories.items(), key=lambda x: x[1], reverse=True)[:10]:
            print(f"   {cat}: {count}")


async def main():
    """CLI interface"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Chimera contract analysis")
    parser.add_argument("--preset", type=str, help="Run a preset hunt")
    parser.add_argument("--list-presets", action="store_true", help="List available presets")
    parser.add_argument("--min-tvl", type=float, default=100_000)
    parser.add_argument("--max-tvl", type=float)
    parser.add_argument("--category", type=str)
    parser.add_argument("--chain", type=str)
    parser.add_argument("--unaudited", action="store_true")
    parser.add_argument("--high-risk", action="store_true")
    parser.add_argument("--growing", action="store_true")
    parser.add_argument("--limit", type=int, default=30)
    parser.add_argument("--save", action="store_true", help="Save results to file")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    
    args = parser.parse_args()
    
    hunter = ContractHunter()
    
    if args.list_presets:
        print("\n🎯 Available Hunt Presets:")
        print("-" * 40)
        for name, config in hunter.PRESETS.items():
            print(f"\n  {name}:")
            print(f"    {config['description']}")
        return
    
    if args.preset:
        result = await hunter.hunt_preset(args.preset)
    else:
        result = await hunter.hunt(
            min_tvl=args.min_tvl,
            max_tvl=args.max_tvl,
            categories=[args.category] if args.category else None,
            chains=[args.chain] if args.chain else None,
            exclude_audited=args.unaudited,
            high_risk_only=args.high_risk,
            growing=args.growing,
            limit=args.limit
        )
    
    if args.json:
        print(json.dumps(result.to_dict(), indent=2))
    else:
        hunter.print_results(result)
    
    if args.save:
        hunter.save_results(result)


if __name__ == "__main__":
    asyncio.run(main())
