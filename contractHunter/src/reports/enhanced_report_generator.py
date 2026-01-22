#!/usr/bin/env python3

import re
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field


KNOWN_AUDITED_PROTOCOLS = {
    "arbitrum": ["Trail of Bits", "OpenZeppelin"],
    "optimism": ["Trail of Bits", "Sherlock"],
    "base": ["Coinbase Security", "OpenZeppelin"],
    "uniswap": ["Trail of Bits", "ABDK", "OpenZeppelin"],
    "aave": ["Trail of Bits", "Certora", "SigmaPrime", "OpenZeppelin"],
    "compound": ["Trail of Bits", "OpenZeppelin"],
    "lido": ["Statemind", "Ackee", "MixBytes"],
    "maker": ["Trail of Bits", "PeckShield"],
    "curve": ["Trail of Bits", "MixBytes"],
    "balancer": ["Trail of Bits", "Certora"],
    "yearn": ["Trail of Bits", "MixBytes"],
    "sushi": ["PeckShield", "Quantstamp"],
    "pancakeswap": ["PeckShield", "SlowMist"],
    "gmx": ["ABDK", "Guardian Audits"],
    "morpho": ["Spearbit", "Cantina"],
    "eigenlayer": ["Sigma Prime", "Cantina"],
    "ether.fi": ["Certora", "Nethermind"],
    "rocketpool": ["Trail of Bits", "Sigma Prime", "Consensys Diligence"],
    "frax": ["Trail of Bits", "ABDK"],
    "convex": ["MixBytes"],
    "stargate": ["Zellic", "LayerZero Labs"],
    "layerzero": ["Zellic", "Trail of Bits"],
    "wormhole": ["Neodyme", "Trail of Bits", "Kudelski"],
    "across": ["OpenZeppelin"],
    "hop": ["OpenZeppelin"],
    "multichain": ["SlowMist"],
    "chainlink": ["Trail of Bits", "Sigma Prime"],
    "tether": ["Multiple audits"],
    "blackrock": ["Big4 audits"],
    "steakhouse": ["Spearbit"],
}


@dataclass
class CodeContext:
    file_name: str
    function_name: str
    line_number: int
    code_snippet: List[str]
    highlighted_line: int


@dataclass
class EnhancedFinding:
    title: str
    severity: str
    detector: str
    description: str
    confidence: float
    location: Optional[CodeContext] = None
    recommendation: str = ""
    false_positive_likelihood: str = "Unknown"
    false_positive_reasons: List[str] = field(default_factory=list)
    references: List[str] = field(default_factory=list)


class EnhancedReportGenerator:
    
    def __init__(self):
        self.severity_emoji = {
            "CRITICAL": "🚨",
            "HIGH": "⚠️",
            "MEDIUM": "⚡",
            "LOW": "📌",
            "INFO": "ℹ️",
        }
        
        self.severity_order = ["CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"]
    
    def extract_code_context(
        self, 
        source_code: str, 
        finding: Dict,
        context_lines: int = 3
    ) -> Optional[CodeContext]:
        if not source_code:
            return None
            
        vuln_type = finding.get("type", finding.get("vulnerability_type", "")).lower()
        description = finding.get("description", "").lower()
        
        lines = source_code.split('\n')
        target_line = None
        function_name = "unknown"
        file_name = finding.get("file", "Contract.sol")
        
        func_patterns = [
            r"function[:\s]+['\"]?(\w+)['\"]?",
            r"['\"](\w+)['\"](?:\s+appears|\s+has|\s+is)",
            r"Missing Access Control:\s*(\w+)",
            r":\s*(\w+)$",
        ]
        
        extracted_func = None
        for pattern in func_patterns:
            match = re.search(pattern, finding.get("vulnerability_type", "") + " " + finding.get("description", ""), re.IGNORECASE)
            if match:
                extracted_func = match.group(1).lower()
                break
        
        if extracted_func:
            for i, line in enumerate(lines):
                if re.search(rf'\bfunction\s+{re.escape(extracted_func)}\s*\(', line, re.IGNORECASE):
                    target_line = i
                    function_name = extracted_func
                    break
        
        if target_line is None:
            locations = finding.get("locations", [])
            if locations:
                location_str = locations[0] if isinstance(locations, list) else str(locations)
                line_match = re.search(r'line\s+(\d+)', location_str, re.IGNORECASE)
                if line_match:
                    try:
                        target_line = int(line_match.group(1)) - 1
                    except ValueError:
                        pass
        
        if target_line is None:
            patterns = {
                "reentrancy": [r'\.call\{value:', r'\.call\(', r'\.send\(', r'\.transfer\('],
                "unchecked": [r'\.call\{?[^}]*\}?\s*\([^)]*\)\s*;', r'unchecked\s*\{'],
                "unchecked_return": [r'\.call\{?[^}]*\}?\s*\([^)]*\)\s*;', r'unchecked\s*\{'],
                "delegatecall": [r'\.delegatecall\('],
                "selfdestruct": [r'selfdestruct\(', r'suicide\('],
                "tx.origin": [r'tx\.origin'],
                "timestamp": [r'block\.timestamp', r'now\b'],
            }
            
            for category, pattern_list in patterns.items():
                if category in vuln_type or category in description:
                    for pattern in pattern_list:
                        for i, line in enumerate(lines):
                            if re.search(pattern, line):
                                target_line = i
                                break
                        if target_line:
                            break
                    if target_line:
                        break
        
        if target_line is None:
            words = re.findall(r'\b([a-z][a-zA-Z0-9]*)\b', description)
            common_func_names = ['burn', 'mint', 'transfer', 'withdraw', 'deposit', 'pause', 
                                 'unpause', 'initialize', 'upgrade', 'execute', 'call',
                                 'approve', 'revoke', 'set', 'update', 'remove', 'add']
            
            for word in words:
                if word.lower() in common_func_names:
                    for i, line in enumerate(lines):
                        if re.search(rf'\bfunction\s+{re.escape(word)}\s*\(', line, re.IGNORECASE):
                            target_line = i
                            function_name = word
                            break
                    if target_line:
                        break
        
        if target_line is None:
            return None
            
        if function_name == "unknown":
            for i in range(target_line, -1, -1):
                if 'function ' in lines[i]:
                    func_match = re.search(r'function\s+(\w+)', lines[i])
                    if func_match:
                        function_name = func_match.group(1)
                    break
        
        start = max(0, target_line - context_lines)
        end = min(len(lines), target_line + context_lines + 1)
        
        snippet = [lines[i] for i in range(start, end)]
        
        return CodeContext(
            file_name=file_name,
            function_name=function_name,
            line_number=target_line + 1,
            code_snippet=snippet,
            highlighted_line=target_line - start
        )
    
    def assess_false_positive(
        self, 
        finding: Dict, 
        protocol_name: str,
        source_code: str = ""
    ) -> Tuple[str, List[str]]:
        reasons = []
        likelihood = "Low"
        
        vuln_type = finding.get("type", finding.get("vulnerability_type", "")).lower()
        description = finding.get("description", "").lower()
        confidence = finding.get("confidence", 1.0)
        
        protocol_lower = protocol_name.lower()
        for known_protocol, auditors in KNOWN_AUDITED_PROTOCOLS.items():
            if known_protocol in protocol_lower:
                reasons.append(f"Protocol audited by: {', '.join(auditors)}")
                likelihood = "Medium"
                break
        
        if confidence < 0.5:
            reasons.append(f"Low detector confidence ({confidence:.0%})")
            likelihood = "High" if likelihood != "Low" else "Medium"
        
        if "likely protected" in description.lower():
            reasons.append("Detector indicates likely protected")
            likelihood = "High"
            
        if "reentrancyguard" in source_code.lower() and "reentrancy" in vuln_type:
            reasons.append("ReentrancyGuard pattern detected in contract")
            likelihood = "High"
            
        if "openzeppelin" in source_code.lower():
            reasons.append("Uses OpenZeppelin contracts (well-audited)")
            if likelihood == "Low":
                likelihood = "Medium"
        
        if "access control" in vuln_type or "access_control" in vuln_type:
            standard_funcs = ["transfer", "approve", "transferfrom", "safetransfer"]
            if any(f in description.lower() for f in standard_funcs):
                reasons.append("Standard ERC20/721 function (intentionally public)")
                likelihood = "High"
                
        if "unchecked" in vuln_type and "arithmetic" in description.lower():
            if "pragma solidity" in source_code and ("0.8" in source_code or "^0.8" in source_code):
                reasons.append("Solidity 0.8+ has built-in overflow protection")
                likelihood = "High"
        
        return likelihood, reasons
    
    def get_recommendation(self, finding: Dict) -> str:
        vuln_type = finding.get("type", finding.get("vulnerability_type", "")).lower()
        
        if finding.get("recommendation"):
            return finding.get("recommendation")
        
        recommendations = {
            "reentrancy": "Implement checks-effects-interactions pattern or use ReentrancyGuard.",
            "access_control": "Add appropriate access modifiers (onlyOwner, onlyRole) or require statements.",
            "unchecked_call": "Check return value of low-level calls or use Address.functionCall().",
            "unchecked call": "Check return value of low-level calls or use Address.functionCall().",
            "unchecked_return": "Check return value of low-level calls or use Address.functionCall().",
            "delegatecall": "Ensure delegatecall target is trusted and cannot be manipulated.",
            "selfdestruct": "Remove selfdestruct or add strict access controls and timelocks.",
            "tx.origin": "Replace tx.origin with msg.sender for authentication.",
            "timestamp": "Avoid using block.timestamp for critical logic or add tolerance.",
            "integer": "Use SafeMath library or Solidity 0.8+ for automatic overflow checks.",
            "arithmetic": "Use SafeMath library or Solidity 0.8+ for automatic overflow checks.",
            "flash_loan": "Implement proper access controls and validate state changes atomically.",
            "oracle": "Use multiple oracle sources and add price deviation checks.",
        }
        
        for key, rec in recommendations.items():
            if key in vuln_type:
                return rec
                
        return "Review the flagged code and assess if the pattern poses a real risk."
    
    def get_references(self, finding: Dict) -> List[str]:
        vuln_type = finding.get("type", finding.get("vulnerability_type", "")).lower()
        
        references = {
            "reentrancy": [
                "https://swcregistry.io/docs/SWC-107",
                "https://consensys.github.io/smart-contract-best-practices/attacks/reentrancy/",
            ],
            "access_control": [
                "https://swcregistry.io/docs/SWC-105",
            ],
            "unchecked": [
                "https://swcregistry.io/docs/SWC-104",
            ],
            "unchecked_return": [
                "https://swcregistry.io/docs/SWC-104",
            ],
            "delegatecall": [
                "https://swcregistry.io/docs/SWC-112",
            ],
            "tx.origin": [
                "https://swcregistry.io/docs/SWC-115",
            ],
            "timestamp": [
                "https://swcregistry.io/docs/SWC-116",
            ],
            "integer": [
                "https://swcregistry.io/docs/SWC-101",
            ],
        }
        
        for key, refs in references.items():
            if key in vuln_type:
                return refs
                
        return []
    
    def enhance_finding(
        self, 
        finding: Dict, 
        protocol_name: str,
        source_code: str = ""
    ) -> EnhancedFinding:
        code_context = self.extract_code_context(source_code, finding)
        fp_likelihood, fp_reasons = self.assess_false_positive(finding, protocol_name, source_code)
        recommendation = self.get_recommendation(finding)
        references = self.get_references(finding)
        
        return EnhancedFinding(
            title=finding.get("vulnerability_type", finding.get("title", "Unknown Vulnerability")),
            severity=finding.get("severity", "MEDIUM").upper(),
            detector=finding.get("detector", "unknown"),
            description=finding.get("description", ""),
            confidence=finding.get("confidence", 0.5),
            location=code_context,
            recommendation=recommendation,
            false_positive_likelihood=fp_likelihood,
            false_positive_reasons=fp_reasons,
            references=references,
        )
    
    def format_code_snippet(self, context: CodeContext, line_width: int = 76) -> str:
        if not context:
            return "   (Code location not available)\n"
            
        output = []
        output.append(f"   File: {context.file_name}")
        output.append(f"   Function: {context.function_name}()")
        output.append(f"   Line: {context.line_number}")
        output.append("")
        output.append("   ┌" + "─" * (line_width - 4) + "┐")
        
        start_line = context.line_number - context.highlighted_line
        
        for i, line in enumerate(context.code_snippet):
            line_num = start_line + i
            display_line = line[:line_width - 14] + "..." if len(line) > line_width - 14 else line
            
            if i == context.highlighted_line:
                output.append(f"   │ {line_num:4d} │→ {display_line}")
            else:
                output.append(f"   │ {line_num:4d} │  {display_line}")
                
        output.append("   └" + "─" * (line_width - 4) + "┘")
        
        return "\n".join(output)
    
    def generate_enhanced_report(
        self,
        protocol_name: str,
        address: str,
        chain: str,
        category: str,
        tvl: float,
        audited: bool,
        priority_score: int,
        findings: List[Dict],
        verdicts: List[Dict],
        source_code: str = "",
        scan_timestamp: str = None,
    ) -> str:
        
        if scan_timestamp is None:
            scan_timestamp = datetime.now().isoformat()
            
        enhanced_findings = [
            self.enhance_finding(f, protocol_name, source_code) 
            for f in findings
        ]
        
        enhanced_findings.sort(
            key=lambda f: self.severity_order.index(f.severity) 
            if f.severity in self.severity_order else 99
        )
        
        severity_counts = {s: 0 for s in self.severity_order}
        for f in enhanced_findings:
            if f.severity in severity_counts:
                severity_counts[f.severity] += 1
        
        known_audit_info = None
        protocol_lower = protocol_name.lower()
        for known_protocol, auditors in KNOWN_AUDITED_PROTOCOLS.items():
            if known_protocol in protocol_lower:
                known_audit_info = auditors
                break
        
        lines = []
        
        lines.append("=" * 80)
        lines.append(f"🔱 BASILISK SECURITY REPORT: {protocol_name}")
        lines.append("=" * 80)
        lines.append("")
        
        lines.append("PROTOCOL OVERVIEW")
        lines.append("-" * 80)
        lines.append(f"{'Name:':<20} {protocol_name}")
        lines.append(f"{'Address:':<20} {address}")
        lines.append(f"{'Chain:':<20} {chain}")
        lines.append(f"{'Category:':<20} {category}")
        lines.append(f"{'TVL:':<20} ${tvl:,.0f}")
        
        if known_audit_info:
            lines.append(f"{'Audit Status:':<20} ✅ Audited by {', '.join(known_audit_info[:3])}")
            lines.append(f"{'Note:':<20} ⚠️  DeFiLlama shows 'unaudited' - actual audits exist")
        else:
            audit_status = "✅ Audited" if audited else "❌ Unaudited (per DeFiLlama)"
            lines.append(f"{'Audit Status:':<20} {audit_status}")
            
        lines.append(f"{'Priority Score:':<20} {priority_score}/100")
        lines.append(f"{'Scanned At:':<20} {scan_timestamp}")
        lines.append("")
        
        if verdicts:
            lines.append("VERDICTS")
            lines.append("-" * 80)
            for verdict in verdicts:
                severity = verdict.get("severity", "INFO").upper()
                emoji = self.severity_emoji.get(severity, "ℹ️")
                title = verdict.get("title", "")
                desc = verdict.get("description", "")
                
                if known_audit_info and "unaudited" in title.lower():
                    lines.append(f"⚠️ [NOTE] {title}")
                    lines.append(f"   ⚡ Override: Protocol IS audited by {', '.join(known_audit_info[:2])}")
                    lines.append(f"   DeFiLlama data may be outdated")
                    continue
                    
                lines.append(f"{emoji} [{severity}] {title}")
                if desc:
                    lines.append(f"   {desc}")
            lines.append("")
        
        lines.append("VULNERABILITY SUMMARY")
        lines.append("-" * 80)
        lines.append(f"{'Total Findings:':<20} {len(enhanced_findings)}")
        lines.append(f"{'🚨 Critical:':<20} {severity_counts['CRITICAL']}")
        lines.append(f"{'⚠️  High:':<20} {severity_counts['HIGH']}")
        lines.append(f"{'⚡ Medium:':<20} {severity_counts['MEDIUM']}")
        lines.append(f"{'📌 Low:':<20} {severity_counts['LOW']}")
        lines.append("")
        
        if known_audit_info:
            lines.append("⚠️  AUDIT NOTICE")
            lines.append("-" * 80)
            lines.append(f"This protocol has been audited by: {', '.join(known_audit_info)}")
            lines.append("Findings below may be:")
            lines.append("  • Known issues accepted by the team")
            lines.append("  • False positives from automated scanning")
            lines.append("  • Intentional design decisions")
            lines.append("  • Already mitigated through other mechanisms")
            lines.append("")
            lines.append("⚠️  Verify each finding manually before reporting.")
            lines.append("")
        
        for severity in self.severity_order:
            severity_findings = [f for f in enhanced_findings if f.severity == severity]
            if not severity_findings:
                continue
                
            emoji = self.severity_emoji.get(severity, "ℹ️")
            lines.append(f"{emoji} {severity} SEVERITY FINDINGS ({len(severity_findings)})")
            lines.append("-" * 80)
            
            for i, finding in enumerate(severity_findings, 1):
                lines.append("")
                lines.append(f"{i}. {finding.title}")
                lines.append(f"   Detector:   {finding.detector}")
                lines.append(f"   Confidence: {finding.confidence:.0%}")
                lines.append("")
                
                lines.append(f"   Description:")
                desc_words = finding.description.split()
                desc_line = "   "
                for word in desc_words:
                    if len(desc_line) + len(word) + 1 > 75:
                        lines.append(desc_line)
                        desc_line = "   " + word
                    else:
                        desc_line += " " + word if desc_line.strip() else "   " + word
                if desc_line.strip():
                    lines.append(desc_line)
                lines.append("")
                
                if finding.location:
                    lines.append("   Code Context:")
                    lines.append(self.format_code_snippet(finding.location))
                    lines.append("")
                
                if finding.false_positive_likelihood != "Low" or finding.false_positive_reasons:
                    if finding.false_positive_likelihood == "High":
                        fp_emoji = "🟢"
                        fp_label = "LIKELY FALSE POSITIVE"
                    elif finding.false_positive_likelihood == "Medium":
                        fp_emoji = "🟡"
                        fp_label = "POSSIBLY FALSE POSITIVE"
                    else:
                        fp_emoji = "🔴"
                        fp_label = "LIKELY REAL"
                    
                    lines.append(f"   {fp_emoji} {fp_label}")
                    if finding.false_positive_reasons:
                        lines.append("   Reasons:")
                        for reason in finding.false_positive_reasons:
                            lines.append(f"      • {reason}")
                    lines.append("")
                
                lines.append(f"   💡 Recommendation:")
                lines.append(f"      {finding.recommendation}")
                lines.append("")
                
                if finding.references:
                    lines.append("   📚 References:")
                    for ref in finding.references:
                        lines.append(f"      • {ref}")
                    lines.append("")
                
                lines.append("   " + "-" * 40)
            
            lines.append("")
        
        lines.append("NEXT STEPS")
        lines.append("-" * 80)
        
        actionable_findings = [
            f for f in enhanced_findings 
            if f.confidence >= 0.6 and f.false_positive_likelihood == "Low"
            and f.severity in ["CRITICAL", "HIGH"]
        ]
        
        if actionable_findings:
            lines.append("☐ High-confidence findings to investigate:")
            for f in actionable_findings[:5]:
                lines.append(f"   • [{f.severity}] {f.title} ({f.confidence:.0%} confidence)")
            lines.append("")
        
        likely_fp = [f for f in enhanced_findings if f.false_positive_likelihood == "High"]
        if likely_fp:
            lines.append(f"ℹ️  {len(likely_fp)} findings flagged as likely false positives")
            lines.append("")
        
        lines.append("☐ Verify findings against protocol documentation")
        lines.append("☐ Check if issues are known/accepted by team")
        lines.append("☐ Develop PoC for confirmed vulnerabilities")
        lines.append("☐ Run Chimera Bridge to find exposed wallets")
        lines.append("")
        
        lines.append("=" * 80)
        lines.append("Generated by Basilisk Contract Hunter (Enhanced Report)")
        lines.append(f"Report Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("=" * 80)
        
        return "\n".join(lines)
    
    def save_report(self, report: str, output_dir: str, filename: str = "summary.txt") -> str:
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        filepath = output_path / filename
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(report)
            
        return str(filepath)


def generate_enhanced_report(
    protocol_data: Dict,
    findings: List[Dict],
    source_code: str = "",
    output_dir: Optional[str] = None,
) -> str:
    generator = EnhancedReportGenerator()
    
    report = generator.generate_enhanced_report(
        protocol_name=protocol_data.get("protocol_name", protocol_data.get("name", "Unknown")),
        address=protocol_data.get("address", ""),
        chain=protocol_data.get("chain", "Ethereum"),
        category=protocol_data.get("category", "Unknown"),
        tvl=protocol_data.get("tvl", 0) or 0,
        audited=protocol_data.get("is_audited", protocol_data.get("audited", False)),
        priority_score=protocol_data.get("priority_score", 0),
        findings=findings,
        verdicts=protocol_data.get("verdicts", []),
        source_code=source_code,
        scan_timestamp=protocol_data.get("scanned_at"),
    )
    
    if output_dir:
        generator.save_report(report, output_dir)
        
    return report


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate enhanced security report")
    parser.add_argument("--profile", "-p", required=True, help="Path to profile.json")
    parser.add_argument("--source", "-s", help="Path to source.sol")
    parser.add_argument("--output", "-o", help="Output directory")
    
    args = parser.parse_args()
    
    with open(args.profile, 'r') as f:
        protocol_data = json.load(f)
        
    source_code = ""
    if args.source:
        with open(args.source, 'r') as f:
            source_code = f.read()
    
    findings = protocol_data.get("vulnerabilities", [])
    scan_results = protocol_data.get("scan_results", {})
    if isinstance(scan_results, dict):
        findings.extend(scan_results.get("findings", []))
    
    report = generate_enhanced_report(
        protocol_data=protocol_data,
        findings=findings,
        source_code=source_code,
        output_dir=args.output,
    )
    
    print(report)
