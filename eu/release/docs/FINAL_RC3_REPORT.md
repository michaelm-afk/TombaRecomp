# RC3 final handoff report

## Scope and owner acceptance

SCES-01330 Europe Rev 1 only; English, French, German, Italian and Dutch.
No second EU disc, 60-Hz mode, interpolation or new audio engine. VSync OFF,
Geometry HLE and Seamless ON, Skip FMV and external texture support OFF by
default. No uploads, issues, PRs or messages to developers were made.

The owner's latest RC2 run recognized the Razer Raiju V3 Pro, with the shared
Analog/Digital behavior already documented. PGXP and FMV-Skip were enabled at
1080p; ordinary play reached the hut, felt smooth and had no controller failure.
Earlier earned-save and later Elder progress evidence are retained, not rerun.

## Startup phase measurements

Seconds from isolated headless processes, same physical host and owned discs.
Application-cold means fresh application caches, not a rebooted OS or cold GPU.
Rows are individual observations, not statistical guarantees. The marker is
before guest execution, not the first visible gameplay image. The first UI
swap was measured separately during RC2 and is not reinterpreted here.

| Phase | EU RC2 first / warm | EU RC3 first / warm | Existing US first / warm |
|---|---:|---:|---:|
| Before guest execution | 4.647 / 2.394 | 3.571 / 1.067 | 1.368 / 1.330 |
| Overlay worker | 2.317 / 0.020 | 2.307 / 0.022 | 0.002 / 0.002 |
| Complete disc SHA-256 | 1.385 / 1.423 | 0.424 / 0.433 | 0.826 / 0.824 |
| Seamless activation | 0.829 / 0.869 | 0.540 / 0.534 | 0.415 / 0.414 |

Nested phases overlap; do not sum parent scopes and child scopes. The overlay
worker is already asynchronous while the launcher is shown. This headless run
joins it immediately. Its first sweep stays enabled and later uses the existing
ABI memo. No new code compilation was observed in these samples. The EU BIN is
492,370,032 bytes versus 280,193,760 for US, explaining much of the old full-hash
cost. Native hashing improves this shared component without skipping bytes or
weakening cache verification. Initial overlay verification was not bypassed.

Native SHA equals the unchanged portable algorithm for boundary/fragmentation
fixtures and reproduces the owned EU BIN's expected SHA-256. The mod-runtime and
resident-resource regression suites pass, including corrupt packs and stock
resource verification. Windows API failure/non-Windows retains the old path.
No extra external runtime package or administrator installation is required.

## Small US/EU movement comparison

Fresh regular new games, controller commands only, private cards and native
builds. No quest/item/RAM writes and no debug states loaded. Both versions
settled at area 0/0, position (64,-52,0), health 4, idle. The initial control
window precedes an original scripted intro: an early capture without movement
was discarded. The final capture waited for actual stable player control.

Matched deterministic input: Right 12 updates, release 30; then a full jump
held 30 updates and release 100. Frame-indexed inputs deliberately test whether
the same update sequence produces the same displacement; the durations below
are converted to seconds using the versions' original nominal video cadence.
They are not compared as equal-duration button holds.

| Observation | EU PAL | US NTSC |
|---|---:|---:|
| Right input duration | 0.2400 s | 0.2002 s |
| Right + release sequence duration | 0.8400 s | 0.7007 s |
| Final X displacement | 10.94140625 world units | 10.94140625 world units |
| Final position | (74.94140625,-50,0) | (74.94140625,-50,0) |
| Full-jump observed height | 76 world units | 76 world units |
| Airborne time, conservative sampled bounds | 1.00-1.22 s | 0.834-1.051 s |
| Whole probe real execution incl. startup/intro | 127.205 s | 29.326 s |

The equal movement per update supports slower PAL progression in this limited
walking/jumping case, approximately the 50/59.94 cadence ratio (about 16.6%
slower / 19.9% longer), rather than complete PAL compensation. The broad jump
bounds come from asynchronous reads bracketed by frame queries, not an exact
landing trace. An earlier equal-time short-hold jump reached different heights;
variable button-hold duration and unequal endpoints make it unsuitable for a
universal speed ratio. The final full-jump starts at exactly matching positions.

Headless CPU throughput, turbo during the intro, and synchronous diagnostic
reads make real probe duration unsuitable as an original-speed stopwatch.
No audio, enemy or event-timer equivalence is claimed. No timing or physics
change was made. This result does not justify blindly changing EU to 60 Hz.
The replayable controller sequence and private samples are retained locally.

## External texture support

OFF by default; no HD graphics bundled. Missing/empty pack: No texture pack
installed, neutral. Select Texture Pack Folder accepts a pack or shallow
wrapper folder. Valid supported images and an EU target declaration produce
Installed in green; the feature can then be enabled. Invalid/incomplete or
US-only packages are refused, and activation validates again on Play.

The US checkerboard example was rejected. Synthetic EU fixtures validate the
installer, not real EU asset coverage. Target declaration plus valid images
cannot prove that the author supplied correct keys or complete translated
artwork. Missing texture matches retain originals. No full EU HD pack has
been qualified. See HD_TEXTURE_PACKS.md for metadata and authoring details.

## Remaining owner acceptance

Test the exact RC3 launcher folder picker/status, launch a regular save, and
confirm expected controller operation and saved settings. Existing cards and
builds remain separate; the candidate's manual folder contains copies only.
No extensive campaign replay is required for this handoff. Broader gameplay
coverage remains owner-led. Developer source patches require review before
upstream integration; this is a local candidate, not an official release.

## Final RC3 package checks

The exact player package passed relocation to a path containing spaces and a
foreign working directory, no-disc error handling, guarded PAL own-disc boot,
a fresh launcher process smoke, and bundled-Python startup with system-only
PATH. All 103 PE files had no unresolved non-system imports. The original BIN
hash remained unchanged. These are process/configuration checks, not visual
acceptance of the new picker. Full-runtime and resident tests use synthetic
fixture discs, not modified player progress.

## Incremental maintainability check

The prior CODE_SIZE_AUDIT remains the US/EU baseline; it was not rerun. Relative
to RC2, the shared framework adds 233 runtime/header lines and removes 3 (net
230), plus 9 build lines and a 5-line test-only stb implementation. Launcher
adds 3 lines. The two new shared runtime helpers total 156 lines: native SHA-256
and read-only texture installation. No game-address hook or generated overlay
was added for these changes. The player EXE increased by 77,312 bytes (about
75.5 KiB); the existing 66 AOT pairs were reused. Tests/research scripts remain
outside the player package. No feature was removed to reduce size, no extra
mod manager was introduced, and no extras.cpp glue was added.
