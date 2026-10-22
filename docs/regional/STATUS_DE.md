# SCES-01331: Untersuchung und Entwicklungsstand

Stand: 22.10.2026. Lokaler Branch `feature/sces-01331`, Ausgangspunkt
`ec11a7e`, Release-Basis `v0.21.0-alpha`. Keine Veröffentlichung, kein Push,
kein Pull Request. Japan wurde nicht implementiert.

## Bestandsaufnahme und Schutz der Originale

Die ursprünglichen zwei Paketordner enthalten 761 Dateien (USA) und 535
Dateien (Europa). Die beiden zusätzlichen Dateien sind SHA-256-Sidecars für
die Release-ZIPs; die ZIPs selbst liegen nicht vor. Daher ist keine vollständige
ZIP-Verifikation gegen diese Sidecars möglich. Die entpackten Pakete wurden
nicht verändert oder als Testinstallation verwendet.

`ROMS/` enthält vier BIN/CUE-Paare, jeweils einen MODE2/2352-Datentrack mit
INDEX 01 bei 00:00:00. `SAVES/` enthält zwei echte EU1-Karten
(`card1/card1.mcd`, `card2/card2.mcd`); die anderen regionalen Save-Ordner
enthalten keine Dateien. Auch leere regionale Ordner bleiben erhalten.

Die vollständige lokale Dateiliste mit Größen liegt außerhalb des Repositorys
in `local-analysis/original-files.json`. ROMs, CUEs und Karten sind zusätzlich
mit SHA-256 erfasst. Release-DLLs/EXEs wurden nach Größe inventarisiert;
blockierende Rohzugriffe auf einzelne DLLs wurden abgebrochen, keine
Binärdateien verändert. Die regionalen ISO-Dateikataloge enthalten für jede
Datei LBA, Größe und SHA-256. Sie liegen ebenfalls in `local-analysis/`.

| Disc | Rohtrack-Bytes | SHA-1 | ISO-Dateien |
|---|---:|---|---:|
| SCUS-94236 | 280193760 | `c259ec7ff6ef4163913991f4e4db2eff71702818` | 1085 |
| SCES-01330 Rev 1 | 492370032 | `2505d958b4439d04844cadd3f968fc7432a48e00` | 2287 |
| SCES-01331 | 492306528 | `684dbf0ad03f872511046d40d3cc85b17d839dbf` | 2287 |
| SLPS-01144 | 289430064 | `c86baf702303e7e0963b99aff307b1c40e40478a` | 1076 |

Kennungen wurden aus `SYSTEM.CNF` und den tatsächlichen PS-X-EXE-Headern
ermittelt. USA und EU1 stimmen mit den offiziellen Track-Prüfsummen überein.
Für EU2/Japan identifizieren die angegebenen Hashes exakt die lokalen Inputs;
eine zusätzliche Redump-Revisionszertifizierung wurde nicht durchgeführt.
MD5, SHA-256 und EXE-Header stehen in `disc-comparison.json`.

Alle Extraktionen und Builds liegen im neuen Checkout unter ignoriertem
`disc/` bzw. `build-eu2/`. Native Tests verwenden frische Karten pro Lauf.
Der manuelle Start verwendet ausschließlich `build-eu2/manual-cards/`.
Es werden keine echten Karten importiert und keine Questzustände gesetzt.

## Offizielle Implementierung gegenüber neuen Änderungen

Bereits vorhanden: getrennte native US-/EU1-Backends, gemeinsamer Framework-
und Launcher-Code, SHA-geprüfte Disc-Vorbereitung, MIPS-zu-C-Recompiler,
Originalbyte-geprüfte native Overlay-Caches, Laufzeit-Fallback, Hardware-
Simulation mit SPU/Controller/Memory Cards, Mod-Katalog und regional gebundene
Seamless-/Geometry-/Widescreen-Policies. Die EU1-Integration kam mit
`93a1e4b`; Widescreen mit `3860b69`; Release-Paketabstimmung mit `de8c67c`.
Die vier Änderungen nach dem Release-Tag betreffen Dokumentation/Urheberschaft.

Neu: `eu2/` als isoliertes SCES-01331-Backend, eigene Disc-/Bootkonfiguration,
Original-Selector-Codegenerierung, fünf sprachabhängige native AOT-Profile,
lesende Testdiagnosen und überprüfte Geometry-Korrespondenzen. Nur die
MAIN-Fingerprint-/GAME-Ableitung wurde um optionale Disc-/Sprachparameter
erweitert; bestehende EU1-Aufrufer behalten ihre Standardwerte. US-/EU1-
Buildziele und Enhancement-Implementierungen wurden nicht umgebaut.

## EU1 gegenüber EU2

2.286 Dateinamen sind gemeinsam; 1.493 davon sind bytegleich, 793 verschieden.
Die Boot-Dateinamen unterscheiden sich zusätzlich. Beide Discs enthalten
neun MAINs. Der originale EU2-Selector nennt MAIN0/5/6/7/8, passend zu
Englisch/Spanisch/Portugiesisch/Schwedisch/Dänisch. Diese Auswahl wird durch
Controller-Eingaben und Live-Fingerprints geprüft, nicht durch Austausch der
Sprachdateien. Keine US-Texte oder künstlichen Sprachressourcen wurden eingebaut.

EU2-Boot: Entry `0x8001E1F8`, Load `0x80010000`, Text `0x9E800`,
Stack `0x801FFFF0`. MAINs laden bei `0x80010000`, Text `0x88800`;
Spanisch startet bei `0x8006BB18`, die anderen vier bei `0x8006BB30`.
Die Runtime erkennt SCES-01331 als PAL und protokolliert 50 Hz.

| Sprache | MAIN | GAME-Basis | Area-/Support-Linkbasis |
|---|---:|---|---|
| Englisch | 0 | `0x8009C450` | `0x800E7B28` |
| Spanisch | 5 | `0x8009C478` | `0x800E7B50` |
| Portugiesisch | 6 | `0x8009C478` | `0x800E7B50` |
| Schwedisch | 7 | `0x8009C458` | `0x800E7B30` |
| Dänisch | 8 | `0x8009C478` | `0x800E7B50` |

GAME wird aus der originalen `memset(...,0,0x988)`-Argumentkonstruktion
abgeleitet. Linkbasen werden unabhängig über 200 Eventtitel-Pointer plus
Backlink gefunden und gegen den originalen Type-F0-Loader abgeglichen.
Ein regionaler Konstantenoffset wurde nicht angenommen. Fonts, Menüs,
Dialoge und Audiodaten bleiben Original-Disc-Ressourcen; eine vollständige
sprachliche Inhalts-/Fontprüfung ist noch kein Bestandteil der Stichprobe.

Wichtige Referenzabweichung: Im untersuchten `psx_tomba`-Commit
`fb3b36715f6966c099be95564c155bd842003b76` passen die Boot-Hashes zum
jeweils benannten EU-Profil. Von den übrigen aufgeführten MAIN-/System-Dateien
passen jedoch jeweils 26 Hashes zur anderen lokalen EU-Disc. Daher dürfen
Profilnamen nicht als Adressbeweis verwendet werden. Der US-Vergleich passt
bei 25 Dateien, Japan bei 18. Details sind maschinell reproduzierbar in
`disc-comparison.json` und `tools/regional/compare.py`.

## Native Abdeckung und bekannte Lücke

Die gemeinsame AOT-Pipeline erstellt vollständige Sprach-MAIN-Rezepte sowie
Anfangsgebiete 0/1 und Dialog-/Info-/Options-/Game-Over-Supportbilder.
Originalbytes und native Ranges werden vor Installation geprüft. Eine
erfolgreiche DLL-Kompilierung allein zählt nicht als Spieltest.

Für `SYSTEM/G6OVER.BIN` (portugiesisches Game Over) erzeugt die gemeinsame
Discovery überlappende `producer_ranges`. Der Compiler lehnt dieses Bild
korrekt ab. Es wird vorläufig nicht nativ angeboten; die reguläre
Originalausführung bleibt als Fallback erhalten. Die übrigen Profile werden
erneut vollständig auditiert. Keine abgeschwächten Byte-/Seed-Guards.
Weitere Gebiete und nicht erfasste Einstiegspunkte behalten Fallback.

## Meilensteine und Testgrenzen

* A: Eigene Disc-Erkennung, nativer Selector, originale Sprachauswahl und
  regulärer englischer Spielstart sind beobachtet. Native MAIN-/Area-
  Ausführung ist im Laufzeitbericht nachgewiesen.
* B: Profile für alle fünf originalen MAINs und ihre eigenen Ressourcen sind
  implementiert. Alle fünf MAINs wurden live identifiziert und erreichen das
  Anfangsgebiet mit nativen MAIN-/Support-/Area-Modulen. Die Anfangsdialoge
  von Spanisch, Portugiesisch, Schwedisch und Dänisch wurden auf Screenshots
  visuell geprüft. Dies ist keine vollständige Inhalts-/Font-Abnahme.
* C: Englische Anfangsdialoge und reguläres Gehen sind nachgewiesen:
  X=64 auf X=74,9414 bei einem kurzen Rechts-Input. Gebietswechsel,
  physischer Controller, Speichern/Beenden/Neustarten/Laden und gegenseitige
  Kartenkompatibilität sind noch offen.
* D: Widescreen technisch analysiert, Geometry-Bindungen statisch geprüft;
  Seamless Loading, Geometry-HLE, Widescreen, PGXP, Hybrid Controller,
  SPU-HQ und Fast Forward sind für EU2 noch nicht als Features freigegeben.
  Die Basis verwendet Original-Geometry und Original-CD-Tasks. Keine
  ungeprüften Enhancement-Mods werden im EU2-Modkatalog angeboten.

Abschließende AOT-Abnahme: **65 native Paare, 54 Rezepte, 15.439 Guards**;
alle Paare gültig und alle Guards Originalbytes zugeordnet. Die vier letzten
Sprachtests hatten Laufzeit-Kompilierung abgeschaltet und jeweils mindestens
drei vorgenerierte native Modul-Loads. Englisch wurde zusätzlich im
OpenGL-Pfad gestartet; `GL GPU pipeline ready` ist protokolliert.
Das kompakte Protokoll steht in `TESTERGEBNISSE.json`, die vollständigen
lokalen Logs/Bilder unter `build-eu2/smoke-*`.

Der abschließende Originalvergleich stimmt mit der Bestandsaufnahme überein:
ROM-/Karten-Hashes und die komplette ursprüngliche Dateiliste samt Größen
sind unverändert. Der Konfigurations-Metadatentest für US/EU1 besteht;
die ursprünglichen EU1-GAME-/Fingerprint-Ableitungen wurden mit Originaldaten
ausgeführt. Kein vollständiger erneuter US-/EU1-Gameplay-Test wurde behauptet.

`eu2/analyze_geometry.py` prüft 15 vollständige Funktionskörper. Triangle und
Quad sind mit EU1 bytegleich. Flat unterscheidet sich nur durch einen intern
relokierten J-Sprung mit gleichem relativem Ziel. Kandidaten sind
`0x80022310`, `0x800225E4`, `0x800227EC`. Das rechtfertigt die spätere
Wiederverwendung derselben HLE, ersetzt aber noch keinen Differentialtest
oder die Store-PC-/Präzisions-/Widescreen-Bindung.

Die vorhandene Memory-Card-Simulation verwendet standardisierte `.mcd`-Karten.
Das sagt nichts über regionale Slot-/Save-Inhaltskompatibilität aus. Ohne
regulären Save-Roundtrip bleibt jede Region separat. CD-Task-/Ladeadressen
und Ressourcenverzeichnisse unterscheiden sich; Seamless benötigt zusätzlich
geprüfte Dateitabellen, Queues, SPU-Felder, Task- und Loader-ABI-Verträge.

## Gemeinsamer Launcher

Der neue Backend-Build nutzt dieselbe Launcher-Bibliothek und seine eigene
SCES-01331-Konfiguration mit exakten Track-Hashes. Eine gemeinsame Oberfläche
mit Dispatch zu mehreren Backends ist möglich, benötigt aber eine explizite
Disc-zu-Backend-Auswahl und getrennte Konfigurations-/Karten-/Cache-Namensräume.
Ein einziges US-Binary kann die anderen statisch generierten Bootprogramme
nicht allein durch Änderung der Disc-ID übernehmen. Der isolierte Ansatz
vermeidet Eingriffe in funktionierende US-/EU1-Targets und ist die erste Stufe.

## Japan: ausschließlich Machbarkeit

Das lokale SLPS-01144 bootet `SLPS_011.44`, Entry `0x80065D80`,
Load `0x80010000`, Text `0x8E000`, Stack `0x801FFFF0`.
Der Dateikatalog enthält nur ein PS-X-EXE statt eines EU-Selectors mit neun
MAINs und insgesamt 1.076 Dateien. `SYSTEM.CNF` nennt Stack `801fff00`,
während der EXE-Header `801ffff0` enthält; beide Befunde bleiben getrennt.
Japan benötigt NTSC-Timing statt PAL-Profilen.

Der Referenzbestand passt für 18 aufgeführte Dateien und enthält japanische
Symbole/Layouts. Das schafft eine brauchbare Ausgangsbasis, beweist aber
keine gleichen SDK-, Loader-, Text-, Font- oder Render-Adressen. Japanische
Glyphendekodierung, Glyphenatlanten, Textbreiten und Menüs müssen anhand der
Originalroutinen geprüft werden; englische Ersatztexte sind kein Port.
Ein sinnvoller Aufwandsschnitt ist: zuerst eigener Boot-/Overlay-Prototyp,
dann Text/Font-/Save-Abnahme, anschließend separat PC-Hook-Profile.
Das ist voraussichtlich ein eigener Portierungszyklus von mehreren
Entwicklungs- und Testtagen, mit derzeit geringer Schätzsicherheit. Eine
verlässliche Stundenangabe wäre ohne Code-/Laufzeitanalyse nicht begründbar.
Es wurden keine japanischen Buildziele oder Runtime-Hooks hinzugefügt.
# Ergänzung: separater Launcher- und Seamless-Teststand, 22.10.2026

Der erste EU2-Prototyp bleibt als Vergleichsstand erhalten. Der neue Build liegt
unter `build-eu2-launcher/native` und verwendet den vorhandenen offiziellen Launcher
sowie den gemeinsamen europäischen Seamless-Loader mit fünf gegen die Originaldisc
geprüften EU2-Profilen. Kurzanleitung: [EU2_LAUNCHER_TEST_DE.md](EU2_LAUNCHER_TEST_DE.md).

Der separate EU1-Direktstarter und die Messungen sind in
[STARTZEITEN_DE.md](STARTZEITEN_DE.md) beschrieben. Die ABI-Prüfung frisch kopierter
Native-Caches erklärt die größten beobachteten Verzögerungen; warme Starts sind
wesentlich kürzer. [STARTUP_SEAMLESS_TESTS.json](STARTUP_SEAMLESS_TESTS.json) trennt
Launcher, Gaststart, erste steuerbare Bewegung und genaue Testgrenzen.

Alle fünf EU2-Sprachen bestehen den neuen Live-Starttest; Bewegung/Sprung sind
englisch, Seamless aus und spanischer Original-CD-Fallback zusätzlich geprüft.
401 unterschiedliche GAM-Streams bestehen den Original-MIPS-Decodervergleich.
Save/Restart/Load und ein Gebietswechsel mit Rückweg bleiben manuelle Abnahmen.
Die Originalinventuren stimmen für 1308 Dateien überein (ROMs/Karten mit SHA256,
Releasepakete nach Dateigröße). Keine Veröffentlichung und kein Pull Request.

---

## Abschluss und Entwicklerübergabe

Der Kartenpfad des bisherigen EU2-Starters ist dauerhaft
`build-eu2-launcher/manual-cards/card1.mcd`. Der gültige spanische Save wurde
vom Besitzer nach Neustart auf Schwedisch geladen und anschließend unabhängig
mit einer Kartenkopie bestätigt. Der reguläre Hütten-Rückweg (Area 0,
Abschnitt 2 → 3 → 2) besteht mit Seamless: 4/19 → 8/29 → 12/39 Batches/Dateien.
Ein zusätzlicher erneuter Speichervorgang auf der Kopie bleibt manuelle Abnahme,
weil die Teststeuerung das Speicherschild nicht zuverlässig auslöste.

Browse wurde im vorhandenen Launcher und im portablen Spieler korrigiert:
Der eingebaute Browser beginnt bei der aktuellen Karte; ein Tooltip zeigt den
vollständigen Pfad. Vorhandene Karten/Einstellungen bleiben unverändert.

Der portable Spieler liegt außerhalb des Entwickler-Checkouts im lokalen
Arbeitsordner `SCES01331-Abschluss/Windows-x64`. Er enthält keinen Debugserver,
keine ROM, kein Sony-BIOS und keine persönlichen Karten. OpenBIOS ist mit
ausdrücklicher Zustimmung und Lizenzhinweisen enthalten. Frischer Start,
Disc-Gates, tatsächlicher Gaststart und Abhängigkeiten ohne Host-Werkzeuge
wurden geprüft. Originalinventuren stimmen weiterhin überein.

Die Entwicklerübergabe enthält Quellpatches gegen exakte offizielle Basen,
Buildanleitung, Berichte und die ergänzte Widescreen-Arbeitsliste. Isolierte
Quellrekonstruktion, Runtime-Neuaufbau und 65 native Paare / 15439 Guards
bestanden. Siehe `eu2/handoff/README.md`, `TEST_REPORT.md`,
`WIDESCREEN.md` und `CLOSEOUT_RESULTS.json`. Keine Widescreen- oder Japan-
Implementierung begonnen; nichts veröffentlicht oder weitergegeben.
