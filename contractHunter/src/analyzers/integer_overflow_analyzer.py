import re
from typing import Dict, Optional
from .base_analyzer import BaseAnalyzer


class IntegerOverflowAnalyzer(BaseAnalyzer):
    def analyze(self, contract_code: str) -> Optional[Dict]:
        if self.model:
            return super().analyze(contract_code)
        return None
    
    def detect_pattern(self, contract_code: str) -> tuple[str, float]:
        code_lower = contract_code.lower()
        if 'pragma solidity' in code_lower:
            version_match = re.search(r'pragma solidity\s+([0-9.]+)', code_lower)
            if version_match:
                version = version_match.group(1)
                if version.startswith('0.7') or version.startswith('0.6') or version.startswith('0.5'):
                    if '+' in code_lower or '*' in code_lower or '-' in code_lower:
                        if 'safemath' not in code_lower:
                            return 'integer_overflow', 0.8
        if 'unchecked' in code_lower:
            if 'overflow' in code_lower or 'underflow' in code_lower:
                return 'integer_overflow', 0.75
        return 'generic', 0.3