from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from src.settings import get_user_data_dir

PROFILE_DATA_PATH = get_user_data_dir() / "players.json"


def _hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def _default_account() -> dict[str, Any]:
    return {
        "password_hash": "",
        "settings": {
            "sound_enabled": True,
            "difficulty": "Medium",
            "timed_games": True,
            "time_limit_minutes": 5,
        },
        "stats": {
            "games_played": 0,
            "white_wins": 0,
            "black_wins": 0,
            "draws": 0,
            "estimated_elo": 1200.0,
            "_white_scores": [],
        },
    }


def load_profiles(path: Path | str = PROFILE_DATA_PATH) -> dict[str, dict[str, Any]]:
    profile_path = Path(path)
    if not profile_path.exists():
        return {}
    try:
        with profile_path.open("r", encoding="utf-8") as handle:
            loaded = json.load(handle)
    except (json.JSONDecodeError, OSError):
        return {}
    if not isinstance(loaded, dict):
        return {}
    normalized: dict[str, dict[str, Any]] = {}
    for username, payload in loaded.items():
        if not isinstance(payload, dict):
            continue
        normalized[username] = {**_default_account(), **payload}
    return normalized


def save_profiles(profiles: dict[str, dict[str, Any]], path: Path | str = PROFILE_DATA_PATH) -> None:
    profile_path = Path(path)
    profile_path.parent.mkdir(parents=True, exist_ok=True)
    with profile_path.open("w", encoding="utf-8") as handle:
        json.dump(profiles, handle, indent=2, sort_keys=True)


class ProfileManager:
    def __init__(self, path: Path | str = PROFILE_DATA_PATH):
        self.path = Path(path)

    def list_profiles(self) -> dict[str, dict[str, Any]]:
        return load_profiles(self.path)

    def leaderboard(self) -> list[tuple[str, dict[str, Any]]]:
        profiles = self.list_profiles()
        return sorted(
            profiles.items(),
            key=lambda item: (
                float(item[1].get("stats", {}).get("estimated_elo", 1200)),
                int(item[1].get("stats", {}).get("games_played", 0)),
                item[0].casefold(),
            ),
            reverse=True,
        )

    def _write_profiles(self, profiles: dict[str, dict[str, Any]]) -> None:
        save_profiles(profiles, self.path)

    def create_account(
        self,
        username: str,
        password: str,
    ) -> dict[str, Any]:
        cleaned = username.strip()
        if not cleaned:
            raise ValueError("Username cannot be empty.")
        if len(password) < 3:
            raise ValueError("Password must be at least 3 characters long.")

        profiles = self.list_profiles()
        if cleaned in profiles:
            raise ValueError("That username already exists.")

        account = _default_account()
        account["password_hash"] = _hash_password(password)
        profiles[cleaned] = account
        self._write_profiles(profiles)
        return profiles[cleaned]

    def authenticate(self, username: str, password: str) -> dict[str, Any] | None:
        cleaned = username.strip()
        profiles = self.list_profiles()
        profile = profiles.get(cleaned)
        if profile is None:
            return None
        if profile.get("password_hash") != _hash_password(password):
            return None
        return profile

    def delete_account(self, username: str) -> None:
        cleaned = username.strip()
        profiles = self.list_profiles()
        if cleaned not in profiles:
            raise ValueError("Profile does not exist.")
        del profiles[cleaned]
        self._write_profiles(profiles)

    def save_profile(self, username: str, settings: dict[str, Any], stats: dict[str, Any]) -> dict[str, Any]:
        cleaned = username.strip()
        profiles = self.list_profiles()
        if cleaned not in profiles:
            raise ValueError("Profile does not exist.")
        profile = profiles[cleaned]
        profile["settings"] = settings
        profile["stats"] = stats
        self._write_profiles(profiles)
        return profile
