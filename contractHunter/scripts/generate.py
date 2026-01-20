#!/usr/bin/env python3
import sys
import argparse
from pathlib import Path
from termcolor import cprint

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.models.model_factory import ModelFactory
from src.analyzers.llm_analyzer import LLMAnalyzer
from src.generators.exploit_generator import ExploitGenerator
from src.utils.compiler import compile_test
from src.utils.debugger import debug_fix_code
from src.utils.logger import save_test


def load_contract(contract_path: Path) -> str:
    if not contract_path.exists():
        cprint(f"❌ Contract not found: {contract_path}", "red")
        sys.exit(1)
    with open(contract_path, "r") as f:
        return f.read()


def main():
    parser = argparse.ArgumentParser(description="⚔️ Generate exploit test from contract")
    parser.add_argument("contract", help="Path to contract file (relative to challenges/)")
    parser.add_argument("--model", default="gpt-4o-mini", help="Model to use")
    parser.add_argument("--max-debug", type=int, default=3, help="Max debug iterations")
    args = parser.parse_args()
    
    contract_path = project_root / "challenges" / args.contract
    contract_code = load_contract(contract_path)
    
    cprint("\n🔱 Basilisk Exploit Generator", "white", "on_blue")
    cprint("=" * 50, "cyan")
    cprint(f"✅ Loaded {contract_path.name}", "green")
    
    factory = ModelFactory()
    model = factory.get_model("openai", args.model)
    
    if not model:
        cprint("❌ Failed to initialize model", "red")
        sys.exit(1)
    
    analyzer = LLMAnalyzer(model)
    analysis = analyzer.analyze(contract_code)
    
    if not analysis or not analysis['vulnerable']:
        cprint("✅ No vulnerability detected", "green")
        return
    
    cprint(f"\n📊 Found: {analysis['type']} ({analysis['severity']})", "yellow")
    cprint(f"   {analysis['explanation'][:100]}...", "yellow")
    
    templates_dir = project_root / "templates"
    generator = ExploitGenerator(templates_dir, model)
    
    contract_relative = args.contract
    test_code = generator.generate(contract_code, analysis, contract_relative)
    
    if not test_code:
        cprint("❌ Failed to generate test", "red")
        sys.exit(1)
    
    contract_name = Path(args.contract).stem
    exploit_dir = project_root / "exploits" / Path(args.contract).parent
    exploit_dir.mkdir(exist_ok=True, parents=True)
    test_path = exploit_dir / f"{contract_name}_Exploit.t.sol"
    
    success, error_msg = compile_test(test_code, test_path, project_root)
    
    if not success:
        cprint(f"\n🔧 Template test needs fixes, entering debug loop...", "yellow")
        
        for attempt in range(1, args.max_debug + 1):
            cprint(f"\n🔄 Debug attempt {attempt}/{args.max_debug}", "yellow")
            cprint(f"   Error: {error_msg[:150]}...", "red")
            
            fixed_code = debug_fix_code(model, test_code, error_msg)
            if not fixed_code:
                continue
            
            success, new_error = compile_test(fixed_code, test_path, project_root)
            if success:
                cprint(f"✅ Fixed after {attempt} attempt(s)!", "green")
                test_code = fixed_code
                break
            
            test_code = fixed_code
            error_msg = new_error
        
        if not success:
            cprint(f"⚠️ Couldn't fix after {args.max_debug} attempts", "yellow")
    
    save_test(test_code, test_path)
    cprint(f"\n✅ Exploit test generated: {test_path}", "green")


if __name__ == "__main__":
    main()
