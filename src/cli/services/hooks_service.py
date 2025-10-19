from __future__ import annotations

from typing import Any, Dict, List, Optional


class HooksService:
    """Handle hooks command execution."""

    def __init__(self, framework: Any):
        self.framework = framework

    def execute(self, request: Any) -> Dict[str, Any]:
        action = getattr(request, "action", None)
        if not action:
            raise ValueError("Hooks command requires --action")

        if action == "status":
            status = self.framework.hooks_status()
            status["command"] = getattr(request.command, "value", "hooks")
            status["action"] = action
            return status

        if action == "enable":
            profile = getattr(request, "profile", None)
            context = self._build_context(request)
            operations = self.framework.enable_hooks(
                getattr(request, "layers", None),
                profile=profile,
                context=context or None,
            )
            response: Dict[str, Any] = {
                "command": getattr(request.command, "value", "hooks"),
                "action": action,
                "operations": operations,
                "status": "ok",
            }
            if context:
                response["context"] = context
            return response

        if action == "disable":
            operations = self.framework.disable_hooks(
                getattr(request, "layers", None) or None
            )
            return {
                "command": getattr(request.command, "value", "hooks"),
                "action": action,
                "operations": operations,
                "status": "ok",
            }

        raise ValueError(f"Unsupported hooks action: {action}")

    def _build_context(self, request: Any) -> Dict[str, Any]:
        context = {
            "target": getattr(request, "target", None)
            or getattr(request, "process", None),
            "process": getattr(request, "process", None),
            "file": getattr(request, "file_path", None),
            "pid": getattr(request, "pid", None),
            "service": getattr(request, "service", None),
            "profile": getattr(request, "profile", None),
        }
        return {k: v for k, v in context.items() if v is not None}
