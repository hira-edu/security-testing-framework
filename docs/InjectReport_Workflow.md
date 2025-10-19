# Inject / Report Implementation Plan

This note captures the proposed implementation details for the upcoming enhancements called out in the CLI roadmap:

* Promote the `inject` command from a stub to a functional workflow that can stage DLL payloads and execute them against a resolved target.
* Deliver a structured reporting pipeline that produces templated artifacts instead of raw JSON.
* Reuse inventory snapshots to drive cross-command scenarios (already wired to CLI verbs via `--from-inventory`) and surface ergonomic selectors for operators.

The goal is to sequence the work so that we can iterate quickly while keeping the footprint understandable for reviewers and operators.

---

## Existing Components

| Area | Relevant Assets | Notes |
| --- | --- | --- |
| CLI plumbing | `src/cli/services/inject_service.py`, `src/cli/services/report_service.py`, `src/cli/shell.py` | Both services currently return placeholder payloads; shell can dispatch any verb, which will be useful for interactive pickers. |
| Inventory | `src/modules/process_inventory.py` | Rich telemetry now includes DirectX/SWDA hints, window metadata, counts, diffs. |
| Native assets | `native/dll/`, `native/drivers/` (empty) | Directory structure exists for packaging DLLs/drivers; staging logic not yet written. |
| Utilities | `src/utils/report_generator.py` | Stub that just prints; ready to become templating entry point. |
| Profiles | `resources/configs/` (empty), `config.json` defaults | Profiles already persist; new verbs need to load/stage settings from inventory snapshots and JSON presets. |

---

## Injection Workflow Design

### Requirements
1. Resolve a target process using either direct `--target`/`--pid` flags or the new `--from-inventory` option (already parsed by the service).
2. Stage the DLL payload locally (copy from `resources/` or download artifact) into a temp working directory where the injector module can access it.
3. Execute the injection using supported strategies (initially “manual-map” + “section-map” to match existing CLI flag semantics).
4. Emit structured status objects capturing staged paths, injection strategy, telemetry (`cpu_percent`, `integrity`, inventory context).
5. Provide dry-run / validation mode that only builds the plan without touching the process (useful for automation and tests).
6. Enforce guardrails (admin checks, architecture compatibility, missing DLL, etc.) with actionable error objects instead of raw strings.

### Proposed Architecture
* New helper module: `src/modules/injection_pipeline.py`
  * `class InjectionOptions`: dataclass describing method, dll path, timeout, dry_run, etc.
  * `class Injector`: orchestrates staging + execution (wrapping native loader / `ctypes` stubs). For the first pass, implement staging + simulated injection with TODO marker where native call will live.
  * Staging helper: `stage_payload(options, data_dir)` that copies from `resources/dll/<profile>` or a path provided by the CLI. Expose to CLI for introspection.
* Extend `InjectService.execute`:
  * Translate CLI arguments into `InjectionOptions` (resolve preset defaults, choose staging directory under `%LOCALAPPDATA%\SecurityTestingFramework\staged`).
  * Instantiate `Injector`, call `.prepare()` (staging) and `.execute()` (optionally simulate until native implementation added). Return payload with `status: "staged"` or `"executed"` plus file hashes, inventory metadata, and warnings.
  * Preserve “not fully implemented” log but augment with structured output until native hook lands.
* Logging: integrate with existing logger (`LOGGER`) and feed events into a new `logs/inject.log` file under `data_dir` (use `logging.FileHandler` in `InjectionPipeline`). This paves the way for telemetry aggregation later.

---

## Report Templating Plan

### Requirements
1. Consume either a fresh `run_comprehensive` result or a provided inventory snapshot to build a human-readable report.
2. Support template-based rendering (Markdown + JSON metadata) without introducing heavy dependencies if possible.
3. Provide extension points for future HTML/PDF output (e.g., via `jinja2` eventually, but start with `string.Template` or `jinja2` optional import).
4. Allow operators to persist both the rendered artifact and the raw data used to generate it.

### Proposed Architecture
* Expand `src/utils/report_generator.py` into a small templating engine:
  * Accept context dict: `{ "tests": ..., "inventory": ..., "metadata": ... }`.
  * Load template files from `resources/templates/` (create directory with base Markdown template). Fallback to built-in default if file missing.
  * Emit Markdown + JSON: `<output>.md` + `<output>.json` (where `<output>` is the user-provided path without extension).
* Update `ReportService.execute`:
  * After resolving target (and optional inventory context), build report context including `directx_flags`, `swda_detected`, etc.
  * Call the new `ReportGenerator.generate(output_path, context, template="default.md")` returning dictionary with `markdown`, `json`, `template` paths.
  * Maintain compatibility with current JSON-only output by allowing `--output` to be `.json`; in that case, still generate the Markdown alongside.
* Document templating in README, including how to place custom templates under `resources/templates/` and reference via `--template-name` (future enhancement).

---

## Inventory-driven Selector UX

While implementing the above, we should prepare the foundation for a “picker” experience:
* CLI flag `--picker` on `inventory` to output a compact table or launch an interactive prompt (Phase 2.1).
* Shell helper command `pick` that reuses the inventory snapshot to select a process, storing it in shell session state (extending `InteractiveShell` with `self.context["selected_process"]`).
* Shared utility to write selected process context to `$DATA_DIR/inventory/last_selection.json` so other verbs can read it when `--from-inventory last` is provided.

These features are not implemented yet but will align with the new pipeline work when we wire them up in the next task.

---

## Implementation Checklist
1. Scaffold `src/modules/injection_pipeline.py` with staging + simulated execution.
2. Extend `InjectService` to consume the new pipeline and surface detailed responses (inventory context, staged payload info).
3. Flesh out `ReportGenerator` and wire `ReportService` to use it, including inventory-derived metadata.
4. Create `resources/templates/default_report.md` for Markdown rendering and document usage.
5. Update CLI docs / README with new instructions (`--from-inventory`, report outputs).
6. Add tests covering staging plan serialization, report generation metadata, and service behaviour with inventory contexts.
7. (Next task) Layer on interactive pickers once the pipeline components exist.

This document should guide the coding work for the next development iteration. Update it as decisions solidify or dependencies evolve.
