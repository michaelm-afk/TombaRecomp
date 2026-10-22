# TombiRecomp Europe — SCES-01330 and SCES-01331

Extract the complete package into a writable folder. Start **TombiRecompEU.exe** in the top-level folder. This is the shared European launcher entry point.

Choose your original European CUE using the normal **Browse For Disc** button. Keep the matching BIN next to its CUE. The launcher checks the serial, complete raw data-track size and SHA-256. Only the recorded SCES-01330 Rev 1 and SCES-01331 revisions are accepted. Wrong or modified discs are rejected.

Selecting another supported region closes the current launcher and opens the matching native backend using the same launcher interface. Press **PLAY**, then use the original language selector:

- SCES-01330: English, French, German, Italian, Dutch.
- SCES-01331: English, Spanish, Portuguese, Swedish, Danish.

The top-level entry point remembers the last verified disc in europe-selection.toml. Start it again to return to that region. If you move a disc and the recorded location is unavailable, the launcher allows you to choose it again. The package does not contain a game image.

Settings and mods are region-specific: EU1 uses settings.toml and mods/state.toml beside the main executable; EU2 uses those files under backends/SCES-01331. Default cards are saves/SCES-01330/card1.mcd and card2.mcd for EU1; backends/SCES-01331/saves/SCES-01331/card1.mcd and card2.mcd for EU2. Existing selected card paths remain supported. Old installations and cards are not moved or imported automatically. Back up a valued card before choosing a copy through the original Memory Card Browse.

A region handoff discards uncommitted edits from the outgoing launcher to prevent a foreign disc or partial settings from being written to that region. Close/reopen the current region after editing settings before changing region if you want to retain those edits. In-game profile changes are blocked; exit to the launcher first.

No installed Python, PowerShell, compiler or development tools are required. Freely licensed OpenBIOS and runtime fallback dependencies are included with notices; no Sony BIOS, ROM, personal save or private logs are included. See FEATURES.md and MANUAL_TESTS_DE.md for limits and remaining manual acceptance.
