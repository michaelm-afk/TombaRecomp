# Common European build

The common launcher selects the native backend for SCES-01330 Rev 1 or
SCES-01331 using the serial, exact raw size and complete SHA-256 in
[the regional catalog](regional-launch.toml). EU1/EU2 mean language groups of
the first Tombi! game. [Current EU2 status](../eu2/README.md) distinguishes
implemented source from runtime/release qualification.

## Build and stage

Use Windows x64 Clang, CMake, Ninja, Python 3.11+ and initialized pinned
submodules. Set TOMBI_TOOLCHAIN_BIN as needed. Keep temporary files,
compiler caches, profiles and output on non-C: storage.

    python -I -B europe/build.py --eu1-disc "path/to/EU1.cue" --eu2-disc "path/to/EU2.cue" --runtime-toolchain "path/to/overlay_toolchain"

The clean runtime fallback toolchain comes from the framework's existing
packaging workflow; it supplies embedded Python, TinyCC and required notices.
Optional --webp-source selects a local pinned dependency source.

The build verifies original inputs, regenerates boot code, catalogs and AOT
inventories, builds both backends and stages dist/TombiRecomp-Europe-Windows-x64.
Native reuse is permitted only after re-auditing every pair against the
current compiler/configuration. EU2's old non-wide cache fails that check;
rebuild its MAIN and area modules for the new Widescreen configuration.

Separate USA/EU1/EU2 candidates can also be built with --region all through
tools/build_regions.py and packaged with tools/package_regions.py.
The EU2 archive/folder explicitly includes SCES01331. Both catalogs exclude
CD Speed and host-paced Fast Loading.

## Routing and isolation

The optional framework catalog routes before SDL/config initialization.
Changing region before Play closes the current launcher, discards outgoing
edits, joins preparation, and starts the selected backend. Relative runtime
paths resolve beside that executable, and a regional backend must own its
adjacent game.toml. Unsupported discs and missing backends fail closed.

Regional card paths stay separate. The shared picker remains in use; New
creates a card exclusively and never truncates an existing card. In-game
region handoff and cross-region card conversion are not offered.

## Qualification

After a fresh combined package is built, use europe/tests/launcher_verification.py
for the real configured Play-gate callback from package-root, other-backend
and neutral working directories. Routing tests exercise both process handoff
directions, remembered selection, missing backends and corrupt inputs.

The source-level profile model, new-card preservation and separate-card I/O
fixtures pass. USA and EU1 rebuilds pass opening movement/native loading and
adaptive resizing. EU2's original-MAIN bindings pass static fixtures; its
fresh full player/AOT build, launcher routing and sampled English/Spanish
gameplay still require the exact SCES-01331 disc.

See [the integration audit](../audit_notes/tombi-eu2-rc2-20261022.json).
Earlier RC2 results under eu2/handoff and docs/regional remain historical
developer evidence. Full campaign, every area/save transition, exhaustive
controller/audio and EU2 FMV teardown are outside the current qualification.
