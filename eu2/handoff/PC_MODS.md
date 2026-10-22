# SCES-01331 PC improvements

All implementations are shared with the official game/framework. No second renderer, loader, SPU or geometry implementation is maintained.

| Feature | Candidate status | Evidence and limits |
|---|---|---|
| Geometry Optimization | Optional, ON by default | Shared EU adapter/HLE; three complete EU2 body guards, five PAL languages, 200 isolated original-vs-HLE batches per routine per language. Initial scene coverage, not full campaign. |
| PGXP Precision | Optional, OFF by default | Shared built-in plugin. Live exact packet dataflow, precise triangles and perspective arming demonstrated. Base hook flavor has reduced coverage; not full CPU propagation coverage. |
| Hybrid Controller | Optional, OFF by default | Same source/plugin and original digital/analog presentation policy; shared policy fixture passes. Physical-controller matrix remains manual. |
| High Quality SPU | Existing Audio setting | Shared shadow normalization, CD passthrough, mismatch fallback and OFF tests pass. Listening across the campaign remains manual. |
| Fast Forward | Existing runtime hotkey/settings | All 41 fractional-speed/presentation/override cases pass. Original PAL 50 Hz remains the normal speed. |
| HD Texture Packs | Optional, OFF by default | Strict SCES-01331 resource target; shared installer and synthetic real-GL replacement tests. No HD artwork is supplied; other regions' packs are rejected. |
| Bezel Artwork | Optional, OFF by default | Shared built-in mod, image resource and OpenGL presentation path. Shared source/ownership guard passes. User artwork and visual acceptance remain manual. |
| Seamless Loading | ON by default, switchable | Existing strict five-language profile, native batches and original fallbacks retained. |
| FMV Skip | Not offered | Original per-movie u16 totals table is 0x800779E4 in Spanish, 0x800779FC in EN/PT/SV/DA. A single fixed EU1 config pointer is unsafe. Need reviewed language-aware teardown metadata, bounds and movie-ID/asset mapping before reusing shared skip plugin. No constant-address workaround. |
| Widescreen Custom Renderer | Not offered | See WIDESCREEN.md. Fit, 16:9, 21:9 and 32:9 require EU2 camera/HUD/culling/overlay contracts; no stretched substitute. |

The official card picker functions are restored byte-for-byte at the recorded UI baseline. The only remaining UI source delta is exclusive creation in the blank-card formatter: New cannot truncate an existing file. This is independent of Browse and does not alter existing paths/cards. A refused creation may have no visible error; choose a new filename.
