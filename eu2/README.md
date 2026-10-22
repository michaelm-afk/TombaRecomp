# Tombi! — SCES-01331 integration

This is the English/Spanish/Portuguese/Swedish/Danish release of the first
Tombi! game. The RC2 backend and common European launcher were contributed by
**michaelm-afk**. USA and EU1 retain their separate native backends.

Adaptive **Widescreen** now reuses the maintained renderer, with Fit to Window
through 34:9 and fixed 16:9, 21:9 and 32:9. It starts disabled. Camera, HUD,
culling, pool and area bindings use strict original-code/data contracts and
live language identity, including the different Spanish code layout.

**Full EU2 player build, fresh wide AOT caches and sampled runtime QA still
need the exact SCES-01331 disc.** Existing v0.21.0 downloads support USA/EU1.
FMV Skip remains hidden for EU2.

## Required input

| Property | Value |
| --- | --- |
| Disc | Tombi! (Europe) (En,Es,Pt,Sv,Da), SCES-01331 |
| Raw BIN size | 492,306,528 bytes |
| SHA-1 | 684dbf0ad03f872511046d40d3cc85b17d839dbf |
| SHA-256 | 2eba3dfdd25f5d270d47f5fe408391971aa25ee09c6aac9874bba4e3bf6f32cc |

Matching MAIN files do not qualify a different boot disc. Exact preparation,
launcher and native-byte gates remain enforced. Keep original discs/cards
read-only and use ignored workspace copies and fresh QA cards.

## Build and sampled QA

Use initialized submodules, Python 3.11+, Git Bash, CMake, Ninja and Windows
Clang. Set TOMBI_TOOLCHAIN_BIN as needed and redirect scratch/caches off C:.

    python -I -B tools/build_regions.py --region eu2 --plan
    python -I -B tools/build_regions.py --region eu2 --eu2-disc 'path/to/Tombi.cue' --check
    python -I -B tools/build_regions.py --region eu2 --eu2-disc 'path/to/Tombi.cue' --qa --jobs 3
    python -I -B eu/tests/test_sampled_gameplay.py --eu2 --build-dir build-eu2-qa/native --languages en es --view Fit --name eu2-fit

Without --qa, the player is build-eu2-release/native/TombiRecompEU2.exe.
--region all selects USA/EU1/EU2; both preserves USA/EU1 behavior. Supply
--us-disc, --eu-disc and --eu2-disc for the corresponding original inputs.
The [combined European build](../europe/DEVELOPER.md) stages both PAL backends.

Sample English and Spanish, plus one fixed 21:9 and one disabled-Widescreen
case; do not run a five-language/aspect matrix. The sampler uses ordinary
menu/dialogue/walk/jump inputs, fresh cards, muted output and disabled runtime
compilation, and requires actual native dispatch and rendered HUD roles.

All MAIN/area modules must be rebuilt for the wide configuration. Packaging
checks the exact native cache tag: RC2's non-wide EU2 cache cannot be relabeled.
CD Speed and host-paced Fast Loading stay excluded.

## Evidence and limits

The adapter compiles and original-MAIN fixtures pass for all five static
profiles: independent field extraction, actual HUD return/parent sites,
world sprite roles, language replacement and unknown/pre-game rejection.
The static correspondence is reproducible with eu2/analyze_widescreen.py.
Its --reference-disc option permits matching-image analysis without qualifying
that input's boot disc. Static profile checks are separate from sampled play.

See [the integration audit](../audit_notes/tombi-eu2-rc2-20261022.json).
Full campaign, all-area spawning/collision/exits, exhaustive audio/controllers,
FMV transitions and an in-game Memory Card roundtrip remain unverified.
The [handoff records](handoff/README.md) describe the developer's original RC2
checkpoint; their older Widescreen status predates this adapter.
