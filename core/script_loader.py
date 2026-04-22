import importlib
import importlib.util
import sys
import os
import logging

logger = logging.getLogger(__name__)

SCRIPTS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "scripts")


def _module_key(script_name):
    return f"_scripts.{script_name}"


def load_script(script_name):
    module_key = _module_key(script_name)
    script_path = os.path.join(SCRIPTS_DIR, f"{script_name}.py")

    if not os.path.exists(script_path):
        logger.warning(f"Script file not found: {script_path}")
        return None

    spec = importlib.util.spec_from_file_location(module_key, script_path)
    if spec is None:
        logger.error(f"Could not create module spec for: {script_path}")
        return None

    module = importlib.util.module_from_spec(spec)
    sys.modules[module_key] = module

    try:
        spec.loader.exec_module(module)
    except Exception as e:
        logger.error(f"Error loading script '{script_name}': {e}")
        return None

    if not hasattr(module, "Script"):
        logger.error(f"Script '{script_name}' has no class named 'Script'")
        return None

    return module


def reload_script(script_name):
    module_key = _module_key(script_name)
    if module_key in sys.modules:
        del sys.modules[module_key]
    return load_script(script_name)


def instantiate_script(script_name):
    module = load_script(script_name)
    if module is None:
        return None
    try:
        return module.Script()
    except Exception as e:
        logger.error(f"Error instantiating Script from '{script_name}': {e}")
        return None


def reload_and_instantiate(script_name):
    module = reload_script(script_name)
    if module is None:
        return None
    try:
        return module.Script()
    except Exception as e:
        logger.error(f"Error instantiating reloaded Script from '{script_name}': {e}")
        return None


def list_available_scripts():
    if not os.path.isdir(SCRIPTS_DIR):
        return []
    names = []
    for fname in sorted(os.listdir(SCRIPTS_DIR)):
        if fname.endswith(".py") and not fname.startswith("_"):
            names.append(fname[:-3])
    return names
