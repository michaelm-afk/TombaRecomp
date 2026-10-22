# Tombi! — SCES-01331 integration

This is the English/Spanish/Portuguese/Swedish/Danish release of the first
Tombi! game. The RC2 backend and common European launcher were contributed by
**michaelm-afk**. USA and EU1 retain their separate native backends.

Adaptive **Widescreen** now reuses the maintained renderer, with Fit to Window
through 34:9 and fixed 16:9, 21:9 and 32:9. It starts disabled. Camera, HUD,
culling, pool and area bindings use strict original-code/data contracts and
live language identity, including the different Spanish code layout.

The original RC2 revision and Rev 1 have separate checked bindings and native
cache configurations. The owner's SCES-01331 Rev 1 disc is now accepted for
builds. Its fresh player and AOT rebuild passed bounded EN/ES runtime QA.
Existing v0.21.0 downloads support USA/EU1. FMV Skip remains hidden for EU2.

## Required input

Both are SCES-01331, English/Spanish/Portuguese/Swedish/Danish. The supplied
track selects the revision automatically; a serial or filename alone does not.

| Revision | Raw BIN bytes | SHA-1 |
| --- | ---: | --- |
| Original RC2 | 492,306,528 | 684dbf0ad03f872511046d40d3cc85b17d839dbf |
| Rev 1 | 492,370,032 | ec50074b6fd98f611bae11e3de68d6e76ffdd6d4 |

Each executable binds one revision. Rev 1's English MAIN and opening overlays
are byte-identical to EU1 Rev 1; its other languages have their own identities
and reviewed fields. Rev 1 uses `eu2/rev1/` contracts. Build-local mod targets,
release disc checks and the combined launcher catalog follow that revision.
A package must not accept another revision's disc or native cache. Matching
MAIN files alone do not qualify a different boot disc. Keep original discs and
cards read-only and use ignored workspace copies and fresh QA cards.

## Build and sampled QA

Use initialized submodules, Python 3.11+, Git Bash, CMake, Ninja and Windows
Clang. Set TOMBI_TOOLCHAIN_BIN as needed and redirect scratch/caches off C:.

    python -I -B tools/build_regions.py --region eu2 --eu2-revision rev1 --plan
    python -I -B tools/build_regions.py --region eu2 --eu2-disc 'path/to/Tombi.cue' --check
    python -I -B tools/build_regions.py --region eu2 --eu2-disc 'path/to/Tombi.cue' --qa --jobs 3
    python -I -B eu/tests/test_sampled_gameplay.py --eu2 --build-dir build-eu2-qa/native --languages en es --view Fit --name eu2-fit

Without --qa, the player is build-eu2-release/native/TombiRecompEU2.exe.
--region all selects USA/EU1/EU2; both preserves USA/EU1 behavior. Supply
--us-disc, --eu-disc and --eu2-disc for the corresponding original inputs.
Rev 1 ZIP names include `Europe-SCES01331-Rev1`. Use separate checkouts to
build both EU2 revisions; preparation refuses to overwrite a different working
disc. `--eu2-revision` also checks an explicitly supplied disc for mismatches.
The [combined European build](../europe/DEVELOPER.md) stages both PAL backends.

Sample English and Spanish, plus one fixed 21:9 and one disabled-Widescreen
case; do not run a five-language/aspect matrix. The sampler uses ordinary
menu/dialogue/walk/jump inputs, fresh cards, muted output and disabled runtime
compilation, and requires actual native dispatch and rendered HUD roles.

All MAIN/area modules must be rebuilt for the wide configuration. Packaging
checks the exact native cache tag: RC2's non-wide EU2 cache cannot be relabeled.
CD Speed and host-paced Fast Loading stay excluded.

## Evidence and limits

Rev 1 passed EN/ES normal-input opening play, geometry HLE, seamless batches
and native dispatch with runtime compilation disabled. Fit passed six live
window sizes in each sample; English also passed fixed 21:9 and Widescreen off.
The fresh cache has 66 audited pairs and 15,440 original-byte guards.
Eighteen combined-launcher checks passed, including real process handoffs and
Play verification in both directions, corrupt-disc/missing-backend rejection,
paths with spaces, and preservation of private settings/mod state/cards.
The standalone release-mode candidate ZIP also passed stripped-cache hashes,
privacy/import checks, relocated Play verification and exact-disc rejection.
It has not been published as a new GitHub release.
The original RC2 revision retains static-only qualification.

The adapter compiles and original-MAIN fixtures pass for all five static
profiles: independent field extraction, actual HUD return/parent sites,
world sprite roles, language replacement and unknown/pre-game rejection.
The static correspondence is reproducible with eu2/analyze_widescreen.py.
For Rev 1, reproduce its loader/geometry contract with
`python -I -B eu2/analyze_revision.py`, and its widescreen contract with
`python -I -B eu2/analyze_widescreen.py --revision rev1`.
The --reference-disc option permits matching-image analysis without qualifying
that input's boot disc. Static profile checks are separate from sampled play.

See [the integration audit](../audit_notes/tombi-eu2-rc2-20261022.json).
Full campaign, all-area spawning/collision/exits, exhaustive audio/controllers,
FMV transitions and an in-game Memory Card roundtrip remain unverified.
The [handoff records](handoff/README.md) describe the developer's original RC2
checkpoint; their older Widescreen status predates this adapter.
