"""Helpers for locating native assets shipped with the Security Testing Framework."""

from __future__ import annotations

import os
from pathlib import Path
from typing import List

ROOT = Path(__file__).resolve().parents[2]
NATIVE_ROOT = ROOT / "native"


def get_native_root() -> Path:
    """Return the root directory that holds native assets."""
    return NATIVE_ROOT


def get_bypass_methods_root() -> Path:
    """Return the root directory for bypass-methods native assets."""
    return get_native_root() / "bypass_methods"


def get_bypass_methods_dll(name: str = "UndownUnlockDXHook.dll", *, expect_exists: bool = False) -> Path:
    """Resolve the path to the primary bypass-methods DLL."""
    dll_path = get_bypass_methods_root() / "dll" / name
    if expect_exists and not dll_path.exists():
        raise FileNotFoundError(f"Bypass-methods DLL not found at: {dll_path}")
    return dll_path


def ensure_native_dirs() -> None:
    """Ensure the expected native directory structure exists."""
    (get_bypass_methods_root() / "dll").mkdir(parents=True, exist_ok=True)
    (get_bypass_methods_root() / "drivers").mkdir(parents=True, exist_ok=True)


def runtime_dll_search_paths() -> List[str]:
    """Return directories to add to the Windows DLL search path."""
    paths: List[str] = []
    dll_dir = get_bypass_methods_root() / "dll"
    if dll_dir.exists():
        paths.append(str(dll_dir))
    drivers_dir = get_bypass_methods_root() / "drivers"
    if drivers_dir.exists():
        paths.append(str(drivers_dir))
    extra = os.environ.get("STF_NATIVE_PATHS")
    if extra:
        paths.extend(p for p in extra.split(os.pathsep) if p)
    return paths


__all__ = [
    "ensure_native_dirs",
    "get_bypass_methods_dll",
    "get_bypass_methods_root",
    "get_native_root",
    "runtime_dll_search_paths",
]
