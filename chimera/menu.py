#!/usr/bin/env python3
"""
CHIMERA - Unified Security Intelligence Platform

Combines:
- contractHunter (Basilisk) - Discover vulnerable smart contracts
- walletHunter (Gargophias) - Profile and hunt whale wallets
- Bridge - Connect vulnerable contracts to exposed wallets
"""

import os
import sys
import json
import subprocess
import asyncio
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

CHIMERA_ROOT = Path(__file__).parent
PROJECT_ROOT = CHIMERA_ROOT.parent

CONTRACT_HUNTER_DIR = PROJECT_ROOT / "contractHunter"
WALLET_HUNTER_DIR = PROJECT_ROOT / "walletHunter"

sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(CONTRACT_HUNTER_DIR))
sys.path.insert(0, str(WALLET_HUNTER_DIR))

CHIMERA_REPORTS = CHIMERA_ROOT / "reports"
CHIMERA_RESULTS = CHIMERA_ROOT / "results"
CHIMERA_CONTRACTS = PROJECT_ROOT / "Contracts"
CHIMERA_REPORTS.mkdir(exist_ok=True)
CHIMERA_RESULTS.mkdir(exist_ok=True)
CHIMERA_CONTRACTS.mkdir(exist_ok=True)


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
    ORANGE = '\033[38;5;208m'
    
    BRIGHT_BLUE = '\033[94m'
    BRIGHT_CYAN = '\033[96m'
    BRIGHT_GREEN = '\033[92m'
    BRIGHT_YELLOW = '\033[93m'
    BRIGHT_MAGENTA = '\033[95m'


def clear_screen():
    os.system('clear' if os.name != 'nt' else 'cls')


def print_header(title: str):
    print(f"\n{Colors.ORANGE}{Colors.BOLD}{'=' * 70}{Colors.RESET}")
    print(f"{Colors.ORANGE}{Colors.BOLD}  {title}{Colors.RESET}")
    print(f"{Colors.ORANGE}{Colors.BOLD}{'=' * 70}{Colors.RESET}\n")


def print_tree(items: List[str], prefix: str = ""):
    for i, item in enumerate(items):
        is_last = i == len(items) - 1
        connector = "└──" if is_last else "├──"
        print(f"{prefix}{connector} {item}")


def get_input(prompt: str = "> ") -> str:
    try:
        return input(prompt).strip()
    except (EOFError, KeyboardInterrupt):
        return 'q'


def run_command(cmd: List[str], cwd: Path = None, silent: bool = False):
    try:
        if silent:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True, cwd=cwd)
            return result.stdout
        else:
            subprocess.run(cmd, check=True, cwd=cwd)
            return None
    except subprocess.CalledProcessError as e:
        print(f"{Colors.RED}Error: {e}{Colors.RESET}")
        return None
    except FileNotFoundError:
        print(f"{Colors.RED}Error: Command not found: {cmd[0]}{Colors.RESET}")
        return None


def get_contract_hunt_results() -> List[Path]:
    results_dir = CHIMERA_CONTRACTS
    if not results_dir.exists():
        return []
    return sorted(results_dir.glob("hunt_*.json"), reverse=True)


def get_wallet_profiles_count() -> int:
    profiles_dir = WALLET_HUNTER_DIR / "profiles"
    if not profiles_dir.exists():
        return 0
    count = 0
    for folder in profiles_dir.iterdir():
        if folder.is_dir():
            count += len(list(folder.glob("0x*")))
    return count


def get_vulnerable_contracts_count() -> int:
    results = get_contract_hunt_results()
    if not results:
        return 0
    
    try:
        with open(results[0], 'r') as f:
            data = json.load(f)
            return sum(1 for t in data.get('targets', []) if t.get('vulnerabilities'))
    except:
        return 0


def menu_contract_hunter():
    while True:
        clear_screen()
        print_header("🔱 CONTRACT HUNTER")
        print("Discover and scan vulnerable smart contracts\n")
        
        print(f"  {Colors.GREEN}[1]{Colors.RESET} 🎯 Hunt Contracts (Full Scan)")
        print(f"      → DeFiLlama discovery + Slither scanning")
        print()
        print(f"  {Colors.CYAN}[2]{Colors.RESET} 🔍 Custom Hunt")
        print(f"      → Configure filters manually")
        print()
        print(f"  {Colors.YELLOW}[3]{Colors.RESET} 📊 View Hunt Results")
        print(f"      → Browse previous scans")
        print()
        print(f"  {Colors.MAGENTA}[4]{Colors.RESET} 📁 Browse Contract Reports")
        print(f"      → View detailed vulnerability reports")
        print()
        print(f"  {Colors.RED}[b]{Colors.RESET} Back")
        print()
        
        choice = get_input().lower()
        
        if choice == 'b':
            return
        elif choice == '1':
            menu_contract_full_scan()
        elif choice == '2':
            menu_contract_custom_hunt()
        elif choice == '3':
            menu_view_hunt_results()
        elif choice == '4':
            menu_browse_contract_reports()


def menu_contract_full_scan():
    clear_screen()
    print_header("🎯 Contract Hunter → Full Scan")
    print("This will:")
    print_tree([
        "Discover protocols from DeFiLlama",
        "Filter by TVL, category, audit status",
        "Fetch contract source from Etherscan",
        "Scan with PatternScanner + Slither",
        "Generate vulnerability reports",
        "Save to Contracts/"
    ])
    print()
    
    save_choice = get_input("Save results? (Y/n): ").lower()
    save_flag = "--save" if save_choice != 'n' else ""
    
    scan_limit = get_input("Max contracts to scan (default: 10): ")
    scan_limit = scan_limit if scan_limit else "10"
    
    print(f"\n{Colors.CYAN}{'=' * 70}")
    print("Running Full Scan...")
    print(f"{'=' * 70}{Colors.RESET}\n")
    
    cmd = ["python3", "scripts/hunt.py", "--preset", "full_scan", "--scan", "--scan-limit", scan_limit]
    if save_flag:
        cmd.append(save_flag)
    
    run_command(cmd, cwd=CONTRACT_HUNTER_DIR)
    
    _copy_latest_results_to_chimera()
    
    input(f"\n{Colors.GREEN}Press Enter to continue...{Colors.RESET}")


def menu_contract_custom_hunt():
    clear_screen()
    print_header("🔍 Contract Hunter → Custom Hunt")
    
    min_tvl = get_input("Min TVL (USD, default: 100000): ")
    min_tvl = min_tvl if min_tvl else "100000"
    
    max_tvl = get_input("Max TVL (USD, optional): ")
    
    category = get_input("Category (Lending, DEX, Bridge, optional): ")
    
    chain = get_input("Chain (Ethereum, Arbitrum, optional): ")
    
    unaudited = get_input("Unaudited only? (y/N): ").lower()
    unaudited_flag = "--unaudited" if unaudited == 'y' else ""
    
    limit = get_input("Max results (default: 30): ")
    limit = limit if limit else "30"
    
    scan_choice = get_input("Scan for vulnerabilities? (Y/n): ").lower()
    scan_flag = "--scan" if scan_choice != 'n' else ""
    
    print(f"\n{Colors.CYAN}{'=' * 70}")
    print("Running custom hunt...")
    print(f"{'=' * 70}{Colors.RESET}\n")
    
    cmd = ["python3", "scripts/hunt.py", "--min-tvl", min_tvl, "--limit", limit, "--save"]
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
    
    run_command(cmd, cwd=CONTRACT_HUNTER_DIR)
    _copy_latest_results_to_chimera()
    
    input(f"\n{Colors.GREEN}Press Enter to continue...{Colors.RESET}")


def menu_view_hunt_results():
    clear_screen()
    print_header("📊 Contract Hunter → Hunt Results")
    
    results = get_contract_hunt_results()
    
    if not results:
        print("No hunt results found.")
        input(f"\n{Colors.GREEN}Press Enter to continue...{Colors.RESET}")
        return
    
    print("Recent hunts:\n")
    for i, result_path in enumerate(results[:10], 1):
        try:
            with open(result_path, 'r') as f:
                data = json.load(f)
            
            vuln_count = sum(1 for t in data.get('targets', []) if t.get('vulnerabilities'))
            total_tvl = sum(t.get('tvl', 0) for t in data.get('targets', []))
            
            timestamp = result_path.stem.replace('hunt_', '')
            print(f"  [{i}] {timestamp}")
            print(f"      Protocols: {len(data.get('targets', []))} | Vulnerable: {vuln_count} | TVL: ${total_tvl:,.0f}")
            print()
        except:
            print(f"  [{i}] {result_path.name} (error reading)")
    
    print(f"  [b] Back\n")
    
    choice = get_input()
    
    if choice.lower() == 'b':
        return
    elif choice.isdigit():
        idx = int(choice) - 1
        if 0 <= idx < len(results):
            _view_hunt_result_detail(results[idx])


def _view_hunt_result_detail(result_path: Path):
    clear_screen()
    print_header(f"Hunt Result: {result_path.name}")
    
    try:
        with open(result_path, 'r') as f:
            data = json.load(f)
        
        targets = data.get('targets', [])
        vulnerable = [t for t in targets if t.get('vulnerabilities')]
        
        print(f"Total Protocols: {len(targets)}")
        print(f"With Vulnerabilities: {len(vulnerable)}")
        print()
        
        if vulnerable:
            print(f"{Colors.RED}Vulnerable Contracts:{Colors.RESET}\n")
            for t in vulnerable[:10]:
                vulns = t.get('vulnerabilities', [])
                crit = sum(1 for v in vulns if v.get('severity') == 'Critical')
                high = sum(1 for v in vulns if v.get('severity') == 'High')
                
                print(f"  • {t.get('protocol_name', 'Unknown')}")
                print(f"    Address: {t.get('address', 'N/A')[:20]}...")
                print(f"    TVL: ${t.get('tvl', 0):,.0f}")
                print(f"    Findings: {len(vulns)} ({crit} critical, {high} high)")
                print()
        
    except Exception as e:
        print(f"Error reading result: {e}")
    
    input(f"\n{Colors.GREEN}Press Enter to continue...{Colors.RESET}")


def menu_browse_contract_reports():
    clear_screen()
    print_header("📁 Contract Hunter → Reports")
    
    reports_dir = CHIMERA_CONTRACTS / "_all"
    
    if not reports_dir.exists():
        print("No reports found. Run a scan first.")
        input(f"\n{Colors.GREEN}Press Enter to continue...{Colors.RESET}")
        return
    
    protocols = list(reports_dir.iterdir())
    
    if not protocols:
        print("No protocol reports found.")
        input(f"\n{Colors.GREEN}Press Enter to continue...{Colors.RESET}")
        return
    
    print("Protocol Reports:\n")
    for i, protocol_dir in enumerate(protocols[:15], 1):
        report_file = protocol_dir / "report.md"
        if report_file.exists():
            print(f"  [{i}] {protocol_dir.name}")
    
    print(f"\n  [b] Back\n")
    
    choice = get_input()
    
    if choice.lower() == 'b':
        return
    elif choice.isdigit():
        idx = int(choice) - 1
        if 0 <= idx < len(protocols):
            report_file = protocols[idx] / "report.md"
            if report_file.exists():
                clear_screen()
                with open(report_file, 'r') as f:
                    print(f.read())
                input(f"\n{Colors.GREEN}Press Enter to continue...{Colors.RESET}")


def menu_wallet_hunter():
    while True:
        clear_screen()
        print_header("🐋 WALLET HUNTER")
        print("Profile and hunt whale wallets\n")
        
        print(f"  {Colors.GREEN}[1]{Colors.RESET} 🔍 Hunt Whales")
        print(f"      → Discover high-value wallets")
        print()
        print(f"  {Colors.CYAN}[2]{Colors.RESET} 🔎 Analyze Address")
        print(f"      → Profile single wallet")
        print()
        print(f"  {Colors.YELLOW}[3]{Colors.RESET} 🎯 Target Search")
        print(f"      → Filter profiles by criteria")
        print()
        print(f"  {Colors.MAGENTA}[4]{Colors.RESET} 📊 View Profiles")
        print(f"      → Browse wallet profiles")
        print()
        print(f"  {Colors.WHITE}[5]{Colors.RESET} 🌐 IPFS OSINT Scan")
        print(f"      → NFT metadata analysis")
        print()
        print(f"  {Colors.RED}[b]{Colors.RESET} Back")
        print()
        
        choice = get_input().lower()
        
        if choice == 'b':
            return
        elif choice == '1':
            menu_hunt_whales()
        elif choice == '2':
            menu_analyze_wallet()
        elif choice == '3':
            menu_target_search()
        elif choice == '4':
            menu_view_profiles()
        elif choice == '5':
            menu_ipfs_scan()


def menu_hunt_whales():
    clear_screen()
    print_header("🔍 Wallet Hunter → Hunt Whales")
    print("This will discover and profile high-value wallets:\n")
    print_tree([
        "Query blockchain for whale wallets",
        "Generate full profiles",
        "IPFS OSINT (optional)",
        "Auto-categorization",
        "Save to profiles/"
    ])
    print()
    
    min_balance = get_input("Minimum balance (USD, default: 100000): ")
    min_balance = min_balance if min_balance else "100000"
    
    limit = get_input("Limit (default: 10): ")
    limit = limit if limit else "10"
    
    include_ipfs = get_input("Include IPFS OSINT? (Y/n): ").lower()
    ipfs_flag = include_ipfs != 'n'
    
    print(f"\n{Colors.CYAN}{'=' * 70}")
    print(f"Starting whale hunt...")
    print(f"  Min Balance: ${int(min_balance):,}")
    print(f"  Limit: {limit} wallets")
    print(f"  IPFS OSINT: {'Enabled' if ipfs_flag else 'Disabled'}")
    print(f"{'=' * 70}{Colors.RESET}\n")
    
    try:
        sys.path.insert(0, str(WALLET_HUNTER_DIR))
        from unified_profiler import hunt_whales_unified
        
        hunt_whales_unified(
            min_balance=int(min_balance),
            limit=int(limit),
            include_ipfs=ipfs_flag,
            api_key=os.getenv('ETHERSCAN_API_KEY')
        )
    except ImportError as e:
        print(f"{Colors.RED}Error importing walletHunter: {e}{Colors.RESET}")
        print("Falling back to CLI...")
        cmd = ["python3", "whale_menu.py"]
        run_command(cmd, cwd=WALLET_HUNTER_DIR)
    except Exception as e:
        print(f"{Colors.RED}Error: {e}{Colors.RESET}")
    
    input(f"\n{Colors.GREEN}Press Enter to continue...{Colors.RESET}")


def menu_analyze_wallet():
    clear_screen()
    print_header("🔎 Wallet Hunter → Analyze Address")
    
    address = get_input("Enter Ethereum address: ")
    
    if not address:
        return
    
    if not address.startswith('0x') or len(address) != 42:
        print(f"{Colors.RED}Invalid Ethereum address format{Colors.RESET}")
        input(f"\n{Colors.GREEN}Press Enter to continue...{Colors.RESET}")
        return
    
    include_ipfs = get_input("Include IPFS OSINT? (Y/n): ").lower()
    
    print(f"\n{Colors.CYAN}{'=' * 70}")
    print(f"Generating profile for {address}...")
    print(f"{'=' * 70}{Colors.RESET}\n")
    
    try:
        sys.path.insert(0, str(WALLET_HUNTER_DIR))
        from unified_profiler import UnifiedProfiler, ProfileConfig
        
        config = ProfileConfig(
            include_ipfs=(include_ipfs != 'n'),
            include_ens=True,
            include_verdicts=True,
            save_to_disk=True,
            verbose=True
        )
        profiler = UnifiedProfiler(config, api_key=os.getenv('ETHERSCAN_API_KEY'))
        profiler.generate_full_profile(address)
    except ImportError as e:
        print(f"{Colors.RED}Error: {e}{Colors.RESET}")
    except Exception as e:
        print(f"{Colors.RED}Error: {e}{Colors.RESET}")
    
    input(f"\n{Colors.GREEN}Press Enter to continue...{Colors.RESET}")


def menu_target_search():
    clear_screen()
    print_header("🎯 Wallet Hunter → Target Search")
    
    print("Search presets:\n")
    print(f"  {Colors.GREEN}[1]{Colors.RESET} Rich & Dumb (Prime Targets)")
    print(f"  {Colors.CYAN}[2]{Colors.RESET} Rich (>$1M)")
    print(f"  {Colors.YELLOW}[3]{Colors.RESET} Newcomers")
    print(f"  {Colors.MAGENTA}[4]{Colors.RESET} Gamblers")
    print(f"  {Colors.WHITE}[5]{Colors.RESET} Easy Targets")
    print(f"  {Colors.BLUE}[6]{Colors.RESET} Custom Search")
    print(f"\n  [b] Back\n")
    
    choice = get_input().lower()
    
    if choice == 'b':
        return
    
    cmd_map = {
        '1': ["python3", "target_search.py", "--rich-dumb", "-v"],
        '2': ["python3", "target_search.py", "--rich", "-v"],
        '3': ["python3", "target_search.py", "--newcomer", "-v"],
        '4': ["python3", "target_search.py", "--gambler", "-v"],
        '5': ["python3", "target_search.py", "--easy", "-v"],
    }
    
    if choice in cmd_map:
        run_command(cmd_map[choice], cwd=WALLET_HUNTER_DIR)
        input(f"\n{Colors.GREEN}Press Enter to continue...{Colors.RESET}")
    elif choice == '6':
        filters = get_input("Enter filters (e.g., --balance '>500k' --newcomer): ")
        if filters:
            cmd = ["python3", "target_search.py"] + filters.split() + ["-v"]
            run_command(cmd, cwd=WALLET_HUNTER_DIR)
            input(f"\n{Colors.GREEN}Press Enter to continue...{Colors.RESET}")


def menu_view_profiles():
    clear_screen()
    print_header("📊 Wallet Hunter → Profiles")
    
    profiles_dir = WALLET_HUNTER_DIR / "profiles"
    
    if not profiles_dir.exists():
        print("No profiles found.")
        input(f"\n{Colors.GREEN}Press Enter to continue...{Colors.RESET}")
        return
    
    folders = [
        ("🎯_actionable", "Actionable"),
        ("📦_archive", "Archive"),
        ("high_priority", "High Priority"),
        ("medium_priority", "Medium Priority"),
    ]
    
    print("Profile folders:\n")
    for i, (folder, name) in enumerate(folders, 1):
        folder_path = profiles_dir / folder
        count = len(list(folder_path.glob("0x*"))) if folder_path.exists() else 0
        print(f"  [{i}] {name}: {count} profiles")
    
    print(f"\n  [o] Open profiles folder")
    print(f"  [b] Back\n")
    
    choice = get_input().lower()
    
    if choice == 'b':
        return
    elif choice == 'o':
        _open_folder(profiles_dir)


def menu_ipfs_scan():
    clear_screen()
    print_header("🌐 Wallet Hunter → IPFS OSINT")
    
    address = get_input("Enter Ethereum address: ")
    
    if not address or not address.startswith('0x'):
        return
    
    print(f"\n{Colors.CYAN}Scanning IPFS for {address}...{Colors.RESET}\n")
    
    print("Use the walletHunter menu for full IPFS scanning.")
    print(f"Run: cd {WALLET_HUNTER_DIR} && python3 whale_menu.py")
    
    input(f"\n{Colors.GREEN}Press Enter to continue...{Colors.RESET}")


def menu_bridge():
    while True:
        clear_screen()
        print_header("🔗 CHIMERA BRIDGE")
        print("Connect vulnerable contracts to exposed wallets\n")
        
        print_tree([
            "Takes vulnerable contracts from contractHunter",
            "Queries on-chain for wallet interactions",
            "Profiles exposed wallets with walletHunter",
            "Generates exposure reports"
        ])
        print()
        
        print(f"  {Colors.GREEN}[1]{Colors.RESET} 🔗 Bridge Hunt Results")
        print(f"      → Process latest contract hunt → find exposed wallets")
        print()
        print(f"  {Colors.CYAN}[2]{Colors.RESET} 🎯 Bridge Single Contract")
        print(f"      → Enter contract address → find exposed wallets")
        print()
        print(f"  {Colors.YELLOW}[3]{Colors.RESET} 📊 View Exposure Reports")
        print(f"      → Browse bridge results")
        print()
        print(f"  {Colors.RED}[b]{Colors.RESET} Back")
        print()
        
        choice = get_input().lower()
        
        if choice == 'b':
            return
        elif choice == '1':
            menu_bridge_hunt_results()
        elif choice == '2':
            menu_bridge_single_contract()
        elif choice == '3':
            menu_view_exposure_reports()


def menu_bridge_hunt_results():
    clear_screen()
    print_header("🔗 Bridge → Hunt Results")
    
    results = get_contract_hunt_results()
    
    if not results:
        print("No hunt results found. Run a contract hunt first.")
        input(f"\n{Colors.GREEN}Press Enter to continue...{Colors.RESET}")
        return
    
    print("Select hunt result to bridge:\n")
    for i, result_path in enumerate(results[:5], 1):
        timestamp = result_path.stem.replace('hunt_', '')
        print(f"  [{i}] {timestamp}")
    
    print(f"\n  [b] Back\n")
    
    choice = get_input()
    
    if choice.lower() == 'b':
        return
    elif choice.isdigit():
        idx = int(choice) - 1
        if 0 <= idx < len(results):
            result_path = results[idx]
            
            max_contracts = get_input("Max contracts to process (default: 5): ")
            max_contracts = int(max_contracts) if max_contracts else 5
            
            print(f"\n{Colors.CYAN}{'=' * 70}")
            print(f"Bridging {result_path.name}...")
            print(f"{'=' * 70}{Colors.RESET}\n")
            
            try:
                sys.path.insert(0, str(CHIMERA_ROOT))
                from bridge import ContractWalletBridge
                
                bridge = ContractWalletBridge(output_dir=str(CHIMERA_REPORTS))
                
                asyncio.run(_run_bridge(bridge, str(result_path), max_contracts))
                
            except ImportError as e:
                print(f"{Colors.RED}Error importing bridge: {e}{Colors.RESET}")
            except Exception as e:
                print(f"{Colors.RED}Error: {e}{Colors.RESET}")
            
            input(f"\n{Colors.GREEN}Press Enter to continue...{Colors.RESET}")


async def _run_bridge(bridge, result_path: str, max_contracts: int):
    reports = await bridge.bridge_from_hunt_results(
        result_path,
        max_contracts=max_contracts,
        profile_wallets=True,
        verbose=True
    )
    
    if reports:
        summary = bridge.generate_exposure_summary(reports)
        
        summary_path = CHIMERA_REPORTS / f"exposure_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        with open(summary_path, 'w') as f:
            f.write(summary)
        
        print(f"\n{Colors.GREEN}Summary saved to: {summary_path}{Colors.RESET}")
        print(f"\n{summary[:1000]}...")


def menu_bridge_single_contract():
    clear_screen()
    print_header("🔗 Bridge → Single Contract")
    
    address = get_input("Enter contract address: ")
    
    if not address or not address.startswith('0x'):
        return
    
    chain = get_input("Chain (default: ethereum): ")
    chain = chain if chain else "ethereum"
    
    name = get_input("Protocol name (optional): ")
    
    print(f"\n{Colors.CYAN}{'=' * 70}")
    print(f"Finding exposed wallets for {address[:20]}...")
    print(f"{'=' * 70}{Colors.RESET}\n")
    
    try:
        sys.path.insert(0, str(CHIMERA_ROOT))
        from bridge import ContractWalletBridge
        
        bridge = ContractWalletBridge(output_dir=str(CHIMERA_REPORTS))
        
        async def run():
            report = await bridge.find_exposed_wallets(
                contract_address=address,
                chain=chain,
                contract_name=name,
                verbose=True
            )
            
            print(f"\n{Colors.GREEN}Top Exposed Wallets:{Colors.RESET}")
            for w in report.exposed_wallets[:10]:
                print(f"  {w.address[:15]}... - ${w.exposure_amount:,.0f}")
        
        asyncio.run(run())
        
    except Exception as e:
        print(f"{Colors.RED}Error: {e}{Colors.RESET}")
    
    input(f"\n{Colors.GREEN}Press Enter to continue...{Colors.RESET}")


def menu_view_exposure_reports():
    clear_screen()
    print_header("📊 Bridge → Exposure Reports")
    
    reports = list(CHIMERA_REPORTS.glob("exposure_*.json"))
    summaries = list(CHIMERA_REPORTS.glob("exposure_summary_*.md"))
    
    if not reports and not summaries:
        print("No exposure reports found. Run the bridge first.")
        input(f"\n{Colors.GREEN}Press Enter to continue...{Colors.RESET}")
        return
    
    print("Reports:\n")
    
    all_files = sorted(reports + summaries, reverse=True)
    for i, f in enumerate(all_files[:10], 1):
        print(f"  [{i}] {f.name}")
    
    print(f"\n  [o] Open reports folder")
    print(f"  [b] Back\n")
    
    choice = get_input().lower()
    
    if choice == 'b':
        return
    elif choice == 'o':
        _open_folder(CHIMERA_REPORTS)
    elif choice.isdigit():
        idx = int(choice) - 1
        if 0 <= idx < len(all_files):
            clear_screen()
            with open(all_files[idx], 'r') as f:
                print(f.read())
            input(f"\n{Colors.GREEN}Press Enter to continue...{Colors.RESET}")


def menu_settings():
    while True:
        clear_screen()
        print_header("⚙️ SETTINGS")
        
        print(f"  [1] View API Keys")
        print(f"  [2] Set Etherscan API Key")
        print(f"  [3] View Paths")
        print(f"  [4] Open Chimera Folder")
        print(f"\n  [b] Back\n")
        
        choice = get_input().lower()
        
        if choice == 'b':
            return
        elif choice == '1':
            etherscan_key = os.getenv('ETHERSCAN_API_KEY', 'Not set')
            print(f"\nEtherscan API Key: {etherscan_key[:10]}..." if etherscan_key != 'Not set' else "\nEtherscan API Key: Not set")
            input(f"\n{Colors.GREEN}Press Enter to continue...{Colors.RESET}")
        elif choice == '2':
            api_key = get_input("Enter Etherscan API Key: ")
            if api_key:
                env_file = CHIMERA_ROOT / '.env'
                with open(env_file, 'w') as f:
                    f.write(f'ETHERSCAN_API_KEY={api_key}\n')
                print(f"{Colors.GREEN}API key saved to chimera/.env{Colors.RESET}")
            input(f"\n{Colors.GREEN}Press Enter to continue...{Colors.RESET}")
        elif choice == '3':
            print(f"\nProject Root: {PROJECT_ROOT}")
            print(f"Contract Hunter: {CONTRACT_HUNTER_DIR}")
            print(f"Wallet Hunter: {WALLET_HUNTER_DIR}")
            print(f"Chimera: {CHIMERA_ROOT}")
            print(f"Reports: {CHIMERA_REPORTS}")
            input(f"\n{Colors.GREEN}Press Enter to continue...{Colors.RESET}")
        elif choice == '4':
            _open_folder(CHIMERA_ROOT)


def _copy_latest_results_to_chimera():
    results = get_contract_hunt_results()
    if results:
        latest = results[0]
        import shutil
        dest = CHIMERA_RESULTS / latest.name
        shutil.copy(latest, dest)
        print(f"{Colors.GREEN}Results copied to: {dest}{Colors.RESET}")


def _open_folder(path: Path):
    import subprocess
    import sys
    
    if sys.platform == "darwin":
        subprocess.run(["open", str(path)])
    elif sys.platform == "win32":
        subprocess.run(["explorer", str(path)])
    else:
        subprocess.run(["xdg-open", str(path)])


def main_menu():
    while True:
        clear_screen()
        
        print(f"""
{Colors.RED}{Colors.BOLD}
 ░▒▓██████▓▒░░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░▒▓██████████████▓▒░░▒▓████████▓▒░▒▓███████▓▒░ ░▒▓██████▓▒░  
░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░      ░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░ 
░▒▓█▓▒░      ░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░      ░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░ 
░▒▓█▓▒░      ░▒▓████████▓▒░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░░▒▓█▓▒░▒▓██████▓▒░ ░▒▓███████▓▒░░▒▓████████▓▒░ 
░▒▓█▓▒░      ░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░      ░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░ 
░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░      ░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░ 
 ░▒▓██████▓▒░░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░░▒▓█▓▒░▒▓████████▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░ 
                                                                                             
                                                                                             
{Colors.RESET}
{Colors.RED}    ═══════════════════════════════════════════════════════════════{Colors.RESET}
{Colors.YELLOW}{Colors.BOLD}    [ OFFENSIVE SECURITY INTELLIGENCE ]{Colors.RESET}
{Colors.RED}    ═══════════════════════════════════════════════════════════════{Colors.RESET}
""")
        
        vuln_count = get_vulnerable_contracts_count()
        profile_count = get_wallet_profiles_count()
        
        print(f"{Colors.YELLOW}  📊 Vulnerable Contracts: {vuln_count} | Wallet Profiles: {profile_count}{Colors.RESET}\n")
        
        print(f"{Colors.BOLD}{'─' * 60}{Colors.RESET}")
        
        print(f"""
  {Colors.GREEN}{Colors.BOLD}[1]{Colors.RESET} {Colors.GREEN}🔱 Contract Hunter{Colors.RESET}
      Discover & scan vulnerable smart contracts
      {Colors.WHITE}DeFiLlama → Etherscan → Slither{Colors.RESET}

  {Colors.CYAN}{Colors.BOLD}[2]{Colors.RESET} {Colors.CYAN}🐋 Wallet Hunter{Colors.RESET}
      Profile & hunt high-value wallets
      {Colors.WHITE}OSINT → Profiling → Categorization{Colors.RESET}

  {Colors.ORANGE}{Colors.BOLD}[3]{Colors.RESET} {Colors.ORANGE}🔗 Chimera Bridge{Colors.RESET}
      Connect contracts → exposed wallets
      {Colors.WHITE}Vulnerable Contract → At-Risk Wallets{Colors.RESET}

  {Colors.WHITE}{Colors.BOLD}[4]{Colors.RESET} {Colors.WHITE}⚙️  Settings{Colors.RESET}
      API keys & configuration

  {Colors.RED}{Colors.BOLD}[q]{Colors.RESET} {Colors.RED}Quit{Colors.RESET}
""")
        
        print(f"{Colors.BOLD}{'─' * 60}{Colors.RESET}\n")
        
        choice = get_input().lower()
        
        if choice == 'q':
            print(f"\n{Colors.ORANGE}Goodbye!{Colors.RESET}\n")
            sys.exit(0)
        elif choice == '1':
            menu_contract_hunter()
        elif choice == '2':
            menu_wallet_hunter()
        elif choice == '3':
            menu_bridge()
        elif choice == '4':
            menu_settings()


if __name__ == "__main__":
    try:
        main_menu()
    except KeyboardInterrupt:
        print(f"\n\n{Colors.ORANGE}Goodbye!{Colors.RESET}\n")
        sys.exit(0)
