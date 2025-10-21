# Bypass Methods Integration Blueprint

This document captures how the `bypass-methods` repository maps into the Security Testing Framework (STF) codebase and what we need to align before producing a combined release build.

## Asset Inventory

### Core native components (required)
- `src/hooks/*` & `src/com_hooks/*`: DirectX 11/12 vtable interception, swap chain hooks, COM factory hooks. Requires C++17, links against `d3d11`, `dxgi`, `windowscodecs`, `user32`, `gdi32`.
- `src/frame/frame_extractor.cpp`: Converts GPU surfaces to host-readable buffers, depends on hook outputs.
- `src/shared/shared_memory_transport*.cpp`: High-throughput shared memory channel with compression hooks.
- `src/memory/*.cpp`: Pattern + memory scanners for signature detection.
- `src/signatures/*.cpp`: LockDown/DX signature catalogs consumed by scanners.
- `src/utils/*.cpp` & `include/utils/*`: Error handling, RAII wrappers, crash reporter, performance monitor required by every hook.
- `src/optimization/*.cpp`: Thread pool, memory pool, performance optimizer used by hook/runtime code paths.
- `include/**/*.h`: Public headers (must ship with DLL build). Missing `src/dllmain_refactored.cpp` reference in CMake — needs correction to `src/dllmain.cpp`.

### Core Python orchestration (required)
- `python/capture/*.py`: Windows Graphics Capture, DXGI duplication, enhanced/advanced capture wrappers. Depend on `numpy`, `Pillow`, `pythonnet`/`clr`, `comtypes`, `pywin32`, `pywinctl`, `win32gui`/`win32con`.
- `python/tools/security_{manager,integrations,tester}.py`: Security policy engine, telemetry, anti-detection features. Depend on `cryptography`, `psutil`, `pywin32`, `colorlog`.
- `python/tools/{injector,named_pipe_manager}.py`: Low-level injector helpers (`ctypes`, `pywin32`). `inject.py` is default staging script.
- `python/tools/configuration_manager.py`: Config schema loader used by GUI/CLI.
- `python/tools/{remote_client,controller}`: Remote orchestration helpers; `controller` pulls in `PyQt5`, `keyboard`, `pywinctl`, `ImageGrab`.

### Advanced UI & monitoring (ship optional)
- `python/tools/{gui_controller,dashboard}.py`: Tkinter dashboard + PyQt5 GUI. Require `tkinter`, `matplotlib`, `PyQt5`, `numpy`.
- `python/accessibility/*`: Accessibility manager/controller, relies on `keyboard`, `comtypes`, `pywin32`.

### Examples, demos, tests (defer unless explicitly requested)
- `demo_*.py`, `python/examples/*`, `python/tests/*`, `tests/*` (C++ GoogleTest suites), launch `.bat` helpers.
- `scripts/*.bat|*.ps1|*.py` (build/install orchestrators) — use as reference when wiring STF build pipeline but do not ship by default.

### Dependency manifests
- `python/requirements/*.txt`: Currently overlapping pins; need consolidation when merged into STF `requirements.txt`.
- `cmake/dependencies.cmake`: FetchContent, dependency validation, and interface libraries for the C++ build.

## Integration Matrix

| Bypass asset | Target STF location | Required deps / build flags | Notes |
| --- | --- | --- | --- |
| `src/{hooks,shared,memory,signatures,optimization,utils,frame}/**` | `native/bypass_methods/src/**` | CMake + MSVC 2019/2022, `/std:c++17`, link `d3d11;dxgi;windowscodecs;user32;gdi32`, optional FetchContent googletest | Update `CMakeLists.txt` to fix `dllmain` path, emit `UndownUnlockDXHook.dll` into `native/dll/bypass_methods`. |
| `include/**` | `native/bypass_methods/include/**` | same as above | Needed for any future native consumers; package alongside DLL. |
| `DLLHooks/*.sln|*.vcxproj` | `native/bypass_methods/DLLHooks/` | Visual Studio solution (optional) | Keep for developers; scripting build should rely on CMake path. |
| `python/capture/*.py` | `src/external/bypass_methods/capture/` | `numpy`, `Pillow`, `pywin32`, `pythonnet` (`clr`), `comtypes`, WinRT runtime (Windows 10 1809+) | Ensure `__init__.py` exposes capture methods; WGC module requires packaged WinRT interop DLL (generated on first run). |
| `python/tools/security_*.py` | `src/external/bypass_methods/security/` | `cryptography`, `psutil`, `pywin32`, `colorlog` | Wire into STF `src/modules/system_monitor` & config toggles. |
| `python/tools/{injector,named_pipe_manager,inject.py}` | `src/external/bypass_methods/injection/` | `pywin32`, `psutil` | Tie `InjectionPipeline` to use `Injector`; expose staging defaults under `config.capture`. |
| `python/tools/{configuration_manager,remote_client}` | `src/external/bypass_methods/tools/` | `pywin32`, `requests` (remote client) | Used by GUI and CLI orchestration. |
| `python/tools/{gui_controller,dashboard}` | `src/external/bypass_methods/ui/` | `PyQt5`, `tkinter`, `matplotlib`, `numpy` | Optional features; guard imports to avoid hard dependency in headless builds. |
| `python/accessibility/*` | `src/external/bypass_methods/accessibility/` | `keyboard`, `comtypes`, `pywin32` | Ship disabled by default; expose via config flag. |
| `python/requirements/*.txt` | Merge into `requirements.txt` or `requirements/bypass_methods.txt` | — | Deduplicate versions; add `pythonnet`, `PyWinCtl`, `matplotlib`, `PyQt5`, `psutil`, `cryptography`. |
| `docs/*` | Merge into STF `docs/` (`docs/bypass_methods/*.md`) | — | Pull key sections into STF install/build docs; retain attributions. |

## Runtime alignment & config changes
- **Module discovery**: Create `src/external/bypass_methods/__init__.py` that exposes subpackages. Update `sys.path` management to load from `Path(__file__).resolve().parent`.
- **Native asset lookup**: Define helper (e.g. `src/utils/native_paths.py`) returning `native/bypass_methods/dll/UndownUnlockDXHook.dll`. Provide fallback if DLL missing and log actionable error.
- **Config schema updates**: Add `config["bypass_methods"]` section with:
  - `enabled`, `dll_path`, `python_package_root`
  - `capture`: default method chain from bypass modules (`windows_graphics_capture`, `dxgi_desktop_duplication`, `advanced_capture`)
  - `security`: booleans for anti-detection, integrity checks; default to `True` but allow downgrade when dependencies absent.
  - `modules.gui`: default `false` to avoid PyQt5 hard dependency; CLI falls back to interactive shell when disabled.
- **Platform assumptions**:
  - Windows 10/11 x64 only; Windows Graphics Capture requires build 17763+.
  - Administrator privileges for injection/kernel-level hooks; warn if not elevated.
  - Visual Studio Build Tools 2022, CMake ≥ 3.16, Python 3.9–3.11, .NET Runtime for WinRT interop.
  - Optional UI paths require desktop session + GPU acceleration.
- **Environment expectations**: Ensure `%LOCALAPPDATA%\SecurityTestingFramework\native` writable for staged DLLs; maintain staging under `%ProgramData%` only if running elevated.

## Packaging & build updates
- **Native pipeline**:
  1. Add CMake preset or PowerShell wrapper (`build_native_bypass_methods.ps1`) invoked from STF build scripts.
  2. Stage outputs under `native/dll/bypass_methods/UndownUnlockDXHook.dll` and copy supporting PDBs to `artifacts/symbols` (optional).
  3. Capture build metadata (commit, toolchain) in `native/bypass_methods/manifest.json` for release notes.
  4. Document optional driver signing workflow (currently no `.sys`; flag as future work).
- **Python packaging**:
  - Fold dependencies into STF virtualenv/requirements; ensure PyInstaller hidden imports include `clr`, `pythonnet`, `win32evtlog`, `matplotlib.backends.backend_tkagg`, `PyQt5.sip`.
  - Add `datas` entries for `src/external/bypass_methods` and native DLL folder in `SecurityTestingFramework_Fixed.spec`.
  - Extend `build_single_file.py` staging step to copy `native/bypass_methods` and register modules in launcher path resolution.
- **Resource metadata**:
  - Update `version_info.py` to surface bypass DLL version + build timestamp.
  - Add `config.json` defaults referencing new capture/injection modes with graceful degradation if dependencies missing.

## Validation & release readiness
- **Unit tests**: Port critical Python tests (security manager, injector, capture fallbacks) into STF `tests/` and adapt to new package paths. Evaluate feasibility of embedding C++ GoogleTests (optional).
- **Smoke tests**:
  1. Windows VM run: build native DLL, execute STF CLI `screen-capture --method windows_graphics_capture` to confirm frame retrieval.
  2. Injection dry-run: `stf inject --method manual-map --dry-run` verifying staging + plan generation.
  3. GUI optional: launch PyQt5 controller verifying dynamic imports.
- **Build verification**: Run PyInstaller to ensure DLL + python packages bundled; verify runtime log surfaces missing dependency warnings (not crashes).
- **Release collateral**: Draft release notes summarizing integration, list new dependencies/licensing, provide hash output for DLL and PyInstaller artifact. Tag GitHub release once smoke tests pass.

---

Open items to track separately:
1. Confirm optional UI modules ship by default or remain gated behind feature flags.
2. Determine packaging strategy for dynamically generated WinRT interop DLL (pre-build vs runtime generation).
3. Run Windows-native build to produce signed DLL/PDB and execute STF smoke tests before tagging a release.
