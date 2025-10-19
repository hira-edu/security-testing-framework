from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

from src.cli.constants import CLICommand


class ProfileValidationError(ValueError):
    """Raised when a CLI profile fails validation."""


@dataclass(frozen=True)
class OptionDefinition:
    """Schema definition for a command option."""

    name: str
    expected_type: type
    required: bool = False
    multiple: bool = False
    choices: Optional[List[str]] = None

    def convert(self, raw: Any) -> Any:
        """Coerce raw values into the expected Python type."""
        if raw is None:
            if self.required:
                raise ProfileValidationError(f"Option '{self.name}' is required.")
            return [] if self.multiple else None

        if self.multiple:
            values: List[Any]
            if isinstance(raw, (list, tuple, set)):
                values = list(raw)
            elif isinstance(raw, str):
                values = [item.strip() for item in raw.split(",") if item.strip()]
            else:
                values = [raw]
            converted = [self._convert_single(value) for value in values]
            if self.choices:
                invalid = [value for value in converted if value not in self.choices]
                if invalid:
                    raise ProfileValidationError(
                        f"Option '{self.name}' received unsupported values: {', '.join(invalid)}"
                    )
            return converted

        value = self._convert_single(raw)
        if self.choices and value not in self.choices:
            raise ProfileValidationError(
                f"Option '{self.name}' must be one of: {', '.join(self.choices)}"
            )
        return value

    def _convert_single(self, raw: Any) -> Any:
        if self.expected_type is bool:
            if isinstance(raw, bool):
                return raw
            if isinstance(raw, str):
                lowered = raw.strip().lower()
                if lowered in {"1", "true", "yes", "on"}:
                    return True
                if lowered in {"0", "false", "no", "off"}:
                    return False
            if isinstance(raw, (int, float)):
                return bool(raw)
            raise ProfileValidationError(
                f"Option '{self.name}' must be a boolean value."
            )

        if self.expected_type is int:
            if isinstance(raw, int):
                return raw
            if isinstance(raw, str) and raw.strip():
                try:
                    return int(raw.strip())
                except ValueError as exc:
                    raise ProfileValidationError(
                        f"Option '{self.name}' must be an integer."
                    ) from exc
            raise ProfileValidationError(f"Option '{self.name}' must be an integer.")

        if self.expected_type is str:
            return str(raw)

        return raw


COMMAND_OPTION_DEFINITIONS: Dict[CLICommand, Dict[str, OptionDefinition]] = {
    CLICommand.MONITOR: {
        "target": OptionDefinition("target", str),
        "profile": OptionDefinition("profile", str),
        "duration": OptionDefinition("duration", int),
        "stealth": OptionDefinition("stealth", bool),
        "comprehensive": OptionDefinition("comprehensive", bool),
        "output": OptionDefinition("output", str),
    },
    CLICommand.INJECT: {
        "target": OptionDefinition("target", str),
        "method": OptionDefinition("method", str, required=True),
        "dll": OptionDefinition("dll", str),
        "profile": OptionDefinition("profile", str),
        "layer": OptionDefinition("layer", str, multiple=True),
        "from_inventory": OptionDefinition("from_inventory", str),
    },
    CLICommand.CAPTURE: {
        "target": OptionDefinition("target", str),
        "method": OptionDefinition("method", str),
        "output": OptionDefinition("output", str),
        "image": OptionDefinition("image", str),
        "metadata": OptionDefinition("metadata", str),
    },
    CLICommand.HOOKS: {
        "action": OptionDefinition(
            "action",
            str,
            required=True,
            choices=["status", "enable", "disable"],
        ),
        "profile": OptionDefinition("profile", str),
        "layer": OptionDefinition("layer", str, multiple=True),
        "from_inventory": OptionDefinition("from_inventory", str),
        "target": OptionDefinition("target", str),
        "process": OptionDefinition("process", str),
        "pid": OptionDefinition("pid", int),
        "service": OptionDefinition("service", str),
        "file": OptionDefinition("file", str),
    },
    CLICommand.REPORT: {
        "target": OptionDefinition("target", str),
        "output": OptionDefinition("output", str, required=True),
        "input": OptionDefinition("input", str),
        "pid": OptionDefinition("pid", int),
        "from_inventory": OptionDefinition("from_inventory", str),
    },
    CLICommand.INVENTORY: {
        "name": OptionDefinition("name", str),
        "pid": OptionDefinition("pid", int),
        "session": OptionDefinition("session", int),
        "integrity": OptionDefinition(
            "integrity",
            str,
            choices=["low", "medium", "high", "system", "protected", "unknown"],
        ),
        "user": OptionDefinition("user", str),
        "window": OptionDefinition("window", str),
        "limit": OptionDefinition("limit", int),
        "baseline": OptionDefinition("baseline", str),
        "sort_by": OptionDefinition("sort_by", str),
        "sort_desc": OptionDefinition("sort_desc", bool),
        "include_windows": OptionDefinition("include_windows", bool),
    },
}


def sanitize_options(command: CLICommand, options: Dict[str, Any]) -> Dict[str, Any]:
    """Validate and normalise option payloads for a command."""
    if command == CLICommand.PROFILES:
        raise ProfileValidationError("Profiles command cannot be stored as a preset.")

    definitions = COMMAND_OPTION_DEFINITIONS.get(command, {})
    normalised: Dict[str, Any] = {}

    for key, value in options.items():
        definition = definitions.get(key)
        if not definition:
            raise ProfileValidationError(
                f"Option '{key}' is not supported for command '{command.value}'."
            )
        normalised[key] = definition.convert(value)

    for definition in definitions.values():
        if definition.required and definition.name not in normalised:
            raise ProfileValidationError(
                f"Option '{definition.name}' is required for command '{command.value}'."
            )

    return normalised


def parse_key_value_pairs(
    command: CLICommand, pairs: Optional[Iterable[str]]
) -> Dict[str, Any]:
    """Parse --set key=value pairs for a given command."""
    if not pairs:
        return {}

    collected: Dict[str, Any] = {}
    for pair in pairs:
        if "=" not in pair:
            raise ProfileValidationError(
                f"Invalid option format '{pair}'. Use key=value."
            )
        key, raw_value = pair.split("=", 1)
        key = key.strip()
        raw_value = raw_value.strip()

        definition = COMMAND_OPTION_DEFINITIONS.get(command, {}).get(key)
        if not definition:
            raise ProfileValidationError(
                f"Option '{key}' is not supported for command '{command.value}'."
            )

        if definition.multiple:
            values = [item.strip() for item in raw_value.split(",") if item.strip()]
            if not values:
                raise ProfileValidationError(
                    f"Option '{key}' requires at least one value."
                )
            existing = collected.get(key, [])
            if isinstance(existing, list):
                existing.extend(values)
                collected[key] = existing
            else:  # defensive fallback
                merged = [existing] if existing else []
                merged.extend(values)
                collected[key] = merged
        else:
            collected[key] = raw_value

    return sanitize_options(command, collected)


@dataclass
class CLIProfile:
    """Persisted CLI preset."""

    name: str
    command: CLICommand
    options: Dict[str, Any]
    description: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        timestamp = datetime.utcnow().replace(microsecond=0).isoformat() + "Z"
        created = self.created_at or timestamp
        return {
            "name": self.name,
            "command": self.command.value,
            "options": sanitize_options(self.command, self.options),
            "description": self.description,
            "created_at": created,
            "updated_at": timestamp,
        }

    @classmethod
    def from_dict(cls, payload: Dict[str, Any]) -> "CLIProfile":
        try:
            command = CLICommand(payload["command"])
        except KeyError as exc:
            raise ProfileValidationError("Profile is missing 'command'.") from exc
        options = sanitize_options(command, payload.get("options", {}))
        return cls(
            name=payload.get("name") or "",
            command=command,
            options=options,
            description=payload.get("description"),
            created_at=payload.get("created_at"),
            updated_at=payload.get("updated_at"),
        )


class ProfileStore:
    """Disk-backed store for CLI profiles."""

    def __init__(self, base_dir: Path):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def exists(self, name: str) -> bool:
        return self._path_for(name).exists()

    def list_profiles(self) -> List[Dict[str, Any]]:
        profiles: List[Dict[str, Any]] = []
        for profile_path in sorted(self.base_dir.glob("*.json")):
            try:
                payload = json.loads(profile_path.read_text(encoding="utf-8"))
                profile = CLIProfile.from_dict(payload)
            except (json.JSONDecodeError, ProfileValidationError):
                continue
            summary = {
                "name": profile.name or profile_path.stem,
                "command": profile.command.value,
                "description": profile.description,
                "updated_at": profile.updated_at,
            }
            profiles.append(summary)
        return profiles

    def load(self, name: str) -> CLIProfile:
        profile_path = self._path_for(name)
        if not profile_path.exists():
            raise FileNotFoundError(f"Profile '{name}' does not exist.")
        payload = json.loads(profile_path.read_text(encoding="utf-8"))
        profile = CLIProfile.from_dict(payload)
        profile.name = profile.name or name
        return profile

    def save(self, profile: CLIProfile, *, overwrite: bool = False) -> CLIProfile:
        if not profile.name:
            raise ProfileValidationError("Profile name cannot be empty.")

        target_path = self._path_for(profile.name)
        if target_path.exists() and not overwrite:
            raise ProfileValidationError(
                f"Profile '{profile.name}' already exists. Use overwrite to replace it."
            )

        payload = profile.to_dict()
        payload["name"] = profile.name
        target_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        return CLIProfile.from_dict(payload)

    def delete(self, name: str) -> None:
        profile_path = self._path_for(name)
        if not profile_path.exists():
            raise FileNotFoundError(f"Profile '{name}' does not exist.")
        profile_path.unlink()

    def apply(
        self,
        name: str,
        overrides: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        profile = self.load(name)
        resolved_options = dict(profile.options)

        if overrides:
            merged = sanitize_options(profile.command, overrides)
            resolved_options.update(merged)

        return {
            "name": profile.name,
            "command": profile.command.value,
            "description": profile.description,
            "options": resolved_options,
        }

    def seed_defaults(self, profiles: Iterable[CLIProfile]) -> None:
        """Persist default profiles if they do not already exist."""
        for profile in profiles:
            if not profile.name:
                continue
            if self.exists(profile.name):
                continue
            try:
                self.save(profile, overwrite=False)
            except ProfileValidationError:
                continue

    def _path_for(self, name: str) -> Path:
        safe_name = name.strip().replace(" ", "_")
        return self.base_dir / f"{safe_name}.json"
