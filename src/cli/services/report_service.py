from __future__ import annotations

from datetime import datetime
from typing import Any, Dict

from src.utils.report_generator import ReportGenerator


class ReportService:
    """Handle report command execution."""

    def __init__(self, framework: Any):
        self.framework = framework

    def execute(self, request: Any) -> Dict[str, Any]:
        output = getattr(request, "output", None)
        if not output:
            raise ValueError("Report command requires --output")

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

        results = self.framework.run_comprehensive(target)
        generator = ReportGenerator(self.framework)
        context = {
            "generated_at": datetime.utcnow().isoformat() + "Z",
            "target": target,
            "pid": pid,
            "tests": results.get("tests") if isinstance(results, dict) else None,
            "raw_results": results,
            "inventory_context": inventory_context,
            "directx_flags": inventory_context.get("directx_flags") if inventory_context else None,
        }
        report_output = generator.generate(output, context)

        response: Dict[str, Any] = {
            "command": getattr(request.command, "value", "report"),
            "target": target,
            "pid": pid,
            "status": "generated",
            "details": {"entries": len(results.get("tests", [])) if isinstance(results, dict) else None},
            **report_output,
        }
        response["output"] = report_output["markdown"]
        if inventory_context:
            response["inventory_snapshot"] = inventory_source
            response["inventory_context"] = inventory_context
        return response
