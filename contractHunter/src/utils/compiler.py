import subprocess
from pathlib import Path
from typing import Tuple
from termcolor import cprint


def compile_test(test_code: str, test_path: Path, project_root: Path) -> Tuple[bool, str]:
    test_path.parent.mkdir(exist_ok=True, parents=True)
    temp_path = test_path.with_suffix('.sol.temp')
    
    try:
        with open(temp_path, "w") as f:
            f.write(test_code)
        
        result = subprocess.run(
            ["forge", "build", "--force"],
            cwd=project_root,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if temp_path.exists():
            temp_path.unlink()
        
        if result.returncode == 0:
            return True, None
        
        output = result.stdout + result.stderr
        error_lines = [l for l in output.split('\n') if 'Error' in l or 'error' in l][:5]
        return False, '\n'.join(error_lines) or "Compilation failed"
        
    except Exception as e:
        if temp_path.exists():
            temp_path.unlink()
        return False, str(e)
