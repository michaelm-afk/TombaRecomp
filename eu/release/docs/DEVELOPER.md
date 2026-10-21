# Developer integration notes

This candidate adds native EU Rev-1 support alongside the US target. It does
not substitute EU files for US program code and does not spoof the disc ID.
Preserve the existing US game configuration and targets during integration.

The EU target lives in `eu/CMakeLists.txt`. EU-specific components are the
five verified language MAIN profiles, guarded loader/task adapter, PAL
geometry adapter and original-disc resident catalog. Address-free Hybrid,
FMV policy, graphics, launcher and audio processing reuse shared components.
Memory Card operations retain the original EU logic.

The source handoff contains Git patches rather than generated game source.
Apply each patch to the exact base listed in SOURCE_BASES.json, including
the framework and UI separately. The shared framework patch contains more
than the isolated upstream bug fixes: review it before merging. The smaller
upstream reports describe independent fixes and regression tests.
These three integration patches deliberately use zero context to avoid
copying unrelated development comments. In each repository run
`git apply --check --unidiff-zero <matching-patch>` followed by
`git apply --unidiff-zero <matching-patch>`. All three were checked against
their exact bases using isolated Git indices; no working tree was reset.
The handoff audit additionally reconstructs and builds an isolated source tree.

Start from https://github.com/mstan/TombaRecomp at the TombaRecomp base in
SOURCE_BASES.json. Initialize submodules recursively, then check out the exact
framework and UI bases from that file before applying their patches. Preserve
the framework's nested gitlink pins: recomp-net
`b1eab87bf3c011da8c22890601c0e659f1f89fbb` and retcomm-rbengine
`2a03e73693acee0fb78076ea058642c931bef12e`.
Do not update dependencies to their current master branches during this rebuild.
Patches contain the relevant source delta, not a full repository snapshot.
Unchanged source and third-party dependencies are obtained from the pinned repos.
The revision fields identify the local development snapshots; they are not
promised public Git refs. To integrate, commit the reviewed framework/UI patches
in their respective repositories, then record those new submodule commits and
the EU changes in the game repository. No additional nested-submodule patch is
required: both nested dependencies are unchanged at the pins above.

## Rebuild from a legally owned disc

Requirements: Python 3.11+, CMake, Ninja and LLVM-MinGW/Clang, Git and the
normal PSXRecomp third-party build dependencies. Set `TOMBI_TOOLCHAIN_BIN`
to your compiler bin directory, or place those tools on PATH. Player builds
do not require these host tools; the bundled overlay fallback is separate.
When using TOMBI_TOOLCHAIN_BIN, also add it to PATH for the direct CMake
commands below. Git Bash/MSYS2 is needed for the framework BIOS helper.

Keep a read-only original and place a working dump copy under
`disc/Tombi! (Europe) (En,Fr,De,It,Nl) (Rev 1).cue` with its matching BIN.
Build `psxrecomp-game` from the pinned framework into `build-eu-tools` first.
Then, from the project root:

```powershell
cmake -S psxrecomp/recompiler -B build-eu-tools -G Ninja -DCMAKE_BUILD_TYPE=Release -DBUILD_TESTING=OFF -DCMAKE_C_COMPILER=clang -DCMAKE_CXX_COMPILER=clang++
cmake --build build-eu-tools --target psxrecomp-game psxrecomp-bios
```

Generate only the redistributable OpenBIOS backend (no retail BIOS dump):

```bash
cd psxrecomp
PSXRECOMP_BIOS_BUILD=../build-eu-tools tools/regen_bios.sh --config bios/OpenBIOS.toml
cd ..
```

Continue in PowerShell:

```powershell
python -I eu/prepare.py --disc 'disc/Tombi! (Europe) (En,Fr,De,It,Nl) (Rev 1).cue'
build-eu-tools/psxrecomp-game.exe --config eu/game.toml
cmake -S eu -B build-eu-prototype/native -G Ninja -DCMAKE_BUILD_TYPE=Release -DPSX_DEBUG_TOOLS=OFF -DPSX_PGXP_VARIANT=OFF -DPSXRECOMP_BIOS_STEMS=OpenBIOS -DCMAKE_C_COMPILER=clang -DCMAKE_CXX_COMPILER=clang++
cmake --build build-eu-prototype/native --target tombi-eu
python -I eu/build_aot.py --scope opening --workers 1
python -I eu/seamless_catalog.py
python -I eu/build_seamless_hooks.py
python -I eu/build_release.py
```

The AOT preparation stages/audits local native pairs. The standalone release
build expects these local generated inputs to exist; it is not a one-command
clean-room bootstrap. Sources emitted from the disc must never be committed
or included in the source handoff. See TEST_STATUS.md for validation scope.

The local packaging script refuses to overwrite an existing public directory.
Staging is local only and does not publish anything. Review licenses and run
the privacy/completeness audit before redistributing a binary candidate.

## Recreating the portable layout

The updated source patch includes the release docs/licenses, staging and source
export helpers, package tests and all five isolated bug reports. Before staging,
download the unmodified Python 3.13.1 embeddable x64 archive from
https://www.python.org/ftp/python/3.13.1/python-3.13.1-embed-amd64.zip into
`build-eu-release/python-3.13.1-embed-amd64.zip`. SHA-256 must be
`7b7923ff0183a8b8fca90f6047184b419b108cb437f75fc1c002f9d2f8bcec16`;
stage_release.py enforces this hash. The compiler distribution must also contain
its LLVM/MinGW licenses, SDL3 license and dependency headers used by staging.

```powershell
python -I eu/stage_release.py --output public-rebuilt
python -I eu/tests/audit_release_imports.py --package public-rebuilt/windows-x64
```

The integration patches already supplied in source/ are authoritative; source
export expects committed revisions and is not needed to compile the game.
Never package the owned disc, generated game C, saves or a used player folder.
See HANDOFF_AUDIT.md in the handoff docs for the tested rebuild boundaries.

## Licenses and attribution

TombaRecomp and PSXRecomp retain PolyForm Noncommercial 1.0.0; recomp-ui retains
its MIT notice. This handoff does not relicense either project. Original game
assets remain the owner's responsibility and are not included. The player
contains only the redistributable PCSX-Redux OpenBIOS, its MIT notice and source
provenance in bios/OpenBIOS.toml, never Sony BIOS firmware. Third-party license
texts/notices (LLVM/MinGW, Python, SDL3, TinyCC, fonts, image/CHD/audio and other
runtime dependencies) remain beside the player. TinyCC's separate unmodified
0.9.27 executable has its exact upstream source/binary links in its license file.
Keep those notices and sources/rebuild information with any redistribution.

## Deliberate scope limits

No new widescreen, interpolation, audio engine or controller recorder.
No speculative loader cleanup: language-specific pointer contracts and
overlay/task guards are necessary additional complexity. Historical campaign
tools and private diagnostics stay outside the player distribution. The
existing code-size audit is retained in development instead of repeated here.

## RC3 integration additions

The address-free host_sha256.h helper dynamically loads the Windows system
bcrypt provider from System32; other platforms and failed native operations
retain the portable SHA-256 path. Every disc byte and resident blob is still
hashed. No checksum receipt or game identity is fabricated. CHD decoding keeps
its existing path. No new installer DLL dependency is required.

A resource may opt into texture installation validation with texture_game_id.
The EU manifest specifies SCES-01330. Shared texture_pack_install.cpp checks the
pack's declared target, supported wire names/configuration and decoded images;
mod_runtime rechecks active replacements on commit. Legacy manifests without
this field retain their existing behavior. Explicit folder selection refreshes
the UI's cached result; the UI does not decode the pack on every draw.
Target metadata is author-declared, not independent proof of full disc coverage.
See HD_TEXTURE_PACKS.md and the synthetic installer tests for the exact contract.

The developer patches include the RC3 SHA and installer regression sources.
No original game bytes, generated game C, cards or personal logs are included.
SCES-01331, 60-Hz mode and interpolation remain excluded.

## Final RC4 audio patch

CD/XA input bypasses the voice-only HQ shadow immediately and invalidates old
proof. The full framework patch includes this correction and its updated
synthetic test. The isolated report 05 targets the normalized RC3 framework;
reports 01-04 retain their original bases. No host buffer reduction or video
delay was added. See FINAL_REPORT.md and STEAM.md for closed optional scope.

The final source allowlist also includes session_state.py (required by profile
generation) and the controller-only campaign helper/route used by the scoped
movement regression. They are source-only dependencies, not player payload.
