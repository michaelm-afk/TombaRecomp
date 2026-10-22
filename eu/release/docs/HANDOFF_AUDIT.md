# RC4 handoff audit - 2026-10-22

No game implementation changes, publication or delivery to third parties were
performed for this audit. The owner's RC4 test confirms German and French,
working Seamless Loading and correctly synchronized prerendered cutscenes.

## Which files to send

- TombiRecompEU-0.1.0-eu-rc4-windows-x64.zip: unchanged tested player package.
- TombiRecompEU-0.1.0-eu-rc4-developer-handoff-r2.zip: revised developer package.
- TombiRecompEU-0.1.0-eu-rc4-handoff-SHA256SUMS.txt: archive hashes.

The older developer archive is preserved but superseded by r2. Its game,
framework and UI patches were already RC4, not RC3. The revision fills a
packaging-reproduction gap: release helpers, package audit tools, documentation,
font licenses and the bug-report source directory were missing from the root
source patch. It also records owner acceptance and bundles standalone notices.

The Windows archive contains 522 files: executable, native overlay modules,
assets, redistributable OpenBIOS, portable compilation support and notices.
It has 271 Python/header/include support files, but no full project source,
CMakeLists.txt, integration patches or generated game C source. The native
overlay DLLs are intentionally part of the playable release. Use the developer
archive for integration; a recipient also needs the exact upstream source bases
in source/SOURCE_BASES.json and their own verified EU Rev-1 disc for generation.

## Rebuild verification

The actual original RC4 developer ZIP was extracted separately. Original source
trees were reconstructed from Git archives of each declared exact base, then
the packaged patches were checked and applied. Nested dependencies were restored
at their exact gitlink commits. No existing generated game source, native overlay
cache or personal card was used as a rebuild input.

The local toolchain and existing unmodified third-party libchdr/libwebp source
downloads were reused; this was not an offline dependency-download test.
OpenBIOS is the redistributable image from the pinned framework source tree.
The owner's verified disc was copied into the isolated tree and read for local
generation. Generated game sources stay local and are excluded from handoff.

Compiler tools, OpenBIOS backend, EU boot code, the baseline EU executable and
the final Seamless release executable were rebuilt successfully. Follow the
documented ordering: the baseline native build generates the codegen hash needed
before overlay compilation. An early parallel attempt was rejected by the
existing stale-codegen guard; it was not bypassed. Windows sandbox temporary
directory restrictions required a normal local compiler execution environment.

See HANDOFF_AUDIT.json for final overlay/staging checks. The r2 delta only adds
handoff helpers/docs/notices; game/runtime/UI source remains the tested RC4 code.
This is source-build reproducibility, not a claim of byte-identical PE output
across different toolchains, timestamps and build locations. No new campaign,
controller interaction or Memory Card tests were performed for packaging.

## Reports and privacy

All five independent English reports, minimal patches and regression guidance
are included under upstream-bugs/. All 20 entries in their CONTENTS.json match
their recorded lengths and SHA-256 hashes. Reports retain exact baseline and
verification limits: report 04 is already fixed in newer official upstream;
report 05 is confirmed against the normalized RC3 framework and does not claim
a newly verified current-upstream issue. The full integration patch already
contains the final fixes; do not apply isolated fixes again on top of it.

ZIP CRC, path traversal, excluded file/directory and ASCII/UTF-16 personal-path
scans are recorded in the machine-readable audit. No original discs, retail
BIOS, cards, saved settings, private logs, crash dumps, Git/Codex metadata or
personal absolute paths are supplied. OpenBIOS is the intentional permitted
binary-image exception. Original archives/builds/cards are preserved.

## Licenses

The player retains the project/framework PolyForm Noncommercial license and
the recomp-ui MIT license. OpenBIOS has its own MIT notice and pinned source
provenance; no Sony firmware is supplied. Third-party notices and texts cover
the shipped compiler/runtime components and fonts. The developer archive also
copies these notices, Python's license and the OpenBIOS notice into licenses/.
Exact TinyCC 0.9.27 source/binary URLs are in its notice. DEVELOPER.md records
upstream repository, submodule, dependency and packaging prerequisites.
This audit does not grant new rights over the original game or change any
upstream license. Preserve all notices and applicable source obligations when
integrating or redistributing.
