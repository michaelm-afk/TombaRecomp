# Re-staging byte-identical audited overlays tries to overwrite loaded DLLs

Project: PSXRecomp. File: `tools/aot_overlay_pipeline.py`, `stage()`.
Patch base: official master `958ae0e396f14d39c86e5c016d405fcdd96af4d5`.
Also source-confirmed at Tomba's pin
`03e635e86dceb540b7b6421ada7ee32cc28ca62b`.

## Reproduction

```sh
python test_overlay_staging.py /path/to/psxrecomp --work-dir /writable/test-dir
```

The test uses the actual `stage()` function, synthetic byte files and a valid
synthetic hash receipt. Stage once, then simulate Windows rejecting replacement
of a mapped DLL by making `shutil.copy2` raise `PermissionError`.

Expected: re-staging already identical audited artifacts succeeds without
replacement. Actual: every file is copied unconditionally and the otherwise
unnecessary write fails. A running native build on Windows can therefore
block a staging operation even when no DLL content changed.

## Fix and boundaries

`fix.patch` skips a copy only if the destination already has the **audited**
hash. Source verification remains before this decision; destination
verification remains after it. Missing or different artifacts must still be
copied, and unaudited extras remain rejected.

This does not make changed mapped DLLs replaceable and is not hot reloading.
Close the running program before staging a genuinely changed DLL. The added
destination hash read is extra staging I/O, not gameplay overhead.

Regression cases: identical locked targets succeed; changed locked targets
still fail; modified source artifacts fail audit before a write; extra files
are still rejected. No game data, native game module, BIOS or card is used.

No exact existing report found by searches for loaded DLLs, overlay staging
and related Clang/overlay results. [PR #456](https://github.com/RetroPortingToolKit/psxrecomp/pull/456)
appeared in a loaded-DLL text search but is about BIOS profiles, not this fix.

Reference: [current stage function](https://github.com/RetroPortingToolKit/psxrecomp/blob/958ae0e396f14d39c86e5c016d405fcdd96af4d5/tools/aot_overlay_pipeline.py).
