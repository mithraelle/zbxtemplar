import os
import sys
import importlib
import pkgutil

# Add src/ to the Python path so we can resolve zbxtemplar without it being installed
src_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src"))
sys.path.insert(0, src_dir)

from zbxtemplar.DictEntity import DictEntity
import zbxtemplar


REFERENCE_ORDER = {
    "ScrollExecutor": 10,
    "DecreeExecutor": 20,
    "UserGroup": 30,
    "User": 40,
    "UserMedia": 50,
    "Token": 60,
    "HostEncryption": 70,
}


def load_all_modules():
    """Dynamically import every file in the zbxtemplar package to register subclasses."""
    package = zbxtemplar
    for _, modname, ispkg in pkgutil.walk_packages(package.__path__, package.__name__ + '.'):
        if modname.endswith('.__main__') or 'main' in modname.split('.')[-1]:
            continue
        try:
            importlib.import_module(modname)
        except Exception as e:
            # Skip safely if there are any import errors on specific files
            print(f"Warning: skipped {modname} due to import error: {e}")


def iter_subclasses(cls, seen=None):
    """Yield all recursive subclasses of cls."""
    if seen is None:
        seen = set()
    for subclass in cls.__subclasses__():
        if subclass in seen:
            continue
        seen.add(subclass)
        yield subclass
        yield from iter_subclasses(subclass, seen)


def reference_sort_key(cls):
    return REFERENCE_ORDER.get(cls.__name__, 1000), cls.__name__


def generate():
    load_all_modules()
    
    # Set output to doc/decree_reference.md relative to the root project struct
    docs_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "doc"))
    os.makedirs(docs_dir, exist_ok=True)
    out_file = os.path.join(docs_dir, "decree_reference.md")
    
    lines = [
        "# Decree Configuration Reference",
        "",
        "> This document is automatically generated from the Python source code (`DictEntity` schemas).",
        "> Any edits or new parameters should be added directly to the `_SCHEMA` definitions in Python.",
        "",
        "---",
        ""
    ]
    
    # Keep reference docs in top-down usage order, then alphabetically for any new schemas.
    subclasses = sorted(iter_subclasses(DictEntity), key=reference_sort_key)
    
    for cls in subclasses:
        schema = getattr(cls, "_SCHEMA", [])
        if not schema:
            print(f"  [WARNING] Class '{cls.__name__}' has no _SCHEMA defined!")
            continue
            
        lines.append(f"## {cls.__name__}")
        
        # Include a docstring if the Python class has one
        if cls.__doc__:
            doc_str = ' '.join(cls.__doc__.strip().split('\n'))
            lines.append(f"{doc_str}\n")
        else:
            print(f"  [WARNING] Class '{cls.__name__}' is missing a docstring!")
            
        for field in schema:
            if not field.description:
                print(f"  [WARNING] Field '{cls.__name__}.{field.key}' is missing a description!")
                
            req_str = "Optional" if field.optional else "**Required**"
            type_str = f"*{field.str_type}*" if field.str_type else ""
            desc = f": {field.description}" if field.description else ""
            
            lines.append(f"* `{field.key}` ({req_str}, {type_str}){desc}")
            
        lines.append("")
        
    with open(out_file, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
        
    print(f"Successfully generated schema documentation: {out_file}")


if __name__ == "__main__":
    generate()
