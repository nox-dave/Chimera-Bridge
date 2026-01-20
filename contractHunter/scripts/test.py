#!/usr/bin/env python3
import sys
import argparse
from pathlib import Path
from termcolor import cprint

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.utils.runner import run_forge_test
from src.utils.logger import log_finding
from src.models.model_factory import ModelFactory
from src.analyzers.llm_analyzer import LLMAnalyzer


def main():
    parser = argparse.ArgumentParser(description="🧪 Run exploit test")
    parser.add_argument("test", help="Path to test file (relative to exploits/)")
    parser.add_argument("--contract", help="Contract path for logging (optional)")
    args = parser.parse_args()
    
    test_path = project_root / "exploits" / args.test
    
    if not test_path.exists():
        cprint(f"❌ Test not found: {test_path}", "red")
        sys.exit(1)
    
    cprint("\n🧪 Running forge test...", "cyan")
    
    relative_test_path = test_path.relative_to(project_root)
    result = run_forge_test(relative_test_path, project_root)
    
    cprint("\n" + "=" * 50, "cyan")
    if result["success"]:
        cprint("✅ EXPLOIT CONFIRMED!", "green")
    else:
        cprint("❌ Test failed", "red")
        if result["stdout"]:
            print(result["stdout"][-1000:])
    
    if args.contract:
        factory = ModelFactory()
        model = factory.get_model("openai", "gpt-4o-mini")
        if model:
            analyzer = LLMAnalyzer(model)
            contract_path = project_root / "challenges" / args.contract
            if contract_path.exists():
                with open(contract_path, "r") as f:
                    contract_code = f.read()
                analysis = analyzer.analyze(contract_code)
                if analysis:
                    results_dir = project_root / "results"
                    contract_name = Path(args.contract).stem
                    log_finding(results_dir, contract_name, analysis, result["success"])


if __name__ == "__main__":
    main()
