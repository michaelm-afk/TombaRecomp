# Audio Sync Fix

Audio Sync Fix is enabled by default for new profiles. It reduces host buffering
and prevents accelerated boot/fast-forward audio from building a delayed queue.
After a real presentation underrun it also avoids queuing accelerated catch-up.
Guest speed and SPU simulation are unchanged. Fast-forward is intentionally mute.

There is no buffer slider. ON uses a fixed 80 ms target; OFF restores the game's
configured fallback. Existing enabled/disabled settings remain authoritative;
legacy target_ms values are ignored. Changes apply at the next game start.
High Quality SPU / Enhanced Audio is independent. Quick Mods and Mods use the
same normal saved feature state. No account or network service is involved.

A long display-mode switch may still cause brief silence while recovering.
These host-buffer changes do not measure or control external TV/receiver delay.
The shared runtime uses no regional game addresses. Platform and regional
listening checks remain necessary; this is not a campaign-wide guarantee.
