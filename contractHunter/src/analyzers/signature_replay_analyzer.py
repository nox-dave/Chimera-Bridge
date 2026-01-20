from typing import Dict, Optional
from .base_analyzer import BaseAnalyzer


class SignatureReplayAnalyzer(BaseAnalyzer):
    def analyze(self, contract_code: str) -> Optional[Dict]:
        if self.model:
            return super().analyze(contract_code)
        return None
    
    def detect_pattern(self, contract_code: str) -> tuple[str, float]:
        code_lower = contract_code.lower()
        if 'ecrecover' in code_lower or 'verify' in code_lower:
            if 'signature' in code_lower or 'r' in code_lower and 's' in code_lower and 'v' in code_lower:
                if 'nonce' not in code_lower and 'deadline' not in code_lower:
                    return 'signature_replay', 0.85
                if 'nonce' in code_lower or 'deadline' in code_lower:
                    return 'signature_replay', 0.6
        return 'generic', 0.3