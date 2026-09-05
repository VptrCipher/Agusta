import ast
import hashlib
from dataclasses import dataclass
from importlib import util
from pathlib import Path


@dataclass(frozen=True)
class ScriptDefinition:
    name: str
    path: Path
    script_class: type


def _load_python_file(path):
    resolved_path = Path(path).resolve()
    digest = hashlib.sha256(str(resolved_path).encode("utf-8")).hexdigest()[:12]
    module_name = f"agentic_script_{resolved_path.stem}_{digest}"
    spec = util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load script file: {path}")
    module = util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _file_defines_class(tree, class_name):
    return any(isinstance(node, ast.ClassDef) and node.name == class_name for node in tree.body)


def _file_has_relative_import(tree):
    return any(isinstance(node, ast.ImportFrom) and node.level > 0 for node in ast.walk(tree))


def discover_script_class(path, *, class_name, base_class):
    path = Path(path)
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    if not _file_defines_class(tree, class_name):
        return None
    if _file_has_relative_import(tree):
        raise ImportError(f"Relative imports are not supported in script files: {path}")
    module = _load_python_file(path)
    script_class = getattr(module, class_name, None)
    if script_class is None:
        return None
    if not issubclass(script_class, base_class):
        raise TypeError(f"{path} {class_name} must inherit from {base_class.__name__}")
    script_class.SCRIPT_PATH = path
    script_name = getattr(script_class, "NAME", "") or path.stem
    return ScriptDefinition(name=script_name, path=path, script_class=script_class)


def discover_script_classes(directory, *, class_name, base_class):
    directory = Path(directory)
    if not directory.exists():
        return []

    definitions = []
    for path in sorted(directory.glob("*.py")):
        if path.name == "__init__.py":
            continue
        definition = discover_script_class(path, class_name=class_name, base_class=base_class)
        if definition is not None:
            definitions.append(definition)
    return definitions


def iter_overlaid_python_scripts(*directories):
    paths_by_name = {}
    for directory in directories:
        directory = Path(directory)
        if not directory.exists():
            continue
        for path in sorted(directory.glob("*.py")):
            if path.name == "__init__.py":
                continue
            paths_by_name[path.name] = path
    return [paths_by_name[name] for name in sorted(paths_by_name)]
