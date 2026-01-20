from typing import Dict, Optional
from .base_analyzer import BaseAnalyzer


class SelfDestructAnalyzer(BaseAnalyzer):
    def analyze(self, contract_code: str) -> Optional[Dict]:
        if self.model:
            return super().analyze(contract_code)
        return None
    
    def detect_pattern(self, contract_code: str) -> tuple[str, float]:
        code_lower = contract_code.lower()
        if 'selfdestruct' in code_lower:
            return 'selfdestruct', 0.9
        if 'balance' in code_lower and 'require' in code_lower:
            if 'address(this).balance' in code_lower:
                if 'selfdestruct' not in code_lower:
                    return 'force_send_eth', 0.85
        return 'generic', 0.3