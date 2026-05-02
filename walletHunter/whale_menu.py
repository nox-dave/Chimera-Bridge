#!/usr/bin/env python3

import os
import sys
import json
import subprocess
import webbrowser
from pathlib import Path
from typing import List, Dict, Optional
from dotenv import load_dotenv

load_dotenv()

sys.path.insert(0, os.path.dirname(__file__))
from unified_profiler import UnifiedProfiler, ProfileConfig, hunt_whales_unified

SCRIPTS = {
    "main": "main.py",
    "triage": "src/utils/priority_triage/legacy_triage.py",
    "osint_triage": "src/utils/priority_triage/osint_triage.py",
    "profiler": "src/core/wallet_profiler.py",
}

PROFILES_ROOT = "profiles"

PRIORITY_FOLDERS = [
    "high_priority",
    "medium_priority",
    "low_priority",
    "filtered",
]

CATEGORY_FOLDERS = [
    "🐸_meme_traders",
    "🏦_defi_farmers",
    "🎨_nft_collectors",
    "🏛️_dao_participants",
    "🌉_bridge_users",
    "🏢_institutions",
    "💎_og_whales",
    "🆕_fresh_whales",
    "🇺🇸_us_traders",
    "🇪🇺_eu_traders",
    "🌏_asia_traders",
    "🎯_high_value_targets",
    "🎰_gamblers",
    "🆕_newcomers",
    "🏆_status_seekers",
    "💤_dormant_whales",
    "🐟_easy_targets",
    "🦊_cautious_holders",
    "🧠_defi_natives",
    "🌙_night_traders",
    "📈_momentum_chasers",
    "🏛️_governance_voters",
    "💎_high_value",
    "🎯_prime_targets",
    "🤖_bots",
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
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            return result.stdout
        else:
            subprocess.run(cmd, check=True)
            return None
    except subprocess.CalledProcessError as e:
        print(f"Error: {e}")
        return None
    except FileNotFoundError:
        print(f"Error: Command not found: {cmd[0]}")
        return None

def open_url(url: str):
    try:
        webbrowser.open(url)
        print(f"Opened: {url}")
    except Exception as e:
        print(f"Error opening URL: {e}")

def open_file_manager(path: str):
    path = os.path.abspath(path)
    if not os.path.exists(path):
        print(f"Path does not exist: {path}")
        return
    
    try:
        if sys.platform == "darwin":
            subprocess.run(["open", path])
        elif sys.platform == "win32":
            subprocess.run(["explorer", path])
        else:
            subprocess.run(["xdg-open", path])
        print(f"Opened file manager: {path}")
    except Exception as e:
        print(f"Error opening file manager: {e}")

def get_profiles_in_folder(folder: str) -> List[str]:
    folder_path = os.path.join(PROFILES_ROOT, folder)
    if not os.path.exists(folder_path):
        return []
    
    profiles = []
    for item in os.listdir(folder_path):
        item_path = os.path.join(folder_path, item)
        if os.path.isdir(item_path) and item.startswith('0x'):
            profiles.append(item)
    
    return sorted(profiles)

def load_profile(address: str, folder: str) -> Optional[Dict]:
    profile_path = os.path.join(PROFILES_ROOT, folder, address, "profile.json")
    if os.path.exists(profile_path):
        try:
            with open(profile_path, 'r') as f:
                return json.load(f)
        except:
            pass
    return None

def display_profile_list(profiles: List[str], folder: str, page: int = 0, per_page: int = 10):
    total = len(profiles)
    start = page * per_page
    end = min(start + per_page, total)
    
    print_header(f"Profiles in {folder}")
    print(f"Showing {start + 1}-{end} of {total}\n")
    
    for i, address in enumerate(profiles[start:end], start=start + 1):
        profile = load_profile(address, folder)
        if profile:
            balance = profile.get('total_value_usd', 0)
            confidence = profile.get('risk_score', profile.get('confidence', 'N/A'))
            print(f"  [{i}] {address}")
            print(f"      Balance: ${balance:,.2f} | Confidence: {confidence}")
        else:
            print(f"  [{i}] {address}")
        print()
    
    if total > per_page:
        print(f"\nPage {page + 1} of {(total + per_page - 1) // per_page}")
        print("Use 'n' for next, 'p' for previous, 'b' to go back")
    
    return start, end

def menu_hunt_whales():
    while True:
        clear_screen()
        print_header("🔍 Bulk address discovery")
        print("  [1] Complete Profile (Unified)")
        print("  [2] Basic Profile (Legacy)")
        print("  [b] Back")
        print()
        
        choice = get_input()
        
        if choice == 'b':
            return
        elif choice == '1':
            clear_screen()
            print_header("🔍 Bulk discovery → Complete profile")
            print("This will generate complete intelligence profiles:")
            print()
            print_tree([
                "Wallet data",
                "Transaction analysis",
                "IPFS OSINT (auto if NFT activity)",
                "ENS resolution",
                "Verdict generation",
                "Auto-categorization"
            ])
            print()
            
            min_balance = get_input("Minimum balance (USD, default 100000): ")
            min_balance = float(min_balance) if min_balance else 100000
            
            limit = get_input("Limit (default 10): ")
            limit = int(limit) if limit else 10
            
            include_ipfs = get_input("Include IPFS OSINT? (y/n, default y): ")
            include_ipfs = include_ipfs != 'n'
            
            print(f"\n{'='*70}")
            print(f"Starting unified batch profiling...")
            print(f"  Min Balance: ${min_balance:,.0f}")
            print(f"  Limit: {limit} addresses")
            print(f"  IPFS OSINT: {'Enabled' if include_ipfs else 'Disabled'}")
            print(f"{'='*70}\n")
            
            try:
                hunt_whales_unified(
                    min_balance=int(min_balance),
                    limit=int(limit),
                    include_ipfs=include_ipfs,
                    api_key=os.getenv('ETHERSCAN_API_KEY')
                )
            except Exception as e:
                print(f"\n❌ Error: {e}")
                import traceback
                traceback.print_exc()
            
            input("\nPress Enter to continue...")
        elif choice == '2':
            clear_screen()
            print_header("🔍 Bulk discovery → Basic profile (legacy)")
            print("This will generate basic profiles (no IPFS/ENS/verdicts):")
            print()
            print_tree([
                "Wallet data",
                "Transaction analysis",
                "Basic categorization"
            ])
            print()
            
            min_balance = get_input("Minimum balance (USD, default 100000): ")
            min_balance = float(min_balance) if min_balance else 100000
            
            limit = get_input("Limit (default 10): ")
            limit = int(limit) if limit else 10
            
            print(f"\nStarting basic batch discovery...")
            print(f"  Min Balance: ${min_balance:,.0f}")
            print(f"  Limit: {limit} addresses\n")
            
            run_command(["python3", SCRIPTS["main"], "--find-whale", "--min-balance", str(min_balance), "--limit", str(limit)])
            input("\nPress Enter to continue...")
        else:
            print("Invalid choice")

def menu_profile_management():
    while True:
        clear_screen()
        print_header("📋 Profile Management")
        print("  [1] Run Priority Triage")
        print("  [2] Dry Run (Preview Changes)")
        print("  [3] Cleanup Trash")
        print("  [b] Back")
        print()
        
        choice = get_input()
        
        if choice == 'b':
            return
        elif choice == '1':
            clear_screen()
            print_header("📋 Profile Management → Run Priority Triage")
            print("This will score and organize all profiles:")
            print()
            print_tree([
                "Score all profiles (0-100)",
                "Consolidate to _all/",
                "Create actionable symlinks (top 50)",
                "Archive low scores (20-29)",
                "Trash disqualified (< 20)",
                "Clean category folders"
            ])
            print()
            print("🎯 Running Priority Triage System...")
            print("   This will score all profiles and organize them automatically.\n")
            run_command(["python3", "priority_triage.py"])
            input("\nPress Enter to continue...")
        elif choice == '2':
            clear_screen()
            print_header("📋 Profile Management → Dry Run")
            print("Preview changes without modifying files:")
            print()
            print_tree([
                "Calculate scores",
                "Show what would be actionable",
                "Show what would be archived",
                "Show what would be trashed",
                "No file modifications"
            ])
            print()
            print("🔍 Previewing changes (dry run)...\n")
            run_command(["python3", "priority_triage.py", "--dry-run"])
            input("\nPress Enter to continue...")
        elif choice == '3':
            clear_screen()
            print_header("📋 Profile Management → Cleanup Trash")
            print("Remove old trash profiles:")
            print()
            print_tree([
                "Scan trash folder",
                "Delete profiles > 7 days old",
                "Show cleanup summary"
            ])
            print()
            print("🗑️  Cleaning up old trash...\n")
            run_command(["python3", "priority_triage.py", "--cleanup-only"])
            input("\nPress Enter to continue...")
        else:
            print("Invalid choice")

def menu_analyze_address():
    while True:
        clear_screen()
        print_header("🔎 Analyze Address")
        print("  [1] Complete Profile (Unified)")
        print("  [2] Basic Analysis (Legacy)")
        print("  [b] Back")
        print()
        
        choice = get_input()
        
        if choice == 'b':
            return
        elif choice == '1':
            clear_screen()
            print_header("🔎 Analyze Address → COMPLETE Profile")
            print("This will generate complete intelligence profile:")
            print()
            print_tree([
                "Wallet data",
                "Transaction analysis",
                "IPFS OSINT (auto if NFT activity)",
                "ENS resolution",
                "Verdict generation",
                "Auto-categorization",
                "Save to profiles/"
            ])
            print()
            
            address = get_input("Enter Ethereum address: ")
            
            if not address:
                continue
            
            if not address.startswith('0x') or len(address) != 42:
                print("Invalid Ethereum address format")
                input("\nPress Enter to continue...")
                continue
            
            include_ipfs = get_input("Include IPFS OSINT? (y/n, default y): ")
            include_ipfs = include_ipfs != 'n'
            
            print(f"\n{'='*70}")
            print(f"Generating complete profile for {address}...")
            print(f"{'='*70}\n")
            
            try:
                config = ProfileConfig(
                    include_ipfs=include_ipfs,
                    include_ens=True,
                    include_verdicts=True,
                    save_to_disk=True,
                    verbose=True
                )
                profiler = UnifiedProfiler(config, api_key=os.getenv('ETHERSCAN_API_KEY'))
                profiler.generate_full_profile(address)
            except Exception as e:
                print(f"\n❌ Error: {e}")
                import traceback
                traceback.print_exc()
            
            input("\nPress Enter to continue...")
        elif choice == '2':
            clear_screen()
            print_header("🔎 Analyze Address → BASIC Analysis (Legacy)")
            print("This will perform basic analysis (no IPFS/ENS/verdicts):")
            print()
            print_tree([
                "Wallet data",
                "Transaction analysis",
                "Display report (no save)"
            ])
            print()
            
            address = get_input("Enter Ethereum address: ")
            
            if not address:
                continue
            
            if not address.startswith('0x') or len(address) != 42:
                print("Invalid Ethereum address format")
                input("\nPress Enter to continue...")
                continue
            
            print(f"\nAnalyzing {address}...")
            run_command(["python3", SCRIPTS["main"], address])
            input("\nPress Enter to continue...")
        else:
            print("Invalid choice")

def _convert_sets_to_lists(obj):
    if isinstance(obj, set):
        return list(obj)
    elif isinstance(obj, dict):
        return {k: _convert_sets_to_lists(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [_convert_sets_to_lists(item) for item in obj]
    return obj

def menu_ipfs_scan():
    clear_screen()
    print_header("🌐 IPFS OSINT Scan")
    print("This will scan NFT metadata for intelligence:")
    print()
    print_tree([
        "Fetch NFT transfers",
        "Extract IPFS hashes",
        "Analyze metadata",
        "Domain intelligence",
        "Social link discovery",
        "Verdict generation",
        "Update profile (if exists)"
    ])
    print()
    
    address = get_input("Enter Ethereum address: ")
    
    if not address:
        return
    
    if not address.startswith('0x') or len(address) != 42:
        print("Invalid Ethereum address format")
        input("\nPress Enter to continue...")
        return
    
    print(f"\n{'='*70}")
    print(f"Scanning IPFS for {address}...")
    print(f"{'='*70}")
    print("Fetching NFT transfers...")
    
    try:
        import sys
        import os
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from src.core.api_clients import EtherscanClient, RPCClient
        from src.utils.ipfs_osint import scan_wallet_ipfs, generate_ipfs_report
        
        etherscan_api_key = os.getenv('ETHERSCAN_API_KEY')
        etherscan = EtherscanClient(etherscan_api_key)
        rpc = RPCClient()
        
        nft_transfers = etherscan.get_nft_transfers(address, limit=50)
        
        if not nft_transfers:
            print("No NFT transfers found for this address")
            print("Checking current NFT holdings...")
            ipfs_data = scan_wallet_ipfs(address, None, rpc, limit=20, debug=True)
        else:
            print(f"Found {len(nft_transfers)} NFT transfers")
            print("Scanning IPFS metadata...")
            ipfs_data = scan_wallet_ipfs(address, nft_transfers, rpc, limit=20, debug=True)
        
        if ipfs_data:
            all_profile_dirs = []
            profile_data = None
            address_lower = address.lower()
            
            for root, dirs, files in os.walk("profiles"):
                root_lower = root.lower()
                if address_lower in root_lower:
                    for file in files:
                        if file == 'profile.json':
                            found_dir = os.path.dirname(os.path.join(root, file))
                            if found_dir not in all_profile_dirs:
                                all_profile_dirs.append(found_dir)
                            if profile_data is None:
                                profile_path = os.path.join(found_dir, file)
                                try:
                                    import json
                                    with open(profile_path, 'r') as f:
                                        profile_data = json.load(f)
                                except:
                                    pass
            
            report = generate_ipfs_report(ipfs_data, profile_data, rpc)
            print("\n" + report)
            
            findings = ipfs_data.get('findings', {})
            
            verdict_section = report.split('🎯 OSINT VERDICTS')
            has_verdicts = len(verdict_section) > 1 and len(verdict_section[1].strip()) > 10
            
            has_intelligence = (
                findings.get('total_hashes', 0) > 0 or
                findings.get('domains') or
                findings.get('linked_urls') or
                findings.get('usernames') or
                findings.get('emails') or
                findings.get('social_links') or
                findings.get('creators') or
                findings.get('collections') or
                has_verdicts
            )
            
            if has_intelligence:
                if all_profile_dirs:
                    import json
                    serializable_data = _convert_sets_to_lists(ipfs_data)
                    
                    if len(all_profile_dirs) > 1:
                        print(f"\n📁 Found profile in {len(all_profile_dirs)} locations, updating all...")
                    
                    for profile_dir in all_profile_dirs:
                        ipfs_file = os.path.join(profile_dir, 'ipfs_osint.json')
                        with open(ipfs_file, 'w') as f:
                            json.dump(serializable_data, f, indent=2)
                        
                        summary_file = os.path.join(profile_dir, 'summary.txt')
                        if os.path.exists(summary_file):
                            with open(summary_file, 'r', encoding='utf-8') as f:
                                existing_summary = f.read()
                            
                            if 'IPFS & DOMAIN OSINT ANALYSIS' not in existing_summary:
                                with open(summary_file, 'a', encoding='utf-8') as f:
                                    f.write("\n\n" + report)
                                print(f"\n✅ IPFS intelligence appended to {profile_dir}/summary.txt")
                            else:
                                old_report_start = existing_summary.find('━' * 80 + '\n🌐 IPFS & DOMAIN OSINT ANALYSIS')
                                if old_report_start != -1:
                                    old_report_end = existing_summary.find('\n\n', old_report_start + 100)
                                    if old_report_end == -1:
                                        old_report_end = len(existing_summary)
                                    new_summary = existing_summary[:old_report_start] + "\n\n" + report
                                    with open(summary_file, 'w', encoding='utf-8') as f:
                                        f.write(new_summary)
                                    print(f"\n✅ IPFS intelligence updated in {profile_dir}/summary.txt")
                                else:
                                    print(f"\n✅ IPFS intelligence already in {profile_dir}/summary.txt")
                        else:
                            with open(summary_file, 'w', encoding='utf-8') as f:
                                f.write(report)
                            print(f"\n✅ Created {profile_dir}/summary.txt with IPFS intelligence")
                        
                        print(f"✅ IPFS data saved to {ipfs_file}")
                else:
                    save = get_input("\nProfile not found. Save IPFS data anyway? (y/n): ")
                    if save == 'y':
                        import json
                        os.makedirs('ipfs_scans', exist_ok=True)
                        ipfs_file = os.path.join('ipfs_scans', f"{address.lower()}_ipfs_osint.json")
                        serializable_data = _convert_sets_to_lists(ipfs_data)
                        with open(ipfs_file, 'w') as f:
                            json.dump(serializable_data, f, indent=2)
                        print(f"✅ Saved to {ipfs_file}")
            else:
                if has_verdicts:
                    print("\n✅ Verdicts generated from wallet analysis (no IPFS-specific data found)")
                else:
                    print("\n⚠️  No valuable intelligence found (no IPFS hashes, domains, metadata, or verdicts)")
        else:
            print("No IPFS data found")
        
    except Exception as e:
        print(f"Error: {e}")
    
    input("\nPress Enter to continue...")

def browse_profiles(folder: str):
    profiles = get_profiles_in_folder(folder)
    if not profiles:
        print(f"No profiles found in {folder}")
        input("\nPress Enter to continue...")
        return
    
    page = 0
    per_page = 10
    
    while True:
        clear_screen()
        start, end = display_profile_list(profiles, folder, page, per_page)
        
        choice = get_input()
        
        if choice == 'b':
            return
        elif choice == 'n':
            if end < len(profiles):
                page += 1
        elif choice == 'p':
            if page > 0:
                page -= 1
        elif choice.isdigit():
            idx = int(choice) - 1
            if 0 <= idx < len(profiles):
                address = profiles[idx]
                view_profile_details(address, folder)
        else:
            print("Invalid choice")

def view_profile_details(address: str, folder: str):
    while True:
        clear_screen()
        print_header(f"Profile: {address}")
        
        profile = load_profile(address, folder)
        if profile:
            print(f"Balance: ${profile.get('total_value_usd', 0):,.2f}")
            print(f"ETH: {profile.get('eth_balance', 0):.4f}")
            print(f"Confidence: {profile.get('risk_score', 'N/A')}")
            print(f"Category: {profile.get('category', 'N/A')}")
            print(f"Priority: {profile.get('priority', 'N/A')}")
        
        summary_path = os.path.join(PROFILES_ROOT, folder, address, "summary.txt")
        if os.path.exists(summary_path):
            print("\nSummary available in summary.txt")
        
        print("\n  [e] Open Etherscan")
        print("  [d] Open Debank")
        print("  [v] View Summary")
        print("  [b] Back")
        print()
        
        choice = get_input()
        
        if choice == 'b':
            return
        elif choice == 'e':
            open_url(f"https://etherscan.io/address/{address}")
        elif choice == 'd':
            open_url(f"https://debank.com/profile/{address}")
        elif choice == 'v':
            if os.path.exists(summary_path):
                with open(summary_path, 'r') as f:
                    print("\n" + f.read())
                input("\nPress Enter to continue...")
            else:
                print("Summary file not found")
                input("\nPress Enter to continue...")

def menu_view_reports():
    while True:
        clear_screen()
        print_header("📊 View Reports")
        
        print("Priority Folders:")
        for i, folder in enumerate(PRIORITY_FOLDERS, 1):
            count = len(get_profiles_in_folder(folder))
            print(f"  [{i}] {folder} ({count} profiles)")
        
        print("\nCategory Folders:")
        category_start = 5
        for i, folder in enumerate(CATEGORY_FOLDERS):
            count = len(get_profiles_in_folder(folder))
            display_idx = category_start + i
            if display_idx < 10:
                print(f"  [{display_idx}] {folder} ({count} profiles)")
            else:
                letter = chr(ord('a') + display_idx - 10)
                print(f"  [{letter}] {folder} ({count} profiles)")
        
        print("\n  [t] View triage report")
        print("  [o] Open profiles folder in file manager")
        print("  [b] Back")
        print()
        
        choice = get_input()
        
        if choice == 'b':
            return
        elif choice == 't':
            report_path = os.path.join(PROFILES_ROOT, "triage_report.md")
            if os.path.exists(report_path):
                with open(report_path, 'r') as f:
                    print("\n" + f.read())
            else:
                print("Triage report not found. Generate it first from Profile Management.")
            input("\nPress Enter to continue...")
        elif choice == 'o':
            open_file_manager(PROFILES_ROOT)
            input("\nPress Enter to continue...")
        elif choice.isdigit():
            idx = int(choice)
            if 1 <= idx <= 4:
                browse_profiles(PRIORITY_FOLDERS[idx - 1])
            elif category_start <= idx < category_start + len(CATEGORY_FOLDERS):
                cat_idx = idx - category_start
                if 0 <= cat_idx < len(CATEGORY_FOLDERS):
                    browse_profiles(CATEGORY_FOLDERS[cat_idx])
        elif choice.isalpha() and len(choice) == 1:
            idx = ord(choice) - ord('a') + 10
            if category_start <= idx < category_start + len(CATEGORY_FOLDERS):
                cat_idx = idx - category_start
                if 0 <= cat_idx < len(CATEGORY_FOLDERS):
                    browse_profiles(CATEGORY_FOLDERS[cat_idx])
        else:
            print("Invalid choice")

def menu_target_search():
    while True:
        clear_screen()
        print_header("🎯 Investigative filters")
        print("  [1] Interactive Search")
        print("  [2] High balance + low sophistication (priority triage)")
        print("  [3] Significant holdings (>$1M)")
        print("  [4] Emerging or recent accounts")
        print("  [5] High-velocity speculative activity")
        print("  [6] Simplified triage queue")
        print("  [7] Europe-region activity pattern")
        print("  [8] Asia-Pacific activity pattern")
        print("  [9] Likely scam-airdrop recipients")
        print("  [0] Custom Search")
        print("  [b] Back")
        print()
        
        choice = get_input()
        
        if choice == 'b':
            return
        elif choice == '1':
            clear_screen()
            print_header("🎯 Investigative filters → Interactive")
            print("Query-based search with filters:")
            print()
            print_tree([
                "Enter search query",
                "Apply filters dynamically",
                "View results in table/verbose",
                "Export address list"
            ])
            print()
            print("🔍 Launching interactive search...\n")
            run_command(["python3", "target_search.py", "-i"])
            input("\nPress Enter to continue...")
        elif choice == '2':
            clear_screen()
            print_header("🎯 Investigative filters → Priority triage")
            print("High balance with low sophistication indicators:")
            print()
            print_tree([
                "Balance > $100k",
                "Sophistication: Novice",
                "High confidence real person",
                "Flag for structured review"
            ])
            print()
            print("🎯 Running priority triage preset...\n")
            run_command(["python3", "target_search.py", "--rich-dumb", "-v"])
            input("\nPress Enter to continue...")
        elif choice == '3':
            clear_screen()
            print_header("🎯 Investigative filters → Significant holdings")
            print("Addresses over $1M notional:")
            print()
            print_tree([
                "Balance > $1,000,000",
                "All categories",
                "Sorted by value"
            ])
            print()
            print("💰 Searching profiles over $1M notional...\n")
            run_command(["python3", "target_search.py", "--rich", "-v"])
            input("\nPress Enter to continue...")
        elif choice == '4':
            clear_screen()
            print_header("🎯 Investigative filters → Emerging accounts")
            print("Recently active or funded addresses:")
            print()
            print_tree([
                "Wallet age < 60 days",
                "Balance > $100k",
                "Low DeFi experience",
                "Elevated technical exposure indicators"
            ])
            print()
            print("🆕 Searching emerging-account preset...\n")
            run_command(["python3", "target_search.py", "--newcomer", "-v"])
            input("\nPress Enter to continue...")
        elif choice == '5':
            clear_screen()
            print_header("🎯 Investigative filters → Speculative activity")
            print("High-velocity meme or speculative token exposure:")
            print()
            print_tree([
                "Meme coin exposure",
                "High transaction frequency",
                "Leverage usage",
                "FOMO-driven behavior"
            ])
            print()
            print("🎰 Searching speculative-activity preset...\n")
            run_command(["python3", "target_search.py", "--gambler", "-v"])
            input("\nPress Enter to continue...")
        elif choice == '6':
            clear_screen()
            print_header("🎯 Investigative filters → Triage queue")
            print("Novice-style activity indicators:")
            print()
            print_tree([
                "Low sophistication",
                "CEX-dependent",
                "Limited DeFi exposure",
                "High trust level"
            ])
            print()
            print("🐟 Searching triage-queue preset...\n")
            run_command(["python3", "target_search.py", "--easy", "-v"])
            input("\nPress Enter to continue...")
        elif choice == '7':
            clear_screen()
            print_header("🎯 Investigative filters → Europe region")
            print("High balance with Europe-weighted activity windows:")
            print()
            print_tree([
                "Balance > $500k",
                "European timezone activity",
                "Active during EU hours"
            ])
            print()
            print("🇪🇺 Searching Europe-region preset...\n")
            run_command(["python3", "target_search.py", "--europe", "--balance", ">500k", "-v"])
            input("\nPress Enter to continue...")
        elif choice == '8':
            clear_screen()
            print_header("🎯 Investigative filters → Asia-Pacific region")
            print("High balance with Asia-Pacific-weighted activity windows:")
            print()
            print_tree([
                "Balance > $500k",
                "Asia-Pacific timezone activity",
                "Active during APAC hours"
            ])
            print()
            print("🌏 Searching Asia-Pacific preset...\n")
            run_command(["python3", "target_search.py", "--asia", "--balance", ">500k", "-v"])
            input("\nPress Enter to continue...")
        elif choice == '9':
            clear_screen()
            print_header("🎯 Investigative filters → Scam-airdrop pattern")
            print("Addresses showing scam NFT airdrop indicators:")
            print()
            print_tree([
                "Scam NFT domains detected",
                "Suspicious airdrops received",
                "Possible ongoing targeting",
                "Priority victim-side review"
            ])
            print()
            print("🎣 Searching scam-airdrop victim pattern...\n")
            run_command(["python3", "target_search.py", "--scam-victim", "-v"])
            input("\nPress Enter to continue...")
        elif choice == '0':
            clear_screen()
            print_header("🎯 Investigative filters → Custom")
            print("Enter custom filter combination:")
            print()
            print_tree([
                "Balance filters (>500k, <100k)",
                "Category filters (gamblers, newcomers)",
                "Confidence filters (>70, <50)",
                "Region filters (europe, asia)",
                "Custom combinations"
            ])
            print()
            print("Examples: --balance '>500k' --newcomer --confidence '>70'")
            filters = get_input("Filters: ")
            if filters:
                cmd = ["python3", "target_search.py"] + filters.split() + ["-v"]
                run_command(cmd)
            input("\nPress Enter to continue...")
        else:
            print("Invalid choice")

def menu_settings():
    while True:
        clear_screen()
        print_header("⚙️ Settings")
        print("  [1] View API Keys")
        print("  [2] Set Etherscan API Key")
        print("  [3] View Configuration")
        print("  [b] Back")
        print()
        
        choice = get_input()
        
        if choice == 'b':
            return
        elif choice == '1':
            api_key = os.getenv('ETHERSCAN_API_KEY', 'Not set')
            print(f"\nEtherscan API Key: {api_key[:10]}..." if api_key != 'Not set' else "\nEtherscan API Key: Not set")
            input("\nPress Enter to continue...")
        elif choice == '2':
            api_key = get_input("Enter Etherscan API Key: ")
            if api_key:
                env_file = Path('.env')
                if env_file.exists():
                    with open(env_file, 'r') as f:
                        lines = f.readlines()
                    with open(env_file, 'w') as f:
                        for line in lines:
                            if not line.startswith('ETHERSCAN_API_KEY='):
                                f.write(line)
                        f.write(f'ETHERSCAN_API_KEY={api_key}\n')
                else:
                    with open(env_file, 'w') as f:
                        f.write(f'ETHERSCAN_API_KEY={api_key}\n')
                print("API key saved to .env file")
            input("\nPress Enter to continue...")
        elif choice == '3':
            print("\nConfiguration:")
            print(f"  Profiles Root: {PROFILES_ROOT}")
            print(f"  Main Script: {SCRIPTS['main']}")
            print(f"  Triage Script: {SCRIPTS['triage']}")
            input("\nPress Enter to continue...")
        else:
            print("Invalid choice")

def get_total_profiles():
    total = 0
    for folder in PRIORITY_FOLDERS + CATEGORY_FOLDERS:
        total += len(get_profiles_in_folder(folder))
    return total

def main_menu():
    while True:
        clear_screen()
        print_header("🐋 WALLET INTELLIGENCE — MAIN MENU")
        total_profiles = get_total_profiles()
        print(f"{Colors.YELLOW}{Colors.BOLD}  Total Profiles: {total_profiles}{Colors.RESET}\n")
        
        menu_items = [
            {
                'num': '1',
                'icon': '🔍',
                'title': 'Bulk address discovery',
                'color': Colors.GREEN,
                'desc': 'Discover and profile multiple addresses',
                'features': ['Batch discovery', 'Full profiles', 'Auto-categorization', 'Batch intelligence']
            },
            {
                'num': '2',
                'icon': '🔎',
                'title': 'Analyze Address',
                'color': Colors.BLUE,
                'desc': 'Profile single address',
                'features': ['Wallet data', 'Transaction analysis', 'IPFS OSINT', 'ENS resolution', 'Verdicts']
            },
            {
                'num': '3',
                'icon': '📋',
                'title': 'Profile Management',
                'color': Colors.CYAN,
                'desc': 'Organize & triage profiles',
                'features': ['Priority scoring', 'Auto-organization', 'Archive/trash', 'Cleanup']
            },
            {
                'num': '4',
                'icon': '🎯',
                'title': 'Investigative filters',
                'color': Colors.YELLOW,
                'desc': 'Filter saved profiles',
                'features': ['Interactive search', 'Preset filters', 'Custom combinations']
            },
            {
                'num': '5',
                'icon': '📊',
                'title': 'View Reports',
                'color': Colors.BRIGHT_CYAN,
                'desc': 'Browse profile reports',
                'features': ['Category folders', 'Priority folders', 'Profile details']
            },
            {
                'num': '6',
                'icon': '🌐',
                'title': 'IPFS OSINT Scan',
                'color': Colors.MAGENTA,
                'desc': 'Manual IPFS analysis',
                'features': ['NFT metadata', 'Domain analysis', 'Social links', 'Verdicts']
            },
            {
                'num': '7',
                'icon': '⚙️',
                'title': 'Settings',
                'color': Colors.WHITE,
                'desc': 'Configuration',
                'features': ['API key management', 'View configuration']
            }
        ]
        
        print(f"{Colors.BOLD}{'─' * 70}{Colors.RESET}")
        print(f"{Colors.GREEN}{Colors.BOLD}  DISCOVERY & PROFILING (CASE SUPPORT){Colors.RESET}")
        print(f"{Colors.BOLD}{'─' * 70}{Colors.RESET}\n")
        
        item1 = menu_items[0]
        item2 = menu_items[1]
        title1 = f"{item1['color']}{Colors.BOLD}[{item1['num']}]{Colors.RESET} {item1['color']}{item1['icon']} {item1['title']}{Colors.RESET}"
        title2 = f"{item2['color']}{Colors.BOLD}[{item2['num']}]{Colors.RESET} {item2['color']}{item2['icon']} {item2['title']}{Colors.RESET}"
        print(f"  {title1:<38}│  {title2}")
        desc1 = f"{item1['color']}     {item1['desc']}{Colors.RESET}"
        desc2 = f"{item2['color']}     {item2['desc']}{Colors.RESET}"
        print(f"{desc1:<42}│  {desc2}")
        features1 = f"{item1['color']}     {' • '.join(item1['features'][:4])}{Colors.RESET}"
        features2 = f"{item2['color']}     {' • '.join(item2['features'][:4])}{Colors.RESET}"
        print(f"{features1:<42}│  {features2}")
        
        print(f"\n{Colors.BOLD}{'─' * 70}{Colors.RESET}")
        print(f"{Colors.CYAN}{Colors.BOLD}  ORGANIZATION & FILTERING{Colors.RESET}")
        print(f"{Colors.BOLD}{'─' * 70}{Colors.RESET}\n")
        
        item3 = menu_items[2]
        item4 = menu_items[3]
        title3 = f"{item3['color']}{Colors.BOLD}[{item3['num']}]{Colors.RESET} {item3['color']}{item3['icon']} {item3['title']}{Colors.RESET}"
        title4 = f"{item4['color']}{Colors.BOLD}[{item4['num']}]{Colors.RESET} {item4['color']}{item4['icon']} {item4['title']}{Colors.RESET}"
        print(f"  {title3:<38}│  {title4}")
        desc3 = f"{item3['color']}     {item3['desc']}{Colors.RESET}"
        desc4 = f"{item4['color']}     {item4['desc']}{Colors.RESET}"
        print(f"{desc3:<42}│  {desc4}")
        features3 = f"{item3['color']}     {' • '.join(item3['features'][:4])}{Colors.RESET}"
        features4 = f"{item4['color']}     {' • '.join(item4['features'][:4])}{Colors.RESET}"
        print(f"{features3:<42}│  {features4}")
        
        print(f"\n{Colors.BOLD}{'─' * 70}{Colors.RESET}")
        print(f"{Colors.BRIGHT_CYAN}{Colors.BOLD}  VIEWING & ANALYSIS{Colors.RESET}")
        print(f"{Colors.BOLD}{'─' * 70}{Colors.RESET}\n")
        
        item5 = menu_items[4]
        item6 = menu_items[5]
        title5 = f"{item5['color']}{Colors.BOLD}[{item5['num']}]{Colors.RESET} {item5['color']}{item5['icon']} {item5['title']}{Colors.RESET}"
        title6 = f"{item6['color']}{Colors.BOLD}[{item6['num']}]{Colors.RESET} {item6['color']}{item6['icon']} {item6['title']}{Colors.RESET}"
        print(f"  {title5:<38}│  {title6}")
        desc5 = f"{item5['color']}     {item5['desc']}{Colors.RESET}"
        desc6 = f"{item6['color']}     {item6['desc']}{Colors.RESET}"
        print(f"{desc5:<42}│  {desc6}")
        features5 = f"{item5['color']}     {' • '.join(item5['features'][:4])}{Colors.RESET}"
        features6 = f"{item6['color']}     {' • '.join(item6['features'][:4])}{Colors.RESET}"
        print(f"{features5:<42}│  {features6}")
        
        print(f"\n{Colors.BOLD}{'─' * 70}{Colors.RESET}")
        print(f"{Colors.WHITE}{Colors.BOLD}  CONFIGURATION{Colors.RESET}")
        print(f"{Colors.BOLD}{'─' * 70}{Colors.RESET}\n")
        
        item7 = menu_items[6]
        title7 = f"{item7['color']}{Colors.BOLD}[{item7['num']}]{Colors.RESET} {item7['color']}{item7['icon']} {item7['title']}{Colors.RESET}"
        print(f"  {title7}")
        desc7 = f"{item7['color']}     {item7['desc']}{Colors.RESET}"
        print(desc7)
        features7 = f"{item7['color']}     {' • '.join(item7['features'][:2])}{Colors.RESET}"
        print(features7)
        
        print(f"\n{Colors.BOLD}{'─' * 70}{Colors.RESET}")
        print(f"  {Colors.RED}{Colors.BOLD}[q]{Colors.RESET} {Colors.RED}Exit{Colors.RESET}\n")
        
        choice = get_input()
        
        if choice == 'q':
            print("\nExiting.")
            sys.exit(0)
        elif choice == '1':
            menu_hunt_whales()
        elif choice == '2':
            menu_analyze_address()
        elif choice == '3':
            menu_profile_management()
        elif choice == '4':
            menu_target_search()
        elif choice == '5':
            menu_view_reports()
        elif choice == '6':
            menu_ipfs_scan()
        elif choice == '7':
            menu_settings()
        else:
            print("Invalid choice")
            input("\nPress Enter to continue...")

if __name__ == "__main__":
    try:
        main_menu()
    except KeyboardInterrupt:
        print("\n\nGoodbye!")
        sys.exit(0)

