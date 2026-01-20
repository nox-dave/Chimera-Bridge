"""
Pattern Scanner - FREE Vulnerability Detection for Basilisk

Combines:
1. Regex-based pattern matching (instant, free)
2. Slither static analysis (fast, free, comprehensive)

No LLM tokens required.

Usage:
    scanner = PatternScanner()
    
    # Scan contract source code
    findings = await scanner.scan(source_code)
    
    # Scan contract file with Slither
    findings = await scanner.scan_file("/path/to/Contract.sol")
"""

import re
import subprocess
import json
import tempfile
import os
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from pathlib import Path
from enum import Enum


class Severity(Enum):
    CRITICAL = "Critical"
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"
    INFO = "Informational"


@dataclass
class Finding:
    """A vulnerability finding"""
    detector: str
    vulnerability_type: str
    severity: Severity
    confidence: float
    title: str
    description: str
    locations: List[str] = field(default_factory=list)
    recommendation: str = ""
    source: str = "pattern"
    
    def to_dict(self) -> Dict:
        return {
            "detector": self.detector,
            "type": self.vulnerability_type,
            "severity": self.severity.value,
            "confidence": self.confidence,
            "title": self.title,
            "description": self.description,
            "locations": self.locations,
            "recommendation": self.recommendation,
            "source": self.source
        }


class PatternScanner:
    """
    FREE vulnerability scanner using pattern matching + Slither
    
    Detects:
    - Reentrancy (multiple variants)
    - Access control issues
    - Delegatecall vulnerabilities
    - Selfdestruct risks
    - Integer overflow/underflow
    - Unchecked returns
    - Oracle manipulation patterns
    - Flash loan attack patterns
    - Signature replay
    - Tx.origin authentication
    - And 20+ more patterns
    """
    
    SLITHER_DETECTORS = [
        "reentrancy-eth",
        "reentrancy-no-eth", 
        "arbitrary-send-eth",
        "controlled-delegatecall",
        "suicidal",
        "unprotected-upgrade",
        "reentrancy-benign",
        "reentrancy-events",
        "missing-zero-check",
        "unchecked-transfer",
        "locked-ether",
        "controlled-array-length",
        "tx-origin",
        "uninitialized-state",
        "uninitialized-storage",
        "arbitrary-send-erc20",
        "divide-before-multiply",
        "unused-return",
        "incorrect-equality",
        "shadowing-state",
        "weak-prng",
        "encode-packed-collision",
    ]
    
    def __init__(self, slither_timeout: int = 120):
        self.slither_timeout = slither_timeout
        self._slither_available = self._check_slither()
        
        if self._slither_available:
            print("[+] Slither detected - full static analysis enabled")
        else:
            print("[!] Slither not found - using pattern matching only")
            print("    Install with: pip install slither-analyzer")
    
    def _check_slither(self) -> bool:
        """Check if Slither is installed"""
        try:
            result = subprocess.run(
                ["slither", "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False
    
    async def scan(
        self,
        source_code: str,
        contract_name: Optional[str] = None,
        use_slither: bool = True
    ) -> List[Finding]:
        """
        Scan source code for vulnerabilities
        
        Args:
            source_code: Solidity source code
            contract_name: Optional contract name for better reporting
            use_slither: Whether to use Slither (if available)
            
        Returns:
            List of Finding objects
        """
        findings = []
        
        pattern_findings = self._scan_patterns(source_code)
        findings.extend(pattern_findings)
        
        if use_slither and self._slither_available:
            slither_findings = await self._scan_with_slither(source_code, contract_name)
            findings.extend(slither_findings)
        
        findings = self._deduplicate_findings(findings)
        
        severity_order = {
            Severity.CRITICAL: 0,
            Severity.HIGH: 1,
            Severity.MEDIUM: 2,
            Severity.LOW: 3,
            Severity.INFO: 4
        }
        findings.sort(key=lambda f: (severity_order[f.severity], -f.confidence))
        
        return findings
    
    async def scan_file(
        self,
        file_path: str,
        use_slither: bool = True
    ) -> List[Finding]:
        """
        Scan a Solidity file for vulnerabilities
        
        Args:
            file_path: Path to .sol file
            use_slither: Whether to use Slither
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Contract file not found: {file_path}")
        
        source_code = path.read_text()
        contract_name = path.stem
        
        findings = []
        
        pattern_findings = self._scan_patterns(source_code)
        findings.extend(pattern_findings)
        
        if use_slither and self._slither_available:
            slither_findings = await self._run_slither_on_file(file_path)
            findings.extend(slither_findings)
        
        findings = self._deduplicate_findings(findings)
        severity_order = {
            Severity.CRITICAL: 0,
            Severity.HIGH: 1,
            Severity.MEDIUM: 2,
            Severity.LOW: 3,
            Severity.INFO: 4
        }
        findings.sort(key=lambda f: (severity_order[f.severity], -f.confidence))
        
        return findings
    
    # =========================================================================
    # PATTERN MATCHING (Layer 1 - Instant, Free)
    # =========================================================================
    
    def _scan_patterns(self, source_code: str) -> List[Finding]:
        """Run all pattern-based detectors"""
        findings = []
        
        findings.extend(self._detect_reentrancy(source_code))
        findings.extend(self._detect_access_control(source_code))
        findings.extend(self._detect_delegatecall(source_code))
        findings.extend(self._detect_selfdestruct(source_code))
        findings.extend(self._detect_integer_issues(source_code))
        findings.extend(self._detect_unchecked_returns(source_code))
        findings.extend(self._detect_tx_origin(source_code))
        findings.extend(self._detect_oracle_patterns(source_code))
        findings.extend(self._detect_flash_loan_patterns(source_code))
        findings.extend(self._detect_signature_issues(source_code))
        findings.extend(self._detect_timestamp_dependence(source_code))
        findings.extend(self._detect_weak_randomness(source_code))
        findings.extend(self._detect_msgvalue_loop(source_code))
        findings.extend(self._detect_unprotected_init(source_code))
        
        return findings
    
    def _detect_reentrancy(self, code: str) -> List[Finding]:
        """Detect reentrancy patterns"""
        findings = []
        
        has_reentrancy_guard = bool(re.search(r'ReentrancyGuard|nonReentrant|_nonReentrantBefore|_reentrancyGuardEntered', code))
        
        pattern1 = re.compile(
            r'\.call\{value:\s*[^}]+\}\s*\([^)]*\).*?[\n\r].*?'
            r'(\w+\s*=|\w+\[.*?\]\s*=|\w+\s*\+=|\w+\s*-=)',
            re.DOTALL
        )
        if pattern1.search(code):
            if has_reentrancy_guard:
                findings.append(Finding(
                    detector="reentrancy-eth-pattern",
                    vulnerability_type="reentrancy",
                    severity=Severity.LOW,
                    confidence=0.3,
                    title="Potential Reentrancy (ETH) - Likely Protected",
                    description="External call with ETH followed by state change detected. ReentrancyGuard is present - likely protected but verify manually.",
                    recommendation="Verify nonReentrant modifier is applied to this function"
                ))
            else:
                findings.append(Finding(
                    detector="reentrancy-eth-pattern",
                    vulnerability_type="reentrancy",
                    severity=Severity.CRITICAL,
                    confidence=0.85,
                    title="Potential Reentrancy (ETH)",
                    description="External call with ETH followed by state change. Classic reentrancy pattern detected.",
                    recommendation="Apply checks-effects-interactions pattern or use ReentrancyGuard"
                ))
        
        pattern2 = re.compile(
            r'\.call\([^)]*\).*?[\n\r].*?(\w+\s*=)',
            re.DOTALL
        )
        if pattern2.search(code) and not pattern1.search(code):
            if has_reentrancy_guard:
                findings.append(Finding(
                    detector="reentrancy-no-eth-pattern",
                    vulnerability_type="reentrancy",
                    severity=Severity.LOW,
                    confidence=0.25,
                    title="Potential Reentrancy (No ETH) - Likely Protected",
                    description="External call followed by state change detected. ReentrancyGuard present.",
                    recommendation="Verify nonReentrant modifier is applied"
                ))
            else:
                findings.append(Finding(
                    detector="reentrancy-no-eth-pattern",
                    vulnerability_type="reentrancy",
                    severity=Severity.HIGH,
                    confidence=0.7,
                    title="Potential Reentrancy (No ETH)",
                    description="External call followed by state change detected.",
                    recommendation="Apply checks-effects-interactions pattern"
                ))
        
        pattern3 = re.compile(
            r'\.(transfer|send)\s*\([^)]+\).*?[\n\r].*?(\w+\s*=|\w+\[)',
            re.DOTALL
        )
        if pattern3.search(code) and not has_reentrancy_guard:
            findings.append(Finding(
                detector="reentrancy-transfer-pattern",
                vulnerability_type="reentrancy",
                severity=Severity.MEDIUM,
                confidence=0.5,
                title="Potential Reentrancy via transfer/send",
                description="State change after transfer/send. Lower risk due to gas limits but still a pattern violation.",
                recommendation="Apply checks-effects-interactions pattern"
            ))
        
        return findings
    
    def _detect_access_control(self, code: str) -> List[Finding]:
        """Detect access control issues"""
        findings = []
        
        func_pattern = re.compile(
            r'function\s+(\w+)\s*\([^)]*\)\s*(?:public|external)(?![^{]*\b(?:view|pure)\b)[^{]*\{',
            re.MULTILINE
        )
        
        sensitive_names = [
            'withdraw', 'mint', 'burn', 'pause', 'unpause',
            'setOwner', 'setAdmin', 'upgrade', 'upgradeTo', 'upgradeToAndCall',
            'initialize', 'init', 'destroy', 'kill', 'sweep', 'drain', 
            'execute', 'emergencyWithdraw', 'pauseContract', 'unPauseContract',
            'setFee', 'setTreasury', 'setOracle', 'addAdmin', 'removeAdmin',
            'grantRole', 'revokeRole', 'renounceOwnership', 'transferOwnership'
        ]
        
        standard_public_functions = [
            'transfer', 'transferFrom', 'approve', 'safeTransferFrom',
            'safeTransfer', 'permit', 'increaseAllowance', 'decreaseAllowance',
            'setApprovalForAll', 'getApproved', 'isApprovedForAll',
            'deposit', 'stake', 'unstake', 'claim', 'redeem', 'wrap', 'unwrap'
        ]
        
        has_ownable = bool(re.search(r'Ownable|onlyOwner|onlyAdmin|onlyRole|AccessControl', code))
        has_initializable = bool(re.search(r'Initializable|initializer|onlyInitializing', code))
        
        for match in func_pattern.finditer(code):
            func_name = match.group(1)
            func_start = match.start()
            
            if func_name in standard_public_functions:
                continue
            
            func_decl = code[func_start:func_start + 800]
            
            has_modifier = bool(re.search(
                r'onlyOwner|onlyAdmin|onlyRole|onlyProxy|onlyInitializing|initializer|'
                r'require\s*\(\s*msg\.sender\s*==|require\s*\(\s*_msgSender\(\)\s*==|'
                r'require\s*\(\s*hasRole|_checkOwner|_checkRole|whenNotPaused|nonReentrant',
                func_decl
            ))
            
            if not has_modifier:
                is_sensitive = any(s.lower() == func_name.lower() for s in sensitive_names)
                
                if func_name.lower() in ['initialize', 'init']:
                    if has_initializable:
                        continue
                    if re.search(r'initialized|_initialized|isInitialized', code):
                        continue
                
                if 'upgrade' in func_name.lower():
                    if re.search(r'UUPSUpgradeable|_authorizeUpgrade|TransparentUpgradeableProxy', code):
                        continue
                
                if is_sensitive:
                    findings.append(Finding(
                        detector="access-control-pattern",
                        vulnerability_type="access_control",
                        severity=Severity.HIGH,
                        confidence=0.8,
                        title=f"Missing Access Control: {func_name}",
                        description=f"Function '{func_name}' appears sensitive but has no obvious access control modifier.",
                        locations=[func_name],
                        recommendation="Add appropriate access control (onlyOwner, onlyAdmin, etc.)"
                    ))
        
        if re.search(r'function[^}]*(?:public|external)[^}]*\{[^}]*selfdestruct', code, re.DOTALL):
            findings.append(Finding(
                detector="unprotected-selfdestruct",
                vulnerability_type="access_control",
                severity=Severity.CRITICAL,
                confidence=0.9,
                title="Unprotected selfdestruct",
                description="selfdestruct found in public/external function without obvious access control",
                recommendation="Add access control to functions containing selfdestruct"
            ))
        
        return findings
    
    def _detect_delegatecall(self, code: str) -> List[Finding]:
        """Detect delegatecall vulnerabilities"""
        findings = []
        
        is_proxy_contract = bool(re.search(
            r'UUPSUpgradeable|TransparentUpgradeableProxy|ERC1967Proxy|'
            r'Proxy|_implementation\(\)|_fallback\(\)|_delegate\(',
            code
        ))
        
        if re.search(r'\.delegatecall\s*\(', code):
            pattern_simple = re.compile(
                r'function\s+\w+\s*\([^)]*address[^)]*\)[^{]*\{[^}]*\.delegatecall',
                re.DOTALL
            )
            
            if pattern_simple.search(code):
                if is_proxy_contract:
                    findings.append(Finding(
                        detector="delegatecall-proxy-pattern",
                        vulnerability_type="delegatecall",
                        severity=Severity.INFO,
                        confidence=0.9,
                        title="Delegatecall in Proxy Contract",
                        description="Contract uses delegatecall as part of proxy pattern. Verify implementation address is properly controlled.",
                        recommendation="Ensure only authorized addresses can update implementation"
                    ))
                else:
                    findings.append(Finding(
                        detector="controlled-delegatecall-pattern",
                        vulnerability_type="delegatecall",
                        severity=Severity.CRITICAL,
                        confidence=0.85,
                        title="Controlled Delegatecall",
                        description="delegatecall target may be user-controlled. This can lead to complete contract takeover.",
                        recommendation="Ensure delegatecall target cannot be user-controlled"
                    ))
            else:
                if not is_proxy_contract:
                    findings.append(Finding(
                        detector="delegatecall-pattern",
                        vulnerability_type="delegatecall",
                        severity=Severity.MEDIUM,
                        confidence=0.6,
                        title="Delegatecall Usage",
                        description="Contract uses delegatecall. Verify target is from a trusted source.",
                        recommendation="Ensure delegatecall target is immutable or properly access-controlled"
                    ))
        
        return findings
    
    def _detect_selfdestruct(self, code: str) -> List[Finding]:
        """Detect selfdestruct vulnerabilities"""
        findings = []
        
        if re.search(r'\bselfdestruct\s*\(', code):
            findings.append(Finding(
                detector="selfdestruct-pattern",
                vulnerability_type="selfdestruct",
                severity=Severity.HIGH,
                confidence=0.7,
                title="Selfdestruct Present",
                description="Contract contains selfdestruct. Can be used to force-send ETH or destroy contract.",
                recommendation="Ensure selfdestruct is properly protected and necessary"
            ))
        
        return findings
    
    def _detect_integer_issues(self, code: str) -> List[Finding]:
        """Detect integer overflow/underflow patterns"""
        findings = []
        
        version_match = re.search(r'pragma\s+solidity\s*[\^~]?\s*(\d+\.\d+)', code)
        if version_match:
            version = version_match.group(1)
            major, minor = map(int, version.split('.'))
            
            if major == 0 and minor < 8:
                if not re.search(r'SafeMath|using\s+SafeMath', code):
                    if re.search(r'[\+\-\*](?!=)', code):
                        findings.append(Finding(
                            detector="integer-overflow-pattern",
                            vulnerability_type="integer_overflow",
                            severity=Severity.HIGH,
                            confidence=0.75,
                            title="Potential Integer Overflow/Underflow",
                            description=f"Solidity {version} without SafeMath. Arithmetic operations may overflow.",
                            recommendation="Use SafeMath library or upgrade to Solidity 0.8.0+"
                        ))
        
        if re.search(r'unchecked\s*\{', code):
            findings.append(Finding(
                detector="unchecked-arithmetic-pattern",
                vulnerability_type="integer_overflow",
                severity=Severity.MEDIUM,
                confidence=0.6,
                title="Unchecked Arithmetic Block",
                description="Contract uses unchecked blocks. Verify overflow is intentional.",
                recommendation="Ensure unchecked arithmetic cannot cause security issues"
            ))
        
        return findings
    
    def _detect_unchecked_returns(self, code: str) -> List[Finding]:
        """Detect unchecked return values"""
        findings = []
        
        call_pattern = re.compile(r'\.call\{?[^}]*\}?\s*\([^)]*\)\s*;', re.MULTILINE)
        
        for match in call_pattern.finditer(code):
            start = max(0, match.start() - 100)
            context_before = code[start:match.start()]
            
            is_checked = bool(re.search(r'\(\s*bool\s+\w*\s*,|\bbool\s+\w+\s*=|=\s*$', context_before))
            
            if not is_checked:
                line_num = code[:match.start()].count('\n') + 1
                findings.append(Finding(
                    detector="unchecked-call-pattern",
                    vulnerability_type="unchecked_return",
                    severity=Severity.HIGH,
                    confidence=0.8,
                    title="Unchecked Call Return",
                    description="Low-level call without checking return value. Call may fail silently.",
                    locations=[f"Line {line_num}"],
                    recommendation="Check return value: (bool success, ) = addr.call(...); require(success);"
                ))
                break
        
        if re.search(r'\.transfer\s*\([^)]+\)\s*;', code):
            uses_safe_erc20 = bool(re.search(r'SafeERC20|safeTransfer|safeTransferFrom', code))
            if not uses_safe_erc20:
                if not re.search(r'bool\s+\w+\s*=\s*\w+\.transfer|require\s*\(\s*\w+\.transfer', code):
                    findings.append(Finding(
                        detector="unchecked-transfer-pattern",
                        vulnerability_type="unchecked_return",
                        severity=Severity.MEDIUM,
                        confidence=0.6,
                        title="Potentially Unchecked ERC20 Transfer",
                        description="ERC20 transfer may not check return value. Non-standard tokens may return false instead of reverting.",
                        recommendation="Use SafeERC20 library or check return value"
                    ))
        
        return findings
    
    def _detect_tx_origin(self, code: str) -> List[Finding]:
        """Detect tx.origin authentication"""
        findings = []
        
        if re.search(r'tx\.origin', code):
            if re.search(r'(?:require|if)\s*\([^)]*tx\.origin', code):
                findings.append(Finding(
                    detector="tx-origin-pattern",
                    vulnerability_type="tx_origin",
                    severity=Severity.HIGH,
                    confidence=0.9,
                    title="tx.origin Authentication",
                    description="tx.origin used for authentication. Vulnerable to phishing attacks.",
                    recommendation="Use msg.sender instead of tx.origin"
                ))
        
        return findings
    
    def _detect_oracle_patterns(self, code: str) -> List[Finding]:
        """Detect oracle manipulation patterns"""
        findings = []
        
        oracle_keywords = ['getPrice', 'latestAnswer', 'latestRoundData', 'oracle', 'priceFeed']
        oracle_count = sum(1 for kw in oracle_keywords if kw.lower() in code.lower())
        
        if oracle_count > 0:
            has_twap = bool(re.search(r'twap|TWAP|timeWeighted', code, re.IGNORECASE))
            has_multiple = bool(re.search(r'oracle.*oracle|price.*price', code, re.IGNORECASE))
            
            if not has_twap and not has_multiple:
                findings.append(Finding(
                    detector="oracle-single-source-pattern",
                    vulnerability_type="oracle_manipulation",
                    severity=Severity.MEDIUM,
                    confidence=0.6,
                    title="Single Oracle Source",
                    description="Contract appears to use a single price oracle. May be vulnerable to manipulation.",
                    recommendation="Consider using TWAP, multiple oracles, or circuit breakers"
                ))
        
        return findings
    
    def _detect_flash_loan_patterns(self, code: str) -> List[Finding]:
        """Detect flash loan attack patterns"""
        findings = []
        
        flash_callbacks = [
            'onFlashLoan', 'executeOperation', 'uniswapV2Call', 
            'uniswapV3FlashCallback', 'pancakeCall'
        ]
        
        for callback in flash_callbacks:
            if callback in code:
                findings.append(Finding(
                    detector="flash-loan-callback-pattern",
                    vulnerability_type="flash_loan",
                    severity=Severity.INFO,
                    confidence=0.9,
                    title=f"Flash Loan Callback: {callback}",
                    description=f"Contract implements {callback}. Ensure proper validation.",
                    recommendation="Verify callback is only callable by legitimate flash loan providers"
                ))
        
        if re.search(r'(executeOperation|onFlashLoan)[^}]*\.call\(', code, re.DOTALL):
            findings.append(Finding(
                detector="flash-loan-arbitrary-call-pattern",
                vulnerability_type="flash_loan",
                severity=Severity.CRITICAL,
                confidence=0.8,
                title="Arbitrary Call in Flash Loan",
                description="Flash loan callback contains arbitrary external call. High exploitation risk.",
                recommendation="Restrict external calls in flash loan callbacks"
            ))
        
        return findings
    
    def _detect_signature_issues(self, code: str) -> List[Finding]:
        """Detect signature replay and related issues"""
        findings = []
        
        if re.search(r'ecrecover', code):
            has_nonce = bool(re.search(r'nonce|Nonce', code))
            has_deadline = bool(re.search(r'deadline|expir', code, re.IGNORECASE))
            has_domain = bool(re.search(r'DOMAIN_SEPARATOR|domainSeparator|EIP712', code))
            
            issues = []
            if not has_nonce:
                issues.append("missing nonce")
            if not has_deadline:
                issues.append("missing deadline")
            if not has_domain:
                issues.append("missing domain separator")
            
            if issues:
                findings.append(Finding(
                    detector="signature-replay-pattern",
                    vulnerability_type="signature_replay",
                    severity=Severity.HIGH if not has_nonce else Severity.MEDIUM,
                    confidence=0.7,
                    title="Potential Signature Replay",
                    description=f"ecrecover used with {', '.join(issues)}. May be vulnerable to replay attacks.",
                    recommendation="Implement EIP-712 with nonce, deadline, and domain separator"
                ))
        
        return findings
    
    def _detect_timestamp_dependence(self, code: str) -> List[Finding]:
        """Detect timestamp dependence"""
        findings = []
        
        if re.search(r'block\.timestamp|now(?!\w)', code):
            if re.search(r'(?:require|if)\s*\([^)]*(?:block\.timestamp|now)', code):
                findings.append(Finding(
                    detector="timestamp-dependence-pattern",
                    vulnerability_type="timestamp_dependence",
                    severity=Severity.LOW,
                    confidence=0.6,
                    title="Timestamp Dependence",
                    description="Contract logic depends on block.timestamp. Miners can manipulate slightly.",
                    recommendation="Avoid using timestamps for critical logic or use block.number"
                ))
        
        return findings
    
    def _detect_weak_randomness(self, code: str) -> List[Finding]:
        """Detect weak randomness sources"""
        findings = []
        
        weak_sources = [
            (r'block\.timestamp', 'block.timestamp'),
            (r'block\.number', 'block.number'),
            (r'blockhash\s*\(', 'blockhash'),
            (r'block\.difficulty', 'block.difficulty'),
            (r'block\.prevrandao', 'block.prevrandao'),
        ]
        
        for pattern, name in weak_sources:
            if re.search(pattern, code):
                if re.search(rf'(?:random|Random|rand|RAND|seed|Seed).*{pattern}|{pattern}.*(?:random|Random|rand|RAND)', code):
                    findings.append(Finding(
                        detector="weak-randomness-pattern",
                        vulnerability_type="weak_randomness",
                        severity=Severity.HIGH,
                        confidence=0.75,
                        title=f"Weak Randomness: {name}",
                        description=f"{name} used for randomness. Predictable by miners/validators.",
                        recommendation="Use Chainlink VRF or commit-reveal scheme"
                    ))
        
        return findings
    
    def _detect_msgvalue_loop(self, code: str) -> List[Finding]:
        """Detect msg.value reuse in loop"""
        findings = []
        
        if re.search(r'(?:for|while)\s*\([^)]*\)\s*\{[^}]*msg\.value', code, re.DOTALL):
            findings.append(Finding(
                detector="msgvalue-loop-pattern",
                vulnerability_type="msg_value_loop",
                severity=Severity.HIGH,
                confidence=0.85,
                title="msg.value Reused in Loop",
                description="msg.value used inside a loop. Same ETH amount counted multiple times.",
                recommendation="Track total amount and compare once, or use msg.value only once"
            ))
        
        return findings
    
    def _detect_unprotected_init(self, code: str) -> List[Finding]:
        """Detect unprotected initializer"""
        findings = []
        
        if re.search(r'function\s+initialize\s*\([^)]*\)\s*(?:public|external)', code):
            if not re.search(r'initializer|initialized|_initialized', code):
                findings.append(Finding(
                    detector="unprotected-init-pattern",
                    vulnerability_type="unprotected_initialization",
                    severity=Severity.CRITICAL,
                    confidence=0.8,
                    title="Unprotected Initializer",
                    description="initialize() function without initializer modifier. Can be called multiple times.",
                    recommendation="Use OpenZeppelin's Initializable or add initialized check"
                ))
        
        return findings
    
    # =========================================================================
    # SLITHER INTEGRATION (Layer 2 - Fast, Free, Comprehensive)
    # =========================================================================
    
    async def _scan_with_slither(
        self,
        source_code: str,
        contract_name: Optional[str] = None
    ) -> List[Finding]:
        """Run Slither on source code via temp file"""
        if not self._slither_available:
            return []
        
        with tempfile.NamedTemporaryFile(
            mode='w',
            suffix='.sol',
            delete=False
        ) as f:
            f.write(source_code)
            temp_path = f.name
        
        try:
            findings = await self._run_slither_on_file(temp_path)
            return findings
        finally:
            try:
                os.unlink(temp_path)
            except:
                pass
    
    async def _run_slither_on_file(self, file_path: str) -> List[Finding]:
        """Run Slither on a file"""
        if not self._slither_available:
            return []
        
        findings = []
        
        try:
            cmd = [
                "slither",
                file_path,
                "--json", "-",
                "--detect", ",".join(self.SLITHER_DETECTORS),
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.slither_timeout
            )
            
            if result.stdout:
                try:
                    data = json.loads(result.stdout)
                    detectors = data.get("results", {}).get("detectors", [])
                    
                    for d in detectors:
                        severity = self._map_slither_severity(d.get("impact", ""))
                        
                        findings.append(Finding(
                            detector=d.get("check", "unknown"),
                            vulnerability_type=d.get("check", "unknown"),
                            severity=severity,
                            confidence=self._map_slither_confidence(d.get("confidence", "")),
                            title=d.get("check", "Unknown Issue"),
                            description=d.get("description", "")[:500],
                            locations=[
                                f"{e.get('name', '')}:{e.get('source_mapping', {}).get('lines', ['?'])[0] if e.get('source_mapping', {}).get('lines') else '?'}"
                                for e in d.get("elements", [])[:3]
                            ],
                            recommendation=d.get("markdown", "")[:200] if d.get("markdown") else "",
                            source="slither"
                        ))
                        
                except json.JSONDecodeError:
                    pass
                    
        except subprocess.TimeoutExpired:
            print(f"[!] Slither timed out after {self.slither_timeout}s")
        except Exception as e:
            print(f"[!] Slither error: {e}")
        
        return findings
    
    def _map_slither_severity(self, impact: str) -> Severity:
        """Map Slither impact to our Severity"""
        mapping = {
            "High": Severity.CRITICAL,
            "Medium": Severity.HIGH,
            "Low": Severity.MEDIUM,
            "Informational": Severity.LOW,
            "Optimization": Severity.INFO,
        }
        return mapping.get(impact, Severity.MEDIUM)
    
    def _map_slither_confidence(self, confidence: str) -> float:
        """Map Slither confidence to 0-1 scale"""
        mapping = {
            "High": 0.9,
            "Medium": 0.7,
            "Low": 0.5,
        }
        return mapping.get(confidence, 0.6)
    
    # =========================================================================
    # UTILITY METHODS
    # =========================================================================
    
    def _deduplicate_findings(self, findings: List[Finding]) -> List[Finding]:
        """Remove duplicate findings, keeping highest confidence"""
        seen = {}
        
        for f in findings:
            key = (f.vulnerability_type, f.title)
            if key not in seen or f.confidence > seen[key].confidence:
                seen[key] = f
        
        return list(seen.values())
    
    def format_findings(self, findings: List[Finding]) -> str:
        """Format findings for display"""
        if not findings:
            return "✅ No vulnerabilities detected"
        
        lines = [
            f"\n🔍 Found {len(findings)} potential vulnerabilities:\n",
            "-" * 50
        ]
        
        severity_icons = {
            Severity.CRITICAL: "🚨",
            Severity.HIGH: "⚠️",
            Severity.MEDIUM: "⚡",
            Severity.LOW: "📌",
            Severity.INFO: "ℹ️"
        }
        
        for i, f in enumerate(findings, 1):
            icon = severity_icons.get(f.severity, "•")
            source_tag = f"[{f.source}]" if f.source else ""
            
            lines.append(f"\n[{i}] {icon} {f.severity.value}: {f.title} {source_tag}")
            lines.append(f"    Confidence: {f.confidence:.0%}")
            lines.append(f"    {f.description[:200]}")
            if f.locations:
                lines.append(f"    Locations: {', '.join(f.locations[:3])}")
            if f.recommendation:
                lines.append(f"    Fix: {f.recommendation[:150]}")
        
        return "\n".join(lines)


# ============================================================================
# CLI Interface
# ============================================================================

async def main():
    """CLI for testing the scanner"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Basilisk Pattern Scanner")
    parser.add_argument("file", help="Solidity file to scan")
    parser.add_argument("--no-slither", action="store_true", help="Disable Slither")
    parser.add_argument("--json", action="store_true", help="Output JSON")
    
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
    import asyncio
    asyncio.run(main())
