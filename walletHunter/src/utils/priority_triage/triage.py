import os
import json
from datetime import datetime, timezone
from typing import List, Tuple

from .config import (
    PROFILES_DIR,
    ACTIONABLE_THRESHOLD,
    KEEP_THRESHOLD,
    ARCHIVE_THRESHOLD,
    MAX_ACTIONABLE,
    TRASH_RETENTION_DAYS
)
from .scoring import score_profile, PriorityScore
from .file_ops import (
    find_all_profiles,
    setup_directory_structure,
    save_profile_to_all,
    create_actionable_symlinks,
    move_to_archive,
    move_to_trash,
    cleanup_old_category_folders,
    cleanup_trash
)


def run_migration(profiles_dir: str = PROFILES_DIR, dry_run: bool = False):
    print("=" * 70)
    print("🎯 PRIORITY SCORING & AUTO-TRIAGE")
    print("=" * 70)
    
    if not dry_run:
        setup_directory_structure(profiles_dir)
    
    print("\n📂 Scanning for profiles...")
    all_profiles = find_all_profiles(profiles_dir)
    print(f"   Found {len(all_profiles)} unique addresses")
    
    if not all_profiles:
        print("   No profiles to process!")
        return
    
    completeness_scores = [p.get('_completeness', 0) for p in all_profiles.values()]
    avg_completeness = sum(completeness_scores) / len(completeness_scores) if completeness_scores else 0
    full_reports = sum(1 for s in completeness_scores if s >= 100)
    print(f"   Full OSINT reports: {full_reports}/{len(all_profiles)}")
    print(f"   Avg completeness score: {avg_completeness:.0f}")
    
    print("\n📊 Scoring profiles...")
    scored: List[Tuple[str, PriorityScore]] = []
    
    for address, profile_data in all_profiles.items():
        score = score_profile(profile_data)
        scored.append((address, score))
        
        if not dry_run:
            save_profile_to_all(address, profile_data, score, profiles_dir)
    
    scored.sort(key=lambda x: -x[1].total_score)
    
    actionable = []
    keep = []
    archive = []
    trash = []
    
    for address, score in scored:
        if score.disqualified:
            trash.append((address, score))
        elif score.total_score >= ACTIONABLE_THRESHOLD:
            actionable.append((address, score))
        elif score.total_score >= KEEP_THRESHOLD:
            keep.append((address, score))
        elif score.total_score >= ARCHIVE_THRESHOLD:
            archive.append((address, score))
        else:
            trash.append((address, score))
    
    print(f"\n   🎯 Actionable (score >= {ACTIONABLE_THRESHOLD}): {len(actionable)}")
    print(f"   📁 Keep (score {KEEP_THRESHOLD}-{ACTIONABLE_THRESHOLD-1}): {len(keep)}")
    print(f"   📦 Archive (score {ARCHIVE_THRESHOLD}-{KEEP_THRESHOLD-1}): {len(archive)}")
    print(f"   🗑️ Trash (score < {ARCHIVE_THRESHOLD} or disqualified): {len(trash)}")
    
    if actionable:
        print(f"\n   Top 10 Actionable Targets:")
        for addr, score in actionable[:10]:
            print(f"      [{score.total_score:2d}] {addr[:16]}... ${score.balance_usd:>12,.0f} | {score.confidence_pct}% conf")
    
    if trash and dry_run:
        print(f"\n   Trash reasons (sample):")
        for addr, score in trash[:5]:
            reason = score.disqualify_reason if score.disqualified else f"Low score: {score.total_score}"
            print(f"      {addr[:16]}... → {reason}")
    
    if dry_run:
        print("\n   [DRY RUN - No changes made]")
        return
    
    print("\n⚡ Executing triage...")
    
    create_actionable_symlinks(scored, profiles_dir)
    print(f"   Created {min(len(actionable), MAX_ACTIONABLE)} actionable symlinks")
    
    for address, score in archive:
        move_to_archive(address, profiles_dir)
    print(f"   Archived {len(archive)} profiles")
    
    for address, score in trash:
        move_to_trash(address, profiles_dir)
    print(f"   Trashed {len(trash)} profiles")
    
    print("\n🧹 Cleaning and repopulating category folders...")
    cleaned = cleanup_old_category_folders(profiles_dir, dry_run)
    print(f"   Cleaned {cleaned} old profiles from category folders")
    if not dry_run:
        print(f"   Category folders repopulated from _all/ (keeps browsing functionality)")
    
    deleted = cleanup_trash(profiles_dir)
    if deleted:
        print(f"   Deleted {deleted} old trash items")
    
    print("\n" + "=" * 70)
    print("✅ TRIAGE COMPLETE")
    print("=" * 70)
    
    all_dir = os.path.join(profiles_dir, "_all")
    actionable_dir = os.path.join(profiles_dir, "🎯_actionable")
    archive_dir = os.path.join(profiles_dir, "📦_archive")
    trash_dir = os.path.join(profiles_dir, "🗑️_trash")
    
    all_count = len(os.listdir(all_dir)) if os.path.exists(all_dir) else 0
    act_count = len(os.listdir(actionable_dir)) if os.path.exists(actionable_dir) else 0
    arch_count = len(os.listdir(archive_dir)) if os.path.exists(archive_dir) else 0
    trash_count = len(os.listdir(trash_dir)) if os.path.exists(trash_dir) else 0
    
    print(f"""

   New structure:

   profiles/

   ├── _all/           {all_count:3d} profiles (single source of truth)

   ├── 🎯_actionable/   {act_count:3d} symlinks (your hit list)

   ├── 📦_archive/      {arch_count:3d} profiles (low priority)

   └── 🗑️_trash/        {trash_count:3d} profiles (auto-delete in {TRASH_RETENTION_DAYS} days)

""")


def generate_hitlist(profiles_dir: str = PROFILES_DIR) -> str:
    actionable_dir = os.path.join(profiles_dir, "🎯_actionable")
    if not os.path.exists(actionable_dir):
        return "No actionable targets found."
    
    lines = [
        "# 🎯 ACTIONABLE TARGETS",
        f"Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')} UTC",
        "",
        "| Score | Address | Balance | Confidence | Categories |",
        "|-------|---------|---------|------------|------------|",
    ]
    
    for item in sorted(os.listdir(actionable_dir), reverse=True):
        item_path = os.path.join(actionable_dir, item)
        
        if os.path.islink(item_path):
            item_path = os.path.realpath(item_path)
        
        score_file = os.path.join(item_path, 'score.json')
        if os.path.exists(score_file):
            with open(score_file) as f:
                score = json.load(f)
            
            addr = score['address'][:16] + "..."
            bal = f"${score['balance_usd']:,.0f}"
            conf = f"{score['confidence_pct']}%"
            cats = ", ".join(c.split('_')[1] if '_' in c else c for c in score['categories'][:2])
            
            lines.append(f"| {score['total_score']} | `{addr}` | {bal} | {conf} | {cats} |")
    
    return "\n".join(lines)

