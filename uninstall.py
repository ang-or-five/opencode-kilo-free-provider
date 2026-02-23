"""
uninstall.py  —  Removes the kilo-gateway-free provider from opencode.json.
All other keys (providers, plugins, MCP settings, etc.) are untouched.
"""

import json
import os
import sys

PROVIDER_KEY = "kilo-gateway-free"


def get_config_path() -> str:
    if sys.platform == "win32":
        base = os.getenv("USERPROFILE")
        if not base:
            print("Error: USERPROFILE environment variable not found.")
            sys.exit(1)
    else:
        base = os.path.expanduser("~")
    return os.path.join(base, ".config", "opencode")


def main():
    config_path = os.path.join(get_config_path(), "opencode.json")

    if not os.path.exists(config_path):
        print(f"No opencode.json found at {config_path} — nothing to uninstall.")
        sys.exit(0)

    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)
    except json.JSONDecodeError:
        print(f"Error: {config_path} contains invalid JSON. Please fix it manually.")
        sys.exit(1)
    except Exception as e:
        print(f"Error reading config: {e}")
        sys.exit(1)

    providers = config.get("provider", {})
    if PROVIDER_KEY not in providers:
        print(f'Provider "{PROVIDER_KEY}" not found — nothing to remove.')
        sys.exit(0)

    confirm = input(f'Remove provider "{PROVIDER_KEY}" from opencode.json? [y/N] ')
    if confirm.strip().lower() != "y":
        print("Aborted.")
        sys.exit(0)

    del providers[PROVIDER_KEY]
    if not providers:
        del config["provider"]
        print("Removed empty 'provider' block.")

    try:
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2)
        print(f'Removed "{PROVIDER_KEY}" — {config_path} updated.')
        print("Restart opencode to apply changes.")
    except Exception as e:
        print(f"Error writing config: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
