from pathlib import Path
from termcolor import cprint


def load_templates(templates_dir: Path, verbose: bool = False) -> dict:
    templates = {}
    
    if not templates_dir.exists():
        if verbose:
            cprint(f"⚠️ Templates directory not found: {templates_dir}", "yellow")
            cprint("   Creating templates directory...", "yellow")
        templates_dir.mkdir(exist_ok=True, parents=True)
        return templates
    
    for template_file in templates_dir.glob("*.sol"):
        template_name = template_file.stem
        try:
            with open(template_file, "r") as f:
                templates[template_name] = f.read()
            if verbose:
                cprint(f"   ✅ Loaded template: {template_name}", "green")
        except Exception as e:
            if verbose:
                cprint(f"   ❌ Failed to load {template_name}: {e}", "red")
    
    if not templates and verbose:
        cprint(f"⚠️ No templates found in {templates_dir}", "yellow")
    
    return templates
