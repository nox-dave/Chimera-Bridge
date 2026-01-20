import os
import json
import shutil
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Tuple

from .config import PROFILES_DIR, TRASH_RETENTION_DAYS
from .scoring import PriorityScore


def get_profile_completeness_score(folder_path: str, profile_data: dict) -> int:
    score = 0
    
    summary_path = os.path.join(folder_path, 'summary.txt')
    if os.path.exists(summary_path):
        size = os.path.getsize(summary_path)
        if size > 5000:
            score += 100
        elif size > 2000:
            score += 50
        elif size > 500:
            score += 20
        else:
            score += 5
    
    ipfs_path = os.path.join(folder_path, 'ipfs_osint.json')
    if os.path.exists(ipfs_path):
        score += 30
    
    if profile_data.get('behavior'):
        score += 20
        if profile_data['behavior'].get('confidence_score'):
            score += 10
        if profile_data['behavior'].get('sophistication'):
            score += 10
    
    if profile_data.get('osint_categories'):
        score += 15
    
    if profile_data.get('token_interests'):
        score += 10
    
    last_updated = profile_data.get('last_updated', profile_data.get('generated', ''))
    if last_updated:
        try:
            updated = datetime.fromisoformat(last_updated.replace('Z', '+00:00'))
            age_days = (datetime.now(updated.tzinfo) - updated).days if updated.tzinfo else 0
            if age_days < 1:
                score += 20
            elif age_days < 7:
                score += 10
        except:
            pass
    
    return score


def find_all_profiles(profiles_dir: str = PROFILES_DIR) -> Dict[str, dict]:
    profiles = {}
    profile_scores = {}
    
    for root, dirs, files in os.walk(profiles_dir):
        if '_all' in root or '📦_archive' in root or '🗑️_trash' in root or '🎯_actionable' in root:
            continue
        
        for file in files:
            if file == 'profile.json':
                filepath = os.path.join(root, file)
                folder_path = os.path.dirname(filepath)
                
                try:
                    with open(filepath, 'r') as f:
                        data = json.load(f)
                    
                    address = data.get('address', '').lower()
                    if not address:
                        continue
                    
                    completeness = get_profile_completeness_score(folder_path, data)
                    
                    if address not in profiles:
                        data['_source_path'] = folder_path
                        data['_completeness'] = completeness
                        profiles[address] = data
                        profile_scores[address] = completeness
                    else:
                        existing_score = profile_scores[address]
                        
                        if completeness > existing_score:
                            data['_source_path'] = folder_path
                            data['_completeness'] = completeness
                            profiles[address] = data
                            profile_scores[address] = completeness
                
                except Exception as e:
                    print(f"  ⚠️ Error loading {filepath}: {e}")
    
    return profiles


def setup_directory_structure(profiles_dir: str = PROFILES_DIR):
    system_dirs = [
        os.path.join(profiles_dir, "_all"),
        os.path.join(profiles_dir, "🎯_actionable"),
        os.path.join(profiles_dir, "📦_archive"),
        os.path.join(profiles_dir, "🗑️_trash"),
    ]
    
    category_dirs = [
        os.path.join(profiles_dir, "🎰_gamblers"),
        os.path.join(profiles_dir, "🆕_newcomers"),
        os.path.join(profiles_dir, "🏆_status_seekers"),
        os.path.join(profiles_dir, "💤_dormant_whales"),
        os.path.join(profiles_dir, "🌉_cross_chain_users"),
        os.path.join(profiles_dir, "🐟_easy_targets"),
        os.path.join(profiles_dir, "🦊_cautious_holders"),
        os.path.join(profiles_dir, "🧠_defi_natives"),
        os.path.join(profiles_dir, "🌙_night_traders"),
        os.path.join(profiles_dir, "📈_momentum_chasers"),
        os.path.join(profiles_dir, "🏛️_governance_voters"),
        os.path.join(profiles_dir, "💎_high_value"),
        os.path.join(profiles_dir, "🎯_prime_targets"),
        os.path.join(profiles_dir, "🏢_institutions"),
        os.path.join(profiles_dir, "🤖_bots"),
    ]
    
    for d in system_dirs + category_dirs:
        os.makedirs(d, exist_ok=True)


def save_profile_to_all(address: str, profile_data: dict, score: PriorityScore, 
                        profiles_dir: str = PROFILES_DIR):
    target_dir = os.path.join(profiles_dir, "_all", address)
    os.makedirs(target_dir, exist_ok=True)
    
    source_path = profile_data.get('_source_path', '')
    
    clean_data = {k: v for k, v in profile_data.items() if not k.startswith('_')}
    clean_data['priority_score'] = score.total_score
    clean_data['last_triage'] = datetime.now(timezone.utc).isoformat()
    
    with open(os.path.join(target_dir, 'profile.json'), 'w') as f:
        json.dump(clean_data, f, indent=2)
    
    from dataclasses import asdict
    with open(os.path.join(target_dir, 'score.json'), 'w') as f:
        json.dump(asdict(score), f, indent=2)
    
    if source_path:
        source_summary = os.path.join(source_path, 'summary.txt')
        target_summary = os.path.join(target_dir, 'summary.txt')
        
        if os.path.exists(source_summary):
            source_size = os.path.getsize(source_summary)
            target_size = os.path.getsize(target_summary) if os.path.exists(target_summary) else 0
            
            if source_size > target_size:
                shutil.copy2(source_summary, target_summary)
        
        source_ipfs = os.path.join(source_path, 'ipfs_osint.json')
        target_ipfs = os.path.join(target_dir, 'ipfs_osint.json')
        
        if os.path.exists(source_ipfs):
            if not os.path.exists(target_ipfs) or os.path.getsize(source_ipfs) > os.path.getsize(target_ipfs):
                shutil.copy2(source_ipfs, target_ipfs)


def create_actionable_symlinks(scored_profiles: List[Tuple[str, PriorityScore]], 
                                profiles_dir: str = PROFILES_DIR):
    from .config import ACTIONABLE_THRESHOLD, MAX_ACTIONABLE
    
    actionable_dir = os.path.join(profiles_dir, "🎯_actionable")
    
    for item in os.listdir(actionable_dir):
        item_path = os.path.join(actionable_dir, item)
        if os.path.islink(item_path):
            os.unlink(item_path)
        elif os.path.isdir(item_path):
            shutil.rmtree(item_path)
    
    actionable = [(addr, score) for addr, score in scored_profiles 
                  if score.total_score >= ACTIONABLE_THRESHOLD and not score.disqualified]
    actionable.sort(key=lambda x: -x[1].total_score)
    
    for addr, score in actionable[:MAX_ACTIONABLE]:
        source = os.path.join(profiles_dir, "_all", addr)
        target = os.path.join(actionable_dir, f"{score.total_score:02d}_{addr[:12]}")
        
        if os.path.exists(source):
            try:
                os.symlink(os.path.relpath(source, actionable_dir), target)
            except OSError:
                shutil.copytree(source, target)


def move_to_archive(address: str, profiles_dir: str = PROFILES_DIR):
    source = os.path.join(profiles_dir, "_all", address)
    target = os.path.join(profiles_dir, "📦_archive", address)
    
    if os.path.exists(source):
        if os.path.exists(target):
            shutil.rmtree(target)
        shutil.move(source, target)


def move_to_trash(address: str, profiles_dir: str = PROFILES_DIR):
    source = os.path.join(profiles_dir, "_all", address)
    target = os.path.join(profiles_dir, "🗑️_trash", address)
    
    if os.path.exists(source):
        if os.path.exists(target):
            shutil.rmtree(target)
        shutil.move(source, target)


def repopulate_category_folders(profiles_dir: str = PROFILES_DIR, dry_run: bool = False):
    all_dir = os.path.join(profiles_dir, "_all")
    if not os.path.exists(all_dir):
        return 0
    
    repopulated = 0
    
    for address in os.listdir(all_dir):
        address_path = os.path.join(all_dir, address)
        if not os.path.isdir(address_path):
            continue
        
        profile_file = os.path.join(address_path, 'profile.json')
        if not os.path.exists(profile_file):
            continue
        
        try:
            with open(profile_file, 'r') as f:
                profile_data = json.load(f)
            
            categories = profile_data.get('osint_categories', [])
            if not categories:
                continue
            
            for category in categories:
                if not isinstance(category, str) or not category.strip():
                    continue
                
                category_dir = os.path.join(profiles_dir, category)
                os.makedirs(category_dir, exist_ok=True)
                
                target_dir = os.path.join(category_dir, address)
                
                if dry_run:
                    print(f"  Would repopulate: {category}/{address}")
                else:
                    os.makedirs(target_dir, exist_ok=True)
                    
                    profile_target = os.path.join(target_dir, 'profile.json')
                    if not os.path.exists(profile_target) or os.path.getsize(profile_file) > os.path.getsize(profile_target) if os.path.exists(profile_target) else True:
                        shutil.copy2(profile_file, profile_target)
                    
                    summary_source = os.path.join(address_path, 'summary.txt')
                    summary_target = os.path.join(target_dir, 'summary.txt')
                    if os.path.exists(summary_source):
                        if not os.path.exists(summary_target) or os.path.getsize(summary_source) > os.path.getsize(summary_target) if os.path.exists(summary_target) else True:
                            shutil.copy2(summary_source, summary_target)
                    
                    ipfs_source = os.path.join(address_path, 'ipfs_osint.json')
                    ipfs_target = os.path.join(target_dir, 'ipfs_osint.json')
                    if os.path.exists(ipfs_source):
                        if not os.path.exists(ipfs_target) or os.path.getsize(ipfs_source) > os.path.getsize(ipfs_target) if os.path.exists(ipfs_target) else True:
                            shutil.copy2(ipfs_source, ipfs_target)
                    
                    score_source = os.path.join(address_path, 'score.json')
                    score_target = os.path.join(target_dir, 'score.json')
                    if os.path.exists(score_source):
                        if not os.path.exists(score_target):
                            shutil.copy2(score_source, score_target)
                
                repopulated += 1
        
        except Exception as e:
            print(f"  ⚠️ Error repopulating {address}: {e}")
    
    return repopulated


def cleanup_old_category_folders(profiles_dir: str = PROFILES_DIR, dry_run: bool = False):
    system_folders = ["_all", "🎯_actionable", "📦_archive", "🗑️_trash"]
    
    cleaned = 0
    for item in os.listdir(profiles_dir):
        item_path = os.path.join(profiles_dir, item)
        
        if not os.path.isdir(item_path) or item in system_folders:
            continue
        
        for profile_dir in os.listdir(item_path):
            profile_path = os.path.join(item_path, profile_dir)
            
            if os.path.isdir(profile_path):
                if dry_run:
                    print(f"  Would clean: {item}/{profile_dir}")
                else:
                    shutil.rmtree(profile_path)
                cleaned += 1
        
        if not dry_run:
            print(f"  Cleaned {item}/ (folder kept)")
    
    if not dry_run:
        repopulated = repopulate_category_folders(profiles_dir, dry_run=False)
        print(f"  Repopulated {repopulated} profiles to category folders from _all/")
    
    return cleaned


def cleanup_trash(profiles_dir: str = PROFILES_DIR):
    trash_dir = os.path.join(profiles_dir, "🗑️_trash")
    if not os.path.exists(trash_dir):
        return 0
    
    deleted = 0
    cutoff = datetime.now() - timedelta(days=TRASH_RETENTION_DAYS)
    
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

