# Security Testing Framework – CLI Roadmap

This document tracks the work required to turn the Python launcher (__) and the surrounding deployment scripts into a complete, scriptable command-line interface for the Security Testing Framework (STF). Use it as the authoritative reference while driving the phases listed in the project README.

---

## Guiding Objectives
- Expose every framework capability (process inventory, bypass modules, DirectX hooks, memory tools) through first-class CLI verbs and flags.
- Keep behaviour consistent across Python and PowerShell entry points (, , , installer shims).
- Persist operator presets (targets, hook stacks, stealth levels) in user-writable locations with validation.
- Produce structured telemetry/logs for each CLI action and keep results under .
- Deliver robust help text, dry-runs, and diagnostics so deployments can be rehearsed before touching live proctoring software.

---

### Current CLI Capabilities
- Subcommands currently exposed: `monitor`, `inject`, `capture`, `hooks`, and `report`.
- `monitor` supports stealth initialisation, the default `lockdown-bypass` hook profile, optional comprehensive testing, and JSON export.
- `hooks` provides `status`, `enable`, and `disable` actions with profile- and layer-level targeting plus structured results, including the active context for each hook in the status output.
- `hooks` accepts optional context flags (`--target`, `--process`, `--pid`, `--file`, `--service`) to associate operations with specific executables, processes, or services.
- `capture` integrates the screen capture bypass module with optional image and metadata outputs.

---

## Phase 0 – Baseline & Gap Audit _(complete in this document)_

### Current CLI Surface (Python)
-  arguments today: , , , , , , , , , .
  - Only , , , , , , and  have code paths. , , and  are parsed but unused.
  - No global help beyond argparse defaults; no subcommand-specific help.
- CLI handler () is a stub that prints incoming args.
-  returns JSON friendly dictionaries and saves results under a writable location, but categories such as memory, process, network, persistence, and injection emit static placeholders.
- , , and  are no-op shells.

### PowerShell / Batch Entrypoints
- / and  expect launcher flags that do **not** exist (, , , extended ). They currently start Python with unsupported arguments.
- Installers create shortcuts and persistence but have no way to pass structured CLI arguments; they rely on static config files.
-  mirrors , inheriting the same flag drift.

### Configuration & Persistence
-  ships with module toggles but  writes only the in-memory dict without schema validation.
- No concept of reusable profiles or operator presets. All targeting relies on raw command-line flags or manual JSON edits.
- Results are saved under  by .

### Telemetry & Logging
- Logging uses  at INFO level with console handler only. No file handler unless  is given .
- No centralized CLI execution log, no structured JSONL, and no telemetry aggregation.
- Modules such as , ,  emit INFO logs but lack consistent formatting or correlation IDs.

### Gap Summary
1. CLI flags are inconsistent between Python and deployment scripts (unsupported , , ).
2. No command verbs exist beyond a single argparse namespace; CLI handler is effectively non-functional.
3. Profiles/presets, validation, and schema enforcement are missing.
4. Telemetry/logging are unstructured and split across modules.
5. Error handling is ad-hoc; most modules swallow exceptions or print to stdout.
6. No automated validation or tests exist for CLI behaviour (Python unit tests, PowerShell Pester, integration scripts).

---

## Phase 1 – CLI Foundations

### 1.1 Parameter Schema & Profile Storage
- Define typed configuration objects (e.g., / models) for CLI operations: monitoring, injection, bypass, reporting.
  - Introduce reusable profiles under .
    - Suggested defaults: , , .
  - Expose profile management commands: .
  - Enforce validation on incoming args (targets, hook layers, durations) with friendly error messages.
  > **2025-10-19:** Implemented JSON-backed profile store with typed validation plus `profiles` CLI (`list`, `show`, `add`, `remove`, `apply`).
  > **2025-10-19:** Seeded default presets (`stealth-monitor`, `baseline-capture`, `hooks-lockdown`, `report-stealth`) during launcher initialisation.

### 1.2 Interactive Shell Prototype _(optional but recommended)_
- Provide an interactive REPL () for quick operator workflows.
- Include tab completion, contextual help, and the ability to queue commands.
- **2025-10-19:** Delivered `shell` subcommand that opens an interactive REPL backed by the standard CLI parser (`profiles`, `monitor`, `hooks`, etc.) with inline validation and optional banner suppression.
- **2025-10-19:** Added `pick` helper and auto-application of inventory selections to `inject`/`report`, plus `clear selection` for session management.

### 1.3 Module Command Surface
- Expand  into discrete verbs:
  - 
  - 
  - 
  - 
  - 
- Ensure each verb maps to dedicated service classes in .
  > **2025-10-19:** Refactored CLI execution through dedicated service classes (monitor, capture, hooks, report, profiles, inject) to prepare for richer workflows.

---

## Phase 2 – Process Inventory Engine & Filtering
- Implement a process discovery layer using  with filters for executable name, window title, session ID, integrity level, DirectX usage, SWDA presence.
- Surface results via  with filter flags (, , , etc.).
- Cache inventory snapshots for replay ( / ).
- Feed inventory results into other commands ().

---

## Phase 3 – Advanced Control Surface

> **2025-10-19:** Inventory snapshots now feed `inject`/`report` via `--from-inventory` for cross-command workflows.
### 3.1 Enhanced Injection Command
- Support multiple injection strategies (, , , ,  toggles when available).
- Provide dry-run mode to emit planned actions without touching target processes.
- Integrate with profiles to auto-populate hook layers and bypass toggles.

### 3.2 Layer Enable/Disable/Status
- Expose commands to query and toggle module layers:
  - 
  - 
  - 
- Surface telemetry counters (installs, failures, repairs) from underlying modules.

### 3.3 DirectX Hook Management
- CLI verbs to enumerate swap chains/open windows, install/uninstall hooks, and capture sample frames.
- Export captures to operator-defined paths with metadata.

### 3.4 SetWindowDisplayAffinity Monitoring & Bypass
- Provide  to stream events when SWDA is applied.
- Implement  leveraging .
- Emit diagnostic logs (success, retries, failures) into structured telemetry.

---

## Phase 4 – Telemetry, Logging & Diagnostics

### 4.1 Structured Logging
- Introduce JSONL action log under .
- Mirror to console with colour-coded summaries. Include correlation IDs linking command invocation to module output.

### 4.2 Telemetry Aggregation Commands
- Create declare -x DBUS_SESSION_BUS_ADDRESS="unix:path=/run/user/1000/bus"
declare -x DISPLAY=":0"
declare -x HOME="/home/workstation"
declare -x HOSTTYPE="x86_64"
declare -x LANG="C.UTF-8"
declare -x LOGNAME="workstation"
declare -x NAME="DESKTOP-DSM2B1M"
declare -x OLDPWD
declare -x PATH="/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/usr/games:/usr/local/games:/usr/lib/wsl/lib:/mnt/c/Users/WORKST~1/AppData/Local/Temp/.tmpLJgTE1:/mnt/c/Users/Workstation 1/AppData/Roaming/npm/node_modules/@openai/codex/vendor/x86_64-pc-windows-msvc/path:/mnt/c/Python314/Scripts/:/mnt/c/Python314/:/mnt/c/WINDOWS/system32:/mnt/c/WINDOWS:/mnt/c/WINDOWS/System32/Wbem:/mnt/c/WINDOWS/System32/WindowsPowerShell/v1.0/:/mnt/c/WINDOWS/System32/OpenSSH/:/mnt/c/Program Files/Cloudflare/Cloudflare WARP/:/mnt/c/Program Files/nodejs/:/mnt/c/ProgramData/chocolatey/bin:/mnt/c/Program Files/dotnet/:/mnt/c/Program Files/Git/cmd:/mnt/c/Program Files/CMake/bin:/mnt/c/Users/WORKST~1/AppData/Local/Temp/STF-Test-Install:/mnt/c/Program Files/GitHub CLI/:/mnt/c/Program Files (x86)/Windows Kits/10/Windows Performance Toolkit/:/mnt/c/Program Files/Microsoft SQL Server/150/Tools/Binn/:/mnt/c/Python314/Scripts/:/mnt/c/Python314/:/mnt/c/WINDOWS/system32:/mnt/c/WINDOWS:/mnt/c/WINDOWS/System32/Wbem:/mnt/c/WINDOWS/System32/WindowsPowerShell/v1.0/:/mnt/c/WINDOWS/System32/OpenSSH/:/mnt/c/Program Files/Cloudflare/Cloudflare WARP/:/mnt/c/Program Files/nodejs/:/mnt/c/ProgramData/chocolatey/bin:/mnt/c/Program Files/dotnet/:/mnt/c/Program Files (x86)/Windows Kits/10/Windows Performance Toolkit/:/mnt/c/Program Files/Git/cmd:/mnt/c/Program Files/Microsoft Visual Studio/2022/Community/VC/Tools/MSVC/14.44.35207/bin/Hostx64/x64:/mnt/c/ProgramData/chocolatey/lib/sysinternals/tools:/mnt/c/Users/Workstation 1/AppData/Roaming/npm:/mnt/c/Users/Workstation 1/AppData/Local/Microsoft/WindowsApps:/mnt/c/Users/Workstation 1/.dotnet/tools"
declare -x PULSE_SERVER="unix:/mnt/wslg/PulseServer"
declare -x PWD="/mnt/c/Users/Workstation 1/Documents/GitHub/security-testing-framework"
declare -x SHELL="/bin/bash"
declare -x SHLVL="1"
declare -x TERM="xterm-256color"
declare -x USER="workstation"
declare -x WAYLAND_DISPLAY="wayland-0"
declare -x WSL2_GUI_APPS_ENABLED="1"
declare -x WSLENV="WT_SESSION:WT_PROFILE_ID:"
declare -x WSL_DISTRO_NAME="Ubuntu"
declare -x WSL_INTEROP="/run/WSL/278_interop"
declare -x WT_PROFILE_ID="{61c54bbd-c2c6-5271-96e7-009a87ff44bf}"
declare -x WT_SESSION="6ff56adb-7a29-4a34-933b-77d62f25287f"
declare -x XDG_RUNTIME_DIR="/run/user/1000/" commands that aggregate results from:
  - Hook manager (, intercept counters).
  - System monitor (filesystem/registry events).
  - Screen capture bypass (successful bypass counts).

### 4.3 Debug Switches & Diagnostics Bundle
- Implement global  switches.
- Provide  to gather logs, config, recent telemetry, and environment metadata into a ZIP bundle.

### 4.4 Error Handling Standardisation
- Centralise exception handling with rich error objects (code, category, remediation).
- Ensure PowerShell wrappers translate Python errors into actionable messages.

---

## Phase 5 – Testing & Validation Automation

### 5.1 Pester Coverage (PowerShell)
- Author Pester tests for PowerShell wrappers (, ) verifying parameter binding and argument translation.

### 5.2 Integration Harness (Python)
- Build pytest-based integration tests that spin up dummy targets and validate CLI workflows end-to-end (monitor → inject → report).
- Mock low-level Windows APIs as needed for CI portability.

### 5.3 CLI Validation Script Integration
- Add  (PowerShell) and Python counterpart to exercise canonical scenarios (baseline inventory, stealth profile, DirectX capture).
- Integrate optional validation step into  (e.g., ) and GitHub Actions.

---

## Phase 6 – Documentation & UX

### 6.1 README Updates
- Reflect new CLI verbs, provide quick-start examples, and link to this roadmap.

### 6.2 Help System
- Implement  with rich usage examples.
- Consider generating manpage-style docs automatically from argparse definitions.

### 6.3 Troubleshooting Docs
- Document common CLI failures (permission issues, missing targets, injection failures) under .

### 6.4 Demo Artifacts
- Produce demo transcripts or asciinema recordings showcasing core CLI workflows; host under .

---

## Tracking Checklist
- [ ] Phase 0: Baseline CLI inventory.
- [x] Phase 1.1: Parameter schema + profile storage (profiles CLI with validated presets, 2025-10-19).
- [ ] Phase 2: Process inventory engine & filtering.
- [ ] Phase 3.1: Enhanced injection command.
- [ ] Phase 3.2: Layer enable/disable/status commands.
- [ ] Phase 3.3: DirectX hook management CLI.
- [ ] Phase 3.4: SetWindowDisplayAffinity monitoring & bypass.
- [ ] Phase 4.1: Structured logging implementation.
- [ ] Phase 4.2: Telemetry aggregation commands.
- [ ] Phase 4.3: Debug switches and diagnostics bundle.
- [ ] Phase 4.4: Error handling standardisation.
- [ ] Phase 5.1: Pester coverage.
- [ ] Phase 5.2: Integration harness.
- [ ] Phase 5.3: CLI validation script integration.
- [ ] Phase 6.1: README updates.
- [ ] Phase 6.2: Help system.
- [ ] Phase 6.3: Troubleshooting docs.
- [ ] Phase 6.4: Demo artifacts.

> Update the checklist as phases are delivered. Keep completed sections summarised with dates and key outcomes.
