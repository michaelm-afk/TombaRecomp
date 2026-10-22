# Features by European disc

| Feature | SCES-01330 | SCES-01331 |
|---|---|---|
| Original PAL timing and five original languages | Supported | Supported |
| Seamless Loading | ON by default | ON by default |
| Geometry Optimization | ON, optional | ON, optional; 3000 isolated original-code comparisons passed |
| PGXP Precision | Optional, OFF | Optional, OFF; exact dataflow/perspective effect proved |
| High Quality SPU | ON | ON |
| Fast Forward | Shared hotkey; 4x hold default | Same |
| Hybrid Controller | Optional, OFF | Optional, OFF |
| HD Texture Packs | Optional matching SCES-01330 pack | Optional matching SCES-01331 pack |
| Bezel Artwork | Optional external image | Same |
| FMV Skip | Optional, OFF | Hidden: live language-aware teardown binding unimplemented |
| Widescreen renderer (Fit/16:9/21:9/32:9) | Optional, OFF | Hidden: camera/HUD/cull/overlay contracts incomplete |

Fresh defaults follow the official EU1 profile: OpenGL, VSync OFF, 1080p internal resolution, windowed output, legacy AA ON/post-AA OFF, 44100 Hz requested audio rate (device may differ), digital controller. Saved preferences take precedence and are never reset by the profile catalog.

The original Memory Card Browse implementation is unchanged. The independent New-card formatter refuses to truncate existing files. No replacement artwork is supplied. PGXP uses the base codegen flavor with reduced coverage. No complete campaign, exhaustive hardware/controller/audio or every save/area-transition certification is claimed. Portuguese game-over retains the already audited interpreter fallback. Detailed upstream source contracts and tests accompany the developer handoff.
