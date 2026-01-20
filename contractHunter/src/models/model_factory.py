"""
Model Factory for OpenAI models
"""

import os
from typing import Optional
from termcolor import cprint
from dotenv import load_dotenv
from pathlib import Path
from .base_model import BaseModel
from .openai_model import OpenAIModel

class ModelFactory:
    """Factory for creating and managing AI models"""
    
    DEFAULT_MODEL = "gpt-5-nano"
    
    def __init__(self):
        cprint("\n🏗️ Creating new ModelFactory instance...", "cyan")
        
        project_root = Path(__file__).parent.parent.parent
        env_path = project_root / '.env'
        cprint(f"\n🔍 Loading environment from: {env_path}", "cyan")
        load_dotenv(dotenv_path=env_path)
        cprint("✨ Environment loaded", "green")
        
        self._models = {}
        self._initialize_models()
    
    def _initialize_models(self):
        """Initialize available models"""
        cprint("\n🏭 Model Factory Initialization", "cyan")
        cprint("═" * 50, "cyan")
        
        api_key = os.getenv("OPENAI_KEY")
        
        if api_key:
            try:
                model_instance = OpenAIModel(api_key)
                if model_instance.is_available():
                    self._models["openai"] = model_instance
                    cprint(f"  ✅ openai: {model_instance.model_name}", "green")
                else:
                    cprint("  ⚠️ openai: API key invalid (skipping)", "yellow")
            except Exception as e:
                error_type = type(e).__name__
                if "Authentication" in error_type or "Invalid" in error_type or "401" in str(e) or "403" in str(e):
                    cprint("  ⚠️ openai: Invalid API key (skipping)", "yellow")
                else:
                    cprint(f"  ⚠️ openai: {error_type} (skipping)", "yellow")
        else:
            cprint("  ⚠️ openai: No API key found (skipping)", "yellow")
        
        cprint("\n" + "═" * 50, "cyan")
        
        if not self._models:
            cprint("⚠️ No AI models available - check OPENAI_KEY in .env", "yellow")
        else:
            cprint(f"✅ Initialized {len(self._models)} model(s): {', '.join(self._models.keys())}", "green")
    
    def get_model(self, model_type: str = "openai", model_name: Optional[str] = None) -> Optional[BaseModel]:
        """Get a specific model instance"""
        cprint(f"\n🔍 Requesting model: {model_type} ({model_name or 'default'})", "cyan")
        
        if model_type != "openai":
            cprint(f"❌ Invalid model type: '{model_type}'. Only 'openai' is supported.", "red")
            return None
        
        if model_type not in self._models:
            cprint(f"❌ Model type '{model_type}' not available - check OPENAI_KEY in .env", "red")
            return None
        
        model = self._models[model_type]
        if model_name and model.model_name != model_name:
            cprint(f"🔄 Reinitializing {model_type} with model {model_name}...", "cyan")
            api_key = os.getenv("OPENAI_KEY")
            if api_key:
                try:
                    model = OpenAIModel(api_key, model_name=model_name)
                    self._models[model_type] = model
                    cprint(f"✨ Successfully reinitialized with new model", "green")
                except Exception as e:
                    cprint(f"❌ Failed to initialize {model_type} with model {model_name}", "red")
                    cprint(f"❌ Error type: {type(e).__name__}", "red")
                    cprint(f"❌ Error: {str(e)}", "red")
                    return None
            else:
                cprint("❌ OPENAI_KEY not found in environment", "red")
                return None
        
        return model
    
    def is_model_available(self, model_type: str = "openai") -> bool:
        """Check if a specific model type is available"""
        return model_type in self._models and self._models[model_type].is_available()
