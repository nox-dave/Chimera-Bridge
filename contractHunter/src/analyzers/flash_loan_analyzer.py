from typing import Dict, Optional
from .base_analyzer import BaseAnalyzer


class FlashLoanAnalyzer(BaseAnalyzer):
    def analyze(self, contract_code: str) -> Optional[Dict]:
        if self.model:
            return super().analyze(contract_code)
        return None
    
    def detect_pattern(self, contract_code: str) -> tuple[str, float]:
        code_lower = contract_code.lower()
        if 'ilendingpool' in code_lower or 'flashloan' in code_lower:
            if 'arbitrary' in code_lower or 'call(' in code_lower:
                return 'flash_loan_arbitrary_call', 0.95
        return 'generic', 0.3
