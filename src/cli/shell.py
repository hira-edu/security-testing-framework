from __future__ import annotations

import argparse
import cmd
import json
import shlex
import textwrap
import time
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from src.cli.cli_handler import CLIHandler, CLIRequest
from src.cli.constants import CLICommand


class ShellParseError(RuntimeError):
    """Raised when shell parsing fails."""


class InteractiveShell(cmd.Cmd):
    """Interactive REPL surface for executing STF CLI commands."""

    prompt = "stf> "
    intro = textwrap.dedent(
        """
        Security Testing Framework - Interactive Shell
        Type a CLI command (e.g. 'monitor --target LockDownBrowser.exe').
        Use 'help' to list available commands, 'help <command>' for details, and 'exit' to quit.
        """
    ).strip()

    def __init__(
        self,
        framework: object,
        parser_factory: Callable[[], argparse.ArgumentParser],
    ) -> None:
        super().__init__()
        self.framework = framework
        self._parser_factory = parser_factory
        self._handler = CLIHandler(framework)
        self._session_state: Dict[str, Any] = {}

    def default(self, line: str) -> None:
        """Handle unrecognised commands by routing to the CLI parser."""
        command = line.strip()
        if not command:
            return
        if command in {"exit", "quit"}:
            self.do_exit("")
            return

        try:
            arguments = shlex.split(command)
        except ValueError as exc:  # pragma: no cover - defensive
            self._emit_error(f"Unable to parse command: {exc}")
            return

        arguments = self._apply_session_shortcuts(arguments)

        parser = self._create_parser()
        try:
            namespace = parser.parse_args(arguments)
        except ShellParseError as exc:
            self._emit_error(str(exc) or "Invalid command.")
            return

        if not getattr(namespace, "command", None):
            self._emit_error("Please provide a subcommand (e.g. 'monitor', 'hooks').")
            return

        if namespace.command == CLICommand.SHELL.value:
            self._emit_error("Cannot launch the shell from within the shell.")
            return

        try:
            request = CLIRequest.from_namespace(namespace)
        except ValueError as exc:
            self._emit_error(str(exc))
            return

        try:
            response = self._handler.execute(request)
        except Exception as exc:  # noqa: BLE001 - surface error to operator
            self._emit_error(f"Command failed: {exc}")
            return

        self._emit_json(response)

    def do_exit(self, line: str) -> bool:  # noqa: D401 - cmd.Cmd interface
        """Exit the interactive shell."""
        return True

    def do_quit(self, line: str) -> bool:  # noqa: D401 - alias for exit
        """Alias for exit."""
        return self.do_exit(line)

    def do_help(self, arg: str) -> None:  # noqa: D401
        """Show general help or command-specific usage."""
        topic = arg.strip()
        parser = self._create_parser()

        if not topic:
            parser.print_help()
            return

        subparser = self._resolve_subparser(parser, topic)
        if not subparser:
            self._emit_error(f"Unknown command '{topic}'.")
            return
        subparser.print_help()

    def do_pick(self, arg: str) -> None:
        """Run process inventory and interactively select a target."""
        arguments = shlex.split(arg) if arg else []
        parser = self._create_parser()
        try:
            namespace = parser.parse_args(["inventory", *arguments])
        except ShellParseError as exc:
            self._emit_error(str(exc) or "Invalid inventory filters.")
            return

        try:
            request = CLIRequest.from_namespace(namespace)
        except ValueError as exc:
            self._emit_error(str(exc))
            return

        try:
            snapshot = self._handler.execute(request)
        except Exception as exc:  # pragma: no cover - defensive
            self._emit_error(f"Inventory command failed: {exc}")
            return

        processes = snapshot.get("processes") or []
        if not processes:
            print("No processes matched the supplied filters.")
            return

        limit = getattr(namespace, "limit", None) or 20
        if limit <= 0:
            limit = min(len(processes), 20)
        showcase = processes[: min(len(processes), limit)]
        self._render_picker_table(showcase)

        try:
            selection_raw = input("Select index (blank to cancel): ").strip()
        except (EOFError, KeyboardInterrupt):  # pragma: no cover - interactive guard
            print()
            return

        if not selection_raw:
            return
        if not selection_raw.isdigit():
            self._emit_error("Selection must be a number.")
            return

        index = int(selection_raw)
        if index < 1 or index > len(showcase):
            self._emit_error("Selection out of range.")
            return

        selection = showcase[index - 1]
        storage_path = self._store_inventory_selection(selection, snapshot)
        print(f"[picker] stored selection pid {selection.get('pid')} at {storage_path}.")
        print("Subsequent inject/report commands will automatically reuse this context. Use 'clear selection' to reset.")

    def help_pick(self) -> None:  # noqa: D401
        print(
            "pick [inventory filters]\n"
            "    Run inventory with optional filters, present results, and store the chosen process for reuse."
        )

    def do_clear(self, arg: str) -> None:
        """Clear stored shell state (currently picker selection)."""
        target = arg.strip().lower()
        if target in {"selection", "inventory", "picker"}:
            cleared = self._clear_inventory_selection(delete_file=True)
            if cleared:
                print("Cleared stored inventory selection.")
            else:
                print("No stored inventory selection.")
        else:
            print("Usage: clear selection")

    def help_clear(self) -> None:  # noqa: D401
        print("clear selection\n    Remove the stored inventory picker selection.")

    def emptyline(self) -> None:
        """Do nothing when the user submits an empty line."""

    def _create_parser(self) -> argparse.ArgumentParser:
        parser = self._parser_factory()
        self._make_non_terminating(parser)
        return parser

    def _make_non_terminating(self, parser: argparse.ArgumentParser) -> None:
        """Convert parser to raise exceptions instead of exiting."""

        def exit_with_error(status: int = 0, message: str | None = None) -> None:
            raise ShellParseError(message or "")

        def error(message: str) -> None:
            raise ShellParseError(message)

        parser.exit = exit_with_error  # type: ignore[assignment]
        parser.error = error  # type: ignore[assignment]

        for action in getattr(parser, "_actions", []):
            if isinstance(action, argparse._SubParsersAction):
                for subparser in action.choices.values():
                    self._make_non_terminating(subparser)

    def _render_picker_table(self, processes: List[Dict[str, Any]]) -> None:
        if not processes:
            return
        header = f"{'Idx':>4} {'PID':>6} {'Integrity':>10} {'DX':>12} {'SWDA':>6} {'Exclusive':>9} Name"
        print(header)
        print("-" * len(header))
        for idx, proc in enumerate(processes, start=1):
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

    def _store_inventory_selection(self, selection: Dict[str, Any], snapshot: Dict[str, Any]) -> str:
        storage_path = self.framework.remember_inventory_selection(selection, snapshot, label="shell")
        self._session_state["inventory_selection"] = selection
        self._session_state["inventory_selection_path"] = storage_path
        self._session_state["inventory_snapshot"] = {
            "filters": snapshot.get("filters"),
            "collected_at": snapshot.get("collected_at"),
        }
        return storage_path

    def _clear_inventory_selection(self, *, delete_file: bool = True) -> bool:
        path = self._session_state.pop("inventory_selection_path", None)
        self._session_state.pop("inventory_selection", None)
        self._session_state.pop("inventory_snapshot", None)
        if delete_file and path:
            try:
                Path(path).unlink(missing_ok=True)
            except Exception:  # pragma: no cover - defensive cleanup
                pass
        return bool(path)

    def _apply_session_shortcuts(self, arguments: List[str]) -> List[str]:
        if not arguments:
            return arguments

        selection_path = self._session_state.get("inventory_selection_path")
        selection = self._session_state.get("inventory_selection")
        if selection_path and not Path(selection_path).exists():
            self._clear_inventory_selection(delete_file=False)
            selection_path = None
            selection = None

        command = arguments[0]
        if command in {"inject", "report"} and selection_path and "--from-inventory" not in arguments:
            arguments = list(arguments)
            arguments.extend(["--from-inventory", selection_path])
            if "--pid" not in arguments and selection and selection.get("pid") is not None:
                arguments.extend(["--pid", str(selection["pid"])])
            print(f"[picker] applied stored inventory selection (pid {selection.get('pid', 'unknown')})")
        return arguments

    def _resolve_subparser(
        self,
        parser: argparse.ArgumentParser,
        command: str,
    ) -> argparse.ArgumentParser | None:
        for action in getattr(parser, "_actions", []):
            if isinstance(action, argparse._SubParsersAction):
                return action.choices.get(command)
        return None

    def _emit_json(self, payload: object) -> None:
        print(json.dumps(payload, indent=2, default=str))

    def _emit_error(self, message: str) -> None:
        print(f"[error] {message}")


def launch_shell(
    framework: object,
    parser_factory: Callable[[], argparse.ArgumentParser],
    *,
    show_banner: bool = True,
) -> None:
    """Convenience helper to execute the interactive shell."""
    shell = InteractiveShell(framework, parser_factory)
    intro = shell.intro if show_banner else None
    shell.cmdloop(intro=intro)
