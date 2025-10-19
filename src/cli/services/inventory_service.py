from __future__ import annotations

import sys
from typing import Any, Dict, List


class InventoryService:
    """Handle process inventory command execution."""

    def __init__(self, framework: Any):
        self.framework = framework

    def execute(self, request: Any) -> Dict[str, Any]:
        filters = dict(getattr(request, "options", {}) or {})
        baseline = getattr(request, "baseline", None)
        if "baseline" in filters:
            baseline = baseline or filters["baseline"]
            filters.pop("baseline", None)
        picker = bool(filters.pop("picker", False))
        result = self.framework.inventory(
            filters=filters,
            output=getattr(request, "output", None),
            baseline=baseline,
        )
        if picker:
            if not sys.stdin.isatty():
                result["picker"] = {"error": "Interactive picker requires a TTY."}
            else:
                selection = self._interactive_picker(result)
                if selection:
                    snapshot_path = self.framework.remember_inventory_selection(selection, result, label="cli")
                    result["picker"] = {"selection": selection, "snapshot": snapshot_path}
                else:
                    result["picker"] = {"selection": None}
        return result

    def _interactive_picker(self, snapshot: Dict[str, Any]) -> Dict[str, Any] | None:
        processes = snapshot.get("processes") or []
        if not processes:
            print("No processes to select from.")
            return None
        limit = min(len(processes), 20)
        self._render_table(processes[:limit])
        try:
            raw = input("Select index (blank to cancel): ").strip()
        except (EOFError, KeyboardInterrupt):  # pragma: no cover - interactive guard
            print()
            return None
        if not raw:
            return None
        if not raw.isdigit():
            print("Selection must be a number.")
            return None
        index = int(raw)
        if index < 1 or index > limit:
            print("Selection out of range.")
            return None
        return processes[index - 1]

    def _render_table(self, rows: List[Dict[str, Any]]) -> None:
        header = f"{'Idx':>4} {'PID':>6} {'Integrity':>10} {'DX':>12} {'SWDA':>6} {'Exclusive':>9} Name"
        print(header)
        print("-" * len(header))
        for idx, proc in enumerate(rows, start=1):
            dx = proc.get("directx_usage") or "-"
            if isinstance(dx, str) and len(dx) > 12:
                dx = dx[:9] + "..."
            swda = "Y" if proc.get("swda_detected") else "-"
            exclusive = "Y" if proc.get("exclusive_display") else "-"
            name = proc.get("name") or proc.get("exe") or "<unknown>"
            print(
                f"{idx:>4} {str(proc.get('pid', '')):>6} "
                f"{str(proc.get('integrity', '-'))[:10]:>10} {dx:>12} {swda:>6} {exclusive:>9} {name}"
            )
