from typing import Dict, Optional
from .base_analyzer import BaseAnalyzer


class OracleManipulationAnalyzer(BaseAnalyzer):
    def analyze(self, contract_code: str) -> Optional[Dict]:
        if self.model:
            return super().analyze(contract_code)
        return None
    
    def detect_pattern(self, contract_code: str) -> tuple[str, float]:
        code_lower = contract_code.lower()
        if 'oracle' in code_lower or 'price' in code_lower:
            if 'getprice' in code_lower or 'latestrounddata' in code_lower:
                if 'chainlink' not in code_lower or 'twap' not in code_lower:
                    return 'oracle_manipulation', 0.8
        if 'uniswap' in code_lower and 'price' in code_lower:
            if 'spot' in code_lower and 'twap' not in code_lower:
                return 'oracle_manipulation', 0.85
        return 'generic', 0.3