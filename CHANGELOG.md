# Changelog

All notable changes to this project are documented here. For release assets, see the GitHub Releases page.

## 1.1.0 - 2025-10-21
- Windows Graphics Capture: added monitor capture workflow with dynamic WinRT interop assembly creation.
- Native bypass DLL: integrated HDE-based prologue analysis to avoid splitting instructions when building trampolines.
- Build tooling: vendored disassembler assets into the tree and updated installers/scripts to report version 1.1.0.

## 1.0.2 - 2025-10-15
- Installers: robust path fallback to user-writable dirs; avoid `systemprofile` writes
- install.bat: add `--no-shortcuts`, use `curl -fL --create-dirs`
- install.ps1: mirrored writable path selection and verification
- Python: launcher uses per-user `data_dir`; results saved to writable locations
- CI: grant `contents: write`; attach portable ZIP to tagged releases
- Docs: corrected CMD→PowerShell one-liner; added flags, notes, troubleshooting

## 1.0.1 — 2025-10-15
- Initial hardening for non-admin install paths and basic docs improvements

## 1.0.0 — 2024-xx-xx
- Initial public release of single-file framework
