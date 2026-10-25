# Japan port handoff status

The original Japanese SLPS-01144 boot program and all 24 SYSTEM code images
are translated through the existing framework. Native overlay dispatch remains
guarded by the original bytes. Unsupported or invalidated code can use the
existing interpreter fallback; complete static execution coverage is not claimed.

The initial prototype was manually confirmed to boot, display Japanese text,
accept controller input, and save and load. On 2026-10-24 the owner played the
enhanced build (Widescreen and Seamless Loading on; the checklist included the
first-house transition and return) and accepted it for merge. These
confirmations do not establish completion of the entire game. The original Japanese title menu includes English labels;
the Japanese in-game menus differ from the western releases by design.

## Reviewed native boundaries

`overlay-contracts.json` pins whole-file SHA-256 values and the final data
intervals described by byte-matching Japanese psx_tomba profiles, reference
revision fb3b36715f6966c099be95564c155bd842003b76. In these intervals the native
producer must not discover random data as instructions. Original byte guards
and the interpreter fallback remain active. In particular X02 previously
discovered unsupported words in its documented data tail. This is a producer
boundary correction, not a replacement or patch to the disc.

## Deferred regional bindings

Geometry Optimization: Japanese candidate routines differ substantially in
argument register use, packet lengths, and packet layout. Shared western HLE
functions are not an established match. Bindings need verified entry/end
addresses, original-byte signatures, and differential coverage of registers,
packet memory, return behavior, and unsupported cases. Until then the original
MIPS path runs (same output, slower); tracked as beads-eio.4.35.

Seamless Loading RC2: the unchanged common EU batch loader is generated with
original-byte-checked Japanese bindings by `jp/seamless_profile.py`. The shared
catalog and C++ preparation path verify 1054 resources and 638 GAM files. Atomic
batch, VRAM/WVD, MAIN protection, hash rejection, original-loader fallback and
codec output/final-bit-state fixtures pass. Ordinary original New Game, Japanese
dialogs, walk/jump/land and audio pass with the loader active. No script timer,
original state or NTSC clock is rewritten. Streaming movies stay original.
After the owner's 2026-10-24 playtest with the loader active it defaults ON,
like the USA release.

FMV Skip RC2: the shared western plugin is reused without code changes. All 22
Japanese descriptor pointers, real STR sector headers and original frame totals
are checked; the Japanese table is 0x80071D3C and movie byte is 0x1F8001CD.
Original teardown/comparison code passes 22 isolated MIPS ON/OFF tests. Original
New Game also passes with the plugin active. These isolated tests do not prove
full-game event progression. Default OFF, like the USA release.

Widescreen: `jp/widescreen_profile.py` binds the common renderer to the Japanese
MAIN (HUD callgraph, area 0/1 hooks, sprite tagging) against the reviewed
`jp/widescreen-contract.json`, and `jp/pc.toml` carries the Japanese culling
sites. It is part of the enhanced build (`--enhancements`) and defaults OFF, like
the USA release. Checked: 16:9 first-area acceptance (426x224 view, corner HUD)
and the owner's 2026-10-24 playtest; other areas are covered by ordinary play.

Launcher localization is a separate project. This port preserves original game
resources and uses the existing English launcher and official memory-card picker.

Hybrid Controller: Japanese vblank 0x80016994 calls PadRead at 0x80064B74,
which uses BIOS B0:0x16 and legacy buffer 0x8009DDB0. The western direct-pad
analog parsing contract is absent from this path. Reusing the western dynamic
pad presentation previously timed out before New Game. The game reads a digital
pad only, so the western analog/digital switch has nothing to switch: the host
folds the left stick onto the D-pad for a digital pad, and stick and D-pad both
move Tomba (`jp/acceptance.py --stick-check`). No Hybrid Controller mod is
offered or needed. See `RC2_MOD_REVIEW_EN.md` for evidence.

## Manual acceptance

Owner acceptance of the enhanced build: 2026-10-24. For later candidates:
use only a new card or a copy of an existing card. Load the Japanese save, cross
one ordinary area boundary, return, and check graphics, text, controls and audio.
Save normally, exit, restart using the common launcher, and load again. Report
both area names and any visual/audio or progression problems. The prototype's
save/load confirmation need not be repeated solely to restate the old result;
this final pass checks the expanded native overlay build.
