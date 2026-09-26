"""Analyze the repository layout and report database/deployment signals."""

import argparse
import ast
import json
import re
from collections import Counter
from pathlib import Path


EXCLUDED = {".git", ".venv", "venv", "node_modules", "__pycache__", "static"}
TABLE_PATTERN = re.compile(r"\b(?:FROM|INTO|UPDATE|JOIN)\s+([A-Za-z_][A-Za-z0-9_]*)", re.IGNORECASE)


def project_files(root):
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        relative = path.relative_to(root)
        if any(part in EXCLUDED for part in relative.parts):
            continue
        yield path


def analyze(root):
    files = list(project_files(root))
    extension_counts = Counter(path.suffix.lower() or "[sin extension]" for path in files)
    api_root = root / "backend" / "API"
    python_files = [
        path for path in api_root.rglob("*.py")
        if path.is_file() and "static" not in path.relative_to(api_root).parts
    ] if api_root.exists() else []

    layers = {}
    for layer in ("Routes", "Controllers", "Services", "Models"):
        layer_path = api_root / layer
        layers[layer] = sorted(
            path.name for path in layer_path.glob("*.py")
            if path.is_file() and path.name != "__init__.py"
        ) if layer_path.exists() else []

    service_files = [path for path in python_files if "Services" in path.parts]
    sql_fragments = []
    for path in service_files:
        source = path.read_text(encoding="utf-8", errors="replace")
        for node in ast.walk(ast.parse(source)):
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                if re.search(r"\b(?:SELECT|INSERT|UPDATE|DELETE)\b", node.value, re.IGNORECASE):
                    sql_fragments.append(node.value)
    table_names = sorted({name.upper() for name in TABLE_PATTERN.findall("\n".join(sql_fragments))})
    database_files = [
        path.relative_to(root).as_posix() for path in files
        if path.suffix.lower() == ".sql" or path.name.lower() in {"alembic.ini", "env.py"}
    ]

    return {
        "root": str(root),
        "file_count": len(files),
        "files_by_extension": dict(sorted(extension_counts.items())),
        "backend_python_file_count": len(python_files),
        "backend_layers": layers,
        "service_files_using_legacy_mysql": [
            path.relative_to(root).as_posix()
            for path in service_files
            if "current_app.mysql" in path.read_text(encoding="utf-8", errors="replace")
        ],
        "table_names_in_service_sql": table_names,
        "schema_or_migration_files": database_files,
        "deployment_files": [
            path.relative_to(root).as_posix() for path in files
            if path.name.lower().startswith(("dockerfile", "compose", "docker-compose"))
            or path.name.lower() in {"netlify.toml", "dokploy.yaml"}
        ],
        "findings": [
            "Los servicios actuales usan cursores MySQL; revisalos antes de migrarlos al ORM.",
            "No se encontro esquema SQL ni migraciones." if not database_files else "Se encontraron archivos de esquema o migracion SQL.",
            "El analizador excluye archivos generados/estaticos y nunca lee archivos .env.",
        ],
    }


def main():
    default_root = Path(__file__).resolve().parent.parent
    parser = argparse.ArgumentParser(description="Analiza estructura, persistencia y despliegue del proyecto.")
    parser.add_argument("--root", type=Path, default=default_root, help="Raiz del repositorio (por defecto, la carpeta padre).")
    args = parser.parse_args()
    report = analyze(args.root.resolve())
    print(json.dumps(report, ensure_ascii=True, indent=2))


if __name__ == "__main__":
    main()
