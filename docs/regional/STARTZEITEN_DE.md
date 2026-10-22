# Regionale Startphasen – lokale Messung vom 22.10.2026

Die Launcher-Ansicht ist bei allen drei Varianten schnell bereit. Der auffälligste
lange Start in frisch kopierten Paketen steckt vor dem Gaststart in der vollständigen
ABI-Prüfung der nativen DLLs. Ein schneller EU2-Prototyp mit vorhandener Prüfmemo
ist deshalb kein fairer Gegenbeweis zu einem frisch kopierten EU1-Paket.

## Bedingungen und Ergebnisse

Originale Releasepakete wurden ausschließlich in private Vergleichsordner kopiert.
Direktstarts verwenden OpenGL, native Auflösung, frische Testkarten und stumme
Audioausgabe. Die automatische Overlay-Kompilierung war für die Messungen
deaktiviert, damit vorhandene native Caches und Fallbacks unterscheidbar bleiben.
Die vollständigen Disc-Prüfungen bleiben aktiv. Zeiten ab Prozessstart, Sekunden:

| Variante/Zustand | Launcher bereit | Gaststart | erstes VBlank |
|---|---:|---:|---:|
| USA, erster abgeschlossener ABI-Durchlauf | separat 0,563 | 113,532 | 113,641 |
| USA, unmittelbar wiederholt | — | 1,157 | 1,250 |
| EU1, erster abgeschlossener ABI-Durchlauf | separat 0,609 | 47,859 | 47,953 |
| EU1, ABI-Memo vorhanden, neuer Resident-Cache | — | 2,610 | 2,703 |
| EU1, unmittelbar wiederholt | — | 1,688 | 1,797 |
| erster EU2-Prototyp, ABI-Memo vorhanden | — | 1,062 | 1,156 |
| neuer EU2-Launcher, Oberfläche vor Seamless-Integration | 0,797 | separat geprüft | separat geprüft |
| fertiger EU2-Launcher mit Seamless, UI-Test | 0,489 | PLAY → Originalauswahl bestanden | — |

Launcher-Messungen endeten zunächst ohne PLAY; ihre Zeiten dürfen nicht als
vollständige Spielstarts gelesen werden. VBlank/Gast-PC bezeichnen ebenfalls
noch kein steuerbares Spielbild. Der abschließende UI-Test betätigt tatsächlich
PLAY und erreicht die originale EU2-Sprachauswahl.

Die ersten 60-Sekunden-Läufe mit noch nicht abgeschlossener ABI-Prüfung sind
Timeouts, keine erfolgreichen Startmessungen. Es wurde kein Betriebssystem-
Dateicache kontrolliert geleert; „erster ABI-Durchlauf“ bedeutet keine garantierte
OS-Kaltstartmessung. Kleine Unterschiede einzelner Läufe sind keine stabile Rangliste.

## Einzelne Phasen

Die instrumentierten privaten Gegenstücke liefern verschachtelte Host-Timings;
Eltern- und Kindzeiten dürfen nicht addiert werden. Beim USA-Spieltest betrugen
Overlay-Worker/Join rund 408 ms, Disc-Hash 252 ms und Seamless-Aktivierung 255 ms.
Beim EU1-Spieltest waren es rund 254 ms, 450 ms und 1118 ms; Geometry-Aktivierung
lag unter 1 ms. Im vergleichbaren EU2-Spieltest: Overlay-Worker/Join rund 24 ms,
Disc-Hash 430 ms und Seamless-Aktivierung 1156 ms. Der anfängliche Resident-Pack-Aufbau des EU2-Tests dauerte rund
1229 ms. Dateihashes und alle abgeleiteten Inhalte werden dabei geprüft.

Die warmen Direktstarts zeigen eine kleine verbleibende EU1-Mehrzeit, überwiegend
passend zur größeren Disc und dem größeren Resident-Katalog. Das ist eine
Interpretation dieser Stichprobe, keine vollständige Erklärung jedes früheren
Startproblems. In den Messlogs erschien kein gestarteter Python-/Compilerlauf.
Native Ausführung wurde zusätzlich mit Laufzeitzählern nachgewiesen; normale
Interpreter-Fallbacks sind kein Beleg für einen im Hintergrund laufenden Compiler.

Die GL-Initialisierung war in den warmen Läufen zusammen mit dem Gaststart nach
rund 1–2 Sekunden beendet. Das CLI-Log hat für diese Teilphase keine unabhängige
feingranulare Uhr; daraus wird keine erfundene reine Rendererzeit abgeleitet.

## Tatsächlich nachgewiesene Spielerkontrolle

Der gemeinsame Controller-Test startet normal über Intro/Titel/Sprachauswahl,
bestätigt originale Dialoge und beweist anschließend Bewegung und Sprung. Kein
RAM-Schreiben, kein Snapshot, keine veränderte Questvariable und kein Turbo.
Die genauen Ergebnisse einschließlich Host-Timings stehen in
`STARTUP_SEAMLESS_TESTS.json`. USA erreichte die nachgewiesene Bewegung nach
72,438 s, EU1 nach 102,906 s und EU2 nach 102,891 s. Das enthält bewusst die ursprünglichen Spielmenüs,
Dialoge und Wartefenster des identischen Tests, nicht nur die Host-Initialisierung.
PAL läuft regulär mit 50 Hz, USA mit 59,94 Hz; gleiche framebasierte Eingaben
brauchen daher unterschiedlich lange. Sprachwahl und Originalablauf unterscheiden
sich zusätzlich. Diese Zahlen sind keine minimale „Zeit bis spielbar“ bei optimalen
menschlichen Eingaben und kein Hinweis auf verlangsamte PAL-Emulation.

## Sicherer Direktstart und praktische Verbesserung

`START_SCES01330_DIREKT_TEST.cmd` startet eine separate Kopie des offiziellen
EU1-Builds direkt. Er übernimmt deren ausgelieferte Konfiguration und Mods;
im vorgefundenen Originalpaket existierten keine zusätzlichen persönlichen
`settings.toml`-/`input.ini`-Dateien. Weitere Einstellungen dieser Kopie bleiben
erhalten. Die Originalpakete und echten Karten werden nicht verwendet oder geändert.

Der Starter prüft bei jedem Aufruf SHA1 **und Größe des gesamten Daten-Tracks**,
prüft die Bootdatei auf Übereinstimmung und übergibt dieselbe Disc an die Runtime.
Diese führt ihre normalen Kompatibilitäts- und Modprüfungen weiterhin aus. Die
vorgeschaltete Trackprüfung kommt zur gemessenen Prozessstartzeit hinzu.
Die separaten dauerhaften Karten liegen in `source/build-startup/eu1-manual-cards`.
Logs: `source/build-startup/comparison/eu1/diagnostics`.

Die einfache Verbesserung ist der separate Direktstart mit dauerhaftem geprüftem
Native- und Resident-Cache. Die vorhandene ABI-Memo wird erst vom normalen
vollständigen Prüfdurchlauf erzeugt; pro geladenem Modul bleiben die ABI-Gates
aktiv. Kein Cache oder Prüfschritt wird zugunsten einer schnellen Zahl entfernt.
Der Diagnoseversuch ohne Native-Cache (EU1: Gaststart 2,391 s) diente nur der
Ursachentrennung und wird ausdrücklich nicht als Starter ausgeliefert.

Reproduzieren aus `source`:

```powershell
python -I -B tools/regional/measure_startup.py --mode direct --repeat 2 --timeout 180
python -I -B tools/regional/measure_startup.py --mode launcher --repeat 1 --eu2-launcher
```

Rohbelege liegen in `source/build-startup/measure-*`, die Controller-Gegenproben
in `source/build-eu-qa/startup-*-normal-*`. Die Tabelle und maschinenlesbare
Zusammenfassung unterscheiden Releasekopien, den ersten Prototyp und den neuen
Launcher-Candidate.
