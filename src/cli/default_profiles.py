from __future__ import annotations

from typing import Iterable, Tuple

from src.cli.constants import CLICommand
from src.cli.profile_store import CLIProfile


def build_default_profiles() -> Iterable[CLIProfile]:
    """Return an iterable of built-in CLI profiles."""
    return (
        CLIProfile(
            name="stealth-monitor",
            command=CLICommand.MONITOR,
            options={
                "target": "LockDownBrowser.exe",
                "stealth": True,
                "comprehensive": True,
                "profile": "lockdown-bypass",
            },
            description="Run stealth monitoring against LockDown Browser using the lockdown-bypass hook profile.",
        ),
        CLIProfile(
            name="baseline-capture",
            command=CLICommand.CAPTURE,
            options={
                "target": "LockDownBrowser.exe",
                "method": "auto",
                "output": "captures/baseline.json",
                "image": "captures/baseline.png",
            },
            description="Capture baseline screen telemetry with metadata and image outputs.",
        ),
        CLIProfile(
            name="hooks-lockdown",
            command=CLICommand.HOOKS,
            options={
                "action": "enable",
                "profile": "lockdown-bypass",
                "target": "LockDownBrowser.exe",
            },
            description="Enable lockdown bypass hook stack for the default target.",
        ),
        CLIProfile(
            name="report-stealth",
            command=CLICommand.REPORT,
            options={
                "target": "LockDownBrowser.exe",
                "output": "reports/stealth_report.json",
            },
            description="Generate a comprehensive report using stealth presets against LockDown Browser.",
        ),
    )
