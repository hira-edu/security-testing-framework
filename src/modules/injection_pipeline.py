from __future__ import annotations

import hashlib
import logging
import shutil
import time
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, Optional

import psutil

from src.utils import native_paths

try:
    from src.external.bypass_methods.tools.injector import Injector  # type: ignore
except Exception:  # pragma: no cover - optional dependency handling
    Injector = None  # type: ignore


LOGGER = logging.getLogger(__name__)


@dataclass
class InjectionOptions:
    """Resolved options for an injection workflow."""

    method: str
    dll_path: Optional[Path]
    target_pid: Optional[int]
    target_name: Optional[str]
    dry_run: bool = False
    staging_dir: Optional[Path] = None


@dataclass
class InjectionPlan:
    """Details about a staged injection operation."""

    method: str
    source_path: Optional[Path]
    staged_path: Optional[Path]
    hashes: Dict[str, str]
    dry_run: bool
    metadata: Dict[str, str]
    target_pid: Optional[int]
    target_name: Optional[str]


class InjectionPipeline:
    """Orchestrates DLL staging and simulated injection workflows."""

    def __init__(self, framework: object):
        self.framework = framework
        self.base_dir = Path(getattr(framework, "base_dir", Path.cwd()))
        self.data_dir = Path(getattr(framework, "data_dir", self.base_dir / "data"))
        self.templates_dir = self.base_dir / "resources" / "dll"
        self.log_dir = self.data_dir / "logs"
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.logger = logging.getLogger("stf.inject")
        if not any(isinstance(handler, logging.FileHandler) and handler.baseFilename == str(self.log_dir / "inject.log") for handler in self.logger.handlers):
            file_handler = logging.FileHandler(self.log_dir / "inject.log", encoding="utf-8")
            file_handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
            self.logger.addHandler(file_handler)
        self.logger.setLevel(logging.INFO)

    def resolve_options(
        self,
        *,
        method: str,
        dll: Optional[str],
        target_pid: Optional[int],
        target_name: Optional[str],
        dry_run: bool,
    ) -> InjectionOptions:
        dll_path: Optional[Path] = None
        if dll:
            dll_path = Path(dll)
            if not dll_path.is_absolute():
                dll_path = (self.base_dir / dll_path).resolve()
        return InjectionOptions(
            method=method,
            dll_path=dll_path,
            target_pid=target_pid,
            target_name=target_name,
            dry_run=dry_run,
        )

    def prepare(self, options: InjectionOptions) -> InjectionPlan:
        source_path = self._resolve_payload(options)
        staged_path = None
        hashes: Dict[str, str] = {}

        if source_path:
            staged_dir = options.staging_dir or (self.data_dir / "staged")
            staged_dir.mkdir(parents=True, exist_ok=True)
            staged_name = f"{options.method}_{int(time.time())}{source_path.suffix}"
            staged_path = staged_dir / staged_name
            if not options.dry_run:
                shutil.copy2(source_path, staged_path)
            hashes = self._compute_hashes(source_path, staged_path if staged_path.exists() else None)

        metadata = {
            "method": options.method,
            "dry_run": str(options.dry_run),
            "target_pid": str(options.target_pid) if options.target_pid is not None else "",
            "target_name": options.target_name or "",
        }
        self.logger.info(
            "Prepared injection plan: %s",
            {"method": options.method, "source": str(source_path) if source_path else None, "staged": str(staged_path) if staged_path else None, "dry_run": options.dry_run},
        )
        return InjectionPlan(
            method=options.method,
            source_path=source_path,
            staged_path=staged_path,
            hashes=hashes,
            dry_run=options.dry_run,
            metadata=metadata,
            target_pid=options.target_pid,
            target_name=options.target_name,
        )

    def execute(self, plan: InjectionPlan) -> Dict[str, str]:
        if plan.dry_run:
            status = "planned"
            note = "Dry-run mode; injection not executed."
            self.logger.info("Injection %s for %s", status, plan.method)
            return {
                "status": status,
                "note": note,
                "staged": str(plan.staged_path) if plan.staged_path else None,
            }

        if not Injector:
            status = "simulated"
            note = "Bypass-methods injector unavailable; ensure Windows dependencies are installed."
            self.logger.info("Injection %s for %s", status, plan.method)
            return {
                "status": status,
                "note": note,
                "staged": str(plan.staged_path) if plan.staged_path else None,
            }

        if not plan.staged_path or not plan.staged_path.exists():
            raise FileNotFoundError("Staged DLL payload missing; cannot execute injection.")

        pid = self._resolve_pid(plan)
        if pid is None:
            raise RuntimeError("Unable to resolve target PID for injection.")

        native_paths.ensure_native_dirs()

        try:
            injector = Injector()
            injector.load_from_pid(pid)
            dll_result = injector.inject_dll(str(plan.staged_path))
            injector.unload()
            status = "executed"
            note = f"Injected {plan.staged_path.name} into PID {pid} (result: {dll_result})."
        except Exception as exc:  # pragma: no cover - defensive
            self.logger.error("Injection failed: %s", exc)
            status = "error"
            note = str(exc)

        self.logger.info("Injection %s for %s", status, plan.method)
        return {
            "status": status,
            "note": note,
            "staged": str(plan.staged_path) if plan.staged_path else None,
        }

    def _resolve_payload(self, options: InjectionOptions) -> Optional[Path]:
        if options.dll_path:
            if not options.dll_path.exists():
                raise FileNotFoundError(f"Specified DLL not found: {options.dll_path}")
            return options.dll_path

        vendor_default = native_paths.get_bypass_methods_dll()
        if vendor_default.exists():
            return vendor_default

        default_name = f"{options.method}.dll"
        candidate = self.templates_dir / default_name
        if candidate.exists():
            return candidate

        fallback = self.templates_dir / "default.dll"
        if options.dry_run or fallback.exists():
            return fallback if fallback.exists() else None

        raise FileNotFoundError(
            f"No DLL provided and default payload missing under {self.templates_dir}. Place '{default_name}' or 'default.dll' to continue."
        )

    def _compute_hashes(self, source: Optional[Path], staged: Optional[Path]) -> Dict[str, str]:
        hashes: Dict[str, str] = {}
        if source and source.exists():
            hashes["source_sha256"] = self._hash_file(source)
        if staged and staged.exists():
            hashes["staged_sha256"] = self._hash_file(staged)
        return hashes

    @staticmethod
    def _hash_file(path: Path) -> str:
        sha256 = hashlib.sha256()
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(8192), b""):
                sha256.update(chunk)
        return sha256.hexdigest()

    def _resolve_pid(self, plan: InjectionPlan) -> Optional[int]:
        if plan.target_pid:
            return plan.target_pid
        if not plan.target_name:
            return None
        query = plan.target_name.lower()
        for proc in psutil.process_iter(["pid", "name", "exe"]):
            try:
                name = (proc.info.get("name") or "").lower()
                exe = (proc.info.get("exe") or "").lower()
                if query in name or query in exe:
                    return proc.info.get("pid")
            except (psutil.NoSuchProcess, psutil.AccessDenied):  # pragma: no cover - defensive
                continue
        return None
