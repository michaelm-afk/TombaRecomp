# HQ voice shadow can suppress newly starting CD/XA audio

Project: PSXRecomp; runtime/src/spu_shadow.c, spu_shadow_process().
Confirmed against our normalized shared framework revision
9580d354a381c5a1433698a49f89d8cdd29c28e3 (RC3). This is independent of EU game
addresses, languages, loaders and original assets. The original voice-only
shadow design contains this omission, but this report does not claim that an
unmodified official executable manifests it: the older normalization defect
can prevent the shadow from proving, masking this second issue. Current online
issue/PR status was not re-searched during finalization. Nothing was submitted.

## Trigger and impact

The HQ shadow has already passed verification while normal voices play.
The game then enables the SPU CD input bus, for example for an XA-voiced FMV.
The canonical mix includes CD/XA, whereas the shadow synthesizes only voices.
Despite the unsupported input, the old code continues replacing the complete
canonical output while the windowed verifier collects three failed windows.
An XA-only start can therefore become silence until fallback. With a
65536-sample verifier window at 44100 Hz, three full windows are about 4.46 s;
the actual delay depends on window phase and signal/verifier state. The normal
host audio queue adds separate latency, not the cause of the missing bus.

The owner observed delayed speech at the start of the EU Wise Man FMV with
HQ-SPU enabled. The session log also contains the eventual zero-correlation /
zero-level-ratio DEGRADED fallback. This supports the trigger, but the exact
owner FMV was not replayed as a final end-to-end acceptance test.

## Synthetic reproduction, no copyrighted inputs

Compile test_spu_shadow_cd_input.c with runtime/src/spu_shadow.c and
runtime/src/audio_shadow.c, with runtime/include on the include path, and libm
where required. No SDL, BIOS, disc, game code or save is needed.

The test first proves a supported synthetic voice stream. It then supplies
nonzero canonical CD samples and zero voice taps with SPUCNT CD input enabled.
Expected: every canonical sample is preserved from the first block.
Before: assertion fails at the first CD block (canonical samples overwritten).
After: passes immediate CD passthrough, repeated CD blocks, unproven CD exit,
fresh supported-voice proof, mismatch fallback and disabled byte equality.

## Minimal fix and tradeoff

The patch targets exactly the framework revision above. Apply with
`git apply --check fix.patch`, then `git apply fix.patch`. It only changes
spu_shadow.c; the test is supplied separately.

When SPUCNT bit 0 enables CD input, preserve the entire canonical block
immediately and invalidate previous voice-only proof once. Require fresh proof
after CD input is disabled. No video delay, timer change, CD decode change or
queue flushing is introduced. Games leaving CD input enabled without CD audio
will conservatively use the canonical mix during that period. That is safer
than suppressing an input the shadow does not implement.

The tested fix intentionally does not redesign general reverb/noise support.
It is separate from report 01's normalization patch. Preserve both fixes when
integrating the HQ feature; do not interpret old verifier fallback as immediate
per-sample protection against every unsupported input.
