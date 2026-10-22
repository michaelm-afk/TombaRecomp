# PSXRecomp bug reports prepared for private review

Nothing in this directory has been submitted, published or sent to maintainers.
These are independent reports and small patches, not the EU port or its game
code. No disc, BIOS image, generated game code, card, screenshot or private
session log is included. All reproducer input is synthetic.

Official source snapshot checked on 2026-10-21:

- Framework: [RetroPortingToolKit/psxrecomp](https://github.com/RetroPortingToolKit/psxrecomp),
  master `958ae0e396f14d39c86e5c016d405fcdd96af4d5`.
  `mstan/psxrecomp` redirects to this repository.
- Tomba: [v0.20.2-alpha / master](https://github.com/mstan/TombaRecomp/commit/1b7bafa5afc3dfd08a4889f2361f9a177e6b0f52),
  commit `1b7bafa5afc3dfd08a4889f2361f9a177e6b0f52`, pins framework
  `03e635e86dceb540b7b6421ada7ee32cc28ca62b`.

| Report | Current official master | Tomba's pinned framework |
| --- | --- | --- |
| [HQ-SPU scale](01-hq-spu/REPORT.md) | Still present | Present |
| [Dynamic overlay forward exports](02-overlay-exports/REPORT.md) | Still present; residual coverage after #344 | Present |
| [Identical DLL restaging](03-overlay-staging/REPORT.md) | Still present | Present |
| [Launcher VSync startup persistence](04-vsync/REPORT.md) | Already fixed by merged #605 | Fix absent from pinned source |

Each patch declares its exact base. Apply reports separately; do not apply a
whole EU development commit. `fix.patch` contains only the runtime/tool fix;
tests are separate source files to make integration choices explicit. Run
`git apply --check /path/to/fix.patch` at the target framework root first.
The VSync patch is for Tomba's pin, not current framework master.

See [classification](CLASSIFICATION.md) for EU-only failures, non-bugs,
unconfirmed findings and a correction to the earlier HQ-SPU live-setting claim.
Public issue/PR searches included open and closed results. No exact existing
report was found for the first three defects; search coverage is recorded in
`evidence.json`. This does not prove that no unindexed discussion exists.

Validation is scoped to source revisions and the targeted reproducer outputs.
Release **source tags** were inspected; downloaded release executables were not
reverse-engineered or assumed to match a source tree. Do not claim every old
release is affected merely from an introducing commit date.

The upstream license is retained as `LICENSE.framework`. No relicensing or
broader game-resource rights are implied. Re-check upstream before forwarding.

## Finalization addendum, 2026-10-22

[HQ CD/XA startup suppression](05-hq-spu-cd-input/REPORT.md) is a separately
reproduced shared-framework issue, tested against the normalization-fixed RC3
revision. It has its own minimal patch and synthetic test. It is not presented
as a freshly verified current-official-upstream finding. Earlier reports and
patches retain their original exact bases and evidence.
