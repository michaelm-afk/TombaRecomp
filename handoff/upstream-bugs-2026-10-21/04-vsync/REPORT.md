# Tomba's pinned framework does not round-trip the launcher VSync row

Project: TombaRecomp dependency integration / PSXRecomp startup launcher.
Affected source: Tomba v0.20.2-alpha / master
`1b7bafa5afc3dfd08a4889f2361f9a177e6b0f52`, pinning framework
`03e635e86dceb540b7b6421ada7ee32cc28ca62b`, `runtime/src/main.cpp`.

**Already fixed in official framework master:**
[PR #605](https://github.com/RetroPortingToolKit/psxrecomp/pull/605), merged
2026-10-10 as `5a6527acc194890b4d369cb2e605e003e968c5d6`. The checked current
master contains its startup wiring. Do not open a duplicate framework report
claiming that startup persistence is still absent there. Commit dates alone
do not establish feature inclusion: the actual Tomba-pinned file was checked.

## Reproduction

1. Use a build from the affected pin and its existing launcher.
2. Choose VSync Off, Play, quit normally, then restart the launcher.
3. Inspect the separate user `settings.toml` and reopen the VSync row.

Expected: Off persists and requests immediate swaps; On and Adaptive also
round-trip. Actual in the affected integration: the row returns to On; its
choice is not copied into the runtime/user-settings layer. This was manually
reported during EU testing, and the same host wiring is absent from the US pin.
The parser/writer themselves already support the setting.

The launcher encodes On/Off/Adaptive as 1/2/3; the runtime uses 1/0/-1.
Config-only VRR=2 must survive an unchanged row. `fix.patch` adapts the two
startup mapping blocks from the existing upstream fix to this exact old pin.
Prefer integrating the existing fix, rather than treating our EU work as its
origin. A wholesale pin update also requires unrelated ABI/cache qualification.

## Regression checks

Follow `tests.md` for a three-mode launcher restart matrix, unchanged VRR
preservation and actual swap-interval checks. Existing
`recompiler/tests/video_enhancement_settings_test.cpp` checks serialization,
but serialization alone cannot catch a missing UI-to-host bridge.

This report does not establish that requested VSync always controls physical
scanout: driver overrides, VRR and compositor behavior remain separate.
[Tomba PR #45](https://github.com/mstan/TombaRecomp/pull/45) and
[framework PR #699](https://github.com/RetroPortingToolKit/psxrecomp/pull/699)
address high-refresh tearing/cadence, not the missing settings bridge.
