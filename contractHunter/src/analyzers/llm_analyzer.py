import re
from typing import Dict, Optional
from termcolor import cprint
from .base_analyzer import BaseAnalyzer


class LLMAnalyzer(BaseAnalyzer):
    def analyze(self, contract_code: str) -> Optional[Dict]:
        if not self.model:
            cprint("❌ No model available for analysis", "red")
            return None
        
        system_prompt = """You are a smart contract security expert. Analyze the provided Solidity contract for vulnerabilities.
    
Respond in this exact format:
VULNERABLE: [YES/NO]
VULNERABILITY_TYPE: [type if vulnerable, or NONE]
SEVERITY: [Critical/High/Medium/Low if vulnerable, or NONE]
EXPLANATION: [brief explanation of the vulnerability and how it can be exploited]"""

        user_content = f"Analyze this contract for vulnerabilities:\n\n```solidity\n{contract_code}\n```"
        
        cprint("\n🔍 Analyzing contract for vulnerabilities...", "cyan")
        response = self.model.generate_response(
            system_prompt=system_prompt,
            user_content=user_content,
            temperature=0.3,
            max_tokens=1024
        )
        
        if not response:
            cprint("❌ Failed to get analysis response", "red")
            return None
        
        content = response.content if hasattr(response, 'content') else str(response)
        
        vulnerable = "VULNERABLE: YES" in content.upper()
        vuln_type = "NONE"
        severity = "NONE"
        explanation = ""
        
        for line in content.split("\n"):
            if "VULNERABILITY_TYPE:" in line.upper():
                vuln_type = line.split(":", 1)[1].strip()
            elif "SEVERITY:" in line.upper():
                severity = line.split(":", 1)[1].strip()
            elif "EXPLANATION:" in line.upper():
                explanation = line.split(":", 1)[1].strip()
        
        if vulnerable and severity == "NONE":
            severity = self.estimate_severity(vuln_type, explanation)
        
        return {
            "vulnerable": vulnerable,
            "type": vuln_type,
            "severity": severity,
            "explanation": explanation,
            "full_response": content
        }
    
    def detect_pattern(self, contract_code: str) -> tuple[str, float]:
        return 'generic', 0.5
