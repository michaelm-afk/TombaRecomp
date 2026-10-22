# Standardwerte EU1 / EU2

Quellen: unveraendertes offizielles EU1-Profil `eu/release/game.toml` am Ausgangsstand ec11a7e, EU1-Mod-Manifeste, gemeinsame Runtime `psxrecomp/runtime/src/main.cpp`, `config_loader.h`, `psx_keybinds.c` und `host_keymap.c`. Keine persoenliche settings.toml wurde als Defaultquelle verwendet. Die gemeinsame EU-Paketarchitektur ist umgesetzt; die folgenden EU2-Profilkorrekturen betreffen ausschliesslich frische Konfigurationen.

| Einstellung | EU1-Default | EU2 bisher | EU2 neu |
|---|---|---|---|
| VSync | OFF (explizit im EU1-Profil) | ON (Framework-Fallback) | OFF |
| Fenstergroesse | Automatisch an Display angepasst | Gleich | Gleich |
| Internal Resolution | 1080p | 1080p | 1080p |
| Vollbild | Fenster (0) | Fenster (0) | Fenster (0), explizit |
| Grafikbackend | OpenGL | OpenGL | OpenGL |
| Antialiasing | ON; Post-AA OFF | Gleich | Gleich |
| Audio-Sample-Rate | 44100 Hz angefordert; SDL-Geraet kann abweichen | Gleich | Gleich |
| High Quality SPU | ON | OFF (Framework-Fallback) | ON |
| Controller-Modus | Digital | Digital | Digital |
| Standardbelegung | Gemeinsame PSX-Belegung | Gleich | Gleich |
| Fast Forward | Nicht aktiv; 4x beim Halten von Tab; Pad Select+L1 | Gleich | Gleich |
| Seamless Loading | ON | ON | ON |
| Geometry Optimization | ON, optional abschaltbar | OFF | ON, optional abschaltbar |
| PGXP Precision | OFF | OFF | OFF |
| Hybrid Controller | OFF | OFF | OFF |
| HD Texture Packs | OFF, externes passendes Pack erforderlich | Gleich fuer EU2 | Gleich |
| Bezel Artwork | OFF, eigenes Bild | Gleich | Gleich |
| Skip FMVs | OFF, EU1-Mod verfuegbar | Nicht angeboten | Weiterhin nicht angeboten; OFF |
| Widescreen | OFF, EU1-Mod verfuegbar | Nicht angeboten | Weiterhin nicht angeboten; OFF |

Tastatur: Pfeile = Bewegung, X/S/Z/A = Kreuz/Kreis/Quadrat/Dreieck, Q/W = L1/R1, E/R = L2/R2, Enter = Start, rechte Umschalttaste = Select. Vorhandene keybinds.ini/settings.toml/mods/state.toml werden nicht umgeschrieben. Nicht unterstuetzte EU2-Mods bleiben ausgeblendet. Regionale Speicherkarten und Mod-Konfigurationen muessen bei der gemeinsamen Integration weiterhin getrennt bleiben.
