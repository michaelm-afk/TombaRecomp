# Classification of findings from the EU port

## Confirmed defects in shared upstream code

- HQ-SPU sample normalization: source-confirmed in current official master,
  four individually inspected release source tags and Tomba's pin. Reproduced
  with preserved US object files and with current official source fixtures.
- Dynamic overlay forward export attributes: source-confirmed and reproduced
  on current official source using synthetic C and Windows-target Clang.
  The real failing input during porting was EU overlay compilation; occurrence
  in every existing US overlay is not claimed.
- Non-idempotent staging of identical audited DLLs under Windows write locks:
  source-confirmed in current official source; the focused lock simulation
  fails before and passes after while retaining hash/audit rejection cases.
- Startup VSync bridge: confirmed in Tomba's pinned framework and manually
  observed in the EU host using that shared code. Already fixed in current
  framework master by #605. Keep its Tomba integration report separate from
  the three still-present framework defects.

## EU implementation defects, not original US defects

- US-plus-EU language-patch event title wrapping and incomplete menu coverage.
  These were limitations/errors of our donor-data approach, not failures of
  the original US translation. Native EU MAIN programs superseded that path.
- Early EU Seamless card-load white screen: our protection window rejected
  a legitimate system-list buffer and the adapter nested whole task calls
  across original coroutine waits. The replacement preserves original stacks
  and narrowly accelerates verified loading waits. Not an upstream card bug.
- Manual session script initially omitted the existing launcher entry option;
  the resulting Keyboard default was our wrapper integration problem.
- US geometry batches use US vertical bounds. EU PAL batches need 256 rather
  than 224. Correct US bounds are not an upstream defect merely because EU
  requires a different contract.

## Correct behavior or missing external prerequisites

- Digital mode folding the left stick into D-Pad directions is intentional.
  Analog mode separates those sources. No reversed mode mapping was proved.
- HD enabled with zero external replacement files produces original artwork.
  A supplied synthetic example did produce matching replacements in EU.
- Bezel needs an image and visible margins. It was visually demonstrated.
- Base-flavor PGXP has documented partial coverage. The grass-area counters
  prove actual corrections; a zero-hit Dwarf Village sample alone was not a
  dead-option bug. Full PGXP hook-flavor qualification is separate work.
- Retired frame-interpolation package entries are not proof of functioning
  frame generation. The US release notes explicitly retired blending.

## Candidates and corrected earlier claims

- Approximately 100 FPS in the owner's exclusive-fullscreen session is not
  established as doubled simulation. Controlled EU samples measured about
  50 guest frames and GL outputs/s; NTSC gameplay about 59.98 guest frames/s.
  Old logs contain short faster intervals without sufficient pacing/turbo
  attribution. New diagnostics distinguish these. Do not file a universal
  double-speed bug or claim physical scanout from GL swap counts alone.
- Related existing work: framework #699 is merged; #713 (video-standard
  cadence re-probe) and #723 (Windows windowed/borderless GL pacing) were open
  at review time. Their R4 reproductions are not additional Tomba reproductions.
- A blue hut-exit fixture involved manipulated progress/inventory. Regular
  owner play through the hut and onward succeeded. Do not submit the fixture
  failure as a confirmed normal-game or original US bug.
- **Correction to an earlier report:** assigning only `g_audio_spu_hq` in the
  second launcher block does not prove a broken live HQ toggle. This is a
  teardown/soft-return path leading to `session_reboot`, which calls
  `spu_shadow_set_enabled()` and `spu_init()` again. The extra local setter is
  conservative/redundant wiring, not an independently confirmed upstream bug.
- The soft-return/netplay launcher's VSync mapping warrants its own integration
  test; missing source wiring there is not evidence of an offline in-game
  settings failure. No standalone confirmed report is supplied without a
  demonstrated reachable reproduction.

No complete game compatibility, release binary identity or hardware-specific
paddle behavior is inferred from these targeted tests.
