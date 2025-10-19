from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from src.cli.constants import CLICommand
from src.cli.services.capture_service import CaptureService
from src.cli.services.hooks_service import HooksService
from src.cli.services.inject_service import InjectService
from src.cli.services.monitor_service import MonitorService
from src.cli.services.profiles_service import ProfilesService
from src.cli.services.report_service import ReportService
from src.cli.services.inventory_service import InventoryService

LOGGER = logging.getLogger(__name__)


@dataclass
class CLIRequest:
    """Structured CLI invocation details."""

    command: CLICommand
    target: Optional[str] = None
    process: Optional[str] = None
    file_path: Optional[str] = None
    profile: Optional[str] = None
    duration: Optional[int] = None
    stealth: bool = False
    comprehensive: bool = False
    method: Optional[str] = None
    layers: List[str] = field(default_factory=list)
    action: Optional[str] = None
    dll: Optional[str] = None
    output: Optional[str] = None
    input_path: Optional[str] = None
    pid: Optional[int] = None
    service: Optional[str] = None
    preset_name: Optional[str] = None
    base_command: Optional[str] = None
    description: Optional[str] = None
    overwrite: bool = False
    kv_pairs: List[str] = field(default_factory=list)
    baseline: Optional[str] = None
    inventory_source: Optional[str] = None
    options: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_namespace(cls, namespace: Any) -> "CLIRequest":
        """Build request from argparse namespace."""
        command = CLICommand(namespace.command)
        raw_layers = getattr(namespace, "layer", None)
        layers: List[str] = []
        if raw_layers:
            if isinstance(raw_layers, (list, tuple)):
                layers = list(raw_layers)
            else:
                layers = [str(raw_layers)]
        options = {
            key: value
            for key, value in vars(namespace).items()
            if key
            not in {
                "command",
                "target",
                "profile",
                "duration",
                "stealth",
                "comprehensive",
                "method",
                "layer",
                "action",
                "dll",
                "output",
                "input",
                "pid",
                "service",
                "process",
                "file",
                "name",
                "base_command",
                "description",
                "overwrite",
                "kv_pairs",
                "baseline",
                "from_inventory",
            }
        }
        return cls(
            command=command,
            target=getattr(namespace, "target", None),
            process=getattr(namespace, "process", None),
            file_path=getattr(namespace, "file", None),
            profile=getattr(namespace, "profile", None),
            duration=getattr(namespace, "duration", None),
            stealth=bool(getattr(namespace, "stealth", False)),
            comprehensive=bool(getattr(namespace, "comprehensive", False)),
            method=getattr(namespace, "method", None),
            layers=layers,
            action=getattr(namespace, "action", None),
            dll=getattr(namespace, "dll", None),
            output=getattr(namespace, "output", None),
            input_path=getattr(namespace, "input", None),
            pid=getattr(namespace, "pid", None),
            service=getattr(namespace, "service", None),
            preset_name=getattr(namespace, "name", None),
            base_command=getattr(namespace, "base_command", None),
            description=getattr(namespace, "description", None),
            overwrite=bool(getattr(namespace, "overwrite", False)),
            kv_pairs=list(getattr(namespace, "kv_pairs", []) or []),
            baseline=getattr(namespace, "baseline", None),
            inventory_source=getattr(namespace, "from_inventory", None),
            options=options,
        )


class CLIHandler:
    """Coordinator for CLI commands."""

    def __init__(self, framework: Any):
        self.framework = framework
        self._services = {
            CLICommand.MONITOR: MonitorService(framework),
            CLICommand.INJECT: InjectService(framework),
            CLICommand.CAPTURE: CaptureService(framework),
            CLICommand.HOOKS: HooksService(framework),
            CLICommand.REPORT: ReportService(framework),
            CLICommand.PROFILES: ProfilesService(framework),
            CLICommand.INVENTORY: InventoryService(framework),
        }

    def execute(self, request: CLIRequest) -> Dict[str, Any]:
        """Dispatch CLI command."""
        LOGGER.info("Executing CLI command: %s", request.command.value)

        service = self._services.get(request.command)
        if not service:
            raise ValueError(
                "Unsupported CLI command: {0}".format(request.command.value)
            )
        return service.execute(request)

