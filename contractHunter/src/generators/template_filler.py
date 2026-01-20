import json
import re
from pathlib import Path
from typing import Dict, List, Tuple
from termcolor import cprint


def safe_format_template(template: str, params: Dict) -> str:
    result = template
    for key, value in params.items():
        result = result.replace(f"{{{key}}}", str(value))
    return result


def extract_template_params(model, contract_code: str, analysis: Dict, contract_path: str, template_name: str) -> Dict:
    challenge_folder = contract_path.rsplit("/", 1)[0] if "/" in contract_path else ""
    main_contract = Path(contract_path).stem
    test_contract_name = f"{main_contract}_ExploitTest"
    
    if template_name == 'flash_loan_arbitrary_call':
        return {
            'challenge_folder': challenge_folder,
            'main_contract': main_contract,
            'test_contract_name': test_contract_name,
            'pool_balance': '1000 ether'
        }
    
    if template_name == 'reentrancy':
        contract_names = re.findall(r'contract\s+(\w+)\s*(?:is|\{)', contract_code)
        vulnerable_contract = contract_names[0] if contract_names else main_contract
        
        params = ask_ai_for_params(model, contract_code, [
            ('target_contract', f'Name of the vulnerable contract class (found in code: {", ".join(contract_names) if contract_names else "none"}, default: {vulnerable_contract})'),
            ('deposit_call', 'Solidity code to deposit (e.g., target.deposit{value: 1 ether}())'),
            ('withdraw_call', 'Solidity code to withdraw (e.g., target.withdraw())'),
            ('initial_balance', 'Initial balance for target (e.g., 10 ether)')
        ])
        
        if not params.get('target_contract') or params['target_contract'] == main_contract:
            params['target_contract'] = vulnerable_contract
        
        params['challenge_folder'] = challenge_folder
        params['main_contract'] = main_contract
        params['test_contract_name'] = test_contract_name
        return params
    
    if template_name == 'access_control':
        contract_names = re.findall(r'contract\s+(\w+)\s*(?:is|\{)', contract_code)
        vulnerable_contract = contract_names[0] if contract_names else main_contract
        
        params = ask_ai_for_params(model, contract_code, [
            ('target_contract', f'Name of the vulnerable contract (found in code: {", ".join(contract_names) if contract_names else "none"}, default: {vulnerable_contract})'),
            ('setup_code', 'Any setup code needed'),
            ('initial_assertion', 'Assertion that attacker is not owner initially'),
            ('exploit_call', 'The function call that exploits the vulnerability'),
            ('final_assertion', 'Assertion that attacker gained access')
        ])
        
        if not params.get('target_contract') or params['target_contract'] == main_contract:
            params['target_contract'] = vulnerable_contract
        
        params['challenge_folder'] = challenge_folder
        params['main_contract'] = main_contract
        params['test_contract_name'] = test_contract_name
        return params
    
    if template_name == 'delegatecall':
        contract_names = re.findall(r'contract\s+(\w+)\s*(?:is|\{)', contract_code)
        vulnerable_contract = contract_names[0] if contract_names else main_contract
        
        params = ask_ai_for_params(model, contract_code, [
            ('target_contract', f'Name of the vulnerable contract (default: {vulnerable_contract})'),
            ('setup_code', 'Any setup code needed'),
            ('initial_assertion', 'Initial state assertion'),
            ('exploit_call', 'The delegatecall exploit function call'),
            ('final_assertion', 'Final state assertion after exploit'),
            ('malicious_storage_layout', 'Storage layout matching target contract'),
            ('malicious_function', 'Function name to execute via delegatecall'),
            ('malicious_code', 'Code that executes in target context')
        ])
        
        if not params.get('target_contract'):
            params['target_contract'] = vulnerable_contract
        
        params['challenge_folder'] = challenge_folder
        params['main_contract'] = main_contract
        params['test_contract_name'] = test_contract_name
        return params
    
    if template_name == 'selfdestruct':
        contract_names = re.findall(r'contract\s+(\w+)\s*(?:is|\{)', contract_code)
        vulnerable_contract = contract_names[0] if contract_names else main_contract
        
        params = ask_ai_for_params(model, contract_code, [
            ('target_contract', f'Name of the vulnerable contract (default: {vulnerable_contract})'),
            ('setup_code', 'Any setup code needed'),
            ('initial_balance', 'Initial balance for attacker (e.g., 1 ether)'),
            ('exploit_logic', 'Code before selfdestruct call'),
            ('final_assertion', 'Final assertion after exploit')
        ])
        
        if not params.get('target_contract'):
            params['target_contract'] = vulnerable_contract
        if not params.get('initial_balance'):
            params['initial_balance'] = '1 ether'
        
        params['challenge_folder'] = challenge_folder
        params['main_contract'] = main_contract
        params['test_contract_name'] = test_contract_name
        return params
    
    if template_name == 'signature_replay':
        contract_names = re.findall(r'contract\s+(\w+)\s*(?:is|\{)', contract_code)
        vulnerable_contract = contract_names[0] if contract_names else main_contract
        
        params = ask_ai_for_params(model, contract_code, [
            ('target_contract', f'Name of the vulnerable contract (default: {vulnerable_contract})'),
            ('owner_address', 'Address of the owner who will sign'),
            ('target_balance', 'Initial balance of target contract'),
            ('amount', 'Amount to withdraw per signature'),
            ('signature_generation', 'Code to generate signature (using vm.sign)'),
            ('setup_code', 'Any additional setup')
        ])
        
        if not params.get('target_contract'):
            params['target_contract'] = vulnerable_contract
        if not params.get('amount'):
            params['amount'] = '1 ether'
        if not params.get('target_balance'):
            params['target_balance'] = '2 ether'
        
        params['challenge_folder'] = challenge_folder
        params['main_contract'] = main_contract
        params['test_contract_name'] = test_contract_name
        return params
    
    if template_name == 'function_selector_clash':
        contract_names = re.findall(r'contract\s+(\w+)\s*(?:is|\{)', contract_code)
        vulnerable_contract = contract_names[0] if contract_names else main_contract
        
        params = ask_ai_for_params(model, contract_code, [
            ('target_contract', f'Name of the vulnerable contract (default: {vulnerable_contract})'),
            ('exploit_contract', 'Name of exploit contract variable'),
            ('exploit_contract_name', 'Name of exploit contract class'),
            ('initial_balance', 'Initial balance for target'),
            ('collision_signature', 'Function signature that collides with target'),
            ('exploit_call', 'Call to exploit function'),
            ('setup_code', 'Any setup code')
        ])
        
        if not params.get('target_contract'):
            params['target_contract'] = vulnerable_contract
        if not params.get('exploit_contract'):
            params['exploit_contract'] = 'exploit'
        if not params.get('exploit_contract_name'):
            params['exploit_contract_name'] = 'FunctionSelectorClashExploit'
        if not params.get('initial_balance'):
            params['initial_balance'] = '10 ether'
        
        params['challenge_folder'] = challenge_folder
        params['main_contract'] = main_contract
        params['test_contract_name'] = test_contract_name
        return params
    
    if template_name == 'storage_collision':
        contract_names = re.findall(r'contract\s+(\w+)\s*(?:is|\{)', contract_code)
        vulnerable_contract = contract_names[0] if contract_names else main_contract
        
        params = ask_ai_for_params(model, contract_code, [
            ('target_contract', f'Name of the vulnerable contract (default: {vulnerable_contract})'),
            ('setup_code', 'Any setup code'),
            ('initial_assertion', 'Initial state assertion'),
            ('exploit_call', 'The exploit function call'),
            ('final_assertion', 'Final state assertion'),
            ('malicious_storage_layout', 'Storage layout that collides with target'),
            ('malicious_function', 'Function to execute via delegatecall'),
            ('malicious_code', 'Code that manipulates storage'),
            ('drain_function', 'Function to drain funds'),
            ('drain_code', 'Code to drain funds')
        ])
        
        if not params.get('target_contract'):
            params['target_contract'] = vulnerable_contract
        
        params['challenge_folder'] = challenge_folder
        params['main_contract'] = main_contract
        params['test_contract_name'] = test_contract_name
        return params
    
    if template_name == 'oracle_manipulation':
        contract_names = re.findall(r'contract\s+(\w+)\s*(?:is|\{)', contract_code)
        vulnerable_contract = contract_names[0] if contract_names else main_contract
        
        params = ask_ai_for_params(model, contract_code, [
            ('target_contract', f'Name of the vulnerable contract (default: {vulnerable_contract})'),
            ('token_contract', 'Name of token contract'),
            ('initial_balance', 'Initial balance for target'),
            ('attacker_balance', 'Initial balance for attacker'),
            ('price_manipulation', 'Code to manipulate price before exploit'),
            ('exploit_call', 'The exploit function call'),
            ('final_assertion', 'Final assertion after exploit'),
            ('setup_code', 'Any additional setup')
        ])
        
        if not params.get('target_contract'):
            params['target_contract'] = vulnerable_contract
        if not params.get('token_contract'):
            params['token_contract'] = 'Token'
        
        params['challenge_folder'] = challenge_folder
        params['main_contract'] = main_contract
        params['test_contract_name'] = test_contract_name
        return params
    
    if template_name == 'dos':
        contract_names = re.findall(r'contract\s+(\w+)\s*(?:is|\{)', contract_code)
        vulnerable_contract = contract_names[0] if contract_names else main_contract
        
        params = ask_ai_for_params(model, contract_code, [
            ('target_contract', f'Name of the vulnerable contract (default: {vulnerable_contract})'),
            ('setup_code', 'Any setup code'),
            ('victim_call', 'Normal call that victim would make'),
            ('victim_call_should_fail', 'Call that should fail after DoS'),
            ('attack_logic', 'Code in attack function'),
            ('receive_logic', 'Code in receive function (usually revert)')
        ])
        
        if not params.get('target_contract'):
            params['target_contract'] = vulnerable_contract
        
        params['challenge_folder'] = challenge_folder
        params['main_contract'] = main_contract
        params['test_contract_name'] = test_contract_name
        return params
    
    if template_name == 'flash_loan_erc20':
        contract_names = re.findall(r'contract\s+(\w+)\s*(?:is|\{)', contract_code)
        vulnerable_contract = contract_names[0] if contract_names else main_contract
        
        params = ask_ai_for_params(model, contract_code, [
            ('target_contract', f'Name of the lending pool contract (default: {vulnerable_contract})'),
            ('token_contract', 'Name of token contract'),
            ('pool_balance', 'Initial pool balance')
        ])
        
        if not params.get('target_contract'):
            params['target_contract'] = vulnerable_contract
        if not params.get('token_contract'):
            params['token_contract'] = 'Token'
        if not params.get('pool_balance'):
            params['pool_balance'] = '1000 ether'
        
        params['challenge_folder'] = challenge_folder
        params['main_contract'] = main_contract
        params['test_contract_name'] = test_contract_name
        return params
    
    if template_name == 'integer_overflow':
        contract_names = re.findall(r'contract\s+(\w+)\s*(?:is|\{)', contract_code)
        vulnerable_contract = contract_names[0] if contract_names else main_contract
        
        params = ask_ai_for_params(model, contract_code, [
            ('target_contract', f'Name of the vulnerable contract (default: {vulnerable_contract})'),
            ('setup_code', 'Any setup code'),
            ('exploit_call', 'The exploit function call'),
            ('final_assertion', 'Final assertion after exploit')
        ])
        
        if not params.get('target_contract'):
            params['target_contract'] = vulnerable_contract
        
        params['challenge_folder'] = challenge_folder
        params['main_contract'] = main_contract
        params['test_contract_name'] = test_contract_name
        return params
    
    if template_name == 'reuse_eth_value':
        contract_names = re.findall(r'contract\s+(\w+)\s*(?:is|\{)', contract_code)
        vulnerable_contract = contract_names[0] if contract_names else main_contract
        
        params = ask_ai_for_params(model, contract_code, [
            ('target_contract', f'Name of the vulnerable contract (default: {vulnerable_contract})'),
            ('deposit_amount', 'Amount to deposit'),
            ('exploit_call', 'The exploit call using msg.value in loop'),
            ('final_assertion', 'Final assertion'),
            ('setup_code', 'Any setup code')
        ])
        
        if not params.get('target_contract'):
            params['target_contract'] = vulnerable_contract
        if not params.get('deposit_amount'):
            params['deposit_amount'] = '10 ether'
        
        params['challenge_folder'] = challenge_folder
        params['main_contract'] = main_contract
        params['test_contract_name'] = test_contract_name
        return params
    
    if template_name == 'merkle_airdrop':
        contract_names = re.findall(r'contract\s+(\w+)\s*(?:is|\{)', contract_code)
        vulnerable_contract = contract_names[0] if contract_names else main_contract
        
        params = ask_ai_for_params(model, contract_code, [
            ('target_contract', f'Name of the airdrop contract (default: {vulnerable_contract})'),
            ('token_contract', 'Name of token contract'),
            ('merkle_root', 'Merkle root hash'),
            ('claim_amount', 'Amount to claim'),
            ('total_airdrop_amount', 'Total airdrop amount'),
            ('setup_code', 'Any setup code')
        ])
        
        if not params.get('target_contract'):
            params['target_contract'] = vulnerable_contract
        if not params.get('token_contract'):
            params['token_contract'] = 'Token'
        
        params['challenge_folder'] = challenge_folder
        params['main_contract'] = main_contract
        params['test_contract_name'] = test_contract_name
        return params
    
    if template_name == 'proxy_upgrade':
        contract_names = re.findall(r'contract\s+(\w+)\s*(?:is|\{)', contract_code)
        vulnerable_contract = contract_names[0] if contract_names else main_contract
        
        params = ask_ai_for_params(model, contract_code, [
            ('target_contract', f'Name of the proxy contract (default: {vulnerable_contract})'),
            ('setup_code', 'Any setup code'),
            ('initial_assertion', 'Initial state'),
            ('upgrade_call', 'Call to upgrade implementation'),
            ('exploit_call', 'Call to exploit malicious implementation'),
            ('final_assertion', 'Final state'),
            ('malicious_storage_layout', 'Storage layout for malicious contract'),
            ('malicious_function', 'Function name in malicious contract'),
            ('malicious_code', 'Code in malicious function')
        ])
        
        if not params.get('target_contract'):
            params['target_contract'] = vulnerable_contract
        
        params['challenge_folder'] = challenge_folder
        params['main_contract'] = main_contract
        params['test_contract_name'] = test_contract_name
        return params
    
    if template_name == 'generic':
        params = ask_ai_for_params(model, contract_code, [
            ('additional_imports', 'Any additional imports needed (or empty string)'),
            ('additional_contracts', 'Any helper contracts needed (or empty string)'),
            ('state_variables', 'State variables for the test contract'),
            ('setup_code', 'Code for setUp() function'),
            ('test_code', 'Code for testExploit() function with assertions')
        ])
        params['challenge_folder'] = challenge_folder
        params['main_contract'] = main_contract
        params['test_contract_name'] = test_contract_name
        return params
    
    return {
        'challenge_folder': challenge_folder,
        'main_contract': main_contract,
        'test_contract_name': test_contract_name
    }


def ask_ai_for_params(model, contract_code: str, param_list: List[Tuple[str, str]]) -> Dict:
    if not model:
        return {name: '' for name, _ in param_list}
    
    param_descriptions = "\n".join([f"- {name}: {desc}" for name, desc in param_list])
    
    system_prompt = f"""You are extracting specific values from a Solidity contract.
Return ONLY a JSON object with these keys:
{param_descriptions}

Rules:
- For code snippets, return valid Solidity code
- For names, return exact contract/function names from the code
- Keep values concise
- Return valid JSON only, no markdown"""

    user_content = f"""Contract:
```solidity
{contract_code}
```

Extract the parameters and return as JSON."""

    response = model.generate_response(
        system_prompt=system_prompt,
        user_content=user_content,
        temperature=0.1,
        max_tokens=1024
    )
    
    if not response:
        return {name: '' for name, _ in param_list}
    
    content = response.content if hasattr(response, 'content') else str(response)
    
    try:
        content = content.strip()
        if content.startswith('```'):
            content = re.search(r'```(?:json)?\s*\n?(.*?)\n?```', content, re.DOTALL)
            content = content.group(1) if content else '{}'
        return json.loads(content)
    except:
        return {name: '' for name, _ in param_list}
