"""
sync_models.py — Syncs the live model list to install.py and README.md.

This script fetches the current free models from the Kilo API and updates:
  1. FALLBACK_MODELS in install.py — for offline mode
  2. README.md model table — for documentation
  3. example-config.json models — for manual install reference

Usage
-----
    python sync_models.py            # fetch and update files
    python sync_models.py --dry-run  # print changes without writing
"""

import json
import os
import re
import sys
import urllib.request
import urllib.error

MODELS_URL = "https://api.kilo.ai/api/openrouter/models"
INSTALL_PATH = os.path.join(os.path.dirname(__file__), "install.py")
README_PATH = os.path.join(os.path.dirname(__file__), "README.md")
EXAMPLE_PATH = os.path.join(os.path.dirname(__file__), "example-config.json")

# Manual model additions not available via the API
MANUAL_MODELS: dict[str, str] = {
    "giga-potato": "Giga Potato (free)",
    "giga-potato-thinking": "Giga Potato Thinking (free)",
}


def fetch_models(url: str) -> list[dict] | None:
    """Download the model catalogue. Returns None on failure."""
    print(f"Fetching models from {url} ...")
    try:
        with urllib.request.urlopen(url, timeout=15) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
        models = payload.get("data", [])
        print(f"  -> {len(models)} models returned")
        return models
    except Exception as e:
        print(f"  Warning: could not fetch models ({e})")
        return None


def is_free_by_suffix(m: dict) -> bool:
    return str(m.get("id", "")).endswith(":free")


def is_free_by_pricing(m: dict) -> bool:
    p = m.get("pricing", {})
    return (str(p.get("prompt", "")).strip() in ("0", "0.0") and
            str(p.get("completion", "")).strip() in ("0", "0.0"))


def collect_free_models(models: list[dict]) -> dict[str, str]:
    """Return { model_id: raw_display_name } for all free models."""
    results: dict[str, str] = {}

    by_suffix = [m for m in models if is_free_by_suffix(m)]
    by_pricing = [m for m in models if is_free_by_pricing(m)]
    print(f"  -> {len(by_suffix)} by :free suffix, {len(by_pricing)} by zero pricing")

    for m in by_suffix + by_pricing:
        results[m["id"]] = m.get("name", m["id"])

    # Add manual models not available via API
    for mid, name in MANUAL_MODELS.items():
        results[mid] = name
        print(f"  -> Added manual model: {mid} ({name})")

    print(f"  -> {len(results)} free models total (including {len(MANUAL_MODELS)} manual additions)")
    return results


def format_fallback_dict(models: dict[str, str]) -> str:
    """Format a dict as a Python FALLBACK_MODELS literal."""
    lines = ["{"]
    for mid, name in sorted(models.items()):
        lines.append(f'    "{mid}": "{name}",')
    lines.append("}")
    return "\n".join(lines)


def update_install_py(install_path: str, models: dict[str, str]) -> None:
    """Update FALLBACK_MODELS in install.py."""
    with open(install_path, "r", encoding="utf-8") as f:
        content = f.read()

    new_fallback = format_fallback_dict(models)
    pattern = r"FALLBACK_MODELS: dict\[str, str\] = \{[^}]*\}"
    replacement = f"FALLBACK_MODELS: dict[str, str] = {new_fallback}"

    new_content = re.sub(pattern, replacement, content, flags=re.DOTALL)

    with open(install_path, "w", encoding="utf-8") as f:
        f.write(new_content)

    print(f"Updated FALLBACK_MODELS in {install_path}")


def get_featured_models(models: dict[str, str]) -> list[tuple[str, str]]:
    """Return featured models (MiniMax M2.5 and GLM-5)."""
    featured = []
    for mid in ["minimax/minimax-m2.5:free", "z-ai/glm-5:free"]:
        if mid in models:
            featured.append((mid, models[mid]))
    return featured


def update_readme(readme_path: str, models: dict[str, str]) -> None:
    """Update the model table in README.md."""
    featured = get_featured_models(models)
    other_models = [(mid, name) for mid, name in sorted(models.items())
                     if mid not in ["minimax/minimax-m2.5:free", "z-ai/glm-5:free"]]

    table_lines = ["| Model ID | Display name |", "|---|---|"]

    for mid, name in featured:
        table_lines.append(f"| `{mid}` | {name} |")

    table_lines.append("")

    for mid, name in other_models:
        table_lines.append(f"| `{mid}` | {name} |")

    new_table = "\n".join(table_lines)

    pattern = r"## Models \(last known list\)\n\n> \*\*Featured\*\*: .*\n\n\| Model ID \| Display name \|[^#]*"
    replacement = f"## Models (last known list)\n\n> **Featured**: **{featured[0][1].split(':')[0]}** and **{featured[1][1].split(':')[0]}** — flagship models available completely free.\n\n{new_table}"

    with open(readme_path, "r", encoding="utf-8") as f:
        content = f.read()

    new_content = re.sub(pattern, replacement, content, flags=re.DOTALL)

    with open(readme_path, "w", encoding="utf-8") as f:
        f.write(new_content)

    print(f"Updated model table in {readme_path}")


def update_example_config(example_path: str, models: dict[str, str]) -> None:
    """Update the models section in example-config.json."""
    with open(example_path, "r", encoding="utf-8") as f:
        config = json.load(f)

    models_config = {}
    for mid, name in sorted(models.items()):
        models_config[mid] = {"name": f"{name} [Kilo Free]"}

    config["provider"]["kilo-gateway-free"]["models"] = models_config

    with open(example_path, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)
        f.write("\n")

    print(f"Updated models in {example_path}")


def main():
    dry_run = "--dry-run" in sys.argv

    raw = fetch_models(MODELS_URL)
    if raw is None:
        print("Failed to fetch models, exiting.")
        sys.exit(1)

    models = collect_free_models(raw)

    print(f"\n{'Model ID':<55} Display name")
    print("-" * 100)
    for mid, entry in sorted(models.items()):
        print(f"  {mid:<53} {entry}")
    print(f"\n{len(models)} free models ready.")

    if dry_run:
        print("\n[dry-run] No files modified.")
        return

    update_install_py(INSTALL_PATH, models)
    update_readme(README_PATH, models)
    update_example_config(EXAMPLE_PATH, models)

    print("\nSync complete. Commit the updated files.")


if __name__ == "__main__":
    main()
