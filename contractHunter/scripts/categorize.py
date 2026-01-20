#!/usr/bin/env python3
"""
Standalone contract categorizer CLI
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utils.contract_categorizer import ContractCategorizer

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Categorize contracts into archetypes")
    parser.add_argument("--hunt-results", "-r", help="Path to hunt results JSON")
    parser.add_argument("--recategorize", "-R", action="store_true", help="Recategorize all contracts in _all/")
    parser.add_argument("--report", action="store_true", help="Print category report")
    parser.add_argument("--contracts-dir", "-d", default="contracts", help="Contracts directory")
    
    args = parser.parse_args()
    
    categorizer = ContractCategorizer(args.contracts_dir)
    
    if args.hunt_results:
        categorizer.categorize_from_hunt_results(args.hunt_results)
    elif args.recategorize:
        print("Recategorizing all contracts...")
        results = categorizer.recategorize_all()
        print(f"Recategorized {len(results)} contracts")
    
    if args.report or not (args.hunt_results or args.recategorize):
        categorizer.print_category_report()
