from __future__ import annotations

import logging
import tempfile
import types
from dataclasses import asdict
from pathlib import Path
from typing import Any, Dict
import unittest

from src.cli.constants import CLICommand
from src.cli.services.inject_service import InjectService
from src.cli.services.inventory_service import InventoryService
from src.cli.services.report_service import ReportService
from src.modules.process_inventory import ProcessInventory, ProcessRecord


def build_record(**overrides: Any) -> ProcessRecord:
    defaults: Dict[str, Any] = {
        "pid": 100,
        "name": "LockDownBrowser.exe",
        "exe": r"C:\Program Files\LockDownBrowser.exe",
        "status": "running",
        "username": "student",
        "create_time": "2024-01-01T00:00:00",
        "session_id": 1,
        "integrity": "medium",
        "ppid": 1,
        "cmdline": ["LockDownBrowser.exe"],
        "window_titles": ["LockDown Browser"],
        "window_details": [{"title": "LockDown Browser", "hwnd": 2001, "affinity": 1, "rect": None, "topmost": False}],
        "window_count": 1,
        "is_elevated": False,
        "display_affinity": "monitor",
        "swda_detected": True,
        "exclusive_display": False,
        "directx_modules": ["d3d11.dll"],
        "directx_usage": "present",
        "directx_flags": [],
        "memory_info": {"rss": 1024, "vms": 2048},
        "cpu_percent": 10.5,
        "handle_count": 150,
        "thread_count": 12,
    }
    defaults.update(overrides)
    return ProcessRecord(**defaults)


class ProcessInventoryTests(unittest.TestCase):
    def test_matches_filters_window_filter(self) -> None:
        inventory = ProcessInventory.__new__(ProcessInventory)
        record = build_record(window_titles=["Secure Window"])
        filters = {
            "pid": None,
            "session": None,
            "name": None,
            "user": None,
            "integrity": None,
            "window": "secure",
        }
        self.assertTrue(ProcessInventory._matches_filters(inventory, record, filters))  # type: ignore[arg-type]
        filters["window"] = "missing"
        self.assertFalse(ProcessInventory._matches_filters(inventory, record, filters))  # type: ignore[arg-type]

    def test_diff_snapshots_detects_changes(self) -> None:
        baseline = {
            "collected_at": "2024-01-01T00:00:00Z",
            "processes": [
                asdict(build_record(pid=1, name="alpha.exe", cpu_percent=2.0, integrity="medium")),
                asdict(build_record(pid=2, name="beta.exe")),
            ],
        }
        current = {
            "collected_at": "2024-01-02T00:00:00Z",
            "processes": [
                asdict(build_record(pid=1, name="alpha.exe", cpu_percent=5.0, integrity="high")),
                asdict(build_record(pid=3, name="gamma.exe")),
            ],
        }

        diff = ProcessInventory.diff_snapshots(baseline, current)
        added_pids = {proc["pid"] for proc in diff["added"]}
        removed_pids = {proc["pid"] for proc in diff["removed"]}
        self.assertEqual(added_pids, {3})
        self.assertEqual(removed_pids, {2})
        self.assertEqual(diff["changed"][0]["pid"], 1)
        fields = diff["changed"][0]["changes"]
        self.assertEqual(fields["cpu_percent"], {"before": 2.0, "after": 5.0})
        self.assertEqual(fields["integrity"], {"before": "medium", "after": "high"})

    def test_inventory_service_passes_baseline_and_filters(self) -> None:
        captured: Dict[str, Any] = {}

        class FrameworkStub:
            def inventory(self, *, filters: Dict[str, Any], output: str | None, baseline: str | None) -> Dict[str, Any]:
                captured["filters"] = filters
                captured["output"] = output
                captured["baseline"] = baseline
                return {"results": []}

        service = InventoryService(FrameworkStub())
        request = types.SimpleNamespace(
            command=CLICommand.INVENTORY,
            options={"name": "browser", "baseline": "snapshots/baseline.json", "include_windows": False},
            output="snapshots/current.json",
            baseline="snapshots/baseline.json",
        )

        result = service.execute(request)
        self.assertEqual(result, {"results": []})
        self.assertEqual(captured["filters"], {"name": "browser", "include_windows": False})
        self.assertEqual(captured["output"], "snapshots/current.json")
        self.assertEqual(captured["baseline"], "snapshots/baseline.json")

    def test_inject_service_resolves_inventory_target(self) -> None:
        snapshot = {"processes": [{"pid": 404, "name": "Exam.exe", "exe": r"C:\Exam\Exam.exe"}]}
        captured: Dict[str, Any] = {}

        with tempfile.TemporaryDirectory() as temp_dir:
            data_dir = Path(temp_dir) / "data"
            data_dir.mkdir(parents=True, exist_ok=True)
            payload = Path(temp_dir) / "manual-map.dll"
            payload.write_bytes(b"stub-dll")

            class FrameworkStub:
                def __init__(self, base_dir: Path, data_dir: Path):
                    self.base_dir = base_dir
                    self.data_dir = data_dir

                def load_inventory_snapshot(self, path: str) -> Dict[str, Any]:
                    captured["snapshot_path"] = path
                    return snapshot

                def resolve_inventory_process(self, snapshot_data: Dict[str, Any], *, pid: int | None, name: str | None) -> Dict[str, Any]:
                    captured["resolve_pid"] = pid
                    captured["resolve_name"] = name
                    return snapshot_data["processes"][0]

            framework = FrameworkStub(Path(temp_dir), data_dir)
            service = InjectService(framework)
            request = types.SimpleNamespace(
                command=CLICommand.INJECT,
                method="manual-map",
                target=None,
                dll=str(payload),
                pid=None,
                options={"dry_run": True},
                inventory_source="snapshots/live.json",
            )

            response = service.execute(request)
            logger = logging.getLogger("stf.inject")
            for handler in list(logger.handlers):
                handler.close()
                logger.removeHandler(handler)

        self.assertEqual(response["target"], "Exam.exe")
        self.assertEqual(response["pid"], 404)
        self.assertEqual(response.get("inventory_snapshot"), "snapshots/live.json")
        self.assertIn("inventory_context", response)
        self.assertEqual(response["inventory_context"]["pid"], 404)
        self.assertEqual(captured["resolve_name"], None)
        self.assertEqual(response["status"], "planned")
        self.assertTrue(response["hashes"].get("source_sha256"))

    def test_report_service_uses_inventory_when_target_missing(self) -> None:
        snapshot = {"processes": [{"pid": 515, "name": "LockDownBrowser.exe", "exe": r"C:\Program Files\LockDownBrowser.exe"}]}
        captured: Dict[str, Any] = {}

        with tempfile.TemporaryDirectory() as temp_dir:
            data_dir = Path(temp_dir) / "data"
            data_dir.mkdir(parents=True, exist_ok=True)

            class FrameworkStub:
                def __init__(self, base_dir: Path, data_dir: Path):
                    self.base_dir = base_dir
                    self.data_dir = data_dir

                def load_inventory_snapshot(self, path: str) -> Dict[str, Any]:
                    captured["snapshot_path"] = path
                    return snapshot

                def resolve_inventory_process(self, snapshot_data: Dict[str, Any], *, pid: int | None, name: str | None) -> Dict[str, Any]:
                    captured["resolve_pid"] = pid
                    captured["resolve_name"] = name
                    return snapshot_data["processes"][0]

                def run_comprehensive(self, target: str | None) -> Dict[str, Any]:
                    captured["target"] = target
                    return {"tests": []}

                def _resolve_path(self, path: str) -> str:
                    return str((self.data_dir / path).resolve())

            framework = FrameworkStub(Path(temp_dir), data_dir)
            service = ReportService(framework)
            output_path = data_dir / "reports" / "summary.md"
            request = types.SimpleNamespace(
                command=CLICommand.REPORT,
                output=str(output_path),
                target=None,
                pid=None,
                inventory_source="snapshots/baseline.json",
            )
            response = service.execute(request)

        self.assertEqual(response["target"], "LockDownBrowser.exe")
        self.assertEqual(response["inventory_snapshot"], "snapshots/baseline.json")
        self.assertEqual(response.get("pid"), 515)
        self.assertIn("inventory_context", response)
        self.assertEqual(captured["target"], "LockDownBrowser.exe")
        self.assertTrue(Path(response["markdown"]).exists())
        self.assertTrue(Path(response["json"]).exists())


if __name__ == "__main__":
    unittest.main()