# SCES-01331 revision 2 verification

This report separates newly completed evidence from the earlier accepted release. No full-campaign certification is claimed.

## New automated evidence

- Geometry: complete original routine hashes checked for EN/ES/PT/SV/DA; the existing shared HLE differential validator passes 200 isolated batches of each of three routines per language (3000 comparisons). It checks original return/register/GTE/RAM/ordering-table behavior. Unknown bodies retain original execution.
- PGXP: all five languages show exact packet precision dataflow, precise triangles and armed perspective correction. An additional Spanish OpenGL run demonstrates the actual renderer path. The first Spanish assertion incorrectly required legacy fallback hits; the primary dataflow counters were already positive. The corrected English/Spanish regressions pass. Base-flavor coverage is reduced.
- Five-language original MAIN identity, new-game initialization, guarded native dispatch and Seamless batches pass with the new hook configuration. English/Spanish final regressions follow the official Browse restoration.
- Native cache audit: 65 DLL/ranges pairs, 54 recipes, 15439 guard rows. No provenance checks bypassed; Portuguese game-over keeps the existing interpreter fallback.
- Shared Hybrid Controller policy fixture, all 41 Fast Forward fractional-speed/presentation cases, SPU shadow normalization/CD passthrough/reproof/fallback/OFF fixtures pass.
- HD textures: ten synthetic SCES-01331 installer cases, including corrupt images, wrong names and incompatible US metadata. Shared real-OpenGL replacement fixture passes with zero failures. No original textures in these fixtures.
- Bezel mod ownership/resource/path guard passes. Visual artwork acceptance remains manual.
- Browse: launcher_imgui.cpp, launcher_files.c and launcher_files.h match the recorded official UI source. No Home/card-start-path/native-dialog extensions remain. The existing picker source guard passes.
- Blank-card formatter: creates valid 131072-byte MC image, refuses an existing filename atomically and preserves its bytes.

## Existing accepted evidence retained

Prior strict loader/decoder coverage, original PAL movement/jump, original-CD fallbacks and the hut exterior/interior/exterior roundtrip remain in the regional reports. The owner successfully saved in Spanish before the hut, restarted and loaded/viewed the cutscene in Swedish. Original ROM/build/card inventories and old archives are preserved.

## Manual acceptance and limits

No desktop automation is used for final closeout. Native dialog selection, New through the GUI, GUI setting persistence and a new ordinary save-sign -> restart -> load test remain explicit manual steps in MANUAL_TESTS_DE.md. A bounded automated attempt on a fresh copy of the current portable card did not reliably navigate the original load menu; it is not a passing load regression and did not write the original card. No debug/state/quest injection was used to force completion.

No physical-controller matrix, exhaustive listening or complete world/quest/save coverage. Widescreen and FMV-Skip are intentionally not offered; PC_MODS.md and WIDESCREEN.md identify the missing EU2 contracts. No HD pack or bezel artwork is bundled. Isolated rebuild and independent player/developer package audits are recorded in CLOSEOUT_RESULTS.json and the final delivery receipt. Private logs, personal hashes, screenshots and absolute user paths are excluded from delivery.
