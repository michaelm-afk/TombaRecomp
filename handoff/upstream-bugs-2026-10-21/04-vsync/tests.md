# VSync startup regression matrix

Use a separate settings directory; do not overwrite player cards. No gameplay
progress is needed. These are UI integration checks, not a claim that they
were newly automated in this package.

For On, Off and Adaptive separately:

1. Start the actual host launcher and select the mode.
2. Play, then quit normally.
3. Check `[video] vsync` in the host's own `settings.toml`:
   On → `on`, Off → `immediate`, Adaptive → `adaptive`.
4. Restart: the same mode must be selected.
5. If the GL debug endpoint is enabled, query `video_info` without mutation
   arguments and inspect `gl_swap_interval`. Off should request 0. On requests
   1 only where the host policy allows synchronized swaps; Adaptive may fall
   back to 1 on a driver that does not support -1. Scanout is not proved by
   this value alone.

Set `vsync = "vrr"` manually, reopen the launcher and leave its On row
unchanged: the stored VRR value must be preserved. Explicitly choosing Off or
Adaptive must replace it. An absent/invalid legacy row must not introduce a
different mode accidentally.

Also run the framework's existing `video_enhancement_settings_test` target
for parser/writer roundtrips. It previously passed despite missing launcher
wiring, so it cannot replace the UI checks above. Upstream PR #605 records an
actual R4 launcher-to-settings integration check.
