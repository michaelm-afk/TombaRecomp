# US and EU Windows build candidates

The EU RC4 handoff has been imported on `integrate/tombi-eu-rc4-20261021`
against its exact game/framework/UI bases. The existing US target remains
at the project root; the separate EU target is in `eu/`. This is an integration
candidate, not a validated feature-parity release.

## Disc inputs

US requires SCUS-94236. EU currently requires **SCES-01330, Europe
(En,Fr,De,It,Nl), Rev 1**, raw single-track BIN/CUE:

- BIN size: `492370032` bytes.
- BIN SHA-1: `2505d958b4439d04844cadd3f968fc7432a48e00`.

SCES-01331 (En,Es,Pt,Sv,Da) is a different release. The supplied copy has SHA-1
`ec50074b6fd98f611bae11e3de68d6e76ffdd6d4` and boots `SCES_013.31`.
It cannot be substituted by renaming files or weakening the identity check.
Its support would require additional boot, language, loader and geometry profiles.

The subsequently supplied `Tombi.zip` has SCES-01330, but a different gameplay
code revision: BIN size `492306528`, SHA-1
`48833672d22ddbafe8c3e904dd3aa013a280e1ee`. Its boot program and the eight checked
selector instructions match the handoff exactly; all three expected geometry
function hashes differ in each of the five profiled MAIN executables. It is
also rejected. Matching a boot serial alone is insufficient to select HLE hooks.

Original game data, generated C, native caches and cards remain local/ignored.

## Common entry point

Use Python 3.11+, initialized pinned submodules, CMake, Ninja, Git Bash and a
Windows Clang toolchain. `TOMBI_TOOLCHAIN_BIN` or `--toolchain-bin` selects its
bin directory. Keep this checkout on a bulk-output drive: EU generation helpers
currently place their output in project-relative ignored build directories.

```powershell
python -I -B tools/build_regions.py --region both --plan
python -I -B tools/build_regions.py --region eu --eu-disc 'G:/owned/Tombi.cue' --check
python -I -B tools/build_regions.py --region both --us-disc 'F:/owned/Tomba.cue' --eu-disc 'G:/owned/Tombi.cue' --jobs 3
```

`--plan` prints the commands without writing. `--check` verifies all selected
disc hashes and developer prerequisites without copying or building. A real
build copies verified inputs into ignored `disc/`, refuses conflicting existing
inputs, redirects process temporary/cache directories to `build-regions/temp`,
and stops on the first failed command. Builds run serially.
Raw `.img` files and equivalent CUE spellings (`TRACK 1` or `TRACK 01`) are
accepted under the same exact data-track hash checks.

The entry point builds shared emitters and OpenBIOS, then selected native
executables and original-disc AOT caches. EU baseline codegen completes before
overlay compilation. EU AOT defaults to `full`, enumerating the configured area
and support images; `--eu-aot-scope opening` reproduces the handoff's narrower
scope. The native entry-hook audit uses the same selected inventory.
Image enumeration and byte guards do not establish full native execution coverage.

US outputs are in `build-regions/us/`. EU retains its documented
`build-eu-prototype`, `build-eu-seamless` and `build-eu-release-final` layouts.
For portable packaging, follow `eu/release/docs/DEVELOPER.md` and the existing
US packager. This entry point builds candidates; it does not publish or launch.
`--qa` builds a separate EU debug-tools executable under `build-eu-qa/native`;
the EU packager rejects debug-tools builds. The bounded test entry point is
`python -I -B eu/tests/test_sampled_gameplay.py`, which samples English and
German with selector changes, fresh cards, read-only RAM observations, real
controller input, native-cache counters, screenshots and muted host audio.
The final candidate builder installs the audited cache beside its executable
and stages its relative game config/seeds. The sampler requires successful
native module loads and actual native dispatches with compilation disabled.
For original-routine comparisons, run this after generating the hook cache:

```powershell
python -I -B eu/build_release.py --debug-tools --geometry-validation --build-dir build-eu-qa/native
python -I -B eu/tests/test_sampled_gameplay.py
```

## Parity assessment and remaining validation

| Feature | EU handoff | Remaining work |
| --- | --- | --- |
| Seamless Loading | Default-on guarded resident loader and original-disc catalog | Validate current integration and fallback on sampled routes |
| Geometry HLE | PAL adapter reuses shared implementation; original-body guards | Recheck sampled language execution and reference comparisons |
| AOT overlays | Build/audit/staging helpers; reported RC4 cache used opening scope | Generate full inventory and exercise representative native transitions |
| recomp-ui, controller, FMV policy | Shared UI and address-free policies; EU-specific manifests/metadata | Focused launcher and gameplay smoke tests |
| Adaptive widescreen | Deliberately excluded; 4:3 only | Port EU camera/projection/culling, entity residency, backgrounds and HUD hooks |
| Native PAL speed | 50 Hz retained | Keep the regional baseline; 60 Hz was excluded |
| Frame interpolation | Deliberately excluded | Separate feature work; US frame blending was also retired |
| Other host platforms | EU helpers target Windows x64 and DLL caches | Adapt build/tool paths, native-module namespaces and packaging for other platforms |

The handoff supplies source patches and dependency identities, not game code
or a disc. Its documents report prior author/owner tests; those are not new
validation of this integration. The outer downloaded ZIP hash differs from the
original archive manifest, but all 67 internal SHA-256 entries passed.

Owner-directed gameplay sampling: English and German, including a language
switch during testing. Cover normal loading and Seamless Loading, representative
AOT transitions with runtime compilation disabled, geometry, FMV audio/sync,
movement and original Memory Card save/restart/load. For a future widescreen
port, also vary the window aspect and check real margin content, entity
visibility, HUD and return to 4:3. Do not create an exhaustive language matrix.

The subsequently supplied `Tombi_EUR_SCES01330_H.zip` contains `TOMBI.img` with
the exact supported data-track SHA-1, boot program and geometry contracts.
No more disc input is needed for SCES-01330 Rev 1. Local compilation and
sampled testing use this image; the original archive remains unchanged.
The earlier SCES-01331 and alternate SCES-01330 dumps remain unsupported.

Focused local checks passed: all 22 EU/build-entry Python sources parsed;
US/EU/both plans rendered with baseline-before-AOT ordering; both disc
verifiers rejected SCES-01331 without extracting project game code; real
overlay export/staging regressions passed; controller, FMV, fractional
fast-forward, VSync and CD/XA shadow regressions compiled and passed; native
and explicitly disabled-native SHA-256 tests both compiled and passed.
No audio device or game process was opened by these checks.

## Current local results

The shared emitters, baseline EU executable and private QA executable rebuilt
successfully. Opening-scope AOT produced **66 audited native pairs and 15,440
guarded entries** from 54 original-disc recipes. All pairs and byte guards
passed; full static execution coverage is not proven.

English and German each passed original-MAIN identity, selector changes,
stationary-to-walk input and a jump. Both executed three prebuilt native modules
with runtime compilation disabled (over 18 million native dispatches per run),
prepared 2,257 verified resident files, and completed four seamless batches
covering 19 files during the opening. In each language, all three geometry
routines matched the original over 200 isolated batches apiece: **1,200 matched
batches total**. Captured native gameplay images were inspected.

The loader unit fixture additionally passed atomicity, memory/range guards,
fallback handling and protected card-menu/internal-wait checks. These synthetic
checks do not establish an in-game Memory Card save/restart/load roundtrip.
No exhaustive five-language gameplay matrix was run.

See the [machine-readable audit](../audit_notes/tombi-eu-integration-20261021.json).
Full campaign/area roundtrips, full-scope AOT execution, physical controllers,
FMV synchronization, in-game card persistence and non-Windows packaging remain
unverified in this integration. Adaptive widescreen is not implemented.
