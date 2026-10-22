# SCES-01331: lokaler Entwicklungsbuild

Aktuelles Produkt: gemeinsames Europa-Paket mit SCES-01330/SCES-01331.
Build und Integration: `europe/DEVELOPER.md`; Benutzeranleitung: `europe/README_EN.md`.
Die folgenden Befehle bleiben fuer das bereits erhaltene regionale Backend
und fruehere Prototypen verfuegbar. Es wird keine zweite Oberflaeche gepflegt.

Eigenständiges Backend mit gemeinsamem PSXRecomp und gemeinsamem Launcher.
Keine Änderungen am US-/EU1-Buildgraph. Standard: PAL, 4:3, digitale Steuerung,
keine ungeprüften Gast-Enhancements. Native Module kommen ausschließlich aus
der geprüften SCES-01331-Arbeitskopie. Keine BIOS-/ROM-/Save-Dateien einchecken.

Initialisierung und Build ab Repository-Wurzel (Python 3.11+, Windows Clang,
CMake und Ninja im PATH; alternativ `TOMBI_TOOLCHAIN_BIN`):

```powershell
git submodule update --init --recursive
python -I -B eu2/build.py --disc 'Pfad/zur/eigenen/Disc.cue' --jobs 3
```

Der Build kopiert die geprüfte Disc nach ignoriertem `disc/eu2/`, extrahiert
den Selector und MAIN0/5/6/7/8, erzeugt nativen Selector-Code und baut
Original-MAIN-/Anfangs-/Support-Module mit der gemeinsamen AOT-Pipeline.
Die Loader-Linkbasis wird pro Sprache über MIPS-Instruktionen und
Eventtabellen-Backlink gegenseitig geprüft. Ungeprüfte Teilresultate werden
nicht installiert. Erster Build lädt ggf. gepinnte Framework-Abhängigkeiten.
Prototypische Debug-Tools bleiben für die lokale Diagnose eingeschaltet.

Kurzer Test mit frischen, isolierten Karten:

```powershell
python -I -B eu2/smoke.py --language en
python -I -B eu2/smoke.py --language da --start
python -I -B eu2/smoke.py --language es --play
```

Diagnosen und Bilder landen unter `build-eu2/smoke-*`. `--start` prüft die
originale Anfangsszene einschließlich Live-Spieler im Dialogzustand.
Tests verändern keine
Questzustände und laden keine RAM-Snapshots. `--play` verwendet originale
Menü-/Dialogeingaben und prüft MAIN-Identität und Anfangsbewegung; das ersetzt
keinen Gebietswechsel oder Memory-Card-Roundtrip.

Direkter manueller Start (PowerShell, ab Repository-Wurzel):

```powershell
& ./build-eu2/native/Tombi__SCES_01331_Prototype.exe --game ./eu2/game.toml --disc ./disc/eu2/disc.cue --memcard-dir ./build-eu2/manual-cards --no-launcher
```

Für bequemes Starten siehe das lokale `START_SCES01331_TEST.cmd` im
übergeordneten Arbeitsordner. Originalkarten nicht auswählen/importieren.
Eine eventuell angezeigte BIOS-Fingerprint-Warnung ist getrennt zu prüfen;
die während dieser Untersuchung frisch erzeugten OpenBIOS-C-Dateien waren
gegenüber dem gepinnten Quellstand inhaltsgleich (nur der Stamp unterschied sich).

Status und noch offene Freigaben stehen in
`docs/regional/STATUS_DE.md`. Dieser Build ist kein Veröffentlichungsartefakt.
