# EU2 renderer follow-up; implementation deliberately deferred

Use the existing shared custom renderer and the official EU1 adapter. No new
renderer or widescreen implementation was started for this handoff. The longer
existing analysis is `docs/regional/WIDESCREEN_ANALYSE_DE.md` in the game patch.

| Binding | Existing evidence | Still required for EU2 |
|---|---|---|
| MAIN identity/state | All five EN/ES/PT/SV/DA identities and GAME bases verified | Recheck identity in every state-touching render callback |
| Camera/projection | Shared camera-origin policy and EU1 field extraction exist | Original EU2 LUI/low-immediate fields, follow/projection tables and call-site windows |
| Sprites/HUD | Shared sprite roles and HUD caller/parent-stack policy exist | EU2 producers, return sites, store PCs and per-language data bases |
| Area overlays | EU2 link bases/native loaders are independently verified | Area0/1 scene hooks, actual overlay identity, camera/residency/script ownership guards |
| PAL culling | Common horizontal expansion; PAL signatures cover 0x100/0x101 and preserve 50 Hz | EU2 MAIN and overlay cull sites, bounded horizontal changes, unchanged quest predicates |
| Geometry | Full original routine correspondence recorded for all five MAINs | Adapter and isolated differential tests now pass; retain guards during integration |

Verified geometry bindings (optional, tested): EU1 0x8002235C/0x80022630/0x80022838
correspond to EU2 0x80022310/0x800225E4/0x800227EC. Complete original bodies and
internal jump relocation checks are in `docs/regional/eu2-geometry-evidence.json`.
The shared geometry adapter now passes 200 isolated original-code comparisons
per kind in each of the five languages; this does not establish widescreen
camera, HUD, script or overlay contracts.

The shared seamless contract already demonstrates why one fixed offset is wrong:
the loader entry is 0x8004EB84 for Spanish and 0x8004EB9C for the other EU2 MAINs;
render-loop hook sites are likewise 0x800504A8 versus 0x800504C0. These are loader
bindings, not a substitute for camera/HUD/projection contracts.

Before exposing widescreen: derive strict code/data/overlay contracts for all
five languages, regenerate MAIN and area native caches with the exact wide
configuration, validate 4:3/off, Fit, 16:9, 21:9 and 32:9 with HUD, world edges,
dialogs, movies and return transitions. Validate Geometry separately. Preserve
PAL's vertical 256-line behavior and original 50 Hz; do not patch story conditions
to obtain extra visible content. The original developer can integrate these
profiles into the maintained adapter or request them as a later regional patch.
