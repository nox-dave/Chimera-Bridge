#!/usr/bin/env python3

import os
import sys
import json
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Optional

try:
    from ..osint_categorizer import OSINT_CATEGORIES, categorize_for_osint, get_category_info
except ImportError:
    import sys
    import os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
    from src.utils.osint_categorizer import OSINT_CATEGORIES, categorize_for_osint, get_category_info

PROFILES_DIR = "profiles"
TRASH_RETENTION_DAYS = 7

LEGACY_FOLDERS = [
    "high_priority",
    "medium_priority",
    "low_priority",
    "filtered",
    "🇪🇺_eu_traders",
    "🇺🇸_us_traders",
    "🌏_asia_traders",
    "🆕_fresh_whales",
    "💎_og_whales",
    "🐸_meme_traders",
    "🏦_defi_farmers",
    "🎨_nft_collectors",
    "🌉_bridge_users",
    "🏛️_dao_participants",
    "🎯_high_value_targets",
]

def load_profile(filepath: str) -> Optional[dict]:
    try:
        with open(filepath, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"  ⚠️ Error loading {filepath}: {e}")
        return None

def find_all_profiles(profiles_dir: str = PROFILES_DIR) -> List[dict]:
    profiles = []
    
    for root, dirs, files in os.walk(profiles_dir):
        if '🗑️_trash' in root or '📦_archive' in root:
            continue
        
        for file in files:
            if file == 'profile.json':
                filepath = os.path.join(root, file)
                data = load_profile(filepath)
                if data:
                    data['_filepath'] = filepath
                    data['_folder'] = os.path.dirname(filepath)
                    profiles.append(data)
    
    return profiles

def ensure_category_dirs(profiles_dir: str = PROFILES_DIR):
    for category in OSINT_CATEGORIES.keys():
        cat_dir = os.path.join(profiles_dir, category)
        os.makedirs(cat_dir, exist_ok=True)
    
    os.makedirs(os.path.join(profiles_dir, "🗑️_trash"), exist_ok=True)
    os.makedirs(os.path.join(profiles_dir, "📦_archive"), exist_ok=True)

def save_profile_to_category(profile_data: dict, category: str, profiles_dir: str = PROFILES_DIR):
    address = profile_data.get('address', '')
    if not address:
        return False
    
    target_dir = os.path.join(profiles_dir, category, address)
    os.makedirs(target_dir, exist_ok=True)
    
    profile_path = os.path.join(target_dir, 'profile.json')
    with open(profile_path, 'w') as f:
        save_data = {k: v for k, v in profile_data.items() if not k.startswith('_')}
        save_data['osint_categories'] = profile_data.get('_categories', [])
        json.dump(save_data, f, indent=2)
    
    source_folder = profile_data.get('_folder', '')
    if source_folder:
        source_summary = os.path.join(source_folder, 'summary.txt')
        if os.path.exists(source_summary):
            target_summary = os.path.join(target_dir, 'summary.txt')
            shutil.copy2(source_summary, target_summary)
    
    return True

def move_to_trash(profile_data: dict, profiles_dir: str = PROFILES_DIR):
    source_folder = profile_data.get('_folder', '')
    address = profile_data.get('address', '')
    
    if not source_folder or not address:
        return False
    
    trash_dir = os.path.join(profiles_dir, "🗑️_trash", address)
    
    try:
        if os.path.exists(trash_dir):
            shutil.rmtree(trash_dir)
        shutil.move(source_folder, trash_dir)
        return True
    except Exception as e:
        print(f"  ⚠️ Error moving to trash: {e}")
        return False

def cleanup_legacy_folders(profiles_dir: str = PROFILES_DIR, dry_run: bool = False):
    removed = 0
    
    for folder in LEGACY_FOLDERS:
        folder_path = os.path.join(profiles_dir, folder)
        if os.path.exists(folder_path):
            if dry_run:
                print(f"  Would remove: {folder}")
            else:
                try:
                    shutil.rmtree(folder_path)
                    print(f"  Removed: {folder}")
                    removed += 1
                except Exception as e:
                    print(f"  ⚠️ Error removing {folder}: {e}")
    
    return removed

def cleanup_trash(profiles_dir: str = PROFILES_DIR, retention_days: int = TRASH_RETENTION_DAYS):
    trash_dir = os.path.join(profiles_dir, "🗑️_trash")
    if not os.path.exists(trash_dir):
        return 0
    
    deleted = 0
    cutoff = datetime.now() - timedelta(days=retention_days)
    
    for item in os.listdir(trash_dir):
        item_path = os.path.join(trash_dir, item)
        try:
            mtime = datetime.fromtimestamp(os.path.getmtime(item_path))
            if mtime < cutoff:
                if os.path.isdir(item_path):
                    shutil.rmtree(item_path)
                else:
                    os.remove(item_path)
                deleted += 1
        except Exception as e:
            print(f"  ⚠️ Error deleting {item}: {e}")
    
    return deleted

def cleanup_empty_dirs(profiles_dir: str = PROFILES_DIR):
    removed = 0
    
    for root, dirs, files in os.walk(profiles_dir, topdown=False):
        for dir_name in dirs:
            dir_path = os.path.join(root, dir_name)
            try:
                if os.path.isdir(dir_path) and not os.listdir(dir_path):
                    if root == profiles_dir and dir_name in OSINT_CATEGORIES.keys():
                        continue
                    if dir_name in ['🗑️_trash', '📦_archive']:
                        continue
                    os.rmdir(dir_path)
                    removed += 1
            except:
                pass
    
    return removed

def should_trash(profile_data: dict) -> bool:
    balance = profile_data.get('balance_usd', profile_data.get('total_value_usd', 0))
    behavior = profile_data.get('behavior', {})
    confidence = behavior.get('confidence_score', profile_data.get('risk_score', 50))
    tx_count = profile_data.get('tx_count', 0)
    
    if balance < 10000:
        return True
    
    if tx_count > 100000:
        return True
    
    if confidence < 20 and balance < 100000:
        return True
    
    return False

def triage_profile(profile_data: dict) -> tuple:
    if should_trash(profile_data):
        return ('trash', [])
    
    categories = categorize_for_osint(profile_data)
    
    if categories == ["🏢_institutions"] or categories == ["🤖_bots"]:
        return ('trash', categories)
    
    return ('categorize', categories)

def run_triage(profiles_dir: str = PROFILES_DIR, dry_run: bool = False, migrate: bool = False) -> Dict:
    print("=" * 60)
    print("🎯 OSINT PROFILE TRIAGE")
    print("=" * 60)
    
    stats = {
        "total_found": 0,
        "categorized": 0,
        "trashed": 0,
        "skipped": 0,
        "by_category": defaultdict(int),
        "legacy_removed": 0,
        "trash_cleaned": 0,
    }
    
    if not dry_run:
        ensure_category_dirs(profiles_dir)
    
    print("\n📂 Scanning for profiles...")
    profiles = find_all_profiles(profiles_dir)
    stats["total_found"] = len(profiles)
    print(f"   Found {len(profiles)} profiles")
    
    if not profiles:
        print("   No profiles to triage!")
        return stats
    
    print("\n🔍 Categorizing profiles...")
    
    for profile in profiles:
        address = profile.get('address', 'Unknown')[:16]
        action, categories = triage_profile(profile)
        
        if action == 'trash':
            if dry_run:
                print(f"   [TRASH] {address}...")
            else:
                move_to_trash(profile, profiles_dir)
            stats["trashed"] += 1
            
        elif action == 'categorize':
            profile['_categories'] = categories
            
            if dry_run:
                print(f"   [OK] {address}... → {', '.join(categories)}")
            else:
                primary_cat = categories[0] if categories else "🐟_easy_targets"
                save_profile_to_category(profile, primary_cat, profiles_dir)
                
                if "🎯_prime_targets" in categories:
                    for cat in categories:
                        if cat != "🎯_prime_targets":
                            save_profile_to_category(profile, cat, profiles_dir)
            
            stats["categorized"] += 1
            for cat in categories:
                stats["by_category"][cat] += 1
        
        else:
            stats["skipped"] += 1
    
    if migrate and not dry_run:
        print("\n🧹 Cleaning up legacy folders...")
        stats["legacy_removed"] = cleanup_legacy_folders(profiles_dir)
    
    if not dry_run:
        print("\n🗑️ Cleaning old trash...")
        stats["trash_cleaned"] = cleanup_trash(profiles_dir)
        cleanup_empty_dirs(profiles_dir)
    
    print("\n" + "=" * 60)
    print("📊 TRIAGE SUMMARY")
    print("=" * 60)
    print(f"""

   Total Profiles:  {stats['total_found']}

   Categorized:     {stats['categorized']}

   Trashed:         {stats['trashed']}

   Skipped:         {stats['skipped']}

   

   Category Distribution:

""")
    
    for cat, count in sorted(stats["by_category"].items(), key=lambda x: -x[1]):
        info = OSINT_CATEGORIES.get(cat, {})
        desc = info.get('description', '')[:40]
        print(f"      {cat}: {count}")
    
    return stats

def generate_report(profiles_dir: str = PROFILES_DIR) -> str:
    profiles = find_all_profiles(profiles_dir)
    
    lines = [
        "# 🎯 OSINT Triage Report",
        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"Total Profiles: {len(profiles)}",
        "",
        "## Category Breakdown",
        "",
    ]
    
    by_category = defaultdict(list)
    
    for profile in profiles:
        _, categories = triage_profile(profile)
        for cat in categories:
            by_category[cat].append(profile)
    
    for cat, cat_profiles in sorted(by_category.items(), key=lambda x: -len(x[1])):
        info = OSINT_CATEGORIES.get(cat, {})
        lines.append(f"### {cat} ({len(cat_profiles)})")
        lines.append(f"*{info.get('description', '')}*")
        lines.append("")
        lines.append(f"**Psychology:** {info.get('psychology', 'Unknown')}")
        lines.append("")
        lines.append("**Attack Vectors:**")
        for vector in info.get('attack_vectors', []):
            lines.append(f"- {vector}")
        lines.append("")
        
        lines.append("**Top Targets:**")
        sorted_profiles = sorted(cat_profiles,
                                key=lambda x: x.get('balance_usd', x.get('total_value_usd', 0)),
                                reverse=True)[:5]
        for p in sorted_profiles:
            addr = p.get('address', '')[:16]
            bal = p.get('balance_usd', p.get('total_value_usd', 0))
            lines.append(f"- `{addr}...` - ${bal:,.0f}")
        lines.append("")
    
    return "\n".join(lines)

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="OSINT Profile Triage System")
    parser.add_argument("--dry-run", action="store_true",
                       help="Preview changes without making them")
    parser.add_argument("--migrate", action="store_true",
                       help="Clean up legacy folders after migration")
    parser.add_argument("--report", action="store_true",
                       help="Generate triage report only")
    parser.add_argument("--cleanup", action="store_true",
                       help="Only clean up trash and empty folders")
    parser.add_argument("--profiles-dir", default=PROFILES_DIR,
                       help="Profiles directory path")
    
    args = parser.parse_args()
    
    if args.report:
        report = generate_report(args.profiles_dir)
        print(report)
        
        report_path = os.path.join(args.profiles_dir, "osint_report.md")
        with open(report_path, 'w') as f:
            f.write(report)
        print(f"\n✅ Report saved to {report_path}")
        
    elif args.cleanup:
        print("🧹 Cleaning up...")
        deleted = cleanup_trash(args.profiles_dir)
        removed = cleanup_empty_dirs(args.profiles_dir)
        print(f"   Deleted {deleted} old trash items")
        print(f"   Removed {removed} empty directories")
        
    else:
        run_triage(args.profiles_dir, dry_run=args.dry_run, migrate=args.migrate)

if __name__ == "__main__":
    main()

