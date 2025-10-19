from __future__ import annotations

from enum import Enum
from typing import List


class CLICommand(str, Enum):
    """Supported CLI verbs available to the launcher."""

    MONITOR = "monitor"
    INJECT = "inject"
    CAPTURE = "capture"
    HOOKS = "hooks"
    REPORT = "report"
    PROFILES = "profiles"
    INVENTORY = "inventory"
    SHELL = "shell"

    @classmethod
    def choices(cls) -> List[str]:
        """Return available verbs for argparse choices."""
        return [command.value for command in cls]
