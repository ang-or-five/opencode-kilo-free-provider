"""
install.py  —  Installs (or updates) the kilo-gateway-free provider in opencode.json.

On every run it:
  1. Fetches the live model catalogue from https://api.kilo.ai/api/openrouter/models
  2. Filters for free models using two strategies:
       a) Models whose id ends with the ':free' suffix
       b) Models where pricing.prompt == "0" AND pricing.completion == "0"
  3. Deep-merges the result into opencode.json, preserving all other keys

Usage
-----
    python install.py            # fetch live models + write config
    python install.py --dry-run  # print model list without saving anything
    python install.py --offline   # use built-in fallback list (updated by sync_models.py)
"""

import json
import os
import sys
import urllib.request
import urllib.error

MODELS_URL   = "https://api.kilo.ai/api/openrouter/models"
PROVIDER_KEY = "kilo-gateway-free"

# Manual model additions not available via the API
MANUAL_MODELS: dict[str, str] = {
    "giga-potato": "Giga Potato (free)",
    "giga-potato-thinking": "Giga Potato Thinking (free)",
}

FALLBACK_MODELS: dict[str, str] = {
    "arcee-ai/trinity-large-preview:free": "Arcee AI: Trinity Large Preview (free)",
    "corethink:free": "CoreThink (free)",
    "giga-potato": "Giga Potato (free)",
    "giga-potato-thinking": "Giga Potato Thinking (free)",
    "minimax/minimax-m2.5:free": "MiniMax: MiniMax M2.5 (free)",
    "openrouter/free": "Free Models Router (free)",
    "qwen/qwen3-235b-a22b-thinking-2507": "Qwen: Qwen3 235B A22B Thinking 2507",
    "qwen/qwen3-vl-235b-a22b-thinking": "Qwen: Qwen3 VL 235B A22B Thinking",
    "qwen/qwen3-vl-30b-a3b-thinking": "Qwen: Qwen3 VL 30B A3B Thinking",
    "stepfun/step-3.5-flash:free": "StepFun: Step 3.5 Flash (free)",
    "z-ai/glm-5:free": "Z.ai: GLM 5 (free)",
}


# ---------------------------------------------------------------------------
# Config helpers
# ---------------------------------------------------------------------------

def get_config_path() -> str:
    if sys.platform == "win32":
        base = os.getenv("USERPROFILE")
        if not base:
            print("Error: USERPROFILE environment variable not found.")
            sys.exit(1)
    else:
        base = os.path.expanduser("~")
    return os.path.join(base, ".config", "opencode")


def deep_merge(base: dict, override: dict) -> dict:
    """Recursively merge override into base without clobbering sibling keys."""
    result = base.copy()
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = value
    return result


# ---------------------------------------------------------------------------
# Model fetching & filtering
# ---------------------------------------------------------------------------

def fetch_models(url: str) -> list[dict] | None:
    """Download the model catalogue. Returns None on failure."""
    print(f"Fetching models from {url} …")
    try:
        with urllib.request.urlopen(url, timeout=15) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
        models = payload.get("data", [])
        print(f"  → {len(models)} models returned")
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

    by_suffix  = [m for m in models if is_free_by_suffix(m)]
    by_pricing = [m for m in models if is_free_by_pricing(m)]
    print(f"  → {len(by_suffix)} by :free suffix, {len(by_pricing)} by zero pricing")

    for m in by_suffix + by_pricing:
        results[m["id"]] = m.get("name", m["id"])

    # Add manual models not available via API
    for mid, name in MANUAL_MODELS.items():
        results[mid] = name
        print(f"  → Added manual model: {mid} ({name})")

    print(f"  → {len(results)} free models total (including {len(MANUAL_MODELS)} manual additions)")
    return results


def build_model_entries(id_to_name: dict[str, str]) -> dict[str, dict]:
    """Return model entries with their display names."""
    return {
        mid: {"name": name}
        for mid, name in sorted(id_to_name.items())
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    dry_run = "--dry-run" in sys.argv
    offline = "--offline" in sys.argv

    # --- Resolve model list -----------------------------------------------------
    if offline:
        print("Offline mode — using built-in fallback model list.")
        id_to_name = dict(FALLBACK_MODELS)
    else:
        raw = fetch_models(MODELS_URL)
        if raw is None:
            print("Falling back to built-in model list.")
            id_to_name = dict(FALLBACK_MODELS)
        else:
            id_to_name = collect_free_models(raw)

    model_entries = build_model_entries(id_to_name)

    # --- Print list ---------------------------------------------------------
    print(f"\n{'Model ID':<55} Display name")
    print("-" * 100)
    for mid, entry in model_entries.items():
        print(f"  {mid:<53} {entry['name']}")
    print(f"\n{len(model_entries)} free models ready.")

    if dry_run:
        print("\n[dry-run] Config not modified.")
        return

    # --- Read existing config -----------------------------------------------
    config_dir  = get_config_path()
    config_path = os.path.join(config_dir, "opencode.json")
    os.makedirs(config_dir, exist_ok=True)

    existing: dict = {}
    if os.path.exists(config_path):
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                existing = json.load(f)
            print(f"\nLoaded existing config from {config_path}")
        except json.JSONDecodeError:
            print(f"Warning: {config_path} has invalid JSON — merging into empty base.")
        except Exception as e:
            print(f"Error reading config: {e}")
            sys.exit(1)

    if "$schema" not in existing:
        existing["$schema"] = "https://opencode.ai/config.json"

    # Preserve existing provider-level options; replace only the models block.
    existing_provider = existing.get("provider", {}).get(PROVIDER_KEY, {})
    updated_provider  = deep_merge(existing_provider, {
        "npm":  "@ai-sdk/openai-compatible",
        "name": "Kilo Gateway Free",
        "options": {
            "baseURL": "https://api.kilo.ai/api/openrouter/",
            "apiKey":  "anonymous",
            "headers": {"User-Agent": "opencode-kilo-provider"},
        },
        "models": model_entries,
    })

    merged = deep_merge(existing, {"provider": {PROVIDER_KEY: updated_provider}})

    try:
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(merged, f, indent=2)
        print(f"Updated {config_path}")
        print(f'\nInstalled provider "{PROVIDER_KEY}" with {len(model_entries)} free models.')
        print("Restart opencode to see the Kilo Gateway Free models in the picker.")
    except Exception as e:
        print(f"Error writing config: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
