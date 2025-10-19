from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from string import Template
from typing import Any, Dict, Tuple


class ReportGenerator:
    """Render structured reports using lightweight Markdown templates."""

    def __init__(self, framework: Any):
        self.framework = framework
        self.base_dir = Path(getattr(framework, "base_dir", Path.cwd()))
        self.data_dir = Path(getattr(framework, "data_dir", self.base_dir / "data"))
        self.templates_dir = self.base_dir / "resources" / "templates"

    def generate(
        self,
        output_file: str,
        context: Dict[str, Any],
        *,
        template_name: str = "default_report.md",
    ) -> Dict[str, str]:
        output_base = self._resolve_output_path(output_file)
        markdown_path, json_path = self._derive_paths(output_base)
        markdown = self._render_markdown(template_name, context)

        markdown_path.parent.mkdir(parents=True, exist_ok=True)
        markdown_path.write_text(markdown, encoding="utf-8")
        json_path.write_text(json.dumps(context, indent=2, default=str), encoding="utf-8")

        return {
            "markdown": str(markdown_path),
            "json": str(json_path),
            "template": template_name,
        }

    def _resolve_output_path(self, output: str) -> Path:
        candidate = Path(output)
        resolver = getattr(self.framework, "_resolve_path", None)
        if callable(resolver):
            return Path(resolver(output))
        if not candidate.is_absolute():
            candidate = self.data_dir / candidate
        return candidate

    @staticmethod
    def _derive_paths(base: Path) -> Tuple[Path, Path]:
        suffix = base.suffix.lower()
        if suffix in {".md", ".markdown"}:
            markdown_path = base
            json_path = base.with_suffix(".json")
        elif suffix == ".json":
            json_path = base
            markdown_path = base.with_suffix(".md")
        else:
            markdown_path = base.with_suffix(".md")
            json_path = base.with_suffix(".json")
        return markdown_path, json_path

    def _render_markdown(self, template_name: str, context: Dict[str, Any]) -> str:
        template_text = self._load_template(template_name)
        substitution = {
            "title": context.get("title") or "Security Testing Report",
            "generated_at": context.get("generated_at") or datetime.utcnow().isoformat(),
            "target": context.get("target") or "Unknown",
            "pid": context.get("pid") or "n/a",
            "summary": self._build_summary(context),
            "tests_section": self._format_tests(context.get("tests")),
            "inventory_section": self._format_inventory(context.get("inventory_context")),
        }
        return Template(template_text).safe_substitute(substitution)

    def _load_template(self, template_name: str) -> str:
        candidate = self.templates_dir / template_name
        if not candidate.suffix:
            candidate = candidate.with_suffix(".md")
        if candidate.exists():
            return candidate.read_text(encoding="utf-8")
        return self._default_template()

    def _build_summary(self, context: Dict[str, Any]) -> str:
        entries = []
        if context.get("directx_flags"):
            entries.append("DirectX flags: " + ", ".join(map(str, context["directx_flags"])))
        inventory = context.get("inventory_context") or {}
        if inventory:
            entries.append(
                "Inventory PID {pid} integrity {integrity}".format(
                    pid=inventory.get("pid", "n/a"),
                    integrity=inventory.get("integrity", "unknown"),
                )
            )
        if not entries:
            entries.append("No additional metadata available.")
        return "\n".join(f"- {line}" for line in entries)

    def _format_tests(self, tests: Any) -> str:
        if not tests:
            return "No test results available."
        lines = []
        for entry in tests:
            if isinstance(entry, dict):
                name = entry.get("name") or entry.get("id") or "Unnamed Test"
                result = entry.get("status") or entry.get("result") or "unknown"
                lines.append(f"- {name}: {result}")
            else:
                lines.append(f"- {entry}")
        return "\n".join(lines)

    def _format_inventory(self, inventory: Any) -> str:
        if not inventory:
            return "Inventory context not provided."
        lines = []
        if inventory.get("pid") is not None:
            lines.append(f"- PID: {inventory['pid']}")
        if inventory.get("exe"):
            lines.append(f"- Executable: {inventory['exe']}")
        if inventory.get("integrity"):
            lines.append(f"- Integrity: {inventory['integrity']}")
        if inventory.get("directx_usage"):
            lines.append(f"- DirectX usage: {inventory['directx_usage']}")
        if inventory.get("directx_flags"):
            lines.append(f"- DX flags: {', '.join(map(str, inventory['directx_flags']))}")
        if inventory.get("swda_detected"):
            lines.append("- SWDA detected")
        if inventory.get("exclusive_display"):
            lines.append("- Exclusive display affinity")
        titles = inventory.get("window_titles") or []
        if titles:
            lines.append(f"- Windows: {', '.join(map(str, titles[:3]))}")
        if not lines:
            lines.append("- No inventory specifics captured.")
        return "\n".join(lines)

    @staticmethod
    def _default_template() -> str:
        return (
            "# ${title}\n\n"
            "*Generated: ${generated_at}*\n\n"
            "## Target\n"
            "- Name: ${target}\n"
            "- PID: ${pid}\n\n"
            "## Summary\n${summary}\n\n"
            "## Test Results\n${tests_section}\n\n"
            "## Inventory Context\n${inventory_section}\n"
        )
