from __future__ import annotations

from typing import Any, Dict

from src.cli.constants import CLICommand
from src.cli.profile_store import (
    CLIProfile,
    ProfileValidationError,
    parse_key_value_pairs,
)


class ProfilesService:
    """Handle profiles command execution."""

    def __init__(self, framework: Any):
        self.framework = framework

    def execute(self, request: Any) -> Dict[str, Any]:
        action = getattr(request, "action", None)
        if not action:
            raise ValueError("Profiles command requires --action")

        try:
            if action == "list":
                profiles = self.framework.list_profiles()
                return {
                    "command": getattr(request.command, "value", "profiles"),
                    "action": action,
                    "profiles": profiles,
                }

            if action == "show":
                name = self._require_name(request, action)
                profile = self.framework.load_profile(name)
                return {
                    "command": getattr(request.command, "value", "profiles"),
                    "action": action,
                    "profile": self._profile_payload(profile),
                }

            if action == "add":
                name = self._require_name(request, action)
                base_command = self._require_base_command(request)
                options = parse_key_value_pairs(base_command, getattr(request, "kv_pairs", []))
                profile = CLIProfile(
                    name=name,
                    command=base_command,
                    options=options,
                    description=getattr(request, "description", None),
                )
                saved = self.framework.save_profile(profile, overwrite=bool(getattr(request, "overwrite", False)))
                status = "updated" if getattr(request, "overwrite", False) else "created"
                return {
                    "command": getattr(request.command, "value", "profiles"),
                    "action": action,
                    "profile": self._profile_payload(saved),
                    "status": status,
                }

            if action == "remove":
                name = self._require_name(request, action)
                self.framework.delete_profile(name)
                return {
                    "command": getattr(request.command, "value", "profiles"),
                    "action": action,
                    "name": name,
                    "status": "removed",
                }

            if action == "apply":
                name = self._require_name(request, action)
                profile = self.framework.load_profile(name)
                overrides = parse_key_value_pairs(profile.command, getattr(request, "kv_pairs", []))
                applied = self.framework.apply_profile(name, overrides=overrides or None)
                return {
                    "command": getattr(request.command, "value", "profiles"),
                    "action": action,
                    "profile": applied,
                }
        except ProfileValidationError as exc:
            raise ValueError(str(exc)) from exc
        except FileNotFoundError as exc:
            raise ValueError(str(exc)) from exc

        raise ValueError(f"Unsupported profiles action: {action}")

    @staticmethod
    def _profile_payload(profile: CLIProfile) -> Dict[str, Any]:
        return {
            "name": profile.name,
            "command": profile.command.value,
            "description": profile.description,
            "options": profile.options,
            "created_at": profile.created_at,
            "updated_at": profile.updated_at,
        }

    @staticmethod
    def _require_name(request: Any, action: str) -> str:
        name = getattr(request, "preset_name", None)
        if not name:
            raise ValueError(f"Profiles '{action}' requires --name")
        return name

    @staticmethod
    def _require_base_command(request: Any):
        base = getattr(request, "base_command", None)
        if not base:
            raise ValueError("Profiles 'add' requires --base-command")
        try:
            base_command = CLICommand(base)
        except ValueError as exc:
            raise ValueError(f"Unsupported base command '{base}'.") from exc
        if base_command in {CLICommand.PROFILES, CLICommand.SHELL}:
            raise ValueError("Profiles cannot target the profiles or shell commands.")
        return base_command
