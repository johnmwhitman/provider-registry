#!/usr/bin/env python3
"""Validate TOML provider registry files for structure and required fields."""

import sys
from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:
    try:
        import tomli as tomllib  # type: ignore[no-redef]
    except ModuleNotFoundError:
        tomllib = None


def validate_file(path: Path) -> tuple[bool, list[str]]:
    """Validate a single TOML file for structure and required fields.

    Returns:
        (parsed_successfully, errors)
    """
    errors: list[str] = []
    try:
        with path.open("rb") as f:
            data = tomllib.load(f)
    except tomllib.TOMLDecodeError as e:
        return False, [f"{path}: TOML parse error: {e}"]
    except OSError as e:
        return False, [f"{path}: read error: {e}"]

    # Required fields per the README spec
    required = ["id", "name", "auth", "api_base", "models"]
    missing = [k for k in required if k not in data]
    if missing:
        errors.append(f"{path}: missing required fields {missing}")
        return True, errors

    models = data.get("models")
    if not isinstance(models, list) or len(models) == 0:
        errors.append(f"{path}: models must be a non-empty list")
    else:
        for m in models:
            if not isinstance(m, dict) or "id" not in m or "name" not in m:
                errors.append(f"{path}: model missing id or name: {m}")

    return True, errors


def main() -> int:
    if tomllib is None:
        print("Error: Python 3.11+ (with tomllib) or the 'tomli' package is required.", file=sys.stderr)
        return 1

    target = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("dist")

    if target.is_file():
        toml_files = [target]
        target_display = str(target)
    else:
        # If default target 'dist' does not exist in cwd, fallback to repo root relative to this script
        if not target.exists() and len(sys.argv) == 1:
            repo_dist = Path(__file__).resolve().parent.parent / "dist"
            if repo_dist.exists():
                target = repo_dist
        toml_files = sorted(target.glob("*.toml"))
        target_display = f"{target.name}/" if target.is_dir() else str(target)

    errors: list[str] = []
    count = 0
    for path in toml_files:
        parsed, file_errors = validate_file(path)
        if parsed:
            count += 1
        errors.extend(file_errors)

    print(f"Validated {count} TOML file(s) in {target_display}")
    if errors:
        print("FAILURES:")
        for e in errors:
            print(f"  - {e}")
        return 1

    print("OK: all TOML files valid")
    return 0


if __name__ == "__main__":
    sys.exit(main())
