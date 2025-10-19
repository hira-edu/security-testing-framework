from __future__ import annotations

import logging
from typing import Any, Dict

LOGGER = logging.getLogger(__name__)

from src.modules.injection_pipeline import InjectionPipeline


class InjectService:
    """Handle inject command execution."""

    def __init__(self, framework: Any):
        self.framework = framework

    def execute(self, request: Any) -> Dict[str, Any]:
        method = getattr(request, "method", None)
        if not method:
            raise ValueError("Injection command requires --method")

        target = getattr(request, "target", None)
        pid = getattr(request, "pid", None)
        inventory_source = getattr(request, "inventory_source", None)
        inventory_context = None

        if inventory_source:
            snapshot = self.framework.load_inventory_snapshot(inventory_source)
            inventory_context = self.framework.resolve_inventory_process(
                snapshot,
                pid=pid,
                name=target,
            )
            if not inventory_context:
                raise ValueError(f"No matching process found in inventory snapshot '{inventory_source}'.")
            target = target or inventory_context.get("name") or inventory_context.get("exe")
            pid = pid or inventory_context.get("pid")

        pipeline = InjectionPipeline(self.framework)
        options_dict = dict(getattr(request, "options", {}) or {})
        dry_run = bool(options_dict.pop("dry_run", False))

        options = pipeline.resolve_options(
            method=method,
            dll=getattr(request, "dll", None),
            target_pid=pid,
            target_name=target,
            dry_run=dry_run,
        )
        plan = pipeline.prepare(options)
        execution = pipeline.execute(plan)

        response: Dict[str, Any] = {
            "command": getattr(request.command, "value", "inject"),
            "target": target,
            "pid": pid,
            "method": method,
            "dll": str(plan.source_path) if plan.source_path else getattr(request, "dll", None),
            "staged_path": str(plan.staged_path) if plan.staged_path else None,
            "hashes": plan.hashes,
            "dry_run": plan.dry_run,
            "status": execution["status"],
            "note": execution["note"],
            "options": options_dict,
        }
        if inventory_context:
            response["inventory_snapshot"] = inventory_source
            response["inventory_context"] = inventory_context
        return response
