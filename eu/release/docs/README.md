# TombiRecomp EU - 0.1.0-eu-rc4

A native Windows x64 port of the original European Tombi!, using PSXRecomp
and the shared TombaRecomp PC runtime. This is a local release candidate for
acceptance testing, not an official Sony release.

## Requirements and first launch

Use Windows 10/11 x64, a working OpenGL graphics driver and a writable folder.
Extract the entire `windows-x64` folder, then double-click `TombiRecompEU.exe`.
No administrator rights, system Python or compiler installation is required.
Keep the companion folders beside the executable. Avoid Program Files and
read-only media: settings, caches and saves are stored beside the program.

Select your own **Tombi! (Europe) (En,Fr,De,It,Nl) (Rev 1)** BIN/CUE dump,
boot executable **SCES_013.30**. Keep its BIN beside its CUE. Other releases
are unsupported; do not rename their game IDs. The accepted raw data track
has SHA-1 `2505d958b4439d04844cadd3f968fc7432a48e00`.
No game image, retail BIOS or original artwork is included.

The original game's language selector appears before the Sony introduction:
English, French, German, Italian and Dutch. The launcher's own interface
language does not select the game's language. The US disc is not required. Language selection waits for explicit confirmation.

## Controls and settings

Connect your controller before opening the launcher. Open Controllers to
choose the device and remap buttons; keyboard bindings are shown there too.
The default digital mode accepts both D-pad and left-stick directions.
Analog mode uses the original game's analog input path. The optional Hybrid
Controller mod switches digital/analog paths according to the active input;
it does not turn every physical controller into a different device.

Use the launcher Display and Audio settings for fullscreen, resolution,
VSync (OFF by default), volume and sample rate. Hover over controls/mods for help. Settings
apply when starting the game and are stored in `settings.toml`; mod choices
are stored under `mods/`. Resource-dependent mods start disabled.

Fast Forward is configured under controller shortcuts: 1.0x-5.0x in 0.1 steps,
with Hold/Toggle modes. Audio also speeds up. The actual maximum depends on
your PC. The legacy Select+L1 chord may also open the game's event menu;
use a dedicated host shortcut when convenient.

## PC enhancements

- Seamless Loading: enabled by default; prepares verified resident data from
  your own disc and reduce area-loading interruptions. Unknown requests use
  the original loader; original card operations are retained.
- Geometry HLE: guarded native terrain processing; enabled by
  default. Compared against original geometry in all five languages, with
  limited scene coverage rather than a full-game guarantee.
- Skip FMVs: skips videos through original movie completion. Its option can
  preserve title/ending/credits. In-game scripted scenes are not FMVs.
- High-quality SPU: enhanced processing where supported; improvements can
  be subtle and unsupported voices retain the original path.
- Perspective texture correction: partial PGXP support; not full PGXP
  geometry precision and not widescreen.

## Optional external artwork

HD Texture Packs is OFF by default and supplies no HD graphics. In Mods, use
Select Texture Pack Folder to validate an external EU pack, then enable it.
Without a pack the status is No texture pack installed; a validated declared
EU pack shows Installed in green. OpenGL displays matching PNG/JPEG/WebP replacements;
unmatched textures keep original artwork. No complete HD pack is supplied.
The optional dump setting captures texture usage and finishes PNG output on
normal exit. See the texture format guide for naming requirements.

Bezel Artwork accepts an external compatible image through its resource
picker and draws around the original picture. No bezel artwork is supplied.
These mods require files you install separately; they are disabled initially.

## Files and saves

Original Memory Cards are stored in `saves/` beside the executable. Back up
this folder before replacing a build. No personal cards are shipped. Exit
normally before copying cards. To bring existing EU saves across, copy your
backed-up `card1.mcd` / `card2.mcd` while the game is closed; never overwrite
your only copy. Keep US and EU cards separate.

The runtime may create caches and diagnostic files in this same writable
folder. They can contain paths to your files; review them before sharing.
The development session logger/controller replay is not part of this package.

## Known limits and test status

Original PAL simulation remains approximately 50 Hz. True 16:9 widescreen,
interpolated 100/120 FPS, independent normal-speed fast-forward music and
fast-forward mute are deliberately omitted. A television reporting 100 Hz
VRR does not establish 100 different game images.

Regular gameplay, area changes and save/full-exit/restart/load were manually
validated through Dwarf Village on the previous preserved EU build. Short
five-language area/geometry regressions and feature tests also passed there.
See `TEST_STATUS.md` for the release candidate's separate acceptance status.
The entire campaign has not been validated. This candidate still needs a
final hands-on launcher and controller acceptance test before redistribution.

## Credits and licensing

Based on TombaRecomp by mstan, PSXRecomp and recomp-ui contributors, with
psx_tomba used as a research reference. Original Tombi!/Tomba! belongs to its
respective rights holders. OpenBIOS is supplied under its accompanying MIT
notice; no Sony BIOS is bundled. See LICENSE and licenses/ for notices.
The project/framework license is PolyForm Noncommercial 1.0.0; this package
does not grant commercial distribution rights or rights to original game data.
Do not redistribute game images, extracted assets or generated game source.

## Controller and startup checks

Disconnected selected controllers are checked independently of hotplug events;
missing devices are retried at bounded intervals. A virtual-device regression
passed. The owner also completed an RC2 Razer test without a disconnect; this
is positive evidence, not a guarantee that every intermittent failure is gone.
Startup measurements distinguish launcher first paint from guest boot, not the
first visible gameplay frame. No disc/cache integrity checks were removed.
Keep this candidate in a separate folder and copy cards only while both games
are closed. Never replace the only copy of a card.

RC3 hashes the same complete disc/cache bytes using the Windows system SHA-256
provider where available, with the portable implementation retained as fallback.
A short warm-start measurement improved from 2.39 to 1.07 seconds before guest
execution; this is not a first-visible-game-frame timing guarantee.

## Final candidate

RC3 was accepted by the owner as visually good and reliable. RC4 additionally
fixes HQ voice processing suppressing newly starting CD/XA movie audio: the
complete original mix now passes through immediately. Fresh proof is required
before enhanced voice processing resumes. The 180-ms stability buffer remains;
no video delay, game-clock change or sequence-specific quest patch was added.
The owner has now accepted RC4 in German and French, including Seamless Loading
and correctly synchronized cutscenes. This is scoped manual acceptance, not
certification of the entire campaign in all five languages.

See [Steam setup](STEAM.md) to add the EXE as a non-Steam game. There is no
unverified automatic Add to Steam button and no Steam data-file editing.
Holding Circle to skip scripted scenes is deliberately not implemented.
See [final report](FINAL_REPORT.md) for tests, scope and known limits.
