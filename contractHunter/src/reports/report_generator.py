"""
Chimera contract analysis — report generator.

Generates structured reports and organizes scan results into directories.

Directory Structure:
    contracts/
    ├── _all/                       # Single source of truth
    │   └── {protocol_slug}/
    │       ├── profile.json        # Complete protocol data (metadata + vulnerabilities + verdicts)
    │       ├── summary.txt         # Human-readable summary (like walletHunter)
    │       ├── source.sol          # Contract source code
    │       ├── scan_results.json  # Vulnerability findings (structured)
    │       └── report.md          # Detailed markdown report
    │
    ├── 🎯_prime_targets/           # Symlinks (high TVL + vulns + unaudited)
    ├── 🎯_critical_vulns/         # Symlinks (CRITICAL findings)
    ├── ⚠️_high_vulns/             # Symlinks (HIGH findings)
    ├── 🌉_bridges/                # Symlinks (bridge protocols)
    ├── 🏦_lending/                # Symlinks (lending protocols)
    ├── 🔀_dex/                     # Symlinks (DEX protocols)
    ├── 🥩_staking/                 # Symlinks (staking protocols)
    ├── 💰_high_tvl_unaudited/     # Symlinks (>$100M unaudited)
    └── ... (other category folders)
    │
    └── reports/
        └── hunt_{timestamp}.md     # Summary report per hunt
"""

import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Any
from dataclasses import dataclass


@dataclass
class VulnerabilityFinding:
    """A single vulnerability finding"""
    detector: str
    vulnerability_type: str
    severity: str
    confidence: float
    title: str
    description: str
    locations: List[str]
    recommendation: str
    source: str


@dataclass 
class ProtocolReport:
    """Complete report for a protocol"""
    protocol_name: str
    protocol_slug: str
    address: str
    chain: str
    category: str
    tvl: float
    is_audited: bool
    priority_score: int
    verdicts: List[Dict]
    vulnerabilities: List[Dict]
    source_code: Optional[str] = None
    scanned_at: str = ""
    
    def __post_init__(self):
        if not self.scanned_at:
            self.scanned_at = datetime.now().isoformat()


class ReportGenerator:
    """
    Generates reports and organizes results into directories.
    """
    
    def __init__(self, output_dir: Optional[str] = None):
        if output_dir is None:
            current_file = Path(__file__).resolve()
            src_dir = current_file.parent.parent
            root_dir = src_dir.parent
            chimera_root = root_dir.parent if root_dir.name == "contractHunter" else root_dir
            self.output_dir = chimera_root / "Contracts"
        else:
            self.output_dir = Path(output_dir)
        self._setup_directories()
    
    def _setup_directories(self):
        """Create directory structure"""
        dirs = [
            self.output_dir / "_all",
            self.output_dir / "🎯_critical",
            self.output_dir / "🎯_high",
            self.output_dir / "📦_archive",
            self.output_dir / "reports",
        ]
        for d in dirs:
            d.mkdir(parents=True, exist_ok=True)
    
    def save_protocol_report(
        self,
        report: ProtocolReport,
        create_symlinks: bool = True
    ) -> Path:
        """
        Save a complete protocol report to disk.
        
        Args:
            report: ProtocolReport object
            create_symlinks: Whether to create symlinks in priority folders
            
        Returns:
            Path to the protocol directory
        """
        slug = self._sanitize_slug(report.protocol_slug)
        protocol_dir = self.output_dir / "_all" / slug
        protocol_dir.mkdir(parents=True, exist_ok=True)
        
        profile = {
            "protocol_name": report.protocol_name,
            "protocol_slug": report.protocol_slug,
            "address": report.address,
            "chain": report.chain,
            "category": report.category,
            "tvl": report.tvl,
            "tvl_formatted": f"${report.tvl:,.0f}",
            "is_audited": report.is_audited,
            "priority_score": report.priority_score,
            "scanned_at": report.scanned_at,
            "verdicts": report.verdicts,
            "vulnerabilities": report.vulnerabilities,
            "vulnerability_summary": {
                "total": len(report.vulnerabilities),
                "critical": sum(1 for v in report.vulnerabilities if v.get("severity", "").upper() == "CRITICAL"),
                "high": sum(1 for v in report.vulnerabilities if v.get("severity", "").upper() == "HIGH"),
                "medium": sum(1 for v in report.vulnerabilities if v.get("severity", "").upper() == "MEDIUM"),
                "low": sum(1 for v in report.vulnerabilities if v.get("severity", "").upper() == "LOW"),
                "info": sum(1 for v in report.vulnerabilities if v.get("severity", "").upper() == "INFORMATIONAL"),
            },
            "has_source_code": report.source_code is not None,
        }
        with open(protocol_dir / "profile.json", "w") as f:
            json.dump(profile, f, indent=2)
        
        if report.source_code:
            with open(protocol_dir / "source.sol", "w") as f:
                f.write(report.source_code)
        
        scan_results = {
            "protocol_slug": report.protocol_slug,
            "scanned_at": report.scanned_at,
            "priority_score": report.priority_score,
            "verdicts": report.verdicts,
            "vulnerabilities": report.vulnerabilities,
            "summary": {
                "total": len(report.vulnerabilities),
                "critical": sum(1 for v in report.vulnerabilities if v.get("severity", "").upper() == "CRITICAL"),
                "high": sum(1 for v in report.vulnerabilities if v.get("severity", "").upper() == "HIGH"),
                "medium": sum(1 for v in report.vulnerabilities if v.get("severity", "").upper() == "MEDIUM"),
                "low": sum(1 for v in report.vulnerabilities if v.get("severity", "").upper() == "LOW"),
                "info": sum(1 for v in report.vulnerabilities if v.get("severity", "").upper() == "INFORMATIONAL"),
            }
        }
        with open(protocol_dir / "scan_results.json", "w") as f:
            json.dump(scan_results, f, indent=2)
        
        md_report = self._generate_markdown_report(report)
        with open(protocol_dir / "report.md", "w") as f:
            f.write(md_report)
        
        try:
            from .enhanced_report_generator import generate_enhanced_report
            source_code = report.source_code or ""
            generate_enhanced_report(
                protocol_data=profile,
                findings=report.vulnerabilities,
                source_code=source_code,
                output_dir=str(protocol_dir),
            )
        except Exception as e:
            summary_txt = self._generate_summary_text(report)
            with open(protocol_dir / "summary.txt", "w", encoding="utf-8") as f:
                f.write(summary_txt)
        
        if create_symlinks:
            self._create_priority_symlinks(report, protocol_dir)
        
        return protocol_dir
    
    def _generate_markdown_report(self, report: ProtocolReport) -> str:
        """Generate a human-readable markdown report"""
        lines = []
        
        lines.append(f"# 🔱 Contract security assessment: {report.protocol_name}")
        lines.append("")
        lines.append(f"> Generated: {report.scanned_at}")
        lines.append("")
        
        lines.append("## Protocol Overview")
        lines.append("")
        lines.append(f"| Property | Value |")
        lines.append(f"|----------|-------|")
        lines.append(f"| **Name** | {report.protocol_name} |")
        lines.append(f"| **Address** | `{report.address}` |")
        lines.append(f"| **Chain** | {report.chain} |")
        lines.append(f"| **Category** | {report.category} |")
        lines.append(f"| **TVL** | ${report.tvl:,.0f} |")
        lines.append(f"| **Audit Status** | {'✅ Audited' if report.is_audited else '❌ Unaudited'} |")
        lines.append(f"| **Priority Score** | **{report.priority_score}/100** |")
        lines.append("")
        
        if report.verdicts:
            lines.append("## Verdicts")
            lines.append("")
            for v in report.verdicts:
                severity = v.get("severity", "INFO")
                icon = {"CRITICAL": "🚨", "HIGH": "⚠️", "MEDIUM": "⚡", "LOW": "📌", "INFO": "ℹ️"}.get(severity, "•")
                lines.append(f"- {icon} **{v.get('title', 'Unknown')}** ({severity})")
                if v.get("description"):
                    lines.append(f"  - {v.get('description')}")
            lines.append("")
        
        vulns = report.vulnerabilities
        critical = []
        high = []
        medium = []
        low = []
        info = []
        
        if vulns:
            critical = [v for v in vulns if v.get("severity") == "Critical"]
            high = [v for v in vulns if v.get("severity") == "High"]
            medium = [v for v in vulns if v.get("severity") == "Medium"]
            low = [v for v in vulns if v.get("severity") == "Low"]
            info = [v for v in vulns if v.get("severity") == "Informational"]
            
            lines.append(f"## Vulnerabilities Found ({len(vulns)})")
            lines.append("")
            lines.append("| Severity | Count |")
            lines.append("|----------|-------|")
            lines.append(f"| 🚨 Critical | {len(critical)} |")
            lines.append(f"| ⚠️ High | {len(high)} |")
            lines.append(f"| ⚡ Medium | {len(medium)} |")
            lines.append(f"| 📌 Low | {len(low)} |")
            lines.append(f"| ℹ️ Info | {len(info)} |")
            lines.append("")
            
            if critical:
                lines.append("### 🚨 Critical Findings")
                lines.append("")
                for i, v in enumerate(critical, 1):
                    lines.append(f"#### {i}. {v.get('title', 'Unknown')}")
                    lines.append("")
                    lines.append(f"- **Detector**: {v.get('detector', 'N/A')}")
                    lines.append(f"- **Confidence**: {v.get('confidence', 0):.0%}")
                    lines.append(f"- **Source**: {v.get('source', 'N/A')}")
                    if v.get("locations"):
                        lines.append(f"- **Locations**: {', '.join(v.get('locations', []))}")
                    lines.append("")
                    lines.append(f"**Description**: {v.get('description', 'N/A')}")
                    lines.append("")
                    if v.get("recommendation"):
                        lines.append(f"**Recommendation**: {v.get('recommendation', 'N/A')}")
                        lines.append("")
            
            if high:
                lines.append("### ⚠️ High Findings")
                lines.append("")
                for i, v in enumerate(high, 1):
                    lines.append(f"#### {i}. {v.get('title', 'Unknown')}")
                    lines.append("")
                    lines.append(f"- **Detector**: {v.get('detector', 'N/A')}")
                    lines.append(f"- **Confidence**: {v.get('confidence', 0):.0%}")
                    if v.get("locations"):
                        lines.append(f"- **Locations**: {', '.join(v.get('locations', []))}")
                    lines.append("")
                    lines.append(f"**Description**: {v.get('description', 'N/A')}")
                    lines.append("")
                    if v.get("recommendation"):
                        lines.append(f"**Recommendation**: {v.get('recommendation')}")
                        lines.append("")
            
            if medium:
                lines.append("### ⚡ Medium Findings")
                lines.append("")
                for v in medium:
                    lines.append(f"- **{v.get('title', 'Unknown')}**: {v.get('description', 'N/A')[:100]}...")
                lines.append("")
            
            if low or info:
                lines.append("### 📌 Low / Info Findings")
                lines.append("")
                for v in low + info:
                    lines.append(f"- {v.get('title', 'Unknown')}")
                lines.append("")
        
        if critical or high:
            lines.append("## Potential Attack Vectors")
            lines.append("")
            
            vuln_types = set(v.get("vulnerability_type", "") for v in critical + high)
            
            if "reentrancy" in vuln_types:
                lines.append("### Reentrancy Attack")
                lines.append("1. Call vulnerable function with malicious contract")
                lines.append("2. Reenter during external call before state update")
                lines.append("3. Drain funds through repeated calls")
                lines.append("")
            
            if "delegatecall" in vuln_types:
                lines.append("### Delegatecall Exploit")
                lines.append("1. Deploy malicious implementation contract")
                lines.append("2. Call function with controlled delegatecall target")
                lines.append("3. Execute arbitrary code in context of victim contract")
                lines.append("")
            
            if "access_control" in vuln_types:
                lines.append("### Access Control Bypass")
                lines.append("1. Identify unprotected sensitive functions")
                lines.append("2. Call directly without authorization")
                lines.append("3. Modify critical state or drain funds")
                lines.append("")
        
        lines.append("## Next Steps")
        lines.append("")
        lines.append("- [ ] Manual code review to verify findings")
        lines.append("- [ ] Develop Proof of Concept for critical issues")
        lines.append("- [ ] Check for existing bug bounty program")
        lines.append("- [ ] Run Chimera contract–wallet correlation for victim or counterpart addresses")
        lines.append("")
        
        lines.append("---")
        lines.append("*Generated by Chimera contract analysis*")
        
        return "\n".join(lines)
    
    def _generate_summary_text(self, report: ProtocolReport) -> str:
        """Generate human-readable summary text file"""
        lines = []
        
        lines.append("=" * 70)
        lines.append(f"🔱 BASILISK SECURITY REPORT: {report.protocol_name}")
        lines.append("=" * 70)
        lines.append("")
        
        lines.append("PROTOCOL OVERVIEW")
        lines.append("-" * 70)
        lines.append(f"Name:           {report.protocol_name}")
        lines.append(f"Address:        {report.address}")
        lines.append(f"Chain:          {report.chain}")
        lines.append(f"Category:       {report.category}")
        lines.append(f"TVL:            ${report.tvl:,.0f}")
        lines.append(f"Audit Status:   {'✅ Audited' if report.is_audited else '❌ Unaudited'}")
        lines.append(f"Priority Score:  {report.priority_score}/100")
        lines.append(f"Scanned At:     {report.scanned_at}")
        lines.append("")
        
        if report.verdicts:
            lines.append("VERDICTS")
            lines.append("-" * 70)
            for v in report.verdicts:
                severity = v.get("severity", "INFO")
                icon = {"CRITICAL": "🚨", "HIGH": "⚠️", "MEDIUM": "⚡", "LOW": "📌", "INFO": "ℹ️"}.get(severity, "•")
                lines.append(f"{icon} [{severity}] {v.get('title', 'Unknown')}")
                if v.get("description"):
                    lines.append(f"   {v.get('description')}")
            lines.append("")
        
        vulns = report.vulnerabilities
        if vulns:
            critical = [v for v in vulns if v.get("severity", "").upper() == "CRITICAL"]
            high = [v for v in vulns if v.get("severity", "").upper() == "HIGH"]
            medium = [v for v in vulns if v.get("severity", "").upper() == "MEDIUM"]
            low = [v for v in vulns if v.get("severity", "").upper() == "LOW"]
            
            lines.append("VULNERABILITY SUMMARY")
            lines.append("-" * 70)
            lines.append(f"Total Findings:     {len(vulns)}")
            lines.append(f"🚨 Critical:        {len(critical)}")
            lines.append(f"⚠️  High:            {len(high)}")
            lines.append(f"⚡ Medium:          {len(medium)}")
            lines.append(f"📌 Low:             {len(low)}")
            lines.append("")
            
            if critical:
                lines.append("CRITICAL FINDINGS")
                lines.append("-" * 70)
                for i, v in enumerate(critical, 1):
                    lines.append(f"\n{i}. {v.get('title', 'Unknown')}")
                    lines.append(f"   Detector: {v.get('detector', 'N/A')}")
                    lines.append(f"   Confidence: {v.get('confidence', 0):.0%}")
                    if v.get("description"):
                        lines.append(f"   Description: {v.get('description')}")
                    if v.get("locations"):
                        lines.append(f"   Locations: {', '.join(v.get('locations', []))}")
                lines.append("")
            
            if high:
                lines.append("HIGH SEVERITY FINDINGS")
                lines.append("-" * 70)
                for i, v in enumerate(high, 1):
                    lines.append(f"\n{i}. {v.get('title', 'Unknown')}")
                    lines.append(f"   Detector: {v.get('detector', 'N/A')}")
                    if v.get("description"):
                        lines.append(f"   Description: {v.get('description')}")
                lines.append("")
        
        lines.append("=" * 70)
        lines.append("Generated by Chimera contract analysis")
        lines.append("=" * 70)
        
        return "\n".join(lines)
    
    def _create_priority_symlinks(self, report: ProtocolReport, protocol_dir: Path):
        """Create symlinks in priority folders"""
        slug = self._sanitize_slug(report.protocol_slug)
        
        has_critical = any(v.get("severity") == "Critical" for v in report.vulnerabilities)
        has_high = any(v.get("severity") == "High" for v in report.vulnerabilities)
        
        for folder in ["🎯_critical", "🎯_high", "📦_archive"]:
            link_path = self.output_dir / folder / slug
            if link_path.is_symlink():
                link_path.unlink()
        
        if has_critical:
            target_folder = "🎯_critical"
        elif has_high:
            target_folder = "🎯_high"
        elif report.priority_score < 60:
            target_folder = "📦_archive"
        else:
            return
        
        link_path = self.output_dir / target_folder / slug
        
        try:
            relative_target = Path("..") / "_all" / slug
            link_path.symlink_to(relative_target)
        except OSError:
            pass
    
    def generate_hunt_summary(
        self,
        hunt_results: Dict,
        protocols_scanned: List[ProtocolReport]
    ) -> Path:
        """
        Generate a summary report for an entire hunt.
        
        Args:
            hunt_results: Raw hunt results dict
            protocols_scanned: List of ProtocolReport objects that were scanned
            
        Returns:
            Path to the summary report
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_path = self.output_dir / "reports" / f"hunt_{timestamp}.md"
        
        lines = []
        
        lines.append("# 🔱 Contract scan summary")
        lines.append("")
        lines.append(f"> Hunt completed: {datetime.now().isoformat()}")
        lines.append("")
        
        lines.append("## Overview")
        lines.append("")
        lines.append(f"| Metric | Value |")
        lines.append(f"|--------|-------|")
        lines.append(f"| Protocols Discovered | {hunt_results.get('protocols_discovered', 0)} |")
        lines.append(f"| Contracts Scanned | {len(protocols_scanned)} |")
        
        total_vulns = sum(len(p.vulnerabilities) for p in protocols_scanned)
        total_critical = sum(
            sum(1 for v in p.vulnerabilities if v.get("severity") == "Critical")
            for p in protocols_scanned
        )
        total_high = sum(
            sum(1 for v in p.vulnerabilities if v.get("severity") == "High")
            for p in protocols_scanned
        )
        
        lines.append(f"| Total Vulnerabilities | {total_vulns} |")
        lines.append(f"| Critical Findings | {total_critical} |")
        lines.append(f"| High Findings | {total_high} |")
        
        total_tvl = sum(p.tvl for p in protocols_scanned)
        lines.append(f"| Total TVL Scanned | ${total_tvl:,.0f} |")
        lines.append("")
        
        critical_protocols = [
            p for p in protocols_scanned
            if any(v.get("severity") == "Critical" for v in p.vulnerabilities)
        ]
        
        if critical_protocols:
            lines.append("## 🚨 Critical Targets")
            lines.append("")
            lines.append("| Protocol | TVL | Score | Critical | High |")
            lines.append("|----------|-----|-------|----------|------|")
            
            for p in sorted(critical_protocols, key=lambda x: x.priority_score, reverse=True):
                crit = sum(1 for v in p.vulnerabilities if v.get("severity") == "Critical")
                high = sum(1 for v in p.vulnerabilities if v.get("severity") == "High")
                slug = self._sanitize_slug(p.protocol_slug)
                lines.append(f"| [{p.protocol_name}](./_all/{slug}/report.md) | ${p.tvl:,.0f} | {p.priority_score} | {crit} | {high} |")
            lines.append("")
        
        high_protocols = [
            p for p in protocols_scanned
            if any(v.get("severity") == "High" for v in p.vulnerabilities)
            and p not in critical_protocols
        ]
        
        if high_protocols:
            lines.append("## ⚠️ High Priority Targets")
            lines.append("")
            lines.append("| Protocol | TVL | Score | High | Medium |")
            lines.append("|----------|-----|-------|------|--------|")
            
            for p in sorted(high_protocols, key=lambda x: x.priority_score, reverse=True):
                high = sum(1 for v in p.vulnerabilities if v.get("severity") == "High")
                med = sum(1 for v in p.vulnerabilities if v.get("severity") == "Medium")
                slug = self._sanitize_slug(p.protocol_slug)
                lines.append(f"| [{p.protocol_name}](./_all/{slug}/report.md) | ${p.tvl:,.0f} | {p.priority_score} | {high} | {med} |")
            lines.append("")
        
        lines.append("## All Scanned Protocols")
        lines.append("")
        lines.append("| Protocol | Category | Chain | TVL | Score | Findings |")
        lines.append("|----------|----------|-------|-----|-------|----------|")
        
        for p in sorted(protocols_scanned, key=lambda x: x.priority_score, reverse=True):
            slug = self._sanitize_slug(p.protocol_slug)
            lines.append(f"| [{p.protocol_name}](./_all/{slug}/report.md) | {p.category} | {p.chain} | ${p.tvl:,.0f} | {p.priority_score} | {len(p.vulnerabilities)} |")
        lines.append("")
        
        lines.append("## Protocols Without Addresses")
        lines.append("")
        lines.append("These protocols were discovered but couldn't be scanned (no contract address available):")
        lines.append("")
        
        lines.append("*See full hunt results JSON for complete list*")
        lines.append("")
        
        lines.append("---")
        lines.append("*Generated by Chimera contract analysis*")
        
        with open(report_path, "w") as f:
            f.write("\n".join(lines))
        
        return report_path
    
    def _sanitize_slug(self, slug: str) -> str:
        """Sanitize slug for use as directory name"""
        slug = slug.replace("/", "-").replace("\\", "-").replace(" ", "-")
        slug = "".join(c for c in slug if c.isalnum() or c in "-_.")
        return slug.lower()


def save_hunt_results(
    hunt_result: Any,
    scanned_targets: List[Any],
    output_dir: Optional[str] = None
) -> Dict[str, Path]:
    """
    Save all hunt results to organized directories.
    
    Args:
        hunt_result: HuntResult object from ContractHunter
        scanned_targets: List of ContractTarget objects that were scanned
        output_dir: Base output directory (defaults to Chimera root/Contracts)
        
    Returns:
        Dict with paths to generated files
    """
    generator = ReportGenerator(output_dir)
    paths = {"protocols": [], "summary": None}
    
    protocols_scanned = []
    for target in scanned_targets:
        if target.vulnerabilities:
            report = ProtocolReport(
                protocol_name=target.protocol_name,
                protocol_slug=target.protocol_slug,
                address=target.address,
                chain=target.chain,
                category=target.category,
                tvl=target.tvl,
                is_audited=target.is_audited,
                priority_score=target.priority_score,
                verdicts=target.verdicts,
                vulnerabilities=target.vulnerabilities,
                source_code=getattr(target, 'source_code', None),
            )
            
            path = generator.save_protocol_report(report)
            paths["protocols"].append(path)
            protocols_scanned.append(report)
    
    if protocols_scanned:
        hunt_dict = {
            "protocols_discovered": hunt_result.protocols_discovered if hasattr(hunt_result, 'protocols_discovered') else 0,
            "contracts_found": hunt_result.contracts_found if hasattr(hunt_result, 'contracts_found') else 0,
        }
        summary_path = generator.generate_hunt_summary(hunt_dict, protocols_scanned)
        paths["summary"] = summary_path
    
    return paths
