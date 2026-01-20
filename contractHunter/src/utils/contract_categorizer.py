#!/usr/bin/env python3
"""
Contract Categorizer - Auto-sort contracts into archetypes
Mirrors walletHunter's OSINT categorization system
"""

import os
import json
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Set
from dataclasses import dataclass, field


@dataclass
class ContractCategory:
    name: str
    emoji: str
    description: str
    folder_name: str
    priority: int = 0


CATEGORIES = {
    "critical_vulns": ContractCategory(
        name="Critical Vulnerabilities",
        emoji="🎯",
        description="Contracts with CRITICAL severity findings",
        folder_name="🎯_critical_vulns",
        priority=100
    ),
    "high_vulns": ContractCategory(
        name="High Vulnerabilities", 
        emoji="⚠️",
        description="Contracts with HIGH severity findings",
        folder_name="⚠️_high_vulns",
        priority=90
    ),
    "access_control_issues": ContractCategory(
        name="Access Control Issues",
        emoji="🔓",
        description="Missing or weak access control",
        folder_name="🔓_access_control_issues",
        priority=85
    ),
    "reentrancy_risk": ContractCategory(
        name="Reentrancy Risk",
        emoji="🔄",
        description="Potential reentrancy vulnerabilities",
        folder_name="🔄_reentrancy_risk",
        priority=85
    ),
    "unchecked_calls": ContractCategory(
        name="Unchecked External Calls",
        emoji="📞",
        description="Unchecked call return values",
        folder_name="📞_unchecked_calls",
        priority=80
    ),
    "bridges": ContractCategory(
        name="Bridge Protocols",
        emoji="🌉",
        description="Cross-chain bridges (high-risk category)",
        folder_name="🌉_bridges",
        priority=75
    ),
    "lending": ContractCategory(
        name="Lending Protocols",
        emoji="🏦",
        description="Lending and borrowing protocols",
        folder_name="🏦_lending",
        priority=70
    ),
    "dex": ContractCategory(
        name="DEX Protocols",
        emoji="🔀",
        description="Decentralized exchanges",
        folder_name="🔀_dex",
        priority=70
    ),
    "staking": ContractCategory(
        name="Staking Protocols",
        emoji="🥩",
        description="Staking and liquid staking",
        folder_name="🥩_staking",
        priority=65
    ),
    "rwa": ContractCategory(
        name="Real World Assets",
        emoji="🏢",
        description="RWA tokenization protocols",
        folder_name="🏢_rwa",
        priority=60
    ),
    "high_tvl_unaudited": ContractCategory(
        name="High TVL Unaudited",
        emoji="💰",
        description=">$100M TVL without audit",
        folder_name="💰_high_tvl_unaudited",
        priority=95
    ),
    "fresh_deployments": ContractCategory(
        name="Fresh Deployments",
        emoji="🆕",
        description="Recently deployed contracts (<30 days)",
        folder_name="🆕_fresh_deployments",
        priority=70
    ),
    "proxy_contracts": ContractCategory(
        name="Proxy Contracts",
        emoji="🔲",
        description="Upgradeable proxy patterns",
        folder_name="🔲_proxy_contracts",
        priority=50
    ),
    "unverified": ContractCategory(
        name="Unverified Contracts",
        emoji="❓",
        description="Source code not verified on Etherscan",
        folder_name="❓_unverified",
        priority=60
    ),
    "prime_targets": ContractCategory(
        name="Prime Targets",
        emoji="🎯",
        description="High TVL + Vulnerabilities + Unaudited",
        folder_name="🎯_prime_targets",
        priority=100
    ),
    "archive": ContractCategory(
        name="Archive",
        emoji="📦",
        description="Low priority or already reviewed",
        folder_name="📦_archive",
        priority=0
    ),
}


CATEGORY_KEYWORDS = {
    "bridges": ["bridge", "canonical bridge", "cross-chain"],
    "lending": ["lending", "borrowing", "cdp", "money market"],
    "dex": ["dex", "dexs", "amm", "exchange", "swap"],
    "staking": ["staking", "liquid staking", "restaking", "liquid restaking", "staking pool"],
    "rwa": ["rwa", "real world", "tokenized"],
}

VULN_CATEGORIES = {
    "access_control_issues": ["access control", "missing access", "onlyowner"],
    "reentrancy_risk": ["reentrancy", "reentrant"],
    "unchecked_calls": ["unchecked call", "unchecked return", "unchecked external"],
}


class ContractCategorizer:
    
    def __init__(self, contracts_dir: Optional[str] = None):
        if contracts_dir is None:
            current_file = Path(__file__).resolve()
            src_dir = current_file.parent.parent.parent
            root_dir = src_dir.parent
            chimera_root = root_dir.parent if root_dir.name == "contractHunter" else root_dir
            self.contracts_dir = chimera_root / "Contracts"
        else:
            self.contracts_dir = Path(contracts_dir)
        self.all_dir = self.contracts_dir / "_all"
        
    def setup_directories(self):
        self.contracts_dir.mkdir(parents=True, exist_ok=True)
        self.all_dir.mkdir(parents=True, exist_ok=True)
        
        for cat in CATEGORIES.values():
            cat_dir = self.contracts_dir / cat.folder_name
            cat_dir.mkdir(parents=True, exist_ok=True)
            
    def categorize_contract(self, contract_data: Dict) -> List[str]:
        categories: Set[str] = set()
        
        name = contract_data.get("name", "") or contract_data.get("protocol", "") or contract_data.get("protocol_name", "")
        name = name.lower()
        category = contract_data.get("category", "").lower()
        tvl = contract_data.get("tvl", 0) or 0
        audited = contract_data.get("audited", False) or contract_data.get("is_audited", False)
        is_proxy = contract_data.get("is_proxy", False)
        verified = contract_data.get("verified", True)
        vulnerabilities = contract_data.get("vulnerabilities", [])
        scan_results = contract_data.get("scan_results", {})
        findings = scan_results.get("findings", []) if isinstance(scan_results, dict) else []
        
        all_vulns = vulnerabilities + findings
        
        severities = set()
        vuln_types = set()
        
        for vuln in all_vulns:
            if isinstance(vuln, dict):
                sev = vuln.get("severity", "").upper()
                vuln_type = vuln.get("vulnerability_type", "").lower()
                desc = vuln.get("description", "").lower()
            elif isinstance(vuln, str):
                sev = ""
                if "[critical]" in vuln.lower():
                    sev = "CRITICAL"
                elif "[high]" in vuln.lower():
                    sev = "HIGH"
                elif "[medium]" in vuln.lower():
                    sev = "MEDIUM"
                vuln_type = vuln.lower()
                desc = vuln.lower()
            else:
                continue
                
            if sev:
                severities.add(sev)
            vuln_types.add(vuln_type)
            vuln_types.add(desc)
        
        if "CRITICAL" in severities:
            categories.add("critical_vulns")
        if "HIGH" in severities:
            categories.add("high_vulns")
            
        vuln_text = " ".join(vuln_types)
        for cat_key, keywords in VULN_CATEGORIES.items():
            if any(kw in vuln_text for kw in keywords):
                categories.add(cat_key)
        
        combined_text = f"{name} {category}"
        for cat_key, keywords in CATEGORY_KEYWORDS.items():
            if any(kw in combined_text for kw in keywords):
                categories.add(cat_key)
        
        if tvl > 100_000_000 and not audited:
            categories.add("high_tvl_unaudited")
            
        if is_proxy:
            categories.add("proxy_contracts")
            
        if not verified:
            categories.add("unverified")
            
        is_prime = (
            tvl > 500_000_000 and
            not audited and
            ("CRITICAL" in severities or "HIGH" in severities)
        )
        if is_prime:
            categories.add("prime_targets")
            
        if not categories:
            if tvl < 10_000_000 or audited:
                categories.add("archive")
                
        return list(categories)
    
    def create_symlink(self, source: Path, category_key: str, contract_slug: str):
        if category_key not in CATEGORIES:
            return
            
        cat = CATEGORIES[category_key]
        cat_dir = self.contracts_dir / cat.folder_name
        cat_dir.mkdir(parents=True, exist_ok=True)
        
        link_path = cat_dir / contract_slug
        
        if link_path.exists() or link_path.is_symlink():
            link_path.unlink()
            
        try:
            rel_path = os.path.relpath(source, cat_dir)
            link_path.symlink_to(rel_path)
        except OSError as e:
            print(f"    [!] Symlink failed, copying instead: {e}")
            if source.is_dir():
                shutil.copytree(source, link_path, dirs_exist_ok=True)
                
    def categorize_from_hunt_results(self, hunt_results_path: str) -> Dict[str, List[str]]:
        self.setup_directories()
        
        with open(hunt_results_path, 'r') as f:
            hunt_data = json.load(f)
            
        targets = hunt_data.get("targets", [])
        categorization_results = {}
        
        print("\n📁 Categorizing contracts into archetypes...")
        print("=" * 50)
        
        category_counts: Dict[str, int] = {}
        
        for target in targets:
            name = target.get("protocol", "") or target.get("protocol_name", "") or target.get("name", "Unknown")
            slug = self._slugify(name)
            address = target.get("address", "")
            
            if not address and not target.get("vulnerabilities"):
                continue
                
            categories = self.categorize_contract(target)
            categorization_results[slug] = categories
            
            if not categories:
                continue
            
            source_dir = None
            slug_dir = self.all_dir / slug
            if slug_dir.exists():
                source_dir = slug_dir
            elif address:
                addr_slug = address[:16] if len(address) >= 16 else address
                addr_dir = self.all_dir / addr_slug
                if addr_dir.exists():
                    source_dir = addr_dir
            
            if not source_dir:
                source_dir = slug_dir
                source_dir.mkdir(parents=True, exist_ok=True)
            
            if not (source_dir / "profile.json").exists():
                profile_data = {
                    "protocol_name": name,
                    "protocol_slug": slug,
                    "address": address,
                    "chain": target.get("chain", ""),
                    "category": target.get("category", ""),
                    "tvl": target.get("tvl", 0),
                    "is_audited": target.get("audited", False),
                    "priority_score": target.get("priority_score", 0),
                    "verdicts": target.get("verdicts", []),
                    "vulnerabilities": target.get("vulnerabilities", []),
                }
                with open(source_dir / "profile.json", "w") as f:
                    json.dump(profile_data, f, indent=2)
            
            for cat_key in categories:
                self.create_symlink(source_dir, cat_key, slug)
                category_counts[cat_key] = category_counts.get(cat_key, 0) + 1
                    
            if categories:
                cat_names = [CATEGORIES[c].emoji + " " + CATEGORIES[c].name for c in categories if c in CATEGORIES]
                print(f"   {name}: {', '.join(cat_names)}")
        
        print("\n" + "=" * 50)
        print("📊 Category Summary:")
        print("-" * 50)
        
        sorted_cats = sorted(
            category_counts.items(),
            key=lambda x: CATEGORIES.get(x[0], ContractCategory("", "", "", "", 0)).priority,
            reverse=True
        )
        
        for cat_key, count in sorted_cats:
            if cat_key in CATEGORIES:
                cat = CATEGORIES[cat_key]
                print(f"   {cat.emoji} {cat.name}: {count}")
                
        return categorization_results
    
    def categorize_single(self, contract_data: Dict, contract_slug: str) -> List[str]:
        self.setup_directories()
        
        categories = self.categorize_contract(contract_data)
        
        source_dir = self.all_dir / contract_slug
        if source_dir.exists():
            for cat_key in categories:
                self.create_symlink(source_dir, cat_key, contract_slug)
                
        return categories
    
    def recategorize_all(self):
        self.setup_directories()
        
        for cat in CATEGORIES.values():
            cat_dir = self.contracts_dir / cat.folder_name
            if cat_dir.exists():
                for item in cat_dir.iterdir():
                    if item.is_symlink():
                        item.unlink()
        
        results = {}
        
        for contract_dir in self.all_dir.iterdir():
            if not contract_dir.is_dir():
                continue
                
            slug = contract_dir.name
            profile_path = contract_dir / "profile.json"
            
            if profile_path.exists():
                with open(profile_path, 'r') as f:
                    contract_data = json.load(f)
                    
                categories = self.categorize_single(contract_data, slug)
                results[slug] = categories
                
        return results
    
    def get_category_contents(self, category_key: str) -> List[str]:
        if category_key not in CATEGORIES:
            return []
            
        cat = CATEGORIES[category_key]
        cat_dir = self.contracts_dir / cat.folder_name
        
        if not cat_dir.exists():
            return []
            
        return [item.name for item in cat_dir.iterdir()]
    
    def print_category_report(self):
        print("\n" + "=" * 60)
        print("🔱 CONTRACT ARCHETYPE REPORT")
        print("=" * 60)
        
        sorted_cats = sorted(
            CATEGORIES.items(),
            key=lambda x: x[1].priority,
            reverse=True
        )
        
        for cat_key, cat in sorted_cats:
            contents = self.get_category_contents(cat_key)
            if contents:
                print(f"\n{cat.emoji} {cat.name} ({len(contents)})")
                print(f"   {cat.description}")
                print("-" * 40)
                for item in contents[:10]:
                    print(f"   • {item}")
                if len(contents) > 10:
                    print(f"   ... and {len(contents) - 10} more")
                    
    def _slugify(self, name: str) -> str:
        import re
        slug = name.lower()
        slug = re.sub(r'[^a-z0-9]+', '-', slug)
        slug = slug.strip('-')
        return slug


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
