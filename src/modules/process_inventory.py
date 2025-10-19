from __future__ import annotations

import ctypes
import ctypes.wintypes as wintypes
import logging
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

import psutil

logger = logging.getLogger(__name__)


@dataclass
class ProcessRecord:
    """Structured view of a running process."""

    pid: int
    name: str
    exe: Optional[str]
    status: Optional[str]
    username: Optional[str]
    create_time: Optional[str]
    session_id: Optional[int]
    integrity: Optional[str]
    ppid: Optional[int]
    cmdline: List[str]
    window_titles: List[str]
    window_details: List[Dict[str, Any]]
    window_count: int
    is_elevated: Optional[bool]
    display_affinity: Optional[str]
    swda_detected: bool
    exclusive_display: bool
    directx_modules: List[str]
    directx_usage: str
    directx_flags: List[str]
    memory_info: Dict[str, Any]
    cpu_percent: Optional[float]
    handle_count: Optional[int]
    thread_count: Optional[int]


class ProcessInventory:
    """Collect process information with optional filtering."""

    _PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
    _TOKEN_QUERY = 0x0008
    _TOKEN_ELEVATION = 20
    _TokenIntegrityLevel = 25

    _INTEGRITY_MAP = {
        0x00001000: "low",
        0x00002000: "medium",
        0x00003000: "high",
        0x00004000: "system",
        0x00005000: "protected",
    }

    def __init__(self) -> None:
        self.kernel32 = ctypes.windll.kernel32  # type: ignore[attr-defined]
        self.user32 = ctypes.windll.user32  # type: ignore[attr-defined]
        self.advapi32 = ctypes.windll.advapi32  # type: ignore[attr-defined]

        self.advapi32.GetSidSubAuthorityCount.argtypes = [ctypes.c_void_p]
        self.advapi32.GetSidSubAuthorityCount.restype = ctypes.POINTER(ctypes.c_ubyte)
        self.advapi32.GetSidSubAuthority.argtypes = [ctypes.c_void_p, ctypes.c_ulong]
        self.advapi32.GetSidSubAuthority.restype = ctypes.POINTER(ctypes.c_ulong)

    def collect(self, filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        filters = self._normalise_filters(filters or {})
        windows = self._collect_window_metadata() if filters["include_windows"] else {}
        processes: List[Dict[str, Any]] = []
        errors: List[Dict[str, Any]] = []

        candidates = list(
            psutil.process_iter(
                [
                    "pid",
                    "name",
                    "exe",
                    "status",
                    "username",
                    "create_time",
                    "ppid",
                    "cmdline",
                    "memory_info",
                ]
            )
        )

        for proc in candidates:
            try:
                record = self._build_record(proc, windows)
            except Exception as exc:  # pragma: no cover - defensive
                logger.debug("Failed to build inventory record for %s: %s", proc, exc)
                errors.append({"pid": proc.pid, "error": str(exc)})
                continue

            if not self._matches_filters(record, filters):
                continue

            processes.append(asdict(record))
            if filters["limit"] and len(processes) >= filters["limit"]:
                break

        if filters["sort_by"]:
            key = filters["sort_by"]
            reverse = filters["sort_desc"]

            def sort_key(item: Dict[str, Any]) -> Any:
                value = item.get(key)
                if isinstance(value, str):
                    return value.lower()
                return value if value is not None else 0

            processes.sort(key=sort_key, reverse=reverse)

        snapshot = {
            "collected_at": datetime.utcnow().replace(microsecond=0).isoformat() + "Z",
            "filters": self._public_filters(filters),
            "matches": len(processes),
            "scanned": len(candidates),
            "processes": processes,
        }
        if errors:
            snapshot["errors"] = errors
        return snapshot

    def _normalise_filters(self, raw: Dict[str, Any]) -> Dict[str, Any]:
        def _to_int(value: Any) -> Optional[int]:
            if value is None:
                return None
            try:
                return int(value)
            except (TypeError, ValueError):
                return None

        def _to_bool(value: Any) -> bool:
            if isinstance(value, bool):
                return value
            if isinstance(value, str):
                return value.strip().lower() in {"1", "true", "yes", "on"}
            return bool(value)

        filters = {
            "name": self._lower_or_none(raw.get("name")),
            "window": self._lower_or_none(raw.get("window")),
            "user": self._lower_or_none(raw.get("user")),
            "integrity": self._lower_or_none(raw.get("integrity")),
            "session": _to_int(raw.get("session")),
            "pid": _to_int(raw.get("pid")),
            "limit": _to_int(raw.get("limit")),
            "sort_by": raw.get("sort_by") if isinstance(raw.get("sort_by"), str) else None,
            "sort_desc": _to_bool(raw.get("sort_desc")),
            "include_windows": _to_bool(raw.get("include_windows", True)),
        }
        return filters

    def _public_filters(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        exported = {k: v for k, v in filters.items() if v not in (None, False)}
        if not filters.get("include_windows", True):
            exported["include_windows"] = False
        return exported

    def _lower_or_none(self, value: Any) -> Optional[str]:
        if value is None:
            return None
        return str(value).strip().lower() or None

    def _build_record(
        self,
        proc: psutil.Process,
        windows: Dict[int, List[Dict[str, Any]]],
    ) -> ProcessRecord:
        info = proc.info
        session_id = self._get_session_id(proc.pid)
        integrity = self._get_integrity_level(proc.pid)
        window_entries = windows.get(proc.pid, [])
        window_titles = [entry["title"] for entry in window_entries]
        window_details = [
            {
                "title": entry.get("title"),
                "hwnd": entry.get("hwnd"),
                "affinity": entry.get("affinity"),
                "rect": entry.get("rect"),
                "topmost": entry.get("topmost"),
            }
            for entry in window_entries
        ]
        display_affinity, swda_detected, exclusive_display = self._evaluate_display_affinity(window_entries)
        memory_info = {}
        try:
            mem = info.get("memory_info")
            if mem:
                memory_info = {
                    "rss": getattr(mem, "rss", None),
                    "vms": getattr(mem, "vms", None),
                }
        except Exception:
            memory_info = {}
        cpu_percent: Optional[float]
        try:
            cpu_percent = proc.cpu_percent(interval=None)
        except Exception:
            cpu_percent = None
        try:
            handle_count = proc.num_handles()
        except Exception:
            handle_count = None
        try:
            thread_count = proc.num_threads()
        except Exception:
            thread_count = None

        directx_modules = self._detect_directx_modules(proc)
        directx_usage, directx_flags = self._classify_directx_usage(
            directx_modules,
            exclusive_display,
            window_entries,
        )

        return ProcessRecord(
            pid=info.get("pid"),
            name=info.get("name"),
            exe=info.get("exe"),
            status=info.get("status"),
            username=info.get("username"),
            create_time=self._format_timestamp(info.get("create_time")),
            session_id=session_id,
            integrity=integrity,
            ppid=info.get("ppid"),
            cmdline=info.get("cmdline") or [],
            window_titles=window_titles,
            window_details=window_details,
            window_count=len(window_titles),
            is_elevated=self._is_process_elevated(proc.pid),
            display_affinity=display_affinity,
            swda_detected=swda_detected,
            exclusive_display=exclusive_display,
            directx_modules=directx_modules,
            directx_usage=directx_usage,
            directx_flags=directx_flags,
            memory_info=memory_info,
            cpu_percent=cpu_percent,
            handle_count=handle_count,
            thread_count=thread_count,
        )

    def _matches_filters(self, record: ProcessRecord, filters: Dict[str, Any]) -> bool:
        if filters["pid"] and record.pid != filters["pid"]:
            return False
        if filters["session"] is not None and record.session_id != filters["session"]:
            return False
        if filters["name"] and filters["name"] not in (record.name or "").lower():
            return False
        if filters["user"] and filters["user"] not in (record.username or "").lower():
            return False
        if filters["integrity"] and filters["integrity"] != (record.integrity or "").lower():
            return False
        if filters["window"]:
            if not record.window_titles:
                return False
            titles = " ".join(record.window_titles).lower()
            if filters["window"] not in titles:
                return False
        return True

    def _collect_window_metadata(self) -> Dict[int, List[Dict[str, Any]]]:
        windows: Dict[int, List[Dict[str, Any]]] = {}

        EnumWindowsProc = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)

        @EnumWindowsProc
        def _callback(hwnd: ctypes.c_void_p, _: ctypes.c_void_p) -> bool:
            if not self.user32.IsWindowVisible(hwnd):
                return True
            length = self.user32.GetWindowTextLengthW(hwnd)
            if length == 0:
                return True

            buffer = ctypes.create_unicode_buffer(length + 1)
            self.user32.GetWindowTextW(hwnd, buffer, length + 1)

            pid = ctypes.c_ulong()
            self.user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))

            rect = wintypes.RECT()
            rect_payload: Optional[Dict[str, int]] = None
            if self.user32.GetWindowRect(hwnd, ctypes.byref(rect)):
                rect_payload = {
                    "left": rect.left,
                    "top": rect.top,
                    "right": rect.right,
                    "bottom": rect.bottom,
                    "width": rect.right - rect.left,
                    "height": rect.bottom - rect.top,
                }

            affinity_value: Optional[int] = None
            if hasattr(self.user32, "GetWindowDisplayAffinity"):
                affinity = ctypes.c_uint()
                try:
                    result = self.user32.GetWindowDisplayAffinity(hwnd, ctypes.byref(affinity))
                except Exception:  # pragma: no cover - defensive
                    result = 0
                if result:
                    affinity_value = int(affinity.value)

            GWL_EXSTYLE = -20
            WS_EX_TOPMOST = 0x00000008
            topmost = False
            try:
                ex_style = self.user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
                topmost = bool(ex_style & WS_EX_TOPMOST)
            except Exception:
                topmost = False

            windows.setdefault(pid.value, []).append(
                {
                    "title": buffer.value,
                    "hwnd": int(hwnd),
                    "affinity": affinity_value,
                    "rect": rect_payload,
                    "topmost": topmost,
                }
            )
            return True

        try:
            self.user32.EnumWindows(_callback, 0)
        except Exception as exc:  # pragma: no cover - defensive
            logger.debug("EnumWindows failed: %s", exc)
        return windows

    def _get_session_id(self, pid: int) -> Optional[int]:
        session_id = ctypes.c_uint()
        result = self.kernel32.ProcessIdToSessionId(pid, ctypes.byref(session_id))
        if result == 0:
            return None
        return int(session_id.value)

    def _get_integrity_level(self, pid: int) -> Optional[str]:
        process_handle = self.kernel32.OpenProcess(
            self._PROCESS_QUERY_LIMITED_INFORMATION,
            False,
            pid,
        )
        if not process_handle:
            return None
        token_handle = ctypes.c_void_p()
        try:
            if not self.advapi32.OpenProcessToken(
                process_handle,
                self._TOKEN_QUERY,
                ctypes.byref(token_handle),
            ):
                return None

            needed = ctypes.c_uint()
            self.advapi32.GetTokenInformation(
                token_handle,
                self._TokenIntegrityLevel,
                None,
                0,
                ctypes.byref(needed),
            )
            buffer = ctypes.create_string_buffer(needed.value)
            if not self.advapi32.GetTokenInformation(
                token_handle,
                self._TokenIntegrityLevel,
                buffer,
                needed,
                ctypes.byref(needed),
            ):
                return None

            class SID_AND_ATTRIBUTES(ctypes.Structure):
                _fields_ = [("Sid", ctypes.c_void_p), ("Attributes", ctypes.c_uint)]

            class TOKEN_MANDATORY_LABEL(ctypes.Structure):
                _fields_ = [("Label", SID_AND_ATTRIBUTES)]

            tml = ctypes.cast(buffer, ctypes.POINTER(TOKEN_MANDATORY_LABEL)).contents
            sid_ptr = tml.Label.Sid
            if not sid_ptr:
                return None
            count_ptr = self.advapi32.GetSidSubAuthorityCount(sid_ptr)
            if not count_ptr:
                return None
            subauth_count = count_ptr.contents.value
            rid_ptr = self.advapi32.GetSidSubAuthority(sid_ptr, subauth_count - 1)
            if not rid_ptr:
                return None
            rid = rid_ptr.contents.value
            return self._INTEGRITY_MAP.get(rid, "unknown")
        except Exception:  # pragma: no cover - defensive
            return None
        finally:
            if token_handle:
                self.kernel32.CloseHandle(token_handle)
            self.kernel32.CloseHandle(process_handle)

    def _is_process_elevated(self, pid: int) -> Optional[bool]:
        process_handle = self.kernel32.OpenProcess(
            self._PROCESS_QUERY_LIMITED_INFORMATION,
            False,
            pid,
        )
        if not process_handle:
            return None
        token_handle = ctypes.c_void_p()
        try:
            if not self.advapi32.OpenProcessToken(
                process_handle,
                self._TOKEN_QUERY,
                ctypes.byref(token_handle),
            ):
                return None
            elevation = ctypes.c_uint()
            size = ctypes.c_uint(ctypes.sizeof(elevation))
            if not self.advapi32.GetTokenInformation(
                token_handle,
                self._TOKEN_ELEVATION,
                ctypes.byref(elevation),
                size,
                ctypes.byref(size),
            ):
                return None
            return bool(elevation.value)
        except Exception:  # pragma: no cover - defensive
            return None
        finally:
            if token_handle:
                self.kernel32.CloseHandle(token_handle)
            self.kernel32.CloseHandle(process_handle)

    def _evaluate_display_affinity(
        self,
        window_entries: List[Dict[str, Any]],
    ) -> Tuple[Optional[str], bool, bool]:
        affinities = [
            entry.get("affinity")
            for entry in window_entries
            if entry.get("affinity") is not None
        ]
        if not affinities:
            return None, False, False

        affinity_map = {0: "none", 1: "monitor", 2: "exclusive"}
        dominant = max(set(affinities), key=affinities.count)
        exclusive = any(value == 2 for value in affinities)
        return affinity_map.get(dominant, "unknown"), True, exclusive

    def _detect_directx_modules(self, proc: psutil.Process) -> List[str]:
        modules: List[str] = []
        try:
            for mmap in proc.memory_maps():
                path = getattr(mmap, "path", "") or ""
                if not path:
                    continue
                lower = path.lower()
                if any(token in lower for token in ("d3d", "dxgi", "direct3d", "dxcore", "swapchain")):
                    modules.append(Path(path).name)
        except Exception:
            return []

        return sorted(set(modules))

    def _classify_directx_usage(
        self,
        modules: List[str],
        exclusive_display: bool,
        window_entries: List[Dict[str, Any]],
    ) -> Tuple[str, List[str]]:
        if not modules:
            return "absent", []

        lower_modules = [module.lower() for module in modules]
        flags: List[str] = []
        status = "present"

        if any("dxgi" in module for module in lower_modules):
            status = "swap_chain"
            flags.append("dxgi")
        if any("d3d12" in module or "d3d11" in module for module in lower_modules):
            flags.append("d3d11_plus")
            if status == "present":
                status = "d3d11"
        elif any("d3d10" in module for module in lower_modules):
            flags.append("d3d10")
            if status == "present":
                status = "d3d10"
        elif any("d3d9" in module for module in lower_modules):
            flags.append("d3d9")
            if status == "present":
                status = "d3d9"

        if any("swapchain" in module for module in lower_modules):
            flags.append("swapchain_module")
            if status == "present":
                status = "swap_chain"

        if exclusive_display:
            flags.append("exclusive_affinity")
            status = f"{status}_exclusive"

        if any(entry.get("topmost") for entry in window_entries):
            flags.append("topmost_window")

        return status, sorted(set(flags))

    @staticmethod
    def diff_snapshots(
        baseline_snapshot: Dict[str, Any],
        current_snapshot: Dict[str, Any],
    ) -> Dict[str, Any]:
        baseline_processes = baseline_snapshot.get("processes") or []
        current_processes = current_snapshot.get("processes") or []

        baseline_map = {
            proc.get("pid"): proc
            for proc in baseline_processes
            if isinstance(proc, dict) and proc.get("pid") is not None
        }
        current_map = {
            proc.get("pid"): proc
            for proc in current_processes
            if isinstance(proc, dict) and proc.get("pid") is not None
        }

        added = [current_map[pid] for pid in current_map.keys() - baseline_map.keys()]
        removed = [baseline_map[pid] for pid in baseline_map.keys() - current_map.keys()]

        changed: List[Dict[str, Any]] = []
        monitored_fields = [
            "integrity",
            "session_id",
            "exe",
            "username",
            "cpu_percent",
            "display_affinity",
            "directx_usage",
            "exclusive_display",
        ]

        for pid in baseline_map.keys() & current_map.keys():
            before = baseline_map[pid]
            after = current_map[pid]
            deltas = {}
            for field in monitored_fields:
                if before.get(field) != after.get(field):
                    deltas[field] = {"before": before.get(field), "after": after.get(field)}
            if deltas:
                changed.append({"pid": pid, "changes": deltas, "name": after.get("name")})

        return {
            "added": added,
            "removed": removed,
            "changed": changed,
            "baseline_collected_at": baseline_snapshot.get("collected_at"),
            "current_collected_at": current_snapshot.get("collected_at"),
        }

    def _format_timestamp(self, ts: Optional[float]) -> Optional[str]:
        if not ts:
            return None
        return datetime.fromtimestamp(ts).isoformat()
