from __future__ import annotations

from typing import Any, Dict


class CaptureService:
    """Handle capture command execution."""

    def __init__(self, framework: Any):
        self.framework = framework

    def execute(self, request: Any) -> Dict[str, Any]:
        options = getattr(request, "options", {}) or {}
        image_path = options.get("image")
        metadata_path = getattr(request, "output", None) or options.get("metadata")

        payload = self.framework.capture(
            target=getattr(request, "target", None),
            method=getattr(request, "method", None) or "auto",
            output_image=image_path,
            output_json=metadata_path,
        )
        payload["command"] = getattr(request.command, "value", "capture")
        return payload
