import re
from typing import Tuple
from termcolor import cprint


def auto_fix_common_errors(broken_code: str, error_message: str) -> Tuple[str, list]:
    fixed_code = broken_code
    fixes_applied = []
    
    if "Source" in error_message and "not found" in error_message:
        old_path_patterns = [
            (r'contracts/([^/]+)/([^/]+)\.sol', r'challenges/\1/\2.sol'),
            (r'contracts/Reentrancy/', r'challenges/reentrancy/'),
            (r'contracts/Challenge\d+_', r'challenges/'),
        ]
        for old_pattern, new_pattern in old_path_patterns:
            if re.search(old_pattern, fixed_code):
                fixed_code = re.sub(old_pattern, new_pattern, fixed_code)
                fixes_applied.append(f"Fixed import path: {old_pattern} → {new_pattern}")
    
    if "Identifier already declared" in error_message or "already declared" in error_message.lower():
        if "interface" in error_message.lower() or "ILendingPool" in error_message:
            interface_pattern = r'interface\s+ILendingPool\s*\{[^}]*\}'
            matches = list(re.finditer(interface_pattern, fixed_code, re.MULTILINE | re.DOTALL))
            if matches and "import" in fixed_code:
                for match in reversed(matches):
                    start, end = match.span()
                    if end < len(fixed_code) and fixed_code[end] == '\n':
                        end += 1
                    fixed_code = fixed_code[:start] + fixed_code[end:]
                fixes_applied.append("Removed duplicate ILendingPool interface")
    
    if "Identifier not found" in error_message or "not found" in error_message.lower():
        if "VulnerableLendingPool" in error_message:
            if "contract VulnerableLendingPool" not in fixed_code:
                vulnerable_impl = '''
contract VulnerableLendingPool is ILendingPool {
    address public immutable token;

    constructor(address _token) {
        token = _token;
    }

    function flashLoan(
        uint256 /* amount */,
        address target,
        bytes calldata data
    ) external {
        (bool success, ) = target.call(data);
        require(success, "Flash loan callback failed");
    }
}
'''
                import_end = fixed_code.rfind('import')
                if import_end != -1:
                    next_newline = fixed_code.find('\n', import_end)
                    while next_newline != -1 and next_newline < len(fixed_code) - 1:
                        if fixed_code[next_newline + 1] not in [' ', '\t', 'i', '/']:
                            break
                        next_newline = fixed_code.find('\n', next_newline + 1)
                    insert_pos = next_newline + 1 if next_newline != -1 else import_end
                    fixed_code = fixed_code[:insert_pos] + "\n" + vulnerable_impl + fixed_code[insert_pos:]
                    fixes_applied.append("Added missing VulnerableLendingPool")
    
    return fixed_code, fixes_applied


def debug_fix_code(model, broken_code: str, error_message: str) -> str:
    auto_fixed, auto_fixes = auto_fix_common_errors(broken_code, error_message)
    
    proactive_fixes = []
    
    if re.search(r'contracts/[^/]+/', auto_fixed):
        auto_fixed = re.sub(r'contracts/([^/]+)/', r'challenges/\1/', auto_fixed)
        auto_fixed = re.sub(r'contracts/Reentrancy/', r'challenges/reentrancy/', auto_fixed, flags=re.IGNORECASE)
        proactive_fixes.append("Fixed old contracts/ paths to challenges/")
    
    if "import" in auto_fixed and "ILendingPool" in auto_fixed:
        if re.search(r'interface\s+ILendingPool\s*\{', auto_fixed):
            interface_pattern = r'interface\s+ILendingPool\s*\{[^}]*\}'
            matches = list(re.finditer(interface_pattern, auto_fixed, re.MULTILINE | re.DOTALL))
            if matches:
                for match in reversed(matches):
                    start, end = match.span()
                    if end < len(auto_fixed) and auto_fixed[end] == '\n':
                        end += 1
                    auto_fixed = auto_fixed[:start] + auto_fixed[end:]
                proactive_fixes.append("Removed duplicate ILendingPool interface")
    
    if "VulnerableLendingPool" in auto_fixed:
        vulnerable_defined = "contract VulnerableLendingPool" in auto_fixed
        if not vulnerable_defined:
            vulnerable_impl = '''
contract VulnerableLendingPool is ILendingPool {
    address public immutable token;

    constructor(address _token) {
        token = _token;
    }

    function flashLoan(
        uint256 /* amount */,
        address target,
        bytes calldata data
    ) external {
        (bool success, ) = target.call(data);
        require(success, "Flash loan callback failed");
    }
}
'''
            import_end = auto_fixed.rfind('import')
            if import_end != -1:
                next_newline = auto_fixed.find('\n', import_end)
                while next_newline != -1 and next_newline < len(auto_fixed) - 1:
                    if auto_fixed[next_newline + 1] not in [' ', '\t', 'i', '/']:
                        break
                    next_newline = auto_fixed.find('\n', next_newline + 1)
                insert_pos = next_newline + 1 if next_newline != -1 else import_end
                auto_fixed = auto_fixed[:insert_pos] + "\n" + vulnerable_impl + auto_fixed[insert_pos:]
                proactive_fixes.append("Added missing VulnerableLendingPool")
    
    if auto_fixes or proactive_fixes:
        all_fixes = auto_fixes + proactive_fixes
        cprint(f"   🔧 Auto-fixed: {', '.join(all_fixes)}", "green")
        return auto_fixed
    
    if not model:
        return auto_fixed
    
    system_prompt = """Fix this Solidity compilation error. Common fixes:

1. "Source not found" / File not found:
   - IMPORTANT: All imports must use "challenges/" not "contracts/"
   - Example: import "../challenges/reentrancy/VulnerableBank.sol" (correct)
   - NOT: import "../contracts/Reentrancy/Challenge1_Vault.sol" (wrong)
   - Fix any old "contracts/" paths to "challenges/"
   
2. "Identifier already declared" for interface/contract:
   - REMOVE the duplicate definition, keep only the import
   
3. "Identifier not found" for VulnerableLendingPool:
   - Make sure the contract is DEFINED before it's used
   
4. Public variable getter conflict:
   - Remove manual function, keep only: address public immutable token;

CRITICAL: Always use "challenges/" in import paths, never "contracts/".

Return ONLY fixed Solidity code."""

    response = model.generate_response(
        system_prompt=system_prompt,
        user_content=f"BROKEN CODE:\n```solidity\n{auto_fixed}\n```\n\nERROR:\n{error_message}\n\nFix it:",
        temperature=0.2,
        max_tokens=2048
    )
    
    if not response:
        return auto_fixed
    
    content = response.content if hasattr(response, 'content') else str(response)
    if '```' in content:
        match = re.search(r'```(?:solidity)?\s*\n(.*?)\n```', content, re.DOTALL)
        if match:
            content = match.group(1)
    
    fixed_by_ai = content.strip()
    
    final_fixed, final_fixes = auto_fix_common_errors(fixed_by_ai, error_message)
    if final_fixes:
        cprint(f"   🔧 Post-AI auto-fixed: {', '.join(final_fixes)}", "green")
    
    return final_fixed
