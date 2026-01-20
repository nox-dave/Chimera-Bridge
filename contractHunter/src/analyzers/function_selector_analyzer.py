from typing import Dict, Optional
from .base_analyzer import BaseAnalyzer


class FunctionSelectorAnalyzer(BaseAnalyzer):
    def analyze(self, contract_code: str) -> Optional[Dict]:
        if self.model:
            return super().analyze(contract_code)
        return None
    
    def detect_pattern(self, contract_code: str) -> tuple[str, float]:
        code_lower = contract_code.lower()
        if 'bytes4' in code_lower and 'keccak256' in code_lower:
            if 'execute' in code_lower or 'call' in code_lower:
                if 'string' in code_lower and 'func' in code_lower:
                    return 'function_selector_clash', 0.9
        if 'abi.encodewithsignature' in code_lower or 'abi.encodewithselector' in code_lower:
            if 'execute' in code_lower:
                return 'function_selector_clash', 0.75
        return 'generic', 0.3