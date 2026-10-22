# Widescreen: Architektur und regionale Portierung

Untersuchter Stand: `v0.21.0-alpha`, danach `ec11a7e` (22.10.2026).
Die vier Commits nach dem Tag ändern Dokumentation/Urheberschaft, keine
Laufzeitimplementierung. Der EU-Widescreen-Integrationscommit ist `3860b69`.
Quellen: `docs/WIDESCREEN.md`, `eu/widescreen_profile.py`,
`eu/widescreen-contract.json`, `src/mods/tomba_widescreen_*`,
`src/hle/tomba_geometry_hle.c` und das gepinnte PSXRecomp-Submodul
`847762995c0fa1af65f0e43604bb2a3e23d92bff`.

## Echtes erweitertes Sichtfeld

Der Mod aktiviert den bestehenden Native-Wide-Pfad des Frameworks. Die
Renderfläche und die horizontalen Sichtbarkeitsgrenzen wachsen gemeinsam.
Das Ergebnis ist zusätzliche Welt links/rechts, keine bloße Streckung der
320 Pixel breiten Originaldarstellung. Recompiler-Konfiguration und
Laufzeit-Mod erfüllen dabei unterschiedliche Aufgaben:

* Die Codegenerierung ersetzt konfigurierte horizontale Cull-Ausdrücke
  und erkennt zusätzliche Screen-X-/Backdrop-Muster. Das betrifft MAIN
  **und** später geladene Area-Overlays.
* Der Mod setzt Zielseitenverhältnis, adaptive Darstellung, Sprite-Rollen,
  Kamera-Anker sowie begrenzte Residency-/Script-Anpassungen.
* Der Framework-Renderer verarbeitet die erweiterte Darstellung und die
  Präzisions-/Sprite-Metadaten. Die gemeinsame Implementation bleibt erhalten.

Die PAL-Konfiguration nutzt `native_wide=true`, `adaptive_view=true`,
32 Pixel Cull-Guard und getrennte 32 Pixel Aktivierungsreserve. Ein sichtbares
Objekt benötigt zusätzlich gültige Lebensdauer und aktive Scripts; ein
erweiterter Draw-Cull allein garantiert weder Spawning noch Kollision.

## Vier Anzeigeoptionen

| Option | Verhalten |
|---|---|
| Fit to Window | Folgt der Fenstergröße zwischen 4:3 und 34:9; darüber Seitenbalken |
| 16:9 | Festes Verhältnis, derselbe Native-Wide-Pfad |
| 21:9 | Festes Verhältnis, derselbe Native-Wide-Pfad |
| 32:9 | Festes Verhältnis, derselbe Native-Wide-Pfad |

`tomba_widescreen_view.h` dekodiert die Auswahl. Unbekannte/alte Werte
fallen auf Fit zurück. Der Mod startet deaktiviert; `offer=false` in TOML
bedeutet, dass die generische Settings-Oberfläche die Option nicht zusätzlich
anbietet. Die Bedienung gehört zum Mod-Katalog. Ausschalten stellt 4:3 wieder her.
Es gibt keinen separaten Renderer pro Seitenverhältnis.

## Kamera und Parallaxe

Im Anfangsgebiet (Area 0, Sector 0) verankert
`tomba_widescreen_camera_shift` die Darstellung am ursprünglichen linken Rand.
Die Follow-Position liegt in 16.16 vor. Aus Abstand zur linken Grenze und
sichtbarer Erweiterung wird ein Screen-Origin-Shift berechnet. Die Gastkamera,
ihre Geschwindigkeit und die Originalpaketkoordinaten werden dafür nicht
verschoben. Vordergrund und langsamere Parallaxeschichten erhalten denselben
Renderer-Ursprung. Ein Verschieben der Gastkamera würde Parallaxe falsch
kompensieren.

Der Refresh läuft auch bei Pause/Dialogen. Area-/Sector-, Camera-Follow- und
Original-Overlay-Instruktionsprüfungen begrenzen ihn auf die bekannte Szene.
Overlay-Adressen sind wiederverwendbar und allein keine ausreichende Identität.

## Sprites, HUD und 4:3-Szenen

`tomba_widescreen_hud.h` bestimmt links/rechts verankerte HUD-Produzenten
über Rücksprungadressen und geprüfte Eltern-Stackframes. AP bleibt rechts,
Vitalität und Ausrüstung links an den tatsächlichen Viewporträndern.
`SetShadeTex` wird auch für Dialoge und Weltobjekte verwendet; eine pauschale
Verschiebung aller Sprites oder ein Klassifizieren nur nach Bildschirmposition
wäre falsch. `tomba_widescreen_sprites.h` kennzeichnet Welt-Sprite-Produzenten
separat. Diese Rollen werden als Metadaten an den Renderer weitergegeben.

Endliche Vollbildkulissen enthalten nicht automatisch zusätzliche Welt. Das
Overhead-Dorf besitzt deshalb eine eigene 4:3-Präsentationsregel. FMVs und
Vollbild-2D behalten ihre vorgesehene Darstellung. Residency- und Script-Adapter
besitzen Szenen-/Ownership-Grenzen. Story-Sichtbarkeit bleibt unabhängig von
weiter gefasster Draw-Zulassung; eine Questbedingung darf nicht durch einen
Widescreen-Cull-Patch geändert werden.

## PAL, NTSC und regionale Bindungen

PAL behält 50 Hz und seine eigenen vertikalen Grenzen. Die EU-Signaturen
berücksichtigen `0x100/0x101` zusätzlich zu `0xE0/0xF1`; die gemeinsame
Geometry-HLE erhält für EU ein Y-Limit von 256 statt 224. Ein Wechsel der
horizontalen Darstellung ist kein PAL-zu-NTSC-Patch.

Der EU-Adapter erzeugt aus gemeinsamer US-Policy regionsgebundene C-Dateien in
ignorierten Build-Ausgaben. `CODE` enthält geprüfte Code-/Return-Sites,
`FIELDS` Orte originaler LUI/Low-Immediate-Adresskonstruktionen,
`TABLES` gemeinsame Tabellen und `OVERLAY` Szenenhooks. Datenadressen werden
pro geladenem Sprach-MAIN aufgelöst. Das Script kontrolliert ursprüngliche
Instruktionswörter, 32-Byte-Fenster um Hooks, Loader-Linkbasis und Tabellen-
Backlinks. `widescreen-contract.json` fixiert diese Fenster als SHA-256.

Die fünf EU1-Sprachen besitzen eindeutige 64-Byte-MAIN-Fingerprints. Jeder
Gastzustand berührende Callback muss die aktuelle Identität erneut prüfen;
unbekannte Bilder setzen den Anker zurück und erhalten keine Gast-Hooks.
Auch gemeinsame Policy-Quelldateien werden gehasht. Policy-Änderungen erzwingen
dadurch eine erneute Prüfung der PAL-Substitutionen.

Die Kommentare dokumentieren das ursprüngliche Auffinden durch vollständige
Instruktionsfenster-Matches mit unabhängiger Prüfung aller fünf MAINs.
Aus dem heutigen Code lässt sich die damalige interaktive Suchsitzung nicht
rekonstruieren. Nachvollziehbar sind die verbindlichen Adressen und Guards.

Beispiele **nur für SCES-01330 Rev 1**: Cull-Bias `0x800202E8`,
Range `0x800202F0`, Sprite-Produzent `0x8005E634`. Diese sind keine
freigegebenen SCES-01331-Hooks.

## Geometry Optimization und PGXP

Die drei nativen Polygon-Batches ersetzen teure MIPS-Schleifen, verwenden
aber weiter gemeinsame GTE-Mathematik, Originalpaketformate, OT-Verkettung
und Präzisionsprovenienz. `PGXP_COP2`, `gte_precision_store_word` und die
regionalen Store-PC-Werte erhalten den Bezug zwischen GTE-Ergebnissen und
GPU-Paketen. Die HLE führt die erweiterten Cull-Grenzen weiter; sie darf
keine ursprüngliche 4:3-Geometrie wiederherstellen.

EU verwendet einen dünnen Adapter um dieselbe HLE-Quelldatei. Vor Eintritt
wird der vollständige live geladene Originalfunktionskörper gehasht.
Unbekannte/geänderte Körper behalten den Originalpfad. Ein separater
Differential-Build vergleicht Original und HLE in isoliertem Zustand.
PGXP verbessert Präzision und Textur-/Geometriezuordnung; es erzeugt allein
kein erweitertes Sichtfeld. Die Features lösen unterschiedliche Probleme.

## Erforderlicher SCES-01331-Vertrag

1. Exakte Disc-Revision und Selector-/MAIN-Auswahl nachweisen.
2. Für MAIN0/5/6/7/8 getrennte Identität und Datenbasen ableiten.
3. Codefenster für Cull, Kamera, Sprite/HUD-Caller und Script-Predicates
   unabhängig finden und prüfen. Kein pauschaler regionaler Offset.
4. Area-Linkbasis aus Loader und Originaldaten gegenseitig bestätigen;
   Area0/1-Szenenhooks über Originalinstruktionen absichern.
5. Native MAIN-/Overlay-Module mit derselben Wide-Konfiguration erzeugen;
   Cache-Konfigurationshash muss dazu passen.
6. Gemeinsame Policy über geprüfte Profile anbinden, anschließend 4:3,
   Fit, 16:9, 21:9 und 32:9 mit HUD, Randinhalt und Szenenwechsel testen.
7. Geometry erst nach Körperprüfung und Differentialtest aktivieren.

Upstream-Evidenz (`audit_notes/tombi-widescreen-20261021.json`) nennt
US-/EU-Stichproben, EU Englisch/Deutsch, festes 21:9, deaktivierten Mod und
2.400 verglichene EU-Geometry-Batches. Das sind übernommene Testergebnisse,
keine hier neu durchgeführten SCES-01331-Tests und kein Kampagnennachweis.
