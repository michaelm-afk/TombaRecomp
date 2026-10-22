# HQ SPU compares unnormalized shadow samples against normalized audio

Project: PSXRecomp. File: `runtime/src/spu_shadow.c`, `spu_shadow_process()`.
Status: present in official master `958ae0e396f14d39c86e5c016d405fcdd96af4d5`.

## Affected sources

The defect exists in introducing commit
`cb00b9c0af5ea204b8b0896b004c066610af309c`, subsequent configuration commit
`5b00d497e444676c4991ee91c187bd9a9cb58894`, Tomba's framework pin
`03e635e86dceb540b7b6421ada7ee32cc28ca62b`, and the checked current master.
Source tags v0.3.0-alpha, v0.3.1-alpha, v0.3.2-alpha and v0.3.3-alpha were
individually checked and contain the same missing conversion. Tomba
v0.20.2-alpha is source-affected through its framework pin.

## Reproduction and observed behavior

Compile the supplied synthetic test against unmodified framework sources:

```sh
cc -std=c11 -Iruntime/include /path/to/test_spu_shadow_normalization.c \
  runtime/src/spu_shadow.c runtime/src/audio_shadow.c -lm -o test-shadow
./test-shadow
```

On Windows Clang/MinGW, omit `-lm` if unnecessary. No game, BIOS or audio file
is required. The test supplies the public voice-tap accessors itself.

The shadow sums decoded int16-scale samples, but the canonical reference is
divided by 32768. Their ratio is therefore approximately 32768 instead of 1.
Expected: identical synthetic voice data proves and retains its output level.
Actual: verification rejects the shadow and the canonical mix stays active.

A probe linked directly against the preserved US build's SPU object files:

```text
before: enabled=1 proven=0 level_ratio=32771.359375 correlation=1.000000
after:  enabled=1 proven=1 level_ratio=1.000103     correlation=1.000000
```

In a regular EU card-load scene, before correction the ratio was 33064.26.
After correction: 17/17 observations proved, ratio 1.003625, correlation
0.983866, no verifier reverts during that short window. These are sanitized
measurements, not private logs supplied with this package.

## Fix and risk

`fix.patch` normalizes both shadow channels with `SHADOW_NORM` before judging.
The existing multiplication by 32768 at final output then restores int16 scale.
This is independent of EU addresses, languages, disc data and game code. It
needs no ABI change, generated-code rebuild or other EU patch; relink the host.

HQ off remains byte-identical. With HQ on, previously dormant cubic/float
output becomes audible, so timbre may change as intended. The unchanged
verifier can still reject unsupported effects/mixes or revert later. This is
not an SPU hardware-accuracy fix: reverb/noise or driver-specific differences
are not solved by normalization. Do not loosen verification thresholds to
force acceptance. The test also verifies mismatch fallback and disabling.

References: [current source](https://github.com/RetroPortingToolKit/psxrecomp/blob/958ae0e396f14d39c86e5c016d405fcdd96af4d5/runtime/src/spu_shadow.c),
[introduction](https://github.com/RetroPortingToolKit/psxrecomp/commit/cb00b9c0af5ea204b8b0896b004c066610af309c).
No exact public issue/PR found by the recorded searches.
