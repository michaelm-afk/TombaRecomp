# Common European launcher integration

This handoff contains committed source patches against the exact upstream bases in SOURCE_BASES.json. Apply each patch in its recorded apply_in repository after recursively initializing pinned dependencies. No unpublished Git ref is required; patches deliberately exclude submodule gitlinks. Commit the UI/framework changes in your own integration repositories and update your gitlinks accordingly.

## Build from source

Windows x64 Clang/clang++, CMake, Ninja and Python 3.11+ are build prerequisites. Set TOMBI_TOOLCHAIN_BIN if needed. Supply legal original raw single-data-track SCES-01330 Rev 1 and SCES-01331 CUE/BIN inputs. The recorded size/hash pairs are in europe/regional-launch.toml. A clean standard framework runtime fallback toolchain (embedded Python, TinyCC, includes/configs and notices) is required for packaging; obtain it through the existing upstream packaging workflow or a compatible clean distribution. OpenBIOS is allowed; Sony BIOS/ROM/save data is excluded.

```powershell
python -I -B europe/build.py --eu1-disc "path/to/EU1.cue" --eu2-disc "path/to/EU2.cue" --runtime-toolchain "path/to/overlay_toolchain"
```

Optional --webp-source points to the pinned local libwebp source dependency. The build reconstructs original boot programs, catalogs and guarded native caches and compiles both native backends. Output: dist/TombiRecomp-Europe-Windows-x64. --reuse-native-from is an optional build optimization: source inventories are regenerated and every reused native pair is re-audited by the rebuilt compiler; old receipts alone are not trusted.

## Framework and UI changes

runtime/include/regional_launch.h owns the optional generic profile catalog, serial+complete-track SHA-256 verification, last-disc record and direct Windows process handoff. Without regional-launch.toml the normal runtime remains unchanged. main.cpp invokes routing before config/SDL setup and delegates preboot disc changes from its existing verification callback. No native game routine, renderer or loader is replaced by routing.

The UI bridge adds a profile_handoff verdict field and one result code. The existing model requests a normal close for that verdict; the C API returns without writing outgoing-region edits or the foreign disc into its settings. The host joins its preparation worker, closes SDL, and starts the selected existing backend. The official picker functions in launcher_imgui.cpp and launcher_files.c/h remain byte-identical to the recorded official base. The earlier independent blank-card formatter safety change refuses to truncate an existing card.

All paths in the shipped profile catalog are package-relative and checked to stay inside it. Full disc contents are hashed; there is no persistent trusted fingerprint cache. A stale last-disc record can be replaced by another selection. In-game region handoff is disabled. Unsupported discs and missing backends fail closed; normal EU1/EU2 game-side validation remains in force. Pending edits are discarded on profile handoff to avoid cross-region state leakage; see DISC_SELECTION_EN.md.

## Tests and remaining limits

RC2 fixes working-directory contamination of regional game.toml resolution. See RC2_DISC_VERIFICATION.md for the fresh-ZIP reproduction and why the previous routing coverage missed it. Run `python europe/tests/launcher_verification.py --archive <Windows-ZIP> --name <new-test-folder>` against the delivered ZIP and legal local discs. This uses the packaged production launcher callback after configuration and real process handoffs without opening a window. `europe/tests/portable.py` additionally boots both packaged backends with package-root cwd.

See TEST_REPORT.json, FEATURES.md and MANUAL_TESTS_DE.md. europe/tests/routing.py tests both real backends and handoff directions without desktop actions, including spaces in paths, corrupted same-size images and persistence/isolation. The model and SIO/card fixtures are in europe/tests. eu2/smoke.py accepts --region eu1/eu2 for original MAIN identity, native-dispatch and Seamless checks. Original language selectors and regional backends are retained.

The isolated verification rebuilds the recompiler and both player runtimes from the three exact reconstructed bases. Previously proved original native modules may be reused only after regenerating inventories and auditing every pair, avoiding unnecessary repeat compilation. Original EU2 geometry/PGXP and decoder evidence is retained. No full campaign, physical controller, exhaustive audio, all area/save transitions or new GUI acceptance is claimed. EU2 FMV and widescreen bindings remain explicitly unimplemented and hidden; their exact follow-up contracts accompany this handoff.

All work is local. No publication, push or PR has occurred. Existing original ROMs, official packages, personal cards and earlier delivery archives remain preserved.
