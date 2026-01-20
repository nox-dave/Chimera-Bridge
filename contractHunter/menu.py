#!/usr/bin/env python3

import os
import sys
import json
import subprocess
from pathlib import Path
from typing import List, Dict, Optional
from dotenv import load_dotenv

load_dotenv()

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

SCRIPTS = {
    "analyze": "scripts/analyze.py",
    "generate": "scripts/generate.py",
    "test": "scripts/test.py",
    "hunt": "scripts/hunt.py",
}

CHALLENGES_ROOT = "challenges"
EXPLOITS_ROOT = "exploits"
RESULTS_ROOT = "results"
TEMPLATES_ROOT = "templates"

VULN_TYPES = [
    "reentrancy",
    "flash-loan",
    "access-control",
    "oracle-manipulation",
    "delegatecall",
    "integer-overflow",
    "selfdestruct",
]

class Colors:
    RESET = '\033[0m'
    BOLD = '\033[1m'
    
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    MAGENTA = '\033[95m'
    RED = '\033[91m'
    WHITE = '\033[97m'
    
    BRIGHT_BLUE = '\033[94m'
    BRIGHT_CYAN = '\033[96m'
    BRIGHT_GREEN = '\033[92m'
    BRIGHT_YELLOW = '\033[93m'
    BRIGHT_MAGENTA = '\033[95m'
    
    BG_BLUE = '\033[44m'
    BG_CYAN = '\033[46m'
    BG_GREEN = '\033[42m'
    BG_YELLOW = '\033[43m'

def clear_screen():
    os.system('clear' if os.name != 'nt' else 'cls')

def print_header(title: str):
    print(f"\n{Colors.CYAN}{Colors.BOLD}{'=' * 70}{Colors.RESET}")
    print(f"{Colors.CYAN}{Colors.BOLD}  {title}{Colors.RESET}")
    print(f"{Colors.CYAN}{Colors.BOLD}{'=' * 70}{Colors.RESET}\n")

def print_tree(items: List[str], prefix: str = ""):
    for i, item in enumerate(items):
        is_last = i == len(items) - 1
        connector = "└──" if is_last else "├──"
        print(f"{prefix}{connector} {item}")
        if not is_last:
            prefix_next = prefix + "│   "
        else:
            prefix_next = prefix + "    "

def get_input(prompt: str = "> ") -> str:
    try:
        return input(prompt).strip().lower()
    except (EOFError, KeyboardInterrupt):
        return 'q'

def run_command(cmd: List[str], silent: bool = False):
    try:
        if silent:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True, cwd=project_root)
            return result.stdout
        else:
            subprocess.run(cmd, check=True, cwd=project_root)
            return None
    except subprocess.CalledProcessError as e:
        print(f"Error: {e}")
        return None
    except FileNotFoundError:
        print(f"Error: Command not found: {cmd[0]}")
        return None

def get_challenges_in_folder(vuln_type: str) -> List[str]:
    folder_path = project_root / CHALLENGES_ROOT / vuln_type
    if not folder_path.exists():
        return []
    
    challenges = []
    for item in folder_path.iterdir():
        if item.is_file() and item.suffix == '.sol' and not item.name.startswith('I') and not item.name == 'Token.sol':
            challenges.append(item.name)
    
    return sorted(challenges)

def get_exploits_in_folder(vuln_type: str) -> List[str]:
    folder_path = project_root / EXPLOITS_ROOT / vuln_type
    if not folder_path.exists():
        return []
    
    exploits = []
    for item in folder_path.iterdir():
        if item.is_file() and item.suffix == '.sol':
            exploits.append(item.name)
    
    return sorted(exploits)

def display_challenge_list(vuln_type: str, page: int = 0, per_page: int = 10):
    challenges = get_challenges_in_folder(vuln_type)
    if not challenges:
        print(f"No challenges found in {vuln_type}")
        return None, None
    
    total = len(challenges)
    start = page * per_page
    end = min(start + per_page, total)
    
    print_header(f"Challenges: {vuln_type}")
    print(f"Showing {start + 1}-{end} of {total}\n")
    
    for i, challenge in enumerate(challenges[start:end], start=start + 1):
        print(f"  [{i}] {challenge}")
        readme_path = project_root / CHALLENGES_ROOT / vuln_type / "README.md"
        if readme_path.exists():
            print(f"      📖 README available")
        print()
    
    if total > per_page:
        print(f"\nPage {page + 1} of {(total + per_page - 1) // per_page}")
        print("Use 'n' for next, 'p' for previous, 'b' to go back")
    
    return start, end

def display_exploit_list(vuln_type: str, page: int = 0, per_page: int = 10):
    exploits = get_exploits_in_folder(vuln_type)
    if not exploits:
        print(f"No exploits found in {vuln_type}")
        return None, None
    
    total = len(exploits)
    start = page * per_page
    end = min(start + per_page, total)
    
    print_header(f"Exploits: {vuln_type}")
    print(f"Showing {start + 1}-{end} of {total}\n")
    
    for i, exploit in enumerate(exploits[start:end], start=start + 1):
        print(f"  [{i}] {exploit}")
        exploit_path = project_root / EXPLOITS_ROOT / vuln_type / exploit
        if exploit_path.exists():
            size = exploit_path.stat().st_size
            print(f"      📦 {size} bytes")
        print()
    
    if total > per_page:
        print(f"\nPage {page + 1} of {(total + per_page - 1) // per_page}")
        print("Use 'n' for next, 'p' for previous, 'b' to go back")
    
    return start, end

def menu_analyze_contract():
    while True:
        clear_screen()
        print_header("🔍 Analyze Contract")
        print("This will analyze a contract for vulnerabilities:")
        print()
        print_tree([
            "Load contract from challenges/",
            "LLM vulnerability analysis",
            "Pattern detection",
            "Display vulnerability report"
        ])
        print()
        
        print("Available vulnerability types:")
        for i, vuln_type in enumerate(VULN_TYPES, 1):
            count = len(get_challenges_in_folder(vuln_type))
            print(f"  [{i}] {vuln_type} ({count} challenges)")
        print("  [b] Back")
        print()
        
        choice = get_input()
        
        if choice == 'b':
            return
        elif choice.isdigit():
            idx = int(choice) - 1
            if 0 <= idx < len(VULN_TYPES):
                vuln_type = VULN_TYPES[idx]
                challenges = get_challenges_in_folder(vuln_type)
                if not challenges:
                    print(f"No challenges found in {vuln_type}")
                    input("\nPress Enter to continue...")
                    continue
                
                clear_screen()
                print_header(f"🔍 Analyze Contract → {vuln_type}")
                print("Select challenge:")
                for i, challenge in enumerate(challenges, 1):
                    print(f"  [{i}] {challenge}")
                print("  [b] Back")
                print()
                
                ch_choice = get_input()
                if ch_choice == 'b':
                    continue
                elif ch_choice.isdigit():
                    ch_idx = int(ch_choice) - 1
                    if 0 <= ch_idx < len(challenges):
                        challenge = challenges[ch_idx]
                        contract_path = f"{vuln_type}/{challenge}"
                        
                        print(f"\n{'='*70}")
                        print(f"Analyzing {contract_path}...")
                        print(f"{'='*70}\n")
                        
                        run_command(["python3", SCRIPTS["analyze"], contract_path])
                        input("\nPress Enter to continue...")
        else:
            print("Invalid choice")

def menu_generate_exploit():
    while True:
        clear_screen()
        print_header("⚔️ Generate Exploit")
        print("This will generate an exploit test from a template:")
        print()
        print_tree([
            "Analyze contract for vulnerabilities",
            "Detect vulnerability pattern",
            "Select appropriate template",
            "Extract parameters (AI-assisted)",
            "Fill template",
            "Compile & debug (auto-fix)",
            "Save to exploits/"
        ])
        print()
        
        print("Available vulnerability types:")
        for i, vuln_type in enumerate(VULN_TYPES, 1):
            count = len(get_challenges_in_folder(vuln_type))
            print(f"  [{i}] {vuln_type} ({count} challenges)")
        print("  [b] Back")
        print()
        
        choice = get_input()
        
        if choice == 'b':
            return
        elif choice.isdigit():
            idx = int(choice) - 1
            if 0 <= idx < len(VULN_TYPES):
                vuln_type = VULN_TYPES[idx]
                challenges = get_challenges_in_folder(vuln_type)
                if not challenges:
                    print(f"No challenges found in {vuln_type}")
                    input("\nPress Enter to continue...")
                    continue
                
                clear_screen()
                print_header(f"⚔️ Generate Exploit → {vuln_type}")
                print("Select challenge:")
                for i, challenge in enumerate(challenges, 1):
                    print(f"  [{i}] {challenge}")
                print("  [b] Back")
                print()
                
                ch_choice = get_input()
                if ch_choice == 'b':
                    continue
                elif ch_choice.isdigit():
                    ch_idx = int(ch_choice) - 1
                    if 0 <= ch_idx < len(challenges):
                        challenge = challenges[ch_idx]
                        contract_path = f"{vuln_type}/{challenge}"
                        
                        model = get_input("Model (default: gpt-4o-mini): ")
                        model = model if model else "gpt-4o-mini"
                        
                        max_debug = get_input("Max debug iterations (default: 3): ")
                        max_debug = max_debug if max_debug else "3"
                        
                        print(f"\n{'='*70}")
                        print(f"Generating exploit for {contract_path}...")
                        print(f"  Model: {model}")
                        print(f"  Max Debug: {max_debug}")
                        print(f"{'='*70}\n")
                        
                        cmd = ["python3", SCRIPTS["generate"], contract_path, "--model", model, "--max-debug", max_debug]
                        run_command(cmd)
                        input("\nPress Enter to continue...")
        else:
            print("Invalid choice")

def menu_test_exploit():
    while True:
        clear_screen()
        print_header("🧪 Test Exploit")
        print("This will run a Foundry test to verify an exploit:")
        print()
        print_tree([
            "Load exploit from exploits/",
            "Run forge test",
            "Display test results",
            "Log findings (optional)"
        ])
        print()
        
        print("Available vulnerability types:")
        for i, vuln_type in enumerate(VULN_TYPES, 1):
            count = len(get_exploits_in_folder(vuln_type))
            print(f"  [{i}] {vuln_type} ({count} exploits)")
        print("  [b] Back")
        print()
        
        choice = get_input()
        
        if choice == 'b':
            return
        elif choice.isdigit():
            idx = int(choice) - 1
            if 0 <= idx < len(VULN_TYPES):
                vuln_type = VULN_TYPES[idx]
                exploits = get_exploits_in_folder(vuln_type)
                if not exploits:
                    print(f"No exploits found in {vuln_type}")
                    input("\nPress Enter to continue...")
                    continue
                
                clear_screen()
                print_header(f"🧪 Test Exploit → {vuln_type}")
                print("Select exploit:")
                for i, exploit in enumerate(exploits, 1):
                    print(f"  [{i}] {exploit}")
                print("  [b] Back")
                print()
                
                ex_choice = get_input()
                if ex_choice == 'b':
                    continue
                elif ex_choice.isdigit():
                    ex_idx = int(ex_choice) - 1
                    if 0 <= ex_idx < len(exploits):
                        exploit = exploits[ex_idx]
                        exploit_path = f"{vuln_type}/{exploit}"
                        
                        contract_path = get_input("Contract path for logging (optional, press Enter to skip): ")
                        
                        print(f"\n{'='*70}")
                        print(f"Testing {exploit_path}...")
                        print(f"{'='*70}\n")
                        
                        cmd = ["python3", SCRIPTS["test"], exploit_path]
                        if contract_path:
                            cmd.extend(["--contract", contract_path])
                        run_command(cmd)
                        input("\nPress Enter to continue...")
        else:
            print("Invalid choice")

def menu_browse_challenges():
    while True:
        clear_screen()
        print_header("📚 Browse Challenges")
        print("View and study vulnerable contracts:")
        print()
        
        for i, vuln_type in enumerate(VULN_TYPES, 1):
            count = len(get_challenges_in_folder(vuln_type))
            print(f"  [{i}] {vuln_type} ({count} challenges)")
        print("  [b] Back")
        print()
        
        choice = get_input()
        
        if choice == 'b':
            return
        elif choice.isdigit():
            idx = int(choice) - 1
            if 0 <= idx < len(VULN_TYPES):
                vuln_type = VULN_TYPES[idx]
                challenges = get_challenges_in_folder(vuln_type)
                if not challenges:
                    print(f"No challenges found in {vuln_type}")
                    input("\nPress Enter to continue...")
                    continue
                
                page = 0
                per_page = 10
                
                while True:
                    clear_screen()
                    start, end = display_challenge_list(vuln_type, page, per_page)
                    if start is None:
                        input("\nPress Enter to continue...")
                        break
                    
                    ch_choice = get_input()
                    
                    if ch_choice == 'b':
                        break
                    elif ch_choice == 'n':
                        if end < len(challenges):
                            page += 1
                    elif ch_choice == 'p':
                        if page > 0:
                            page -= 1
                    elif ch_choice.isdigit():
                        ch_idx = int(ch_choice) - 1
                        if 0 <= ch_idx < len(challenges):
                            challenge = challenges[ch_idx]
                            view_challenge_details(vuln_type, challenge)
        else:
            print("Invalid choice")

def view_challenge_details(vuln_type: str, challenge: str):
    while True:
        clear_screen()
        print_header(f"Challenge: {challenge}")
        
        challenge_path = project_root / CHALLENGES_ROOT / vuln_type / challenge
        readme_path = project_root / CHALLENGES_ROOT / vuln_type / "README.md"
        
        if challenge_path.exists():
            print(f"File: {challenge_path}")
            size = challenge_path.stat().st_size
            print(f"Size: {size} bytes\n")
        
        if readme_path.exists():
            print("📖 README available")
        
        print("\n  [v] View contract code")
        print("  [r] View README")
        print("  [e] Edit in editor")
        print("  [b] Back")
        print()
        
        choice = get_input()
        
        if choice == 'b':
            return
        elif choice == 'v':
            if challenge_path.exists():
                with open(challenge_path, 'r') as f:
                    print("\n" + f.read())
                input("\nPress Enter to continue...")
        elif choice == 'r':
            if readme_path.exists():
                with open(readme_path, 'r') as f:
                    print("\n" + f.read())
                input("\nPress Enter to continue...")
        elif choice == 'e':
            editor = os.getenv('EDITOR', 'vim')
            subprocess.run([editor, str(challenge_path)])
        else:
            print("Invalid choice")

def menu_browse_exploits():
    while True:
        clear_screen()
        print_header("⚔️ Browse Exploits")
        print("View your working exploit PoCs:")
        print()
        
        for i, vuln_type in enumerate(VULN_TYPES, 1):
            count = len(get_exploits_in_folder(vuln_type))
            print(f"  [{i}] {vuln_type} ({count} exploits)")
        print("  [b] Back")
        print()
        
        choice = get_input()
        
        if choice == 'b':
            return
        elif choice.isdigit():
            idx = int(choice) - 1
            if 0 <= idx < len(VULN_TYPES):
                vuln_type = VULN_TYPES[idx]
                exploits = get_exploits_in_folder(vuln_type)
                if not exploits:
                    print(f"No exploits found in {vuln_type}")
                    input("\nPress Enter to continue...")
                    continue
                
                page = 0
                per_page = 10
                
                while True:
                    clear_screen()
                    start, end = display_exploit_list(vuln_type, page, per_page)
                    if start is None:
                        input("\nPress Enter to continue...")
                        break
                    
                    ex_choice = get_input()
                    
                    if ex_choice == 'b':
                        break
                    elif ex_choice == 'n':
                        if end < len(exploits):
                            page += 1
                    elif ex_choice == 'p':
                        if page > 0:
                            page -= 1
                    elif ex_choice.isdigit():
                        ex_idx = int(ex_choice) - 1
                        if 0 <= ex_idx < len(exploits):
                            exploit = exploits[ex_idx]
                            view_exploit_details(vuln_type, exploit)
        else:
            print("Invalid choice")

def view_exploit_details(vuln_type: str, exploit: str):
    while True:
        clear_screen()
        print_header(f"Exploit: {exploit}")
        
        exploit_path = project_root / EXPLOITS_ROOT / vuln_type / exploit
        
        if exploit_path.exists():
            print(f"File: {exploit_path}")
            size = exploit_path.stat().st_size
            print(f"Size: {size} bytes\n")
        
        print("\n  [v] View exploit code")
        print("  [t] Test exploit")
        print("  [e] Edit in editor")
        print("  [b] Back")
        print()
        
        choice = get_input()
        
        if choice == 'b':
            return
        elif choice == 'v':
            if exploit_path.exists():
                with open(exploit_path, 'r') as f:
                    print("\n" + f.read())
                input("\nPress Enter to continue...")
        elif choice == 't':
            exploit_path_str = f"{vuln_type}/{exploit}"
            print(f"\nTesting {exploit_path_str}...\n")
            run_command(["python3", SCRIPTS["test"], exploit_path_str])
            input("\nPress Enter to continue...")
        elif choice == 'e':
            editor = os.getenv('EDITOR', 'vim')
            subprocess.run([editor, str(exploit_path)])
        else:
            print("Invalid choice")

def menu_view_results():
    clear_screen()
    print_header("📊 View Results")
    
    findings_path = project_root / RESULTS_ROOT / "findings.json"
    
    if findings_path.exists():
        print("Recent findings:\n")
        try:
            with open(findings_path, 'r') as f:
                lines = f.readlines()
                recent = lines[-10:] if len(lines) > 10 else lines
                for line in recent:
                    if line.strip():
                        try:
                            finding = json.loads(line)
                            status = "✅" if finding.get('test_passed') else "❌"
                            print(f"  {status} {finding.get('contract', 'Unknown')} - {finding.get('vulnerability_type', 'Unknown')} ({finding.get('severity', 'Unknown')})")
                        except:
                            pass
        except:
            print("Error reading findings.json")
    else:
        print("No findings yet. Run analysis and generation to create findings.")
    
    print("\n  [f] View full findings.json")
    print("  [o] Open results folder")
    print("  [b] Back")
    print()
    
    choice = get_input()
    
    if choice == 'b':
        return
    elif choice == 'f':
        if findings_path.exists():
            with open(findings_path, 'r') as f:
                print("\n" + f.read())
            input("\nPress Enter to continue...")
    elif choice == 'o':
        if sys.platform == "darwin":
            subprocess.run(["open", str(project_root / RESULTS_ROOT)])
        elif sys.platform == "win32":
            subprocess.run(["explorer", str(project_root / RESULTS_ROOT)])
        else:
            subprocess.run(["xdg-open", str(project_root / RESULTS_ROOT)])

def menu_learning_log():
    while True:
        clear_screen()
        print_header("📖 Learning Log")
        
        log_path = project_root / "LEARNING_LOG.md"
        
        if log_path.exists():
            with open(log_path, 'r') as f:
                content = f.read()
                print(content)
        else:
            print("LEARNING_LOG.md not found. Create it to track your learning progress.")
        
        print("\n  [e] Edit learning log")
        print("  [b] Back")
        print()
        
        choice = get_input()
        
        if choice == 'b':
            return
        elif choice == 'e':
            editor = os.getenv('EDITOR', 'vim')
            subprocess.run([editor, str(log_path)])

def menu_hunt_contracts():
    while True:
        clear_screen()
        print_header("🎯 Hunt Contracts")
        print("Discover vulnerable smart contracts from DeFiLlama:")
        print()
        print_tree([
            "Fetch protocols from DeFiLlama",
            "Filter by TVL, category, audit status",
            "Fetch contract source from Etherscan",
            "Scan for vulnerabilities (PatternScanner + Slither)",
            "Generate verdicts and priority scores",
            "Save results to JSON"
        ])
        print()
        
        print("  [1] Run Full Scan (Default)")
        print("      → Hunt + Fetch + Scan with PatternScanner")
        print("  [2] Custom Hunt")
        print("  [b] Back")
        print()
        
        choice = get_input()
        
        if choice == 'b':
            return
        elif choice == '1' or choice == '':
            print(f"\n{'='*70}")
            print("Running Full Scan with PatternScanner...")
            print("  • Discovering protocols from DeFiLlama")
            print("  • Fetching contract source from Etherscan")
            print("  • Scanning for vulnerabilities (Pattern + Slither)")
            print("  • Generating verdicts and priority scores")
            print(f"{'='*70}\n")
            
            save_choice = get_input("Save results? (y/n, default: y): ")
            save_flag = "--save" if save_choice.lower() != 'n' else ""
            
            scan_limit = get_input("Max contracts to scan (default: 10): ")
            scan_limit = scan_limit if scan_limit else "10"
            
            cmd = ["python3", SCRIPTS["hunt"], "--preset", "full_scan", "--scan", "--scan-limit", scan_limit]
            if save_flag:
                cmd.append(save_flag)
            
            run_command(cmd)
            input("\nPress Enter to continue...")
        elif choice == '2':
            clear_screen()
            print_header("🎯 Hunt Contracts → Custom Hunt")
            print("Configure your hunt:")
            print()
            
            min_tvl = get_input("Min TVL (USD, default: 100000): ")
            min_tvl = min_tvl if min_tvl else "100000"
            
            max_tvl = get_input("Max TVL (USD, optional, press Enter to skip): ")
            
            category = get_input("Category (e.g., Lending, DEX, Bridge, optional): ")
            
            chain = get_input("Chain (e.g., Ethereum, Arbitrum, optional): ")
            
            unaudited = get_input("Unaudited only? (y/n, default: n): ")
            unaudited_flag = "--unaudited" if unaudited.lower() == 'y' else ""
            
            limit = get_input("Max results (default: 30): ")
            limit = limit if limit else "30"
            
            scan_choice = get_input("Scan for vulnerabilities? (y/n, default: n): ")
            scan_flag = "--scan" if scan_choice.lower() == 'y' else ""
            
            save_choice = get_input("Save results? (y/n, default: y): ")
            save_flag = "--save" if save_choice.lower() != 'n' else ""
            
            print(f"\n{'='*70}")
            print("Running custom hunt...")
            print(f"{'='*70}\n")
            
            cmd = ["python3", SCRIPTS["hunt"], "--min-tvl", min_tvl, "--limit", limit]
            if max_tvl:
                cmd.extend(["--max-tvl", max_tvl])
            if category:
                cmd.extend(["--category", category])
            if chain:
                cmd.extend(["--chain", chain])
            if unaudited_flag:
                cmd.append(unaudited_flag)
            if scan_flag:
                cmd.append(scan_flag)
            if save_flag:
                cmd.append(save_flag)
            
            run_command(cmd)
            input("\nPress Enter to continue...")
        elif choice == '3':
            print(f"\n{'='*70}")
            print("Available Presets:")
            print(f"{'='*70}\n")
            run_command(["python3", SCRIPTS["hunt"], "--list-presets"], silent=True)
            input("\nPress Enter to continue...")
        else:
            print("Invalid choice")

def menu_settings():
    while True:
        clear_screen()
        print_header("⚙️ Settings")
        print("  [1] View API Keys")
        print("  [2] Set OpenAI API Key")
        print("  [3] View Configuration")
        print("  [b] Back")
        print()
        
        choice = get_input()
        
        if choice == 'b':
            return
        elif choice == '1':
            api_key = os.getenv('OPENAI_KEY', 'Not set')
            etherscan_key = os.getenv('ETHERSCAN_API_KEY', 'Not set')
            print(f"\nOpenAI API Key: {api_key[:10]}..." if api_key != 'Not set' else "\nOpenAI API Key: Not set")
            print(f"Etherscan API Key: {etherscan_key[:10]}..." if etherscan_key != 'Not set' else "Etherscan API Key: Not set")
            input("\nPress Enter to continue...")
        elif choice == '2':
            api_key = get_input("Enter OpenAI API Key: ")
            if api_key:
                env_file = project_root / '.env'
                if env_file.exists():
                    with open(env_file, 'r') as f:
                        lines = f.readlines()
                    with open(env_file, 'w') as f:
                        for line in lines:
                            if not line.startswith('OPENAI_KEY='):
                                f.write(line)
                        f.write(f'OPENAI_KEY={api_key}\n')
                else:
                    with open(env_file, 'w') as f:
                        f.write(f'OPENAI_KEY={api_key}\n')
                print("API key saved to .env file")
            input("\nPress Enter to continue...")
        elif choice == '3':
            print("\nConfiguration:")
            print(f"  Challenges Root: {CHALLENGES_ROOT}")
            print(f"  Exploits Root: {EXPLOITS_ROOT}")
            print(f"  Results Root: {RESULTS_ROOT}")
            print(f"  Templates Root: {TEMPLATES_ROOT}")
            print(f"  Analyze Script: {SCRIPTS['analyze']}")
            print(f"  Generate Script: {SCRIPTS['generate']}")
            print(f"  Test Script: {SCRIPTS['test']}")
            print(f"  Hunt Script: {SCRIPTS['hunt']}")
            input("\nPress Enter to continue...")
        else:
            print("Invalid choice")

def get_total_challenges():
    total = 0
    for vuln_type in VULN_TYPES:
        total += len(get_challenges_in_folder(vuln_type))
    return total

def get_total_exploits():
    total = 0
    for vuln_type in VULN_TYPES:
        total += len(get_exploits_in_folder(vuln_type))
    return total

def main_menu():
    while True:
        clear_screen()
        print_header("🔱 BASILISK - MAIN MENU")
        total_challenges = get_total_challenges()
        total_exploits = get_total_exploits()
        print(f"{Colors.YELLOW}{Colors.BOLD}  Challenges: {total_challenges} | Exploits: {total_exploits}{Colors.RESET}\n")
        
        menu_items = [
            {
                'num': '1',
                'icon': '🔍',
                'title': 'Analyze Contract',
                'color': Colors.GREEN,
                'desc': 'Detect vulnerabilities in contracts',
                'features': ['LLM analysis', 'Pattern detection', 'Vulnerability report', 'Severity assessment']
            },
            {
                'num': '2',
                'icon': '⚔️',
                'title': 'Generate Exploit',
                'color': Colors.RED,
                'desc': 'AI-assisted exploit generation',
                'features': ['Template-based', 'Auto-parameter extraction', 'Auto-compile & debug', 'Path fixing']
            },
            {
                'num': '3',
                'icon': '🧪',
                'title': 'Test Exploit',
                'color': Colors.BLUE,
                'desc': 'Verify exploits with Foundry',
                'features': ['Forge test execution', 'Result verification', 'Findings logging', 'Test reports']
            },
            {
                'num': '4',
                'icon': '📚',
                'title': 'Browse Challenges',
                'color': Colors.CYAN,
                'desc': 'Study vulnerable contracts',
                'features': ['View by type', 'Read READMEs', 'View source', 'Edit contracts']
            },
            {
                'num': '5',
                'icon': '⚔️',
                'title': 'Browse Exploits',
                'color': Colors.YELLOW,
                'desc': 'View your exploit PoCs',
                'features': ['View by type', 'View source', 'Test exploits', 'Edit exploits']
            },
            {
                'num': '6',
                'icon': '📊',
                'title': 'View Results',
                'color': Colors.BRIGHT_CYAN,
                'desc': 'View analysis findings',
                'features': ['Recent findings', 'Full JSON log', 'Results folder']
            },
            {
                'num': '7',
                'icon': '📖',
                'title': 'Learning Log',
                'color': Colors.MAGENTA,
                'desc': 'Track your progress',
                'features': ['View log', 'Edit log', 'Cyfrin mapping']
            },
            {
                'num': '9',
                'icon': '🎯',
                'title': 'Hunt Contracts',
                'color': Colors.BRIGHT_YELLOW,
                'desc': 'Discover vulnerable protocols',
                'features': ['DeFiLlama integration', 'Preset hunts', 'Vulnerability scanning']
            },
            {
                'num': '8',
                'icon': '⚙️',
                'title': 'Settings',
                'color': Colors.WHITE,
                'desc': 'Configuration',
                'features': ['API key management', 'View configuration']
            }
        ]
        
        print(f"{Colors.BOLD}{'─' * 70}{Colors.RESET}")
        print(f"{Colors.GREEN}{Colors.BOLD}  EXPLOIT WORKFLOW{Colors.RESET}")
        print(f"{Colors.BOLD}{'─' * 70}{Colors.RESET}\n")
        
        item1 = menu_items[0]
        item2 = menu_items[1]
        item3 = menu_items[2]
        title1 = f"{item1['color']}{Colors.BOLD}[{item1['num']}]{Colors.RESET} {item1['color']}{item1['icon']} {item1['title']}{Colors.RESET}"
        title2 = f"{item2['color']}{Colors.BOLD}[{item2['num']}]{Colors.RESET} {item2['color']}{item2['icon']} {item2['title']}{Colors.RESET}"
        title3 = f"{item3['color']}{Colors.BOLD}[{item3['num']}]{Colors.RESET} {item3['color']}{item3['icon']} {item3['title']}{Colors.RESET}"
        print(f"  {title1:<25}│  {title2:<25}│  {title3}")
        desc1 = f"{item1['color']}     {item1['desc']}{Colors.RESET}"
        desc2 = f"{item2['color']}     {item2['desc']}{Colors.RESET}"
        desc3 = f"{item3['color']}     {item3['desc']}{Colors.RESET}"
        print(f"{desc1:<29}│  {desc2:<29}│  {desc3}")
        features1 = f"{item1['color']}     {' • '.join(item1['features'][:2])}{Colors.RESET}"
        features2 = f"{item2['color']}     {' • '.join(item2['features'][:2])}{Colors.RESET}"
        features3 = f"{item3['color']}     {' • '.join(item3['features'][:2])}{Colors.RESET}"
        print(f"{features1:<29}│  {features2:<29}│  {features3}")
        
        print(f"\n{Colors.BOLD}{'─' * 70}{Colors.RESET}")
        print(f"{Colors.BRIGHT_CYAN}{Colors.BOLD}  TRACKING{Colors.RESET}")
        print(f"{Colors.BOLD}{'─' * 70}{Colors.RESET}\n")
        
        item6 = menu_items[5]
        item7 = menu_items[6]
        title6 = f"{item6['color']}{Colors.BOLD}[{item6['num']}]{Colors.RESET} {item6['color']}{item6['icon']} {item6['title']}{Colors.RESET}"
        title7 = f"{item7['color']}{Colors.BOLD}[{item7['num']}]{Colors.RESET} {item7['color']}{item7['icon']} {item7['title']}{Colors.RESET}"
        print(f"  {title6:<38}│  {title7}")
        desc6 = f"{item6['color']}     {item6['desc']}{Colors.RESET}"
        desc7 = f"{item7['color']}     {item7['desc']}{Colors.RESET}"
        print(f"{desc6:<42}│  {desc7}")
        features6 = f"{item6['color']}     {' • '.join(item6['features'][:4])}{Colors.RESET}"
        features7 = f"{item7['color']}     {' • '.join(item7['features'][:4])}{Colors.RESET}"
        print(f"{features6:<42}│  {features7}")
        
        print(f"\n{Colors.BOLD}{'─' * 70}{Colors.RESET}")
        print(f"{Colors.WHITE}{Colors.BOLD}  CONFIG & DISCOVERY{Colors.RESET}")
        print(f"{Colors.BOLD}{'─' * 70}{Colors.RESET}\n")
        
        item8 = menu_items[7]
        item9 = menu_items[8]
        title8 = f"{item8['color']}{Colors.BOLD}[{item8['num']}]{Colors.RESET} {item8['color']}{item8['icon']} {item8['title']}{Colors.RESET}"
        title9 = f"{item9['color']}{Colors.BOLD}[{item9['num']}]{Colors.RESET} {item9['color']}{item9['icon']} {item9['title']}{Colors.RESET}"
        print(f"  {title8:<38}│  {title9}")
        desc8 = f"{item8['color']}     {item8['desc']}{Colors.RESET}"
        desc9 = f"{item9['color']}     {item9['desc']}{Colors.RESET}"
        print(f"{desc8:<42}│  {desc9}")
        features8 = f"{item8['color']}     {' • '.join(item8['features'][:4])}{Colors.RESET}"
        features9 = f"{item9['color']}     {' • '.join(item9['features'][:3])}{Colors.RESET}"
        print(f"{features8:<42}│  {features9}")
        
        print(f"\n{Colors.BOLD}{'─' * 70}{Colors.RESET}")
        print(f"  {Colors.RED}{Colors.BOLD}[q]{Colors.RESET} {Colors.RED}Quit{Colors.RESET}\n")
        
        choice = get_input()
        
        if choice == 'q':
            print("\nGoodbye!")
            sys.exit(0)
        elif choice == '1':
            menu_analyze_contract()
        elif choice == '2':
            menu_generate_exploit()
        elif choice == '3':
            menu_test_exploit()
        elif choice == '4':
            menu_browse_challenges()
        elif choice == '5':
            menu_browse_exploits()
        elif choice == '6':
            menu_view_results()
        elif choice == '7':
            menu_learning_log()
        elif choice == '8':
            menu_settings()
        elif choice == '9':
            menu_hunt_contracts()
        else:
            print("Invalid choice")
            input("\nPress Enter to continue...")

if __name__ == "__main__":
    try:
        main_menu()
    except KeyboardInterrupt:
        print("\n\nGoodbye!")
        sys.exit(0)
