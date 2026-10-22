# RC2: regional verification after handoff

The owner's manual test found that SCES-01331 was rejected by the shared launcher's Play gate. EU1 continued working. The defect was configuration lookup, not disc data or native backend dispatch.

## Reproduction and cause

A fresh extraction of the original combined Windows ZIP was used with the actual supported SCES-01331 CUE/BIN, without desktop automation. Starting the packaged EU2 executable with the package root as its working directory loaded the root EU1 game.toml. Its log reported expected SCES-01330, the actual disc SCES-01331, and incompatible EU1 game identity for the EU2 mod packages. Starting the same packaged binary from an external working directory loaded its own SCES-01331 config and reached original PAL execution.

The process handoff selected the right executable and forwarded the complete disc path correctly. Both packaged game.toml files and fingerprints were correct. However, resolve_existing_runtime_path checked a relative path in cwd before checking the executable directory, contrary to its comment. Windows child processes inherit cwd, so an EU2 child launched from the common package root inherited EU1's config. The display used the detected disc serial, hiding the expected-serial mismatch.

The original regional probes returned before configuration and the real launcher callback. The prior portable startup test used an external cwd. Neither covered this combination. Their passing results did not prove the real Play gate after handoff.

## Minimal framework correction

Relative runtime paths now resolve from the executable directory, without accepting an unrelated cwd file. Absolute paths retain their normal behavior. A catalog backend additionally requires its own adjacent game.toml; a missing file fails closed instead of inheriting another region's parent config. Native game code, UI, picker functions, hashes and verification policies are unchanged.

The optional --launcher-disc-check CLI runs after actual configuration/settings resolution and calls ae_disc_verify, the same callback used by the launcher. It exits before SDL/window creation and prints expected/detected serial, verdict, ISO state and active config. It cannot enable Play or weaken the callback. The new ZIP regression invokes it through actual process handoffs, using the actual discs and the packaged player binaries, from root, foreign-region and neutral working directories. It also checks remembered selection, explicit relative --game and missing own config. The portable boot test now uses package-root cwd and requires the correct regional config as well as original PAL execution.

## Unchanged supported identity

| Profile | Raw data bytes | SHA-256 | Native executable |
|---|---:|---|---|
| SCES-01330 Rev 1 | 492370032 | 25aa80a9f7000fc68a4621e17c60fd1505df540dd6ed383baac305c37087bce2 | TombiRecompEU.exe |
| SCES-01331 | 492306528 | 2eba3dfdd25f5d270d47f5fe408391971aa25ee09c6aac9874bba4e3bf6f32cc | backends/SCES-01331/TombiRecompEU2.exe |

The regional catalog still checks serial, exact raw size and complete SHA-256. The normal launcher still checks header/expected serial and configured CRC/SBI policies; these two profiles do not declare a CRC. No fingerprint has been substituted, no safety gate disabled and no game image supplied.

Card compatibility is deliberately left for the owner's manual tests using copies. No conversion or cross-region save experiment was performed for RC2. Standard cards remain regional; originals, user paths and earlier release archives are preserved. Visible GUI acceptance remains manual because desktop automation is excluded.
