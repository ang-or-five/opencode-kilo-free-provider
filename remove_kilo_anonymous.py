"""
remove_kilo_anonymous.py  —  One-time migration from the old provider name.

Removes the "kilo-anonymous" provider block that was used before this project
was renamed to "kilo-gateway-free". Run this once, then run install.py.
"""

import json
import os
import sys

OLD_KEY = "kilo-anonymous"


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
        print(f"No opencode.json found at {config_path} — nothing to do.")
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
    if OLD_KEY not in providers:
        print(f'Old provider "{OLD_KEY}" not found — nothing to remove.')
        print("You're already clean. Run  python install.py  to add kilo-gateway-free.")
        sys.exit(0)

    confirm = input(f'Remove legacy provider "{OLD_KEY}" from opencode.json? [y/N] ')
    if confirm.strip().lower() != "y":
        print("Aborted.")
        sys.exit(0)

    del providers[OLD_KEY]
    if not providers:
        del config["provider"]

    try:
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2)
        print(f'Removed "{OLD_KEY}" from {config_path}.')
        print("\nNext step:  python install.py")
    except Exception as e:
        print(f"Error writing config: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
