from __future__ import annotations

from typing import Any, Dict


class MonitorService:
    """Handle monitor command execution."""

    def __init__(self, framework: Any):
        self.framework = framework

    def execute(self, request: Any) -> Dict[str, Any]:
        return self.framework.monitor(
            target=getattr(request, "target", None),
            profile=getattr(request, "profile", None),
            duration=getattr(request, "duration", None),
            stealth=bool(getattr(request, "stealth", False)),
            comprehensive=bool(getattr(request, "comprehensive", False)),
            output=getattr(request, "output", None),
        )
