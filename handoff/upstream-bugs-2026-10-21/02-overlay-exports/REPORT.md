# Dynamic overlay patcher adds dllexport after an earlier unexported declaration

Project: PSXRecomp. File: `tools/compile_overlays.py`, `patch_generated_c()`.
Patch base: official master `958ae0e396f14d39c86e5c016d405fcdd96af4d5`.
Also source-confirmed at Tomba's pin
`03e635e86dceb540b7b6421ada7ee32cc28ca62b`.

## Reproduction

Run the supplied function-level synthetic regression against a framework tree:

```sh
python test_overlay_exports.py /path/to/psxrecomp --cc clang
```

The test executes the actual patcher function extracted from that file, with
an empty dispatch preamble. Its only C input is a pair of synthetic functions
where the first calls the second through a forward declaration. No generated
game code or disc is required. Clang syntax checking uses a Windows target
and a header-free fixture, so no retail/runtime assets are needed.

Expected: in-overlay declarations and definitions have identical export
attributes, compile on Windows Clang, and out-of-overlay calls use dispatch.
Actual: the regex annotates definition lines but not declarations ending in
`;`. After the earlier declaration is used, Clang rejects the later export
attribute. Typical diagnostic:

```text
error: redeclaration of 'func_80010004' cannot add 'dllexport' attribute
```

This was encountered while compiling EU overlays; it is a generic code
generation-tool defect, not proof that every existing US overlay triggers it.

## Fix and relation to existing work

`fix.patch` admits an optional semicolon in the export regex. The existing
in-overlay predicate remains in force. This does not change guest code,
addresses, dispatch semantics or the overlay ABI. The regression checks
declarations, definitions, removal of external declarations and external-call
dispatch, plus actual Clang syntax when requested.

[PR #344](https://github.com/RetroPortingToolKit/psxrecomp/pull/344) was merged
and fixes related export handling in shared generated headers/preambles.
However, the dynamic `patch_generated_c()` regex in checked master still has
this separate omission. Present this as residual coverage, not as a claim
that #344 was never merged. Static overlay handling is outside this patch.

Reference: [current patcher](https://github.com/RetroPortingToolKit/psxrecomp/blob/958ae0e396f14d39c86e5c016d405fcdd96af4d5/tools/compile_overlays.py).
