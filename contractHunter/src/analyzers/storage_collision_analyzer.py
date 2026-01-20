from typing import Dict, Optional
from .base_analyzer import BaseAnalyzer


class StorageCollisionAnalyzer(BaseAnalyzer):
    def analyze(self, contract_code: str) -> Optional[Dict]:
        if self.model:
            return super().analyze(contract_code)
        return None
    
    def detect_pattern(self, contract_code: str) -> tuple[str, float]:
        code_lower = contract_code.lower()
        if 'delegatecall' in code_lower:
            if 'implementation' in code_lower or 'proxy' in code_lower:
                if 'slot' in code_lower or 'storage' in code_lower:
                    return 'storage_collision', 0.9
        if 'upgradeable' in code_lower or 'upgrade' in code_lower:
            if 'delegatecall' in code_lower:
                return 'storage_collision', 0.85
        return 'generic', 0.3