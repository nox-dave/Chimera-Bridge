from typing import Dict


def detect_vulnerability_template(analysis: Dict, contract_code: str) -> tuple[str, float]:
    vuln_type = analysis.get('type', '').lower()
    explanation = analysis.get('explanation', '').lower()
    code_lower = contract_code.lower()
    
    if any(x in vuln_type or x in explanation for x in ['flash loan', 'flashloan']):
        if 'erc20' in code_lower or 'token' in code_lower:
            if 'arbitrary' in code_lower or 'call(' in code_lower:
                return 'flash_loan_arbitrary_call', 0.95
            return 'flash_loan_erc20', 0.9
        return 'flash_loan_arbitrary_call', 0.85
    
    if 'reentrancy' in vuln_type or 'reentrancy' in explanation:
        if 'call{value' in code_lower or '.call(' in code_lower:
            return 'reentrancy', 0.9
    
    if any(x in vuln_type or x in explanation for x in ['access control', 'authorization', 'permission', 'owner', 'privilege']):
        return 'access_control', 0.8
    
    if any(x in vuln_type or x in explanation for x in ['overflow', 'underflow', 'integer']):
        return 'integer_overflow', 0.8
    
    if 'delegatecall' in vuln_type or 'delegatecall' in explanation or 'delegatecall' in code_lower:
        if 'storage' in code_lower and ('collision' in explanation or 'layout' in code_lower):
            return 'storage_collision', 0.9
        return 'delegatecall', 0.85
    
    if 'selfdestruct' in vuln_type or 'selfdestruct' in explanation or 'selfdestruct' in code_lower:
        return 'selfdestruct', 0.85
    
    if any(x in vuln_type or x in explanation for x in ['signature replay', 'signature', 'ecrecover']):
        if 'nonce' not in code_lower and 'deadline' not in code_lower:
            return 'signature_replay', 0.85
    
    if any(x in vuln_type or x in explanation for x in ['function selector', 'selector clash', 'selector collision']):
        return 'function_selector_clash', 0.9
    
    if any(x in vuln_type or x in explanation for x in ['oracle', 'price manipulation', 'price oracle']):
        return 'oracle_manipulation', 0.8
    
    if any(x in vuln_type or x in explanation for x in ['dos', 'denial of service', 'griefing']):
        return 'dos', 0.75
    
    if 'msg.value' in code_lower and 'loop' in code_lower:
        return 'reuse_eth_value', 0.85
    
    if 'merkle' in code_lower or 'airdrop' in code_lower:
        return 'merkle_airdrop', 0.8
    
    if 'proxy' in code_lower and 'upgrade' in code_lower:
        return 'proxy_upgrade', 0.75
    
    return 'generic', 0.5
