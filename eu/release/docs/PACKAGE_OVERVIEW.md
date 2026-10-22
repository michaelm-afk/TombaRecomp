# Local handoff - TombiRecomp EU 0.1.0-eu-rc4

Nothing in this package has been uploaded, published or sent to maintainers.

- `windows-x64/`: standalone player candidate; read its README before testing.
- `source/`: three integration patches, exact source bases and build notes.
- `docs/`: player, developer, texture-format and scoped test documentation.
- `upstream-bugs/`: independent English reports, minimal fixes and synthetic
  regressions for confirmed shared defects. The VSync report is already fixed
  in current upstream, but absent from the original Tomba framework pin.
- Licenses and third-party notices are under `windows-x64/licenses/`, with
  the project LICENSE beside the application and in the source handoff.
  The revised developer archive also includes a standalone licenses/ directory,
  Python's license and the OpenBIOS notice, plus the source provenance notes.
- `PACKAGE_AUDIT.json` and `SHA256SUMS.txt`: final payload checks and hashes.

Feature freeze deliberately excludes true widescreen, frame interpolation,
new audio modes and controller recording/replay. Original PAL speed, five
languages, EU-only disc validation and card compatibility are retained.
Optional resource mods start off and require external files; no HD pack or
bezel is supplied. Geometry and Seamless Loading default ON; partial PGXP
remains optional. VSync defaults OFF. A 60-Hz mode is excluded.

The owner accepted RC4 in German and French, with Seamless Loading and correctly
synchronized cutscenes. This is not a claim that every
launcher control or the entire campaign was manually tested on this exact
binary. See TEST_STATUS.md. Earlier successful regular gameplay/save tests
are retained as evidence rather than repeated automated campaigns.

Always test an extracted copy of the clean player archive in a new writable
folder. After playing, the working folder may contain personal settings,
disc paths, cards, logs and caches. Do not redistribute that used folder;
keep the original clean archive and source handoff unchanged.

HD Texture Packs is technical support for external mods, OFF by default; no
complete EU HD artwork pack is bundled or certified. Read HD_TEXTURE_PACKS.md.
SCES-01331 and its additional languages are outside this release.

Final scope, audio correction and closed optional requests: FINAL_REPORT.md.
Steam manual setup: STEAM.md. Reports 01-04 are retained; report 05 is a
separately scoped CD/XA passthrough addendum.
