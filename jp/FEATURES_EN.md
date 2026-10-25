# Regional feature scope

| Feature | USA | EU1 | EU2 | Japan |
| --- | --- | --- | --- | --- |
| Common launcher and checked regional routing | Yes | Yes | Yes | Yes |
| Original game languages | English | Five original languages | Five original languages | Japanese |
| Separate settings and default cards | Yes | Yes | Yes | Yes |
| Native boot / guarded overlay fallback | Yes | Yes | Yes | Yes, 24 precompiled images |
| Normal controller, audio, Fast Forward | Shared implementation | Shared implementation | Shared implementation | Shared implementation; physical-device check remains manual |
| Seamless Loading | Existing | Existing | Existing | Shared loader with checked Japanese profile; default on, like USA |
| Geometry Optimization | Existing | Existing | Existing | Not yet: original MIPS path (same output, slower); Japanese packet ABI differs, tracked as beads-eio.4.35 |
| PGXP Precision | Existing framework support | Existing | Existing | Verified in ordinary gameplay; off by default |
| Hybrid Controller | Existing | Existing | Existing | Not needed: the original driver is digital-only, and the left stick folds onto the D-pad (stick and D-pad both move Tomba) |
| HD Texture Packs | External matching pack | External matching pack | External matching pack | Shared renderer; Japanese-target installer fixtures passed |
| Bezel Artwork | External image | External image | External image | Shared renderer; external image |
| FMV Skip | Existing, default off | Existing, default off | Hidden | 22 checked original movie bindings; default off |
| Widescreen renderer | Existing, default off | Existing, default off | Hidden | Checked shared-renderer adapter; default off |

The unchanged EU backends retain their previous defaults and test results.
Japanese defaults preserve the prototype baseline (native scale, digital pad,
original SPU path, NTSC-J, windowed OpenGL, VSync off). Mod defaults match
USA: Seamless Loading on, the other optional mods off. Existing user settings
always take precedence. The launcher retains the official memory-card Browse
implementation.

Owner-confirmed Japanese prototype results include boot, controls, Japanese
text/menus and saving/loading. On 2026-10-24 the owner played the enhanced build
(Widescreen and Seamless Loading on) and accepted it. Automated checks on current
psxrecomp master pass original New Game, walk/jump/land, left-stick movement,
audio, native overlay dispatch and 16:9 widescreen (`jp/acceptance.py
--stick-check --view 16:9`). Campaign-wide play remains open.
