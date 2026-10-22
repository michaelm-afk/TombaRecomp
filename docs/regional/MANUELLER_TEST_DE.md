# Kurzer manueller SCES-01331-Test

Im übergeordneten Ordner `START_SCES01331_TEST.cmd` doppelklicken.
Der Starter öffnet direkt den isolierten Prototyp und die originale
Sprachauswahl. Es werden nur neue Karten unter
`source/build-eu2/manual-cards/` verwendet. Originalkarten bleiben außen vor.

1. Gewünschte Sprache auf der Original-Sprachauswahl wählen.
2. Ein neues Spiel beginnen, Anfangsdialoge regulär lesen/weiterklicken.
3. Gehen, Springen und normale Controllersteuerung prüfen.
4. Den ersten auf regulärem Weg erreichbaren Gebietswechsel ausprobieren;
   wenn möglich zurückkehren. Auffällige Ladepausen oder fehlende Grafik notieren.
5. Sobald das Originalspiel Speichern anbietet, einen neuen Spielstand auf
   der frischen Testkarte anlegen.
6. Das Programm vollständig schließen. Den gleichen Starter erneut öffnen,
   dieselbe Sprache wählen und den Testspielstand regulär laden.
7. Prüfen, ob Gebiet, Position/Fortschritt, Inventar und Sprache plausibel
   wiederhergestellt werden. Die echten EU1-Karten dafür nicht verwenden.

Wichtige Rückmeldung: gewählte Sprache, letzter funktionierender Schritt,
Controller, fehlerhafte Texte/Zeichen, Gebietsname und ob Speichern nach einem
vollständigen Neustart wieder ladbar war. Bei Problemen den Zustand der
separaten Testkarte aufbewahren; es müssen keine privaten Originalkarten
weitergegeben werden.

Dieser Build startet mit 4:3 und Original-Geometry/Original-CD-Tasks.
Widescreen, Seamless und weitere PC-Mods sind noch nicht für EU2 aktiviert.
Für weitere Gebiete liegt eine unveränderte Kopie der offiziellen
Fallback-Toolchain im Testbuild; zusätzliche native Module können beim ersten
Besuch entstehen. Dafür ist keine Änderung an der Original-Disc erforderlich.

Die bisherige automatisierte Stichprobe ersetzt diesen Save-/Gebiets-Test
nicht. Native Cache-Abdeckung ist ausdrücklich keine vollständige
Spielbarkeitsfreigabe.
