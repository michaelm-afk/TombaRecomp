# Native wait evaluation

`TOMBA_NATIVE_IDLE_WAIT=ON` declares three audited SCUS-94236 edges. The
framework's ENHANCED profile selects native induction and REFERENCE selects
original polling. Selection is fixed at build time and recorded in execution
identity. The enhanced USA release selects this policy by default.

The complete 156-byte PsyQ `v_wait` at `0x80067D78` polls the frame counter at
`0x800974D4`. Its two edges are `0x80067DA0` and `0x80067DEC`. Each iteration
decrements one timeout word at `sp+16`; timeout callbacks remain at
`0x800665D0`, `0x8005CD88` and `0x80067E14`. No MMIO or other work occurs
inside the wait. `tomba_vwait_contract` compares the actual regenerated caller
with the shared induction path across event boundaries and timeout cases.

The main loop also has a read-only wait at `0x80016588`..`0x8001659F`.
It reads the unsigned 16-bit scratchpad counter at `0x1F8001E8`, compares it
with the fixed target in `v1`, and repeats while below that target. There are
no calls, stores or additional exits. Scratchpad is RAM, not device MMIO.
Its only check edge is `0x80016588`; its normal exit is `0x800165A0`.
`tomba_scratch_wait_contract` extracts that actual block and the runtime's
real load-timing helpers into private temporary files. It compares registers,
load pipeline, clock, event and exit continuation with skipping disabled and
enabled at cycle scales one and two. Retail-derived instructions are never
committed.

The existing engine verifies stable iterations, advances normal device clocks
and preserves real exit/interrupt delivery. Netplay and precise diagnostics
retain original polling. Existing native geometry and original-disc overlay
caches are preserved equally in A/B builds.

Early private whole-detector measurements saved about 37% CPU per frame in
the opening scene. Activation receipts show that gain came from the main-loop
scratchpad wait, not the SDK wait. These were diagnostic exploratory runs
under background host load; final production qualification remains pending.
Central Beads `beads-ko9b`, `beads-wuhs` and `beads-fobc` hold raw evidence and
limitations, related to optimization campaign `beads-2wy8.1`.
