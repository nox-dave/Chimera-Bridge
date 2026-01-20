from typing import Dict, Optional
from .base_analyzer import BaseAnalyzer


class AccessControlAnalyzer(BaseAnalyzer):
    def analyze(self, contract_code: str) -> Optional[Dict]:
        if self.model:
            return super().analyze(contract_code)
        return None
    
    def detect_pattern(self, contract_code: str) -> tuple[str, float]:
        code_lower = contract_code.lower()
        if 'onlyowner' in code_lower or 'onlyadmin' in code_lower:
            if 'modifier' in code_lower and 'owner' in code_lower:
                return 'access_control', 0.8
        return 'generic', 0.3
