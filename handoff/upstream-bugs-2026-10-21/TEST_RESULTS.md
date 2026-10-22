# Targeted upstream reproducer results

Public source baseline: framework master
`958ae0e396f14d39c86e5c016d405fcdd96af4d5`, captured on 2026-10-21.
Only the affected functions/modules were tested. Previously passed campaign,
card and renderer tests were not repeated for this report preparation.

Environment: Windows, Python 3.13, Clang 22.1.8 (LLVM
`ca7933e47d3a3451d81e72ac174dcb5aa28b59d1`), GNU Windows target.

| Focused test | Unmodified official source | Same source plus isolated fix |
| --- | --- | --- |
| SPU normalization / verifier | FAIL, exit 1 | PASS, exit 0 |
| Overlay declarations plus actual Clang syntax | FAIL, exit 1 | PASS, exit 0 |
| Identical locked staging plus audit boundaries | FAIL, exit 1 | PASS, exit 0 |

SPU output:

```text
before: enabled=1 proven=0 level_ratio=32771.359375 correlation=1.000000
after:  enabled=1 proven=1 level_ratio=1.000103 correlation=1.000000
```

The fixed SPU test deliberately introduces a 32-fold mismatch later. Its
expected `DEGRADED` message proves the fallback path remains enabled; it is
not a failure of the corrected equal-level test. Disabled output is checked
byte-for-byte. No audio device is opened.

Original export patcher:

```text
FAIL: missing exported declaration: 80010000
FAIL: missing exported declaration: 80010004
error: redeclaration of 'func_80010004' cannot add 'dllexport' attribute
```

Fixed export patcher:

```text
PASS: declaration/definition exports and external dispatch
```

Staging:

```text
before: FAIL: identical audited target was unnecessarily replaced
after:  PASS: identical locked targets, changed targets and audit boundaries
```

All four `fix.patch` files passed `git apply --check` against their declared
private source fixtures. VSync uses the old Tomba pin as its base; the other
three use current official master. No patch was applied to a foreign repo.
The VSync serializer tests and existing local launcher mapping tests had
already passed; actual launcher restart instructions are supplied separately,
without claiming a newly performed end-to-end UI test here.

CD/XA addendum: synthetic first-CD-block preservation fails with shared RC3
source, then passes with report 05 patch. Fresh voice reproof and existing
normalization/mismatch/off checks also pass. The owner identified the affected
sequence as a prerendered FMV. Exact scene replay remains owner acceptance.
