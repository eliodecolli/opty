from pathlib import Path

import yaml


def load_config(path: Path = Path("opty.config.yaml")) -> dict:
    if not path.is_file():
        raise FileNotFoundError(f"Config file not found: {path}")
    with open(path) as f:
        data = yaml.safe_load(f)
    return data.get("config", {})
