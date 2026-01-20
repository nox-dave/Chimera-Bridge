from abc import ABC, abstractmethod
from typing import Dict, Optional
from termcolor import cprint


class BaseAnalyzer(ABC):
    def __init__(self, model=None):
        self.model = model
    
    @abstractmethod
    def analyze(self, contract_code: str) -> Optional[Dict]:
        pass
    
    @abstractmethod
    def detect_pattern(self, contract_code: str) -> tuple[str, float]:
        pass
    
    def estimate_severity(self, vuln_type: str, explanation: str) -> str:
        vuln_lower = vuln_type.lower()
        explanation_lower = explanation.lower()
        
        critical_keywords = ["reentrancy", "access control", "privilege", "flash loan", "arbitrary call", "overflow", "underflow", "selfdestruct"]
        high_keywords = ["dos", "denial", "front-running", "timestamp"]
        
        if any(k in vuln_lower or k in explanation_lower for k in critical_keywords):
            return "Critical"
        elif any(k in vuln_lower or k in explanation_lower for k in high_keywords):
            return "High"
        return "Medium"
