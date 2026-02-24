# Kilo Gateway Free for Opencode

Enable Opencode to use Kilo AI Free so you can use Kilo's free model gateway and access models like **MiniMax M2.5** and **GLM-5 Z.AI**.

> Intended for use with [OH MY OPENCODE](https://github.com/code-yeongyu/oh-my-opencode) extension but **not required**

---

## Requirements

- Python 3.6+
- [opencode](https://opencode.ai) installed

---

## Quick Install (one-liner)

Copy and run one of these commands:

### Windows (PowerShell)
```powershell
irm https://raw.githubusercontent.com/ang-or-five/opencode-kilo-free-provider/refs/heads/main/install.py | python
```

### macOS / Linux (curl)
```bash
curl -sSL https://raw.githubusercontent.com/ang-or-five/opencode-kilo-free-provider/refs/heads/main/install.py | python
```

This fetches the latest `install.py` directly from GitHub and runs it. On every run, it **fetches the live model catalogue** from Kilo AI, filters for free models, and deep-merges the result into your `opencode.json`. Running the command again later updates the model list.

---

## Models (last known list)

> **Featured**: **MiniMax** and **Z.ai** — flagship models available completely free.

| Model ID | Display name |
|---|---|
| `minimax/minimax-m2.5:free` | MiniMax: MiniMax M2.5 (free) |
| `z-ai/glm-5:free` | Z.ai: GLM 5 (free) |

| `arcee-ai/trinity-large-preview:free` | Arcee AI: Trinity Large Preview (free) |
| `corethink:free` | CoreThink (free) |
| `giga-potato` | Giga Potato (free) |
| `giga-potato-thinking` | Giga Potato Thinking (free) |
| `openrouter/free` | Free Models Router (free) |
| `qwen/qwen3-235b-a22b-thinking-2507` | Qwen: Qwen3 235B A22B Thinking 2507 |
| `qwen/qwen3-vl-235b-a22b-thinking` | Qwen: Qwen3 VL 235B A22B Thinking |
| `qwen/qwen3-vl-30b-a3b-thinking` | Qwen: Qwen3 VL 30B A3B Thinking |
| `stepfun/step-3.5-flash:free` | StepFun: Step 3.5 Flash (free) |## Install / Update (manual)

```bash
python install.py
```

Options:

```bash
python install.py --dry-run   # preview model list without saving
python install.py --offline   # skip fetch, use the built-in fallback list
```

### Config file locations

| Platform | Path |
|---|---|
| Windows | `%USERPROFILE%\.config\opencode\opencode.json` |
| macOS / Linux | `~/.config/opencode/opencode.json` |

### Manual install

Copy the `provider.kilo-gateway-free` block from [`example-config.json`](./example-config.json) into your `opencode.json` by hand.

---

## How free models are identified

Two complementary filters are applied and the results are merged:

**Strategy A — `:free` suffix**
```
select models where id ends with ":free"
```

**Strategy B — zero pricing**
```
select models where pricing.prompt == "0" AND pricing.completion == "0"
```


---

## Uninstall

```bash
python uninstall.py
```

Prompts for confirmation, then removes only the `kilo-gateway-free` block from your config. All other settings untouched.

---

## Migrating from the old `kilo-anonymous` provider

```bash
python remove_kilo_anonymous.py
python install.py
```

`remove_kilo_anonymous.py` removes the old provider key and leaves everything else intact.

---

## File overview

| File | Purpose |
|---|---|
| `install.py` | Fetches live models + installs/updates `kilo-gateway-free` |
| `uninstall.py` | Removes `kilo-gateway-free` from opencode.json |
| `remove_kilo_anonymous.py` | One-time migration from old provider name |
| `example-config.json` | Reference config snippet for manual install |

---

## License

MIT
