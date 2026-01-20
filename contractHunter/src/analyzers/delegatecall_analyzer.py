from typing import Dict, Optional
from .base_analyzer import BaseAnalyzer


class DelegateCallAnalyzer(BaseAnalyzer):
    def analyze(self, contract_code: str) -> Optional[Dict]:
        if self.model:
            return super().analyze(contract_code)
        return None
    
    def detect_pattern(self, contract_code: str) -> tuple[str, float]:
        code_lower = contract_code.lower()
        if 'delegatecall' in code_lower:
            if 'fallback' in code_lower or 'receive' in code_lower:
                if 'implementation' in code_lower or 'proxy' in code_lower:
                    return 'delegatecall', 0.95
                if 'storage' in code_lower and ('slot' in code_lower or 'layout' in code_lower):
                    return 'storage_collision', 0.9
                return 'delegatecall', 0.85
        return 'generic', 0.3