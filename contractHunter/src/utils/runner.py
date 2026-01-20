import subprocess
import shutil
from pathlib import Path
from typing import Dict


def run_forge_test(test_path, project_root: Path) -> Dict:
    try:
        if isinstance(test_path, Path):
            source_path = test_path
        else:
            source_path = project_root / "exploits" / test_path
        
        if not source_path.exists():
            return {"success": False, "stdout": "", "stderr": f"Test file not found: {source_path}"}
        
        test_dir = project_root / "test"
        test_dir.mkdir(exist_ok=True)
        
        test_file_name = source_path.name
        temp_test_path = test_dir / test_file_name
        
        shutil.copy2(source_path, temp_test_path)
        
        try:
            result = subprocess.run(
                ["forge", "test", "--match-path", f"test/{test_file_name}", "-vvv"],
                cwd=project_root,
                capture_output=True,
                text=True,
                timeout=60
            )
            return {
                "success": result.returncode == 0,
                "stdout": result.stdout,
                "stderr": result.stderr
            }
        finally:
            if temp_test_path.exists():
                temp_test_path.unlink()
                
    except Exception as e:
        return {"success": False, "stdout": "", "stderr": str(e)}
