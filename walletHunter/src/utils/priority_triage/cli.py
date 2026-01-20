#!/usr/bin/env python3

import argparse

from .config import PROFILES_DIR
from .triage import run_migration, generate_hitlist
from .file_ops import cleanup_trash


def main():
    parser = argparse.ArgumentParser(description="Priority Scoring & Auto-Triage System")
    parser.add_argument("--dry-run", action="store_true", 
                       help="Preview changes without making them")
    parser.add_argument("--hitlist", action="store_true",
                       help="Generate actionable targets hitlist")
    parser.add_argument("--cleanup-only", action="store_true",
                       help="Only clean up trash, don't run full triage")
    parser.add_argument("--profiles-dir", default=PROFILES_DIR,
                       help="Profiles directory path")
    
    args = parser.parse_args()
    
    if args.hitlist:
        print(generate_hitlist(args.profiles_dir))
    elif args.cleanup_only:
        deleted = cleanup_trash(args.profiles_dir)
        print(f"Deleted {deleted} old trash items")
    else:
        run_migration(args.profiles_dir, dry_run=args.dry_run)


if __name__ == "__main__":
    main()

