# Bypass Methods Native Build

This directory mirrors the upstream bypass-methods C++ code and compiles the
`UndownUnlockDXHook.dll` payload that STF loads at runtime.

## Notes

- Windows 10/11 x64 with Visual Studio 2019/2022 is required.
- All original headers and sources now live under `include/` and `src/`.
- Post-build steps stage the generated DLL (and PDB when available) back into
  `native/bypass_methods/dll/`, which matches the lookup logic in
  `src/utils/native_paths.py`.

## Building Locally (Windows)

```powershell
cmake -S native -B native/build -G "Visual Studio 17 2022" -A x64
cmake --build native/build --config Release
```

The resulting DLL is copied to `native/bypass_methods/dll/UndownUnlockDXHook.dll`.
Copy the accompanying PDB (if generated) to the same folder for debugging
purposes.

### Verification

After building:

1. Confirm `native/bypass_methods/dll/UndownUnlockDXHook.dll` and, if available,
   `UndownUnlockDXHook.pdb` exist.
2. Run `cmake --build native/build --config Release --target UndownUnlockTestClient`
   to produce the test harness.
3. Execute smoke tests on a Windows host to ensure the DLL loads via STF before
   publishing release artifacts.
