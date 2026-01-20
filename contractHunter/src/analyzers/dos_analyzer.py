from typing import Dict, Optional
from .base_analyzer import BaseAnalyzer


class DoSAnalyzer(BaseAnalyzer):
    def analyze(self, contract_code: str) -> Optional[Dict]:
        if self.model:
            return super().analyze(contract_code)
        return None
    
    def detect_pattern(self, contract_code: str) -> tuple[str, float]:
        code_lower = contract_code.lower()
        if 'revert' in code_lower and 'receive' in code_lower:
            if 'call{value' in code_lower or 'transfer' in code_lower:
                return 'dos', 0.85
        if 'loop' in code_lower or 'for' in code_lower:
            if 'gas' in code_lower or 'unbounded' in code_lower:
                return 'dos', 0.75
        if 'array.push' in code_lower and 'require' not in code_lower:
            if 'length' in code_lower:
                return 'dos', 0.7
        return 'generic', 0.3