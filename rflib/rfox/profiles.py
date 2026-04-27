"""User-saved radio profiles in ~/.rfcat/profiles.json."""
import json
import os
from typing import Dict

from .config import RFConfig


_HOME = os.path.expanduser("~")
PROFILE_DIR = os.path.join(_HOME, ".rfcat")
PROFILE_FILE = os.path.join(PROFILE_DIR, "profiles.json")


def _load_all() -> Dict[str, dict]:
    if not os.path.exists(PROFILE_FILE):
        return {}
    with open(PROFILE_FILE, "r") as f:
        return json.load(f)


def _save_all(data: Dict[str, dict]) -> None:
    os.makedirs(PROFILE_DIR, exist_ok=True)
    tmp = PROFILE_FILE + ".tmp"
    with open(tmp, "w") as f:
        json.dump(data, f, indent=2, sort_keys=True)
    os.replace(tmp, PROFILE_FILE)


def list_profiles() -> Dict[str, RFConfig]:
    return {name: RFConfig.from_dict(d) for name, d in _load_all().items()}


def load(name: str) -> RFConfig:
    data = _load_all()
    if name not in data:
        raise KeyError(f"profile {name!r} not found in {PROFILE_FILE}")
    return RFConfig.from_dict(data[name])


def save(name: str, cfg: RFConfig) -> None:
    data = _load_all()
    data[name] = cfg.to_dict()
    _save_all(data)


def delete(name: str) -> None:
    data = _load_all()
    if name not in data:
        raise KeyError(f"profile {name!r} not found")
    del data[name]
    _save_all(data)
