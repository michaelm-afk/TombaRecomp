# Japan native port (SLPS-01144)

Uses the existing framework and launcher, with no US/EU runtime source changes.
Original raw track: 289430064 bytes, SHA256
`fb5b8ea9e3bd328e88a6b8b8ecb0b493d0dda5a9b5f732a7a6e4c9b146d9cd2b`.
Boot SHA1: `07d577698ad31ec1a69b9d7b80a7c3f90b650888`.
Seeds are the pinned byte-matched Japan reference function addresses plus entry.
Boot loads at 0x80010000, entry 0x80065D80, GP initialized by original code to
0x8009DAC8. Overlay destination 0x800E9AF8 is checked at original loader words
0x8002025C/60. No US/PAL function hooks are registered.

Use Windows Clang/CMake/Ninja on PATH (or TOMBI_TOOLCHAIN_BIN) and Python 3.11+.
The existing `build-eu-tools/psxrecomp-game.exe` must match the framework checkout.
The player uses the existing OpenBIOS source/backend workflow.

Release builds and packages use the same entry points as every other region:

```
python -I -B tools/build_regions.py --region jp --jp-disc path/to/Japan.cue
python -I -B tools/package_regions.py --region jp
```

The steps it runs (also usable directly for development):

```
python -I -B jp/build.py --enhancements --player --disc path/to/Japan.cue
python -I -B jp/build_aot.py --config jp/pc.toml --all-areas --flavor 2 --work-dir build-jp/rc2/aot --destination build-jp/rc2/player/native
```

`build.py --webp-source <directory>` accepts a pinned libwebp source tree;
the default reuses the existing local dependency cache. Build the shared
`psxrecomp-game` and `psxrecomp-bios` tools into `build-eu-tools` first and run
the canonical `psxrecomp/runtime/hash_codegen.cmake` hash-header generator.
All 24 Japanese SYSTEM code files now pass both native flavors' audits:
7,277 manifest rows per flavor. Reviewed, hash-checked data tails resolve the
earlier X02 discovery failure. This is not proof of complete static execution.
Runtime gaps retain the standard guarded native-cache/interpreter fallback.

QA uses `jp/probe.py --name new-test-folder --hold 600`; the local debug endpoint
is only present in the private QA executable. Tests permit ordinary controller
input, RAM/status reads and internal framebuffer captures, never RAM writes,
state injection, forced inventory/quests or desktop automation. Each run creates
fresh isolated cards. Do not access a port belonging to another test process.

Reproducible first-area acceptance (fresh normal New Game and controller inputs):
`python -I -B jp/acceptance.py --name new-opengl-test --opengl`.
The OpenGL test uses the existing hidden rendering context, not desktop actions.
Add `--pgxp` for the validated precision path. The default checks PGXP off.
`python -I -B jp/package_test.py --package <stage-or-zip> --name <new-folder> --all-regions`
checks all four real launcher callbacks and production Japan/USA boot without
developer tools. `jp/test_codec.py` needs Unicorn 2.1.4 and compares 638 assets
against the Japanese decoder's original MIPS instructions, not another port.
`--view 16:9` (enhanced build) checks the widescreen renderer, `--stick-check`
checks left-stick movement through the host input layer, and `--try-roundtrip`
attempts the first-house transition (a bounded route; manual play is decisive).
Saving/loading was confirmed manually on the prototype; the owner played and
accepted the enhanced build on 2026-10-24.

The new common package reuses both exact EU-RC2 executable files. The generic
regional catalog supports all four profiles; no launcher UI fork is needed.
Japan config/cards live under backends/SLPS-01144. Launcher localization remains
a separate task. `jp/rebuild.py --handoff <directory> --name <new-folder>`
reconstructs the recorded upstream bases and patches, rebuilds the compiler and
Japanese player, then re-audits reused native pairs against freshly extracted
original bytes. See PORT_STATUS_EN.md for deferred regional bindings.
The staging script expects the independently verified EU RC2 base, new USA host
and original-disc-audited USA cache; it never uses a played installation.

## Enhanced build (release)

Use `jp/build.py --enhancements --disc <cue>` and the corresponding `--player`
build, with `jp/build_aot.py --config jp/pc.toml --all-areas --flavor 2`.
It uses `jp/pc.toml`, `build-jp/rc2` and a separate audited native tag, and
carries Seamless Loading (default on, like USA), FMV Skip (default off) and
Widescreen (default off). The shared EU loader, FMV plugin and widescreen
renderer use checked Japanese profiles; see FEATURES_EN.md.
For the isolated rebuild add `--enhancements` to `jp/rebuild.py`.
The owner save before the hut was located and copied privately. Original hashes
are unchanged.
