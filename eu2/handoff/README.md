> Historical developer handoff. For the current adaptive Widescreen integration
> and qualification status, use [the active EU2 guide](../README.md).

# SCES-01331 / Tombi! Europe 2 developer handoff

Historical backend-only handoff. The current common European product uses the
three repository patches and instructions in `europe/DEVELOPER.md`. The older
standalone preparation steps below are retained as backend history.

Local review candidate, Windows x64. No publication or external transfer has occurred.
The game repository baseline already includes the official EU1 integration.
Exact source revisions and repository URLs are in `SOURCE_BASES.json`.

## Apply

1. Obtain TombaRecomp at the exact `TombaRecomp.base` revision.
2. Initialize its submodules recursively at the recorded base revisions.
3. At the game root run `git apply --check TombaRecomp-EU2.patch`, then
   `git apply TombaRecomp-EU2.patch`.
4. Inside `recomp-ui`, apply `recomp-ui-memory-card-safety.patch` the same way.
   No psxrecomp source patch is needed.

Patches contain source deltas, not generated game code. They deliberately leave
submodule gitlinks unchanged: the UI revision after applying the patch is a local
review commit, not a published ref. Commit the reviewed UI patch and set the
gitlink to your own integration commit. There is no dependency on a private ref.

## Build

Python 3.11+, CMake, Ninja and Windows x64 Clang are developer prerequisites.
Use the framework's pinned dependencies and initialize nested submodules.
Set `TOMBI_TOOLCHAIN_BIN` only if the tools are not on PATH. The required disc
is a legal SCES-01331 raw data track: size 492306528 bytes,
SHA1 `684dbf0ad03f872511046d40d3cc85b17d839dbf`.

From the game root:

```powershell
python -I -B eu2/prepare.py --disc "path/to/owned/disc.cue"
$eu2Root = (Get-Location).Path.Replace('\', '/')
$eu2Map = "-ffile-prefix-map=$eu2Root=. -fmacro-prefix-map=$eu2Root=."
cmake -S psxrecomp/recompiler -B build-eu-tools -G Ninja -DCMAKE_BUILD_TYPE=Release "-DCMAKE_C_FLAGS=$eu2Map" "-DCMAKE_CXX_FLAGS=$eu2Map"
cmake --build build-eu-tools --target psxrecomp-game psxrecomp-bios
build-eu-tools/psxrecomp-game.exe --config eu2/game.toml
python -I -B eu/seamless_catalog.py --variant eu2
python -I -B eu2/build_release.py
python -I -B eu2/build_aot.py --seamless --workers 3
python -I -B eu2/stage_release.py --runtime-toolchain "path/to/bundled/overlay_toolchain"
```

Configure the tools with Clang/clang++ and Ninja explicitly if these are not
your CMake defaults. Generate the redistributable OpenBIOS backend with the
framework's BIOS generator if its normal staleness check requires regeneration;
no Sony BIOS is needed. `build_release.py` disables debug tools, uses reproducible
source-prefix mappings and does not overwrite the manual prototype.

The final staging step needs the standard runtime fallback distribution
(embedded Python, TinyCC, headers/configurations and their notices). Obtain it
through the maintained framework packaging workflow, or supply an existing
clean compatible distribution. These are runtime dependencies; no system Python,
PowerShell or installed compiler is required by the player. Rebuilt recompiler
executables replace the cached copies when present. Keep their license notices.

All generated disc data, C code, caches and test cards stay outside Git and
outside this source handoff. Player staging is allowlisted and rejects personal
absolute paths, ROMs, Sony BIOS files, cards, logs and debug symbols.

## Implementation boundaries

- `eu2/prepare.py`: strict revision check and original selector/MAIN extraction.
- `eu2/build_aot.py`: maintained shared AOT pipeline, five original MAIN images,
  audited guarded native pairs; no speculative provenance bypass.
- `eu2/seamless-contract.json` and `seamless_profile.py`: five-language code/data
  contracts, exact instruction windows and shared-policy hash checks.
- Shared `eu/seamless/loader.c` and `src/mods/tomba_seamless_prepare.cpp` remain
  the implementations. EU2 supplies generated address/profile bindings and its
  own catalog/cache format; no second loader is maintained.
- `eu2/release`: relocatable launcher configuration and player instructions.
- UI patch: official Browse functions are unchanged. Only blank-card exclusive
  creation prevents accidental truncation of an existing card.
- `eu2/tests` and `tools/regional`: developer-only probes; never staged for players.

The original five MAINs are 0/5/6/7/8 (EN/ES/PT/SV/DA). Address mappings may
vary even between languages. The reference disassembly's EU1/EU2 MAIN/System
hash labels were found swapped; boot hashes and exact original bytes determine
identity. Do not treat a reference label or a constant regional offset as proof.

See `PC_MODS.md` for the feature matrix and `MANUAL_TESTS_DE.md` for pending
manual acceptance. See `TEST_REPORT.md` for evidence and explicit gaps, and `WIDESCREEN.md` for the
unimplemented renderer work. No Japanese implementation is included.

## Licensing

The game project and framework retain their existing licenses, including the
root PolyForm Noncommercial license; this work does not relicense upstream code.
The UI and bundled dependencies retain their respective notices. OpenBIOS is
freely licensed and explicitly approved for this local package. No Sony BIOS,
ROM image, generated original game source, personal card or source-control
history is supplied. Review licenses before any distribution.
