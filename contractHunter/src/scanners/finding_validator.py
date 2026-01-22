import re
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
from enum import Enum


class ValidationStatus(Enum):
    CONFIRMED = "CONFIRMED"
    FALSE_POSITIVE = "FALSE_POSITIVE"
    LIKELY_FALSE_POSITIVE = "LIKELY_FALSE_POSITIVE"
    NEEDS_REVIEW = "NEEDS_REVIEW"


@dataclass
class ValidatedFinding:
    original_finding: Dict
    status: ValidationStatus
    reason: str
    evidence: Optional[str] = None
    line_number: Optional[int] = None


@dataclass
class ValidationResult:
    confirmed: List[ValidatedFinding] = field(default_factory=list)
    false_positives: List[ValidatedFinding] = field(default_factory=list)
    likely_false_positives: List[ValidatedFinding] = field(default_factory=list)
    needs_review: List[ValidatedFinding] = field(default_factory=list)
    
    @property
    def total_findings(self) -> int:
        return len(self.confirmed) + len(self.false_positives) + len(self.likely_false_positives) + len(self.needs_review)
    
    @property
    def elimination_rate(self) -> float:
        if self.total_findings == 0:
            return 0.0
        eliminated = len(self.false_positives) + len(self.likely_false_positives)
        return (eliminated / self.total_findings) * 100
    
    def summary(self) -> str:
        lines = [
            "=" * 60,
            "FINDING VALIDATION SUMMARY",
            "=" * 60,
            f"Total Findings Analyzed: {self.total_findings}",
            f"",
            f"✅ CONFIRMED:            {len(self.confirmed)}",
            f"❌ FALSE POSITIVE:       {len(self.false_positives)}",
            f"⚠️  LIKELY FALSE POS:    {len(self.likely_false_positives)}",
            f"🔍 NEEDS MANUAL REVIEW:  {len(self.needs_review)}",
            f"",
            f"Elimination Rate: {self.elimination_rate:.1f}%",
            "=" * 60,
        ]
        return "\n".join(lines)


class FindingValidator:
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        
        self.validators = {
            'tx-origin-pattern': self._validate_tx_origin,
            'tx-origin': self._validate_tx_origin,
            'selfdestruct-pattern': self._validate_selfdestruct,
            'selfdestruct': self._validate_selfdestruct,
            'suicidal': self._validate_selfdestruct,
            'unchecked-call-pattern': self._validate_unchecked_call,
            'unchecked-call': self._validate_unchecked_call,
            'unchecked-low-level': self._validate_unchecked_call,
            'unchecked-transfer': self._validate_unchecked_call,
            'access-control-pattern': self._validate_access_control,
            'access-control': self._validate_access_control,
            'missing-access-control': self._validate_access_control,
            'unprotected-upgrade': self._validate_access_control,
            'reentrancy-pattern': self._validate_reentrancy,
            'reentrancy': self._validate_reentrancy,
            'reentrancy-eth': self._validate_reentrancy,
            'reentrancy-no-eth': self._validate_reentrancy,
            'reentrancy-benign': self._validate_reentrancy,
            'reentrancy-events': self._validate_reentrancy,
            'delegatecall-pattern': self._validate_delegatecall,
            'delegatecall': self._validate_delegatecall,
            'controlled-delegatecall': self._validate_delegatecall,
            'arbitrary-send-eth': self._validate_arbitrary_send,
            'arbitrary-send': self._validate_arbitrary_send,
            'arbitrary-send-erc20': self._validate_arbitrary_send,
        }
        
        self.known_protected_functions = {
            'renounceOwnership',
            'transferOwnership',
            'upgradeTo',
            'upgradeToAndCall',
            '_authorizeUpgrade',
            'pause',
            'unpause',
            'setAdmin',
            'changeAdmin',
        }
        
        self.proxy_modifiers = {
            'onlyOwner',
            'onlyAdmin',
            'onlyRole',
            'onlyProxy',
            'onlyDelegateCall',
            'proxyCallIfNotAdmin',
            'ifAdmin',
        }
    
    def validate_findings(self, findings: List[Dict], source_code: str) -> ValidationResult:
        result = ValidationResult()
        
        for finding in findings:
            validated = self._validate_single_finding(finding, source_code)
            
            if validated.status == ValidationStatus.CONFIRMED:
                result.confirmed.append(validated)
            elif validated.status == ValidationStatus.FALSE_POSITIVE:
                result.false_positives.append(validated)
            elif validated.status == ValidationStatus.LIKELY_FALSE_POSITIVE:
                result.likely_false_positives.append(validated)
            else:
                result.needs_review.append(validated)
        
        if self.verbose:
            print(result.summary())
        
        return result
    
    def _validate_single_finding(self, finding: Dict, source_code: str) -> ValidatedFinding:
        detector = finding.get('detector') or finding.get('check') or finding.get('vulnerability_type', '')
        detector = detector.lower().replace('_', '-')
        
        if detector in self.validators:
            return self.validators[detector](finding, source_code)
        
        return ValidatedFinding(
            original_finding=finding,
            status=ValidationStatus.NEEDS_REVIEW,
            reason=f"No automated validator for detector: {detector}"
        )
    
    def _validate_tx_origin(self, finding: Dict, source_code: str) -> ValidatedFinding:
        if 'tx.origin' not in source_code:
            return ValidatedFinding(
                original_finding=finding,
                status=ValidationStatus.FALSE_POSITIVE,
                reason="tx.origin not found in source code"
            )
        
        lines = source_code.split('\n')
        for i, line in enumerate(lines, 1):
            if 'tx.origin' in line:
                stripped = line.strip()
                if stripped.startswith('//') or stripped.startswith('*'):
                    continue
                
                if 'require' in line or '==' in line or '!=' in line:
                    return ValidatedFinding(
                        original_finding=finding,
                        status=ValidationStatus.CONFIRMED,
                        reason="tx.origin used in authentication check",
                        evidence=line.strip(),
                        line_number=i
                    )
                else:
                    return ValidatedFinding(
                        original_finding=finding,
                        status=ValidationStatus.NEEDS_REVIEW,
                        reason="tx.origin found but usage unclear",
                        evidence=line.strip(),
                        line_number=i
                    )
        
        return ValidatedFinding(
            original_finding=finding,
            status=ValidationStatus.FALSE_POSITIVE,
            reason="tx.origin only found in comments"
        )
    
    def _validate_selfdestruct(self, finding: Dict, source_code: str) -> ValidatedFinding:
        has_selfdestruct = 'selfdestruct' in source_code.lower()
        has_suicide = 'suicide(' in source_code.lower()
        
        if not has_selfdestruct and not has_suicide:
            return ValidatedFinding(
                original_finding=finding,
                status=ValidationStatus.FALSE_POSITIVE,
                reason="selfdestruct/suicide not found in source code"
            )
        
        lines = source_code.split('\n')
        for i, line in enumerate(lines, 1):
            line_lower = line.lower()
            if 'selfdestruct' in line_lower or 'suicide(' in line_lower:
                stripped = line.strip()
                if stripped.startswith('//') or stripped.startswith('*'):
                    continue
                    
                return ValidatedFinding(
                    original_finding=finding,
                    status=ValidationStatus.CONFIRMED,
                    reason="selfdestruct found in code",
                    evidence=line.strip(),
                    line_number=i
                )
        
        return ValidatedFinding(
            original_finding=finding,
            status=ValidationStatus.FALSE_POSITIVE,
            reason="selfdestruct only found in comments"
        )
    
    def _validate_unchecked_call(self, finding: Dict, source_code: str) -> ValidatedFinding:
        call_patterns = [
            r'\.call\s*[\(\{]',
            r'\.delegatecall\s*[\(\{]',
            r'\.staticcall\s*[\(\{]',
        ]
        
        lines = source_code.split('\n')
        unchecked_calls = []
        checked_calls = []
        
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            if stripped.startswith('//') or stripped.startswith('*'):
                continue
            
            for pattern in call_patterns:
                if re.search(pattern, line):
                    if re.search(r'\(\s*bool\s+\w*success', line):
                        context = '\n'.join(lines[i-1:i+3])
                        if re.search(r'require\s*\(\s*success', context, re.IGNORECASE):
                            checked_calls.append((i, line.strip()))
                        else:
                            unchecked_calls.append((i, line.strip()))
                    elif 'require(' in line:
                        checked_calls.append((i, line.strip()))
                    else:
                        unchecked_calls.append((i, line.strip()))
                    break
        
        if not unchecked_calls and not checked_calls:
            return ValidatedFinding(
                original_finding=finding,
                status=ValidationStatus.FALSE_POSITIVE,
                reason="No low-level calls found in source code"
            )
        
        if not unchecked_calls:
            return ValidatedFinding(
                original_finding=finding,
                status=ValidationStatus.LIKELY_FALSE_POSITIVE,
                reason=f"All {len(checked_calls)} low-level calls appear to check return values",
                evidence=checked_calls[0][1] if checked_calls else None
            )
        
        return ValidatedFinding(
            original_finding=finding,
            status=ValidationStatus.CONFIRMED,
            reason=f"Found {len(unchecked_calls)} potentially unchecked low-level calls",
            evidence=unchecked_calls[0][1],
            line_number=unchecked_calls[0][0]
        )
    
    def _validate_access_control(self, finding: Dict, source_code: str) -> ValidatedFinding:
        description = finding.get('description', '')
        
        func_match = re.search(r"[Ff]unction\s*['\"]?(\w+)['\"]?", description)
        func_name = func_match.group(1) if func_match else None
        
        if not func_name:
            title = finding.get('title', '')
            func_match = re.search(r"['\"]?(\w+)['\"]?", title)
            func_name = func_match.group(1) if func_match else None
        
        if not func_name:
            return ValidatedFinding(
                original_finding=finding,
                status=ValidationStatus.NEEDS_REVIEW,
                reason="Could not extract function name from finding"
            )
        
        func_pattern = rf'function\s+{func_name}\s*\('
        if not re.search(func_pattern, source_code):
            return ValidatedFinding(
                original_finding=finding,
                status=ValidationStatus.FALSE_POSITIVE,
                reason=f"Function '{func_name}' not found in source code"
            )
        
        if func_name in self.known_protected_functions:
            if re.search(r'is\s+.*Ownable', source_code) or \
               re.search(r'is\s+.*AccessControl', source_code) or \
               re.search(r'import.*Ownable', source_code):
                return ValidatedFinding(
                    original_finding=finding,
                    status=ValidationStatus.LIKELY_FALSE_POSITIVE,
                    reason=f"'{func_name}' likely has inherited access control from OpenZeppelin"
                )
        
        lines = source_code.split('\n')
        for i, line in enumerate(lines, 1):
            if re.search(func_pattern, line):
                context = '\n'.join(lines[max(0, i-1):i+3])
                
                for modifier in self.proxy_modifiers:
                    if modifier in context:
                        return ValidatedFinding(
                            original_finding=finding,
                            status=ValidationStatus.FALSE_POSITIVE,
                            reason=f"Function has '{modifier}' access control",
                            evidence=line.strip(),
                            line_number=i
                        )
                
                if re.search(rf'{func_name}\s*\([^)]*\)\s+\w+\s*(public|external)', context):
                    return ValidatedFinding(
                        original_finding=finding,
                        status=ValidationStatus.NEEDS_REVIEW,
                        reason="Function may have custom access control modifier",
                        evidence=line.strip(),
                        line_number=i
                    )
        
        return ValidatedFinding(
            original_finding=finding,
            status=ValidationStatus.CONFIRMED,
            reason=f"Function '{func_name}' appears to lack access control",
        )
    
    def _validate_reentrancy(self, finding: Dict, source_code: str) -> ValidatedFinding:
        if 'ReentrancyGuard' in source_code or 'nonReentrant' in source_code:
            return ValidatedFinding(
                original_finding=finding,
                status=ValidationStatus.LIKELY_FALSE_POSITIVE,
                reason="Contract uses ReentrancyGuard/nonReentrant modifier"
            )
        
        call_pattern = r'\.(call|transfer|send)\s*[\(\{]'
        if not re.search(call_pattern, source_code):
            return ValidatedFinding(
                original_finding=finding,
                status=ValidationStatus.FALSE_POSITIVE,
                reason="No external calls (call/transfer/send) found in code"
            )
        
        return ValidatedFinding(
            original_finding=finding,
            status=ValidationStatus.NEEDS_REVIEW,
            reason="External calls present - manual review needed for CEI pattern"
        )
    
    def _validate_delegatecall(self, finding: Dict, source_code: str) -> ValidatedFinding:
        if 'delegatecall' not in source_code:
            return ValidatedFinding(
                original_finding=finding,
                status=ValidationStatus.FALSE_POSITIVE,
                reason="delegatecall not found in source code"
            )
        
        if 'Proxy' in source_code or 'proxy' in source_code.lower():
            lines = source_code.split('\n')
            for i, line in enumerate(lines, 1):
                if 'delegatecall' in line:
                    context = '\n'.join(lines[max(0, i-5):i+3])
                    if 'IMPLEMENTATION' in context or '_implementation' in context:
                        return ValidatedFinding(
                            original_finding=finding,
                            status=ValidationStatus.LIKELY_FALSE_POSITIVE,
                            reason="delegatecall appears to be standard proxy pattern",
                            evidence=line.strip(),
                            line_number=i
                        )
        
        return ValidatedFinding(
            original_finding=finding,
            status=ValidationStatus.NEEDS_REVIEW,
            reason="delegatecall found - verify target is not user-controlled"
        )
    
    def _validate_arbitrary_send(self, finding: Dict, source_code: str) -> ValidatedFinding:
        send_patterns = [
            r'\.transfer\s*\(',
            r'\.send\s*\(',
            r'\.call\s*\{\s*value\s*:',
        ]
        
        found = False
        for pattern in send_patterns:
            if re.search(pattern, source_code):
                found = True
                break
        
        if not found:
            return ValidatedFinding(
                original_finding=finding,
                status=ValidationStatus.FALSE_POSITIVE,
                reason="No ETH transfer patterns found in code"
            )
        
        return ValidatedFinding(
            original_finding=finding,
            status=ValidationStatus.NEEDS_REVIEW,
            reason="ETH transfer found - verify recipient is not arbitrary"
        )
    
    def generate_report(self, result: ValidationResult, protocol_name: str = "Unknown") -> str:
        lines = [
            "═" * 70,
            f"🔍 FINDING VALIDATION REPORT: {protocol_name}",
            "═" * 70,
            "",
            result.summary(),
            "",
        ]
        
        if result.confirmed:
            lines.append("")
            lines.append("✅ CONFIRMED FINDINGS (Require Attention)")
            lines.append("-" * 50)
            for f in result.confirmed:
                detector = f.original_finding.get('detector', 'unknown')
                severity = f.original_finding.get('severity', 'UNKNOWN')
                lines.append(f"  [{severity}] {detector}")
                lines.append(f"       Reason: {f.reason}")
                if f.evidence:
                    lines.append(f"       Evidence: {f.evidence[:80]}...")
                if f.line_number:
                    lines.append(f"       Line: {f.line_number}")
                lines.append("")
        
        if result.needs_review:
            lines.append("")
            lines.append("🔍 NEEDS MANUAL REVIEW")
            lines.append("-" * 50)
            for f in result.needs_review:
                detector = f.original_finding.get('detector', 'unknown')
                severity = f.original_finding.get('severity', 'UNKNOWN')
                lines.append(f"  [{severity}] {detector}")
                lines.append(f"       Reason: {f.reason}")
                lines.append("")
        
        if result.false_positives or result.likely_false_positives:
            lines.append("")
            lines.append("❌ ELIMINATED (False Positives)")
            lines.append("-" * 50)
            for f in result.false_positives + result.likely_false_positives:
                detector = f.original_finding.get('detector', 'unknown')
                status = "FP" if f.status == ValidationStatus.FALSE_POSITIVE else "LIKELY FP"
                lines.append(f"  [{status}] {detector}")
                lines.append(f"       Reason: {f.reason}")
                lines.append("")
        
        lines.append("═" * 70)
        lines.append("Generated by FindingValidator - Zero LLM, Pure Code Analysis")
        lines.append("═" * 70)
        
        return "\n".join(lines)


def validate_scan_results(findings: List[Dict], source_code: str, verbose: bool = True) -> ValidationResult:
    validator = FindingValidator(verbose=verbose)
    return validator.validate_findings(findings, source_code)


if __name__ == "__main__":
    import json
    import sys
    
    print("=" * 60)
    print("FindingValidator - Automated False Positive Filter")
    print("=" * 60)
    
    sample_findings = [
        {
            "detector": "tx-origin-pattern",
            "severity": "HIGH",
            "description": "tx.origin used for authentication"
        },
        {
            "detector": "selfdestruct-pattern", 
            "severity": "HIGH",
            "description": "Contract contains selfdestruct"
        },
        {
            "detector": "unchecked-call-pattern",
            "severity": "HIGH", 
            "description": "Low-level call without checking return value"
        },
        {
            "detector": "access-control-pattern",
            "severity": "HIGH",
            "description": "Function 'renounceOwnership' has no access control"
        }
    ]
    
    sample_code = '''
    // SPDX-License-Identifier: MIT
    pragma solidity ^0.8.0;
    
    import "@openzeppelin/contracts/access/Ownable.sol";
    
    contract Example is Ownable {
        function doSomething() external {
            (bool success, bytes memory data) = target.call(abi.encodeWithSignature("foo()"));
            require(success, "Call failed");
        }
        
        function withdraw() external onlyOwner {
            payable(msg.sender).transfer(address(this).balance);
        }
    }
    '''
    
    print("\nSample Findings:")
    for f in sample_findings:
        print(f"  - [{f['severity']}] {f['detector']}")
    
    print("\n" + "=" * 60)
    print("Running Validation...")
    print("=" * 60 + "\n")
    
    result = validate_scan_results(sample_findings, sample_code, verbose=True)
    
    print("\n")
    validator = FindingValidator()
    report = validator.generate_report(result, "Example Contract")
    print(report)
