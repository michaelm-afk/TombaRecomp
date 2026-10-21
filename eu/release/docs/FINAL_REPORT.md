# Final candidate - TombiRecomp EU 0.1.0-eu-rc4

Local Windows x64 handoff, 2026-10-22. Nothing published, uploaded, submitted or
sent to developers. Owner RC4 acceptance: German and French tested successfully,
Seamless Loading working and prerendered cutscenes correctly synchronized. This final
candidate preserves the existing five-language SCES-01330 EU-only target.

## Finished functions

- Original EU English/French/German/Italian/Dutch programs, menus, fonts,
  dialogue and quest layouts; explicit original language confirmation.
- Guarded EU Seamless Loading and Geometry HLE, shared OpenGL presentation,
  controller settings, optional Hybrid policy, partial perspective correction,
  original Memory Cards and FMV-Skip. Host fractional Fast Forward remains.
- VSync OFF, Seamless/Geometry/HQ-SPU ON, FMV-Skip/external HD textures OFF by
  default. True widescreen/interpolation and unqualified pipeline controls stay
  hidden. Texture support states clearly that no HD graphics are supplied.
- Faster complete Windows SHA-256 checks with portable fallback. RC3 measured
  warm pre-guest startup 1.07 s versus 2.39 s before the optimization; no repeat
  timing campaign was needed for the audio-only correction.
- HD folder selection, declared EU-target/format/image validation, neutral
  missing status and green Installed status. US checkerboard example refused.
  Installed is not proof of complete artwork coverage. No complete EU pack
  has been qualified or bundled.

## Wise Man FMV audio correction

The owner identified the affected scene as a prerendered film. In the shared
HQ mixer, previously proven voice-only output could replace canonical CD/XA
samples while the slow verifier accumulated failures. The existing session log
contains the corresponding eventual zero-ratio fallback. The standalone
synthetic test fails on the first CD block with RC3 code, then passes after the
fix. CD input now selects the full canonical mix immediately. Voice proof is
invalidated and earned again after CD input is disabled.

No video wait, stream time stretch, scene-specific RAM write or queue flush.
The existing 180-ms host buffer stays: its documented reserve covers measured
streamed-stage stalls around 140 ms. Reducing it blindly would risk gaps.
Ordinary host/device/display latency still exists; this fix removes unsupported
HQ substitution, not all end-to-end latency. The owner confirmed correctly
synchronized cutscenes in RC4; this is manual acceptance, separate from the
synthetic regression. No artificial campaign state was used as acceptance.
Games leaving CD enabled without audio conservatively retain canonical mixing.

Read-only original-disc inspection found the Wise Man STR video at relative
sector 0 and XA sectors first at relative sector 7, then 15 and 23, in EU and US.
This shared authored interleave is not evidence of an EU-only late stream start.
No original audio, frame, disc sector, screenshot or private log is distributed.

## Two optional requests deliberately closed without implementation

Steam: use STEAM.md and Valve's manual workflow. No verified low-cost automatic
registration path was established, so no Steam files are modified and no fake
Add to Steam button is offered.

Hold Circle for scripted scenes: recognizing a one-second hold is small
(roughly 0.5-1 h), but safe skipping is not. Scripted player state also covers
respawn, reading signs and item sequences. Scripts contain object cleanup,
quest changes and area transitions; jumping to an end state can omit side
effects. A restricted scene-aware prototype would likely take 8-16 h plus
scene coverage; a reliable broad implementation about 24-40+ h. No general
original skip path was established. Excluded from this release, independently
of existing movie-only FMV-Skip. Short Circle presses are unchanged.

## Verification and handoff boundaries

- Real shadow mixer/verifier synthetic regression: supported voice proof and
  level, first/repeated CD-block byte preservation, new proof after CD, mismatch
  fallback and disabled byte equality. Before-fix failure retained locally.
- Five original MAIN/loader/geometry contracts are verified during the build;
  no address, overlay catalog or save format was changed for this correction.
- Previous short five-language area/geometry, card persistence and host-feature
  results are retained; owner RC3 acceptance is separate from automated tests.
- Final package checks: relative config, fresh settings/disc selection, private
  relocated copy with spaces/foreign working directory, system-only PATH,
  no-disc error, guarded own-disc boot, dependency and excluded-data scans.
  Exact outcomes are recorded in PACKAGE_AUDIT and local handoff receipt.
- Existing isolated PSXRecomp reports 01-04 remain. Report 05 adds the newly
  reproduced shared CD/XA issue, minimal patch and synthetic reproducer. Its
  exact baseline is the normalized RC3 framework, not an unverified claim
  about current official executable releases or newly searched issue status.

Known scope: whole campaign not certified; partial PGXP, no true 16:9, no frame
interpolation/60-Hz mode, no SCES-01331, no independent fast-forward music, no
full controller recorder. Existing freeze/crash diagnostics remain active;
private development session tools are excluded from the player package.

Safe cleanup removes a duplicate development report body and fixes stale audio
comments; useful historical tests and preserved local builds/cards remain.
Only allowlisted runtime files and relevant developer patches are shipped.
No extras.cpp, new mod manager or large refactoring was introduced.

Final short unit regressions passed: five loader profiles and protected card
waits, original selector guards/all MAIN exclusions, virtual reconnect, all
41 Fast Forward values, VSync persistence, Hybrid policy, movie skip and the
new immediate CD/XA passthrough/reproof cases. These fixtures do not represent
a new campaign or modified-save acceptance test.
