# External texture mods (OFF by default)

This is technical support for future external texture mods, not an included
HD graphics upgrade. No HD artwork or captured game textures are supplied.
Without a pack the launcher shows **No texture pack installed**. Leaving the
feature OFF uses original disc textures.

## Install a pack

In Mods, open HD Texture Packs and click **Select Texture Pack Folder**.
Choose the downloaded folder, its game folder, or its replacements folder.
The picker finds a uniquely identified EU pack inside a shallow wrapper folder;
you do not need to copy files into the program's internal directories.
The selected path is saved; the original external files are not modified.

A pack passes when its target declaration includes SCES-01330, replacement
filenames are supported and unambiguous, and all replacement images decode
within supported size/scale limits. Its status becomes **Installed** in green.
You may then enable HD Texture Packs with Load replacements ON. OpenGL is
required. Invalid/incomplete images, unknown targets, US-only targets and
unsupported configurations produce an error and cannot enable replacements.
The runtime checks again on Play, including selections edited outside the UI.
Use the folder picker again to explicitly recheck a modified pack.

The US Tomba-HD-texture-example is deliberately rejected as an EU installation.
It contains synthetic cyan/magenta checkerboards, not finished HD artwork.
No complete real EU pack has been qualified in this release.

Target declaration is not proof of full-game asset coverage: the renderer
still matches actual texture-content keys. A wrongly authored pack can name
EU without matching its assets. Missing matches retain the original artwork;
Installed does not mean all areas, fonts or five translated menus are replaced.

## Creating a pack

See [the texture format guide](DUCKSTATION_TEXTURE_FORMAT.md) for source keys,
PNG/JPEG/WebP naming, dimensions, transparency and config.yaml support.
Capture-only use remains available: leave Load replacements OFF and enable
Dump textures. Exit normally to finish PNGs under the selected folder's dumps.
Do not distribute captured original textures or extracted game data.

For this installer's supported DuckStation format, arrange:

```
MyPack/
  texture-pack.toml
  replacements/
    texpage-...png
```

The small metadata file declares the intended game:

```toml
game_ids = ["SCES-01330"]
```

Alternatively, the pack's game folder may be named SCES-01330. Explicit
metadata takes precedence over the folder name; renaming a US pack does not
convert its texture keys or artwork into a working EU pack. This declaration
never changes or bypasses disc verification. Older Beetle-format runtime
support is retained for existing manifests, but this EU installer accepts the
DuckStation naming scheme documented above.
