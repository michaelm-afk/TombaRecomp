# Release candidate test status

Automated evidence already completed during EU development (not repeated as
a full campaign):

- Original disc identity and all five MAIN/loader/geometry contracts verified.
- Short earned-save Dwarf Village -> Forest -> Dwarf Village roundtrip in all
  five languages; original loader fallback and original card loading tested.
- Geometry differential comparison: 600 batches per language, 3,000 total;
  RAM, scratch, GTE, preserved registers and return values matched.
- Fast-forward 41 fractional settings round-tripped; 2.1x/3.7x timing samples;
  VSync persistence, Hybrid policy, FMV and HQ-SPU regression tests passed.
- Actual external texture replacements and bezel rendering observed; HQ-SPU
  shadow/canonical amplitude comparison passed after independent shared fix.
- Native cache: 66 audited DLL/ranges pairs, 15,440 guarded entries; full
  static coverage is not proven. Interpreter fallback remains available.

Owner manual evidence: regular fog task, chick collection, German cutscene,
upper hut exit and subsequent areas through Dwarf Village succeeded. Saves
in both Memory Card slots survived full exit/restart/load. No artificial
progress or injected inventory was used in that acceptance run.

Release-only changes: relative config default, stripped/path-remapped native
executable, hidden unqualified render-pipeline controls, improved tooltips,
clean allowlisted staging. Build and configuration-capability unit test pass.
Final relocation, first-run and UI acceptance results are recorded separately
in the package audit. Prior gameplay results do not prove every new UI control.

Exact-candidate checks completed during finalization:

- Relocated folder and foreign working directory, including spaces: relative
  config and OpenBIOS resolved correctly. With no disc, headless startup
  reported that a disc must be selected and exited. With a private disc copy,
  PAL/SCES-01330 and the boot image guard were confirmed in a 12-second smoke.
- Fresh launcher process remained running in a 7-second smoke. This is not a
  visual acceptance test of its file picker or every control.
- No host Python/compiler on PATH: bundled Python imported json/pathlib;
  both emitters started; TinyCC compiled and loaded a synthetic Windows DLL.
  Missing Python standard library and emitter runtime DLLs were found during
  packaging and corrected before handoff.
- 103 PE files: no unresolved non-system import dependencies after including
  emitter C++ runtime DLLs. The GUI application uses only system dependencies.
- All 66 stripped native DLLs loaded under Windows; all .text sections and
  original-byte guard ranges matched their previously audited inputs.
- Loader, 41-step Fast Forward, VSync, HQ-SPU, Hybrid and FMV unit regressions
  passed. Video/settings-capability and export-declaration tests passed.
- Personal Windows-path and excluded-file scans passed before final source
  staging; PACKAGE_AUDIT.json records the complete final scan and sizes.

Toolchain binaries may retain upstream LLVM CI build provenance strings.
These are third-party build paths, not user/development-session paths or
runtime file dependencies. Original cards and preserved executables were not
used as output locations by any finalization test.

Remaining manual acceptance: fresh disc picker/error feedback, every visible
tooltip and setting, persisted preferences, physical controller mapping and
short play/save/restart/load on this exact candidate. No full campaign rerun
is required before the owner performs this focused acceptance test.

## RC2 incremental evidence

- SDL virtual disconnect/reconnect passed with hotplug events deliberately
  discarded, a new device instance and bounded retry. This does not reproduce
  or certify the owner's physical Razer XInput failure.
- Selector timeout unit regression passed against the owned boot and all five
  MAIN files; only the guarded original idle timer is held. Synthetic memory
  is used for this unit test, not for campaign acceptance.
- Fractional Fast Forward, VSync persistence and Hybrid unit regressions passed.
- Owner reports regular play through the Elder, with save/load and Seamless
  Loading working. This is owner evidence; no new full campaign was automated.
- 60-Hz mode, interpolation and further VSync/VRR investigations are excluded.
- RC1 exact-candidate results above remain RC1 evidence; RC2 relocation and
  dependency results are recorded in its own audit, not inferred from RC1.

RC2 exact-package relocation smoke passed: fresh launcher remained alive, own
disc boot reached guarded PAL execution, no-disc startup exited with a clear
error, bundled Python worked with a system-only PATH, and 103 PE files had no
unresolved imports. Original disc hash stayed unchanged. Controller-only
selector regression waited 1,400 PAL frames (28 simulated seconds), then
confirmed German and reached its original MAIN: 22.463 real seconds including
startup and load. This is a short boot regression, not campaign coverage.

## RC3 final incremental checks

Owner RC2 test: Razer Raiju V3 Pro recognized, Analog stick worked without the
D-pad, Digital/D-Pad accepted both; PGXP and FMV-Skip enabled, internal resolution
1080p; regular play to the hut, smooth feel and no controller failure observed.
The shared US/EU mapping policy was previously compared, so it was not repeated.

- SHA-256 native/portable equivalence: empty, block/padding boundaries, large
  buffers, fragmented updates and the complete owned BIN digest passed.
- Real mod-runtime and resident-resource tests passed, including corrupt-cache
  rejection, plan invalidation, relocation, stock policy and range guards.
- Ten installer cases passed using synthetic images: missing/empty pack, valid
  declared EU target, outer wrapper discovery, replacements-directory selection,
  conflicting target metadata, damaged image, bad filename and US example denial.
  These are format/target tests, not a complete EU artwork pack qualification.
- Isolated startup phase probes found hashing and resident preparation costs.
  Full checks remain enabled. Detailed timings are in FINAL_RC3_REPORT.md.
- A small controller-only US/EU new-game comparison reached the same walking
  endpoint and jump height. At nominal 50/59.94 Hz the matched sequence takes
  about 19.9% longer in EU game time. No claim about every timer, enemy or music.
  Headless execution time is separately recorded and is not normal-speed gameplay.

RC1/RC2 exact-package results above remain evidence for those candidates.
RC3 package-specific dependency/relocation/privacy checks are recorded in its
PACKAGE_AUDIT and the final handoff receipt; physical launcher acceptance of the
new folder picker and status colors remains an owner test.

## Final RC3 package checks

The exact player package passed relocation to a path containing spaces and a
foreign working directory, no-disc error handling, guarded PAL own-disc boot,
a fresh launcher process smoke, and bundled-Python startup with system-only
PATH. All 103 PE files had no unresolved non-system imports. The original BIN
hash remained unchanged. These are process/configuration checks, not visual
acceptance of the new picker. Full-runtime and resident tests use synthetic
fixture discs, not modified player progress.

## Final RC4 changes

Owner accepted RC3 visuals and reliability. The confirmed shared HQ/CD startup
regression now preserves CD/XA output immediately, then requires fresh voice
proof. The synthetic before-fix case fails; the patched case passes. No timing,
loader, card-format or quest changes were made. See FINAL_REPORT.md for exact
scope. The owner subsequently accepted RC4 manual tests in German and French:
Seamless Loading works and cutscenes are correctly synchronized. This does not
replace the earlier five-language contract checks or certify the entire campaign.
