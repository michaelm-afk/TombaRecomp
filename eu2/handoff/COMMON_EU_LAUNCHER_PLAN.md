# Common European launcher: implementation assessment

## Findings

Both backends already compile the same recomp-ui and PSXRecomp launcher implementation. EU2 has no separate UI source implementation. However, the current runtime loads one game configuration and its mod capabilities before opening the launcher (`main.cpp`: load_game_config around 15985; run_window around 17665). The EU1 executable links the SCES_013.30 boot dispatcher; EU2 links SCES_013.31. Their regional MAIN hooks, loaders and native cache namespaces differ.

The existing [game] discs/disc_serials roster supports multiple CDs belonging to one backend, not multiple compiled regional backends. Adding SCES-01331 to EU1's accepted serial list would not select the EU2 dispatcher/mod profiles and is unsafe. The disc verification callback identifies the selected disc and gates Play; it currently does not select another game configuration or backend. Existing relaunch helpers belong to Generate/Rebuild, not a shipped regional profile transition.

## Smallest maintainable integration

1. Keep two already verified native backends. Extend the existing EU1 entry host with a two-entry European profile catalog (serial, full data-track size/hash, backend and config paths, supported capabilities).
2. Add one generic host-driven profile handoff at disc selection, outside all file-picker functions. After verifying the selected profile, close the current launcher cleanly and reuse the process-launch helper to open the appropriate existing backend with its regional config. The UI library remains shared. No new executable picker, custom file dialog or UI fork.
3. Store only last selected profile/disc in a small common selection record. Keep settings, mod state, resident caches and cards in separate regional roots; do not migrate or overwrite old installations or existing paths.
4. Each backend exposes its own verified mod catalog. EU1 retains its renderer/FMV capabilities; EU2 retains tested Geometry/PGXP/Seamless and hides unsupported FMV/Widescreen.
5. Package both backends under one European distribution with one documented entry point, English disc-selection instructions and full upstream patches (game, UI bridge if needed, framework bridge). Keep exact codegen/cache identities separate.

## Scope gate and estimate

This needs a bounded framework/launcher host extension, not only regional TOML files. Expected surface: approximately 5-8 implementation/build files plus profile catalog and tests, roughly 300-600 source lines. Order-of-magnitude estimate: 1-2 development days and about 1 test/integration day. This is an estimate, not a measured delivery promise. The owner approved this scope. The generic framework handoff and shared UI verdict bridge are implemented; current evidence and packaging instructions are under europe/.

## Acceptance

Automated serial+full-hash routing for both discs; malformed/unknown inputs rejected; cold start and persisted cross-region selection; per-region settings/card isolation; all ten original language MAIN programs; shared loader regression for EU1 and EU2; failed handoff leaves settings/cards intact; relocated clean package without development tools; source and binary privacy/dependency checks; clean source reconstruction/build. Reuse already passed EU2 geometry/PGXP and decoder evidence instead of repeating campaign tests. Native file-dialog and actual save-sign operation remain owner-run manual acceptance without desktop automation.

## Preserved evidence

The complete isolated EU2 source reconstruction, recompiler/runtime rebuild, 65 native pairs and allowlisted package staging passed before this architecture change (private receipt: build-eu2-closeout/pc-mods-v2-clean/result.json). It was built at checkpoint 2bad1db and precedes the prepared fresh-default corrections. It is retained as build evidence and backend input, not delivered as the new common European package. Existing release archives and personal cards are preserved.
