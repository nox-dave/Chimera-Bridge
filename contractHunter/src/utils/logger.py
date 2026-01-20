import json
from datetime import datetime
from pathlib import Path
from typing import Dict
from termcolor import cprint


def log_finding(results_dir: Path, contract_name: str, analysis: Dict, test_passed: bool):
    results_dir.mkdir(exist_ok=True, parents=True)
    findings_json = results_dir / "findings.json"
    
    result = {
        "contract": contract_name,
        "vulnerability_type": analysis['type'],
        "severity": analysis['severity'],
        "test_passed": test_passed,
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }
    
    with open(findings_json, "a") as f:
        json.dump(result, f)
        f.write("\n")


def save_test(test_code: str, test_path: Path):
    test_path.parent.mkdir(exist_ok=True, parents=True)
    
    backup_path = test_path.with_suffix('.sol.backup')
    if test_path.exists():
        import shutil
        shutil.copy(test_path, backup_path)
    
    with open(test_path, "w") as f:
        f.write(test_code)
    cprint(f"💾 Saved to {test_path}", "green")
