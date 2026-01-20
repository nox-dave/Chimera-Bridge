#!/usr/bin/env python3

import os
import json
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional, List, Dict
from collections import defaultdict
from ..osint_categorizer import categorize_for_osint, OSINT_CATEGORIES

PROFILES_ROOT = "profiles"

CATEGORIES = {
    "🐸_meme_traders": "Meme coin speculators (PEPE, SHIB, DOGE, etc.)",
    "🏦_defi_farmers": "Active DeFi users (Uniswap, Aave, Compound)",
    "🎨_nft_collectors": "NFT whales and collectors",
    "🏛️_dao_participants": "Governance token holders who participate",
    "🌉_bridge_users": "Cross-chain power users",
    "🏢_institutions": "Likely exchanges, funds, or bots",
    "💎_og_whales": "Old wallets (2+ years) with significant holdings",
    "🆕_fresh_whales": "New wallets (<30 days) with large balances",
    "🇺🇸_us_traders": "Likely US-based (Americas timezone)",
    "🇪🇺_eu_traders": "Likely Europe-based",
    "🌏_asia_traders": "Likely Asia-Pacific based",
    "🎯_high_value_targets": "Best candidates for deep investigation",
    "🎰_gamblers": "High-risk traders, meme coins, leverage users",
    "🆕_newcomers": "Fresh wallets (<60 days) with significant holdings",
    "🏆_status_seekers": "NFT collectors, blue chip holders, social identity tied to crypto",
    "💤_dormant_whales": "Large holders with low recent activity",
    "🐟_easy_targets": "Low sophistication, CEX-dependent, limited DeFi exposure",
    "🦊_cautious_holders": "Security-conscious, hardware wallet likely, minimal exposure",
    "🧠_defi_natives": "Advanced DeFi users, yield farmers, protocol power users",
    "🌙_night_traders": "Active during off-hours (likely different timezone or insomniac)",
    "📈_momentum_chasers": "Buys during pumps, sells during dumps, reactive trader",
    "🏛️_governance_voters": "Active in DAOs, holds governance tokens, votes on proposals",
    "💎_high_value": "Balance > $1M, confirmed individual (not institution)",
    "🎯_prime_targets": "Perfect storm: High value + Low sophistication + Vulnerable patterns",
    "🤖_bots": "Automated trading, MEV bots, arbitrage",
    "high_priority": "High confidence real individuals",
    "medium_priority": "Moderate confidence, worth monitoring",
    "low_priority": "Low confidence or low value",
    "filtered": "Likely exchanges/bots, filtered out",
    "🗑️_trash": "Marked for deletion",
    "📦_archive": "Old profiles kept for reference",
}

TRASH_RETENTION_DAYS = 7
ARCHIVE_AFTER_DAYS = 30
MIN_BALANCE_TO_KEEP = 50000
MIN_CONFIDENCE_TO_KEEP = 30

@dataclass
class ProfileMetadata:
    address: str
    filepath: str
    balance_usd: float = 0
    balance_eth: float = 0
    confidence: int = 50
    priority: str = "medium"
    is_meme_trader: bool = False
    is_defi_user: bool = False
    is_nft_collector: bool = False
    is_dao_participant: bool = False
    is_bridge_user: bool = False
    is_likely_bot: bool = False
    is_likely_exchange: bool = False
    likely_region: str = "Unknown"
    wallet_age_days: int = 0
    tx_count: int = 0
    last_active: str = ""
    file_created: datetime = None
    file_modified: datetime = None
    categories: List[str] = field(default_factory=list)
    triage_action: str = "keep"
    current_folder: str = ""

def parse_profile_json(filepath: str) -> Optional[ProfileMetadata]:
    try:
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        behavior = data.get('behavior', {})
        
        address = data.get('address', '')
        if not address:
            return None
        
        current_folder = os.path.basename(os.path.dirname(filepath))
        
        meta = ProfileMetadata(
            address=address.lower(),
            filepath=filepath,
            balance_usd=behavior.get('balance_usd', data.get('total_value_usd', data.get('balance_usd', 0))),
            balance_eth=behavior.get('balance_eth', data.get('eth_balance', data.get('balance_eth', 0))),
            confidence=behavior.get('confidence_score', data.get('risk_score', 50)),
            priority=data.get('priority', 'medium'),
            is_meme_trader=behavior.get('meme_exposure', False),
            is_defi_user=len(behavior.get('defi_protocols', [])) > 0 or data.get('defi_activity', False),
            is_nft_collector=len(behavior.get('nft_platforms', [])) > 0 or data.get('nft_activity', False),
            is_dao_participant='dao' in str(data.get('categories', '')).lower(),
            is_bridge_user=len(behavior.get('bridges_used', [])) > 0 or data.get('bridge_activity', False),
            is_likely_bot=behavior.get('confidence_score', data.get('risk_score', 50)) < 40 and data.get('tx_count', 0) > 10000,
            is_likely_exchange=data.get('tx_count', 0) > 50000 or data.get('category', '').lower() in ['likely_exchange', 'exchange'],
            likely_region=behavior.get('likely_region', 'Unknown'),
            wallet_age_days=data.get('wallet_age_days', data.get('age_days', 0)),
            tx_count=data.get('tx_count', 0),
            last_active=data.get('last_tx_date', data.get('last_active', '')),
            current_folder=current_folder
        )
        
        if not meta.wallet_age_days and data.get('first_seen'):
            try:
                first_seen = datetime.fromisoformat(data.get('first_seen').replace('Z', '+00:00'))
                age_days = (datetime.now() - first_seen.replace(tzinfo=None)).days
                meta.wallet_age_days = max(0, age_days)
            except:
                pass
        
        stat = os.stat(filepath)
        meta.file_created = datetime.fromtimestamp(stat.st_ctime)
        meta.file_modified = datetime.fromtimestamp(stat.st_mtime)
        
        return meta
        
    except Exception as e:
        print(f"    ⚠️ Error parsing {filepath}: {e}")
        return None

def parse_profile_txt(filepath: str) -> Optional[ProfileMetadata]:
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        meta = ProfileMetadata(
            address="",
            filepath=filepath,
        )
        
        if "Target:" in content:
            for line in content.split('\n'):
                if line.strip().startswith("Target:"):
                    meta.address = line.split("Target:")[-1].strip().lower()
                    break
        
        if not meta.address:
            return None
        
        if "Confidence:" in content:
            for line in content.split('\n'):
                if "Confidence:" in line and "%" in line:
                    try:
                        conf_str = line.split("Confidence:")[-1].strip()
                        meta.confidence = int(conf_str.replace('%', '').strip())
                    except:
                        pass
                    break
        
        if "Total Portfolio Value:" in content:
            for line in content.split('\n'):
                if "Total Portfolio Value:" in line:
                    try:
                        val_str = line.split("$")[-1].strip().replace(',', '').replace(' ', '')
                        meta.balance_usd = float(val_str)
                    except:
                        pass
                    break
        
        meta.is_meme_trader = "🐸 Meme Coins" in content or "Meme Coin" in content
        meta.is_defi_user = "DeFi Protocols:" in content and "None detected" not in content.split("DeFi Protocols:")[1][:50]
        meta.is_nft_collector = "NFT Platforms:" in content and "None detected" not in content.split("NFT Platforms:")[1][:50]
        meta.is_bridge_user = "Bridge Usage:" in content and "None detected" not in content.split("Bridge Usage:")[1][:50]
        
        if "Probable Region:" in content:
            for line in content.split('\n'):
                if "Probable Region:" in line:
                    meta.likely_region = line.split("Probable Region:")[-1].strip()
                    break
        
        if "Wallet Age:" in content:
            for line in content.split('\n'):
                if "Wallet Age:" in line:
                    try:
                        age_str = line.split("Wallet Age:")[-1].strip()
                        if "days" in age_str.lower():
                            meta.wallet_age_days = int(age_str.split()[0])
                    except:
                        pass
                    break
        
        stat = os.stat(filepath)
        meta.file_created = datetime.fromtimestamp(stat.st_ctime)
        meta.file_modified = datetime.fromtimestamp(stat.st_mtime)
        
        current_folder = os.path.basename(os.path.dirname(filepath))
        meta.current_folder = current_folder
        
        return meta
        
    except Exception as e:
        print(f"    ⚠️ Error parsing {filepath}: {e}")
        return None

def load_all_profiles(profiles_dir: str = PROFILES_ROOT) -> List[ProfileMetadata]:
    profiles = []
    profile_map = {}
    
    for root, dirs, files in os.walk(profiles_dir):
        if '🗑️_trash' in root or '📦_archive' in root:
            continue
            
        for file in files:
            filepath = os.path.join(root, file)
            
            if file == 'profile.json' or file.endswith('_data.json'):
                meta = parse_profile_json(filepath)
                if meta and meta.address:
                    profile_map[meta.address] = meta
            elif file == 'summary.txt' or file.endswith('_intel.txt') or file.endswith('_report.txt'):
                json_path = filepath.replace('_intel.txt', '_data.json').replace('_report.txt', '_data.json').replace('summary.txt', 'profile.json')
                if not os.path.exists(json_path):
                    meta = parse_profile_txt(filepath)
                    if meta and meta.address:
                        if meta.address not in profile_map:
                            profile_map[meta.address] = meta
                        else:
                            existing = profile_map[meta.address]
                            if not existing.confidence or existing.confidence == 50:
                                existing.confidence = meta.confidence
                            if not existing.balance_usd:
                                existing.balance_usd = meta.balance_usd
                            if not existing.is_meme_trader:
                                existing.is_meme_trader = meta.is_meme_trader
                            if not existing.is_defi_user:
                                existing.is_defi_user = meta.is_defi_user
                            if not existing.is_nft_collector:
                                existing.is_nft_collector = meta.is_nft_collector
                            if not existing.is_bridge_user:
                                existing.is_bridge_user = meta.is_bridge_user
                            if existing.likely_region == "Unknown":
                                existing.likely_region = meta.likely_region
                            if not existing.wallet_age_days:
                                existing.wallet_age_days = meta.wallet_age_days
    
    return list(profile_map.values())

def categorize_profile(meta: ProfileMetadata) -> List[str]:
    categories = []
    
    if meta.is_meme_trader:
        categories.append("🐸_meme_traders")
    
    if meta.is_defi_user:
        categories.append("🏦_defi_farmers")
    
    if meta.is_nft_collector:
        categories.append("🎨_nft_collectors")
    
    if meta.is_dao_participant:
        categories.append("🏛️_dao_participants")
    
    if meta.is_bridge_user:
        categories.append("🌉_bridge_users")
    
    if meta.is_likely_exchange or meta.is_likely_bot:
        categories.append("🏢_institutions")
    
    wallet_age = meta.wallet_age_days or 0
    if wallet_age > 730:
        categories.append("💎_og_whales")
    elif wallet_age < 30 and meta.balance_usd > 100000:
        categories.append("🆕_fresh_whales")
    
    if meta.likely_region == "Americas":
        categories.append("🇺🇸_us_traders")
    elif meta.likely_region == "Europe":
        categories.append("🇪🇺_eu_traders")
    elif meta.likely_region == "Asia-Pacific":
        categories.append("🌏_asia_traders")
    
    if (meta.confidence >= 70 and 
        meta.balance_usd >= 500000 and 
        not meta.is_likely_exchange and 
        not meta.is_likely_bot):
        categories.append("🎯_high_value_targets")
    
    profile_dict = {
        "balance_usd": meta.balance_usd,
        "total_value_usd": meta.balance_usd,
        "tx_count": meta.tx_count,
        "wallet_age_days": wallet_age,
        "age_days": wallet_age,
        "risk_score": meta.confidence,
        "nft_activity": meta.is_nft_collector,
        "defi_activity": meta.is_defi_user,
        "bridge_activity": meta.is_bridge_user,
        "behavior": {
            "confidence_score": meta.confidence,
            "meme_exposure": meta.is_meme_trader,
            "sophistication": "Unknown",
            "defi_protocols": ["Uniswap"] if meta.is_defi_user else [],
            "nft_platforms": ["OpenSea"] if meta.is_nft_collector else [],
            "bridges_used": ["Bridge"] if meta.is_bridge_user else [],
            "likely_region": meta.likely_region,
        }
    }
    
    osint_categories = categorize_for_osint(profile_dict)
    for cat in osint_categories:
        if cat not in categories:
            categories.append(cat)
    
    return categories

def determine_triage_action(meta: ProfileMetadata) -> str:
    if meta.confidence >= 75 and meta.balance_usd >= 500000:
        return "promote"
    
    if meta.confidence >= MIN_CONFIDENCE_TO_KEEP and meta.balance_usd >= MIN_BALANCE_TO_KEEP:
        return "keep"
    
    if meta.file_modified and (datetime.now() - meta.file_modified).days > ARCHIVE_AFTER_DAYS:
        if meta.balance_usd >= 100000 or meta.confidence >= 50:
            return "archive"
    
    if meta.balance_usd < MIN_BALANCE_TO_KEEP and meta.confidence < MIN_CONFIDENCE_TO_KEEP:
        return "trash"
    
    if (meta.is_likely_bot or meta.is_likely_exchange) and meta.confidence < 40:
        return "trash"
    
    return "keep"

def ensure_category_dirs(profiles_dir: str = PROFILES_ROOT):
    for category in CATEGORIES.keys():
        cat_dir = os.path.join(profiles_dir, category)
        os.makedirs(cat_dir, exist_ok=True)

def move_profile(meta: ProfileMetadata, target_category: str, profiles_dir: str = PROFILES_ROOT):
    target_dir = os.path.join(profiles_dir, target_category)
    os.makedirs(target_dir, exist_ok=True)
    
    source_dir = os.path.dirname(meta.filepath)
    address = meta.address or os.path.basename(source_dir)
    
    target_address_dir = os.path.join(target_dir, address)
    
    if os.path.exists(target_address_dir) and target_address_dir != source_dir:
        for file in os.listdir(source_dir):
            src = os.path.join(source_dir, file)
            dst = os.path.join(target_address_dir, file)
            if os.path.exists(src) and not os.path.exists(dst):
                shutil.copy2(src, dst)
        shutil.rmtree(source_dir)
    elif source_dir != target_address_dir:
        if os.path.exists(target_address_dir):
            shutil.rmtree(target_address_dir)
        shutil.move(source_dir, target_address_dir)
    
    return 1

def copy_profile_to_category(meta: ProfileMetadata, category: str, profiles_dir: str = PROFILES_ROOT):
    cat_dir = os.path.join(profiles_dir, category)
    os.makedirs(cat_dir, exist_ok=True)
    
    source_dir = os.path.dirname(meta.filepath)
    address = meta.address or os.path.basename(source_dir)
    
    target_dir = os.path.join(cat_dir, address)
    
    if os.path.exists(target_dir):
        return 0
    
    try:
        shutil.copytree(source_dir, target_dir)
        return 1
    except Exception as e:
        print(f"    ⚠️ Error copying {address[:16]} to {category}: {e}")
        return 0

def cleanup_trash(profiles_dir: str = PROFILES_ROOT, retention_days: int = TRASH_RETENTION_DAYS):
    trash_dir = os.path.join(profiles_dir, "🗑️_trash")
    if not os.path.exists(trash_dir):
        return 0
    
    deleted = 0
    cutoff = datetime.now() - timedelta(days=retention_days)
    
    for root, dirs, files in os.walk(trash_dir):
        for file in files:
            filepath = os.path.join(root, file)
            try:
                mtime = datetime.fromtimestamp(os.path.getmtime(filepath))
                if mtime < cutoff:
                    os.remove(filepath)
                    deleted += 1
            except Exception as e:
                print(f"    ⚠️ Error deleting {file}: {e}")
    
    for root, dirs, files in os.walk(trash_dir, topdown=False):
        for dir_name in dirs:
            dir_path = os.path.join(root, dir_name)
            try:
                if not os.listdir(dir_path):
                    os.rmdir(dir_path)
            except:
                pass
    
    return deleted

def cleanup_empty_dirs(profiles_dir: str = PROFILES_ROOT):
    removed = 0
    
    category_folder_names = set(CATEGORIES.keys())
    protected_folders = category_folder_names | {'🗑️_trash', '📦_archive'}
    
    for root, dirs, files in os.walk(profiles_dir, topdown=False):
        for dir_name in dirs:
            dir_path = os.path.join(root, dir_name)
            try:
                if not os.listdir(dir_path):
                    if root == profiles_dir:
                        if dir_name not in protected_folders:
                            os.rmdir(dir_path)
                            removed += 1
                    else:
                        os.rmdir(dir_path)
                        removed += 1
            except:
                pass
    
    return removed

def cleanup_link_files(profiles_dir: str = PROFILES_ROOT):
    removed = 0
    
    for root, dirs, files in os.walk(profiles_dir):
        for file in files:
            if file.endswith('_link.txt'):
                filepath = os.path.join(root, file)
                try:
                    os.remove(filepath)
                    removed += 1
                except:
                    pass
    
    return removed

def reset_category_folders(profiles_dir: str = PROFILES_ROOT):
    removed = 0
    
    emoji_prefixes = ('🐸', '🏦', '🎨', '🏛️', '🌉', '🏢', '💎', '🆕', '🇺🇸', '🇪🇺', '🌏', '🎯', '🎰', '🏆', '💤', '🐟', '🦊', '🧠', '🌙', '📈', '🤖')
    
    for item in os.listdir(profiles_dir):
        item_path = os.path.join(profiles_dir, item)
        if os.path.isdir(item_path) and item.startswith(emoji_prefixes):
            try:
                shutil.rmtree(item_path)
                removed += 1
            except Exception as e:
                print(f"    ⚠️ Error removing {item}: {e}")
    
    return removed

def run_triage(profiles_dir: str = PROFILES_ROOT, dry_run: bool = False, reset: bool = False) -> Dict:
    print("=" * 60)
    print("🗂️  WHALE PROFILE TRIAGE SYSTEM")
    print("=" * 60)
    
    stats = {
        "total_profiles": 0,
        "promoted": 0,
        "kept": 0,
        "archived": 0,
        "trashed": 0,
        "categorized": defaultdict(int),
        "trash_cleaned": 0,
        "links_cleaned": 0,
        "categories_reset": 0,
    }
    
    if not dry_run:
        print("\n🧹 Cleaning up old link files...")
        stats["links_cleaned"] = cleanup_link_files(profiles_dir)
        if stats["links_cleaned"] > 0:
            print(f"   Removed {stats['links_cleaned']} old link files")
    
    if reset and not dry_run:
        print("\n🔄 Resetting category folders...")
        stats["categories_reset"] = reset_category_folders(profiles_dir)
        print(f"   Removed {stats['categories_reset']} category folders")
    
    ensure_category_dirs(profiles_dir)
    
    print("\n📂 Loading profiles...")
    profiles = load_all_profiles(profiles_dir)
    stats["total_profiles"] = len(profiles)
    print(f"   Found {len(profiles)} profiles")
    
    if not profiles:
        print("   No profiles to triage!")
        return stats
    
    print("\n🔍 Analyzing profiles...")
    
    for meta in profiles:
        meta.categories = categorize_profile(meta)
        for cat in meta.categories:
            stats["categorized"][cat] += 1
        
        meta.triage_action = determine_triage_action(meta)
    
    print("\n⚡ Executing triage actions...")
    
    for meta in profiles:
        if dry_run:
            print(f"   [DRY RUN] Would {meta.triage_action}: {meta.address[:16]}...")
            continue
        
        if meta.triage_action == "promote":
            move_profile(meta, "high_priority", profiles_dir)
            stats["promoted"] += 1
            meta.filepath = os.path.join(profiles_dir, "high_priority", meta.address, os.path.basename(meta.filepath))
            for cat in meta.categories:
                if cat not in ["high_priority", "medium_priority", "low_priority", "filtered"]:
                    copy_profile_to_category(meta, cat, profiles_dir)
            
        elif meta.triage_action == "archive":
            move_profile(meta, "📦_archive", profiles_dir)
            stats["archived"] += 1
            
        elif meta.triage_action == "trash":
            move_profile(meta, "🗑️_trash", profiles_dir)
            stats["trashed"] += 1
            
        else:
            for cat in meta.categories:
                if cat not in ["high_priority", "medium_priority", "low_priority", "filtered"]:
                    copy_profile_to_category(meta, cat, profiles_dir)
            stats["kept"] += 1
    
    if not dry_run:
        print("\n🧹 Cleaning up trash...")
        stats["trash_cleaned"] = cleanup_trash(profiles_dir)
        cleanup_empty_dirs(profiles_dir)
    
    print("\n" + "=" * 60)
    print("📊 TRIAGE SUMMARY")
    print("=" * 60)
    print(f"""
    Total Profiles:    {stats['total_profiles']}
    
    Actions Taken:
      ⬆️  Promoted:      {stats['promoted']}
      ✅ Kept:          {stats['kept']}
      📦 Archived:      {stats['archived']}
      🗑️  Trashed:       {stats['trashed']}
      🧹 Trash Cleaned: {stats['trash_cleaned']}
    
    Category Distribution:
    """)
    
    for cat, count in sorted(stats["categorized"].items(), key=lambda x: -x[1]):
        desc = CATEGORIES.get(cat, "")
        print(f"      {cat}: {count}")
    
    return stats

def generate_triage_report(profiles_dir: str = PROFILES_ROOT) -> str:
    profiles = load_all_profiles(profiles_dir)
    
    lines = [
        "# 🗂️ Whale Profile Triage Report",
        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        "## Summary",
        f"- Total Profiles: {len(profiles)}",
        "",
    ]
    
    by_category = defaultdict(list)
    by_action = defaultdict(list)
    
    for meta in profiles:
        meta.categories = categorize_profile(meta)
        meta.triage_action = determine_triage_action(meta)
        
        for cat in meta.categories:
            by_category[cat].append(meta)
        by_action[meta.triage_action].append(meta)
    
    lines.append("## 🎯 High Value Targets")
    lines.append("")
    
    high_value = by_category.get("🎯_high_value_targets", [])
    if high_value:
        lines.append("| Address | Balance | Confidence | Region | Type |")
        lines.append("|---------|---------|------------|--------|------|")
        for meta in sorted(high_value, key=lambda x: -x.balance_usd)[:20]:
            types = []
            if meta.is_meme_trader: types.append("🐸")
            if meta.is_defi_user: types.append("🏦")
            if meta.is_nft_collector: types.append("🎨")
            if meta.is_bridge_user: types.append("🌉")
            
            lines.append(f"| `{meta.address[:12]}...` | ${meta.balance_usd:,.0f} | {meta.confidence}% | {meta.likely_region} | {''.join(types)} |")
    else:
        lines.append("*No high value targets identified*")
    lines.append("")
    
    lines.append("## 📋 Triage Actions")
    lines.append("")
    lines.append(f"- **Promote to High Priority:** {len(by_action['promote'])}")
    lines.append(f"- **Keep as-is:** {len(by_action['keep'])}")
    lines.append(f"- **Archive:** {len(by_action['archive'])}")
    lines.append(f"- **Move to Trash:** {len(by_action['trash'])}")
    lines.append("")
    
    if by_action['trash']:
        lines.append("### 🗑️ Profiles Marked for Trash")
        lines.append("")
        for meta in by_action['trash'][:10]:
            lines.append(f"- `{meta.address[:20]}...` - ${meta.balance_usd:,.0f} - {meta.confidence}% confidence")
        if len(by_action['trash']) > 10:
            lines.append(f"- ... and {len(by_action['trash']) - 10} more")
        lines.append("")
    
    lines.append("## 📁 Category Breakdown")
    lines.append("")
    
    for cat, profiles_list in sorted(by_category.items(), key=lambda x: -len(x[1])):
        desc = CATEGORIES.get(cat, "")
        lines.append(f"### {cat}")
        lines.append(f"*{desc}*")
        lines.append(f"Count: {len(profiles_list)}")
        lines.append("")
    
    return "\n".join(lines)

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Whale Profile Triage System")
    parser.add_argument("--dry-run", action="store_true", help="Show what would happen without making changes")
    parser.add_argument("--report", action="store_true", help="Generate triage report only")
    parser.add_argument("--cleanup", action="store_true", help="Only clean up trash and link files")
    parser.add_argument("--reset", action="store_true", help="Reset category folders and rebuild from scratch")
    parser.add_argument("--profiles-dir", default=PROFILES_ROOT, help="Profiles directory")
    
    args = parser.parse_args()
    
    if args.report:
        report = generate_triage_report(args.profiles_dir)
        print(report)
        
        report_path = os.path.join(args.profiles_dir, "triage_report.md")
        with open(report_path, 'w') as f:
            f.write(report)
        print(f"\n✅ Report saved to {report_path}")
        
    elif args.cleanup:
        print("🧹 Cleaning up...")
        links = cleanup_link_files(args.profiles_dir)
        deleted = cleanup_trash(args.profiles_dir)
        removed = cleanup_empty_dirs(args.profiles_dir)
        print(f"   Removed {links} link files")
        print(f"   Deleted {deleted} files from trash")
        print(f"   Removed {removed} empty directories")
        
    else:
        run_triage(args.profiles_dir, dry_run=args.dry_run, reset=args.reset)

if __name__ == "__main__":
    main()
