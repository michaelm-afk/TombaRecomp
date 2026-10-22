# SCES-01331: separater Launcher-Teststand (22.10.2026)

Im Ordner `Tombi` **START_SCES01331_LAUNCHER_TEST.cmd** doppelklicken.
Der Starter prüft den vollständigen Daten-Track und öffnet den vorhandenen
offiziellen Launcher. Dort **PLAY** wählen, danach die originale Sprachauswahl
Englisch, Spanisch, Portugiesisch, Schwedisch oder Dänisch bedienen.

Der neue Build liegt unter `source/build-eu2-launcher/native`. Der bisherige
Direktstart `START_SCES01331_TEST.cmd` und `source/build-eu2/native` bleiben
als erster Vergleichsstand erhalten. Nicht beide EU2-Starter gleichzeitig öffnen.

## Einstellungen und Karten

- Controller im Launcher unter **Controller** konfigurieren. Die reguläre
  Eingabeverarbeitung des Frameworks bleibt erhalten; Tests verwenden dieselben
  digitalen PSX-Tasten. Ein physischer Controller wurde nicht automatisch getestet.
- Grafik, Auflösung, Vollbild und Audio stehen in **Settings** zur Verfügung.
  Standard ist OpenGL, 1080p, originales 4:3. Die automatischen Spieltests verwenden
  native Auflösung und stummen SDL-Ausgang; die reale Audioausgabe bitte manuell prüfen.
- **Mods → Seamless Loading** ist im neuen Teststand standardmäßig aktiv und
  lässt sich für den nächsten Start deaktivieren. Widescreen, Geometry Optimization,
  PGXP und weitere ungeprüfte EU2-Erweiterungen sind nicht angeboten/registriert.
- Beide Karten liegen dauerhaft in `source/build-eu2-launcher/manual-cards`.
  Das sind neue Testkarten; die echten Karten und die Karten des ersten Prototyps
  werden nicht benutzt. Automatische Tests verwenden nochmals eigene frische Karten.
- Einstellungen und Modzustand verbleiben beim neuen Build. Der Starter setzt sie
  nicht bei jedem Aufruf zurück. Er erzwingt weder Testeingaben noch Turbo-Modus.

## Kurzer manueller Test

1. Eine Sprache wählen und normal ein neues Spiel beginnen; Bewegung, Sprung,
   Controllerbelegung und Ton prüfen.
2. Beim regulär erreichbaren Speicherpunkt auf eine neue Testkarte speichern.
   Den laufenden Kartenzugriff vollständig abwarten.
3. Spiel regulär beenden, denselben neuen Starter erneut öffnen und im originalen
   Spielmenü **Load** verwenden. Fortschritt und Sprache kontrollieren.
4. Einen Gebietswechsel und den Rückweg spielen. Anschließend dasselbe mit
   deaktiviertem Seamless Loading vergleichen.

Originale Kartenfunktionen und PAL-Taktung sind unverändert. Ein kompletter
Speichern–Neustarten–Laden-Durchlauf und Gebietswechsel mit Rückweg sind noch
offene manuelle Abnahmen; sie werden hier nicht als bereits bestanden bezeichnet.
Die Speicherpunkt- und Questlogik wurde dafür nicht umgangen.

## Diagnose

Jeder manuelle Start schreibt `source/build-eu2-launcher/native/diagnostics/<Zeit>.log`
und nach Programmende eine gleichnamige JSON-Datei mit Disc-Prüfzeit und Exitcode.
Bei Problemen Zeitstempel, Sprache, letzten Gebietswechsel und aktivierte Mods nennen.
Relevante Meldungen beginnen mit `seamless:`, `EU seamless:` oder `psxrecomp:`.

Beim ersten Start einer neuen Cache-Kopie kann die vollständige DLL-Prüfung dauern.
Den `cache`-Ordner und die regulär erzeugte `.abi_*.ok`-Datei nicht vor jedem Start
neu kopieren oder löschen. Es werden keine Prüfmarker künstlich erstellt.
Der Resident-Cache bleibt separat unter `source/build-eu2-launcher/resident-cache`.

## Nachgewiesener Umfang

Der EU2-Adapter verwendet den gemeinsamen `eu/seamless/loader.c` und
`src/mods/tomba_seamless_prepare.cpp`. Aus der verifizierten SCES-01331-Disc werden
fünf sprachabhängige Profile, Loader-/Task-/SDK-Adressen und originale Dateilisten
geprüft. Der Vertrag bindet außerdem die gemeinsame Loader-Quelle an ihren Hash:
Änderungen erfordern eine erneute Prüfung statt stillschweigend alter Adressen.

Alle 401 unterschiedlichen GAM-Streams wurden gegen den originalen MIPS-Decoder
mit zwei Speicherfüllungen geprüft. Der Katalog umfasst 2257 Dateien; STR-Videos
bleiben auf dem Originalpfad. Fünf Profil-Fixtures prüfen atomare Batches,
RAM-/VRAM-/SPU-Grenzen, ungültige Anfragen und geschützte Kartenwartephasen.
EU1-Fixtures bestehen weiterhin. Live nachgewiesen sind englischer Spielstart und
Bewegung, Seamless aus sowie spanischer Start mit erzwungenem originalem
CD-Listen-Fallback. Auch Portugiesisch, Schwedisch und Dänisch erreichen mit
aktivem Seamless-Mod ihr originales MAIN und den regulären Spielstart. Die Laufzeit
nutzt vorab geprüfte native Overlays. Der fertige Launcher wurde zusätzlich über
seinen echten PLAY-Knopf bis zur sichtbar kontrollierten Original-Sprachauswahl geprüft.

Das ist ein lokaler Teststand, keine Freigabe einer kompletten Kampagne.
Die geerbte portugiesische Game-over-Overlay-Ausnahme bleibt auf dem sicheren
Interpreterpfad; ihre Producer-Prüfung wird nicht umgangen.

## Reproduzieren

Aus `source`, mit CMake/Ninja/Clang und Python 3.11+:

```powershell
python -I -B eu2/build_launcher.py --disc disc/eu2/disc.cue
python -I -B eu2/smoke.py --build-dir build-eu2-launcher/native --config build-eu2-launcher/native/game.toml --seamless on --play --language en
python -I -B tools/regional/test_eu2_launcher.py
```

Der Build benötigt einen legalen passenden Dump und die vorhandene gebündelte
Overlay-Toolchain aus der ersten lokalen Vorbereitung. `--skip-aot` behält einen
bereits geprüften Candidate-Cache. Keine ROM-/Cache-/Karteninhalte werden in Git
aufgenommen. Es erfolgt weder Veröffentlichung noch Pull Request.
