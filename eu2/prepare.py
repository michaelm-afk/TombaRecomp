"""Stage a checked local SCES-01331 copy; never modify source discs or saves."""
import argparse
import hashlib
from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / 'tools'), str(ROOT / 'psxrecomp/tools')]
from build_regions import data_track, sha1
from extract_overlays import DiscReader, enumerate_files

SHA1 = '684dbf0ad03f872511046d40d3cc85b17d839dbf'
BOOT_SHA256 = 'dc65210e6601cbb4ab1cc0878a73f926a2ffd1bd3d8d7923d781164fd2835f29'
LANGUAGES = {'en': 0, 'es': 5, 'pt': 6, 'sv': 7, 'da': 8}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--disc', type=Path, required=True)
    args = parser.parse_args()
    source = data_track(args.disc)
    if source.stat().st_size != 492306528 or sha1(source) != SHA1:
        raise ValueError('Unsupported disc revision; exact original track required')
    home = ROOT / 'disc/eu2'
    home.mkdir(parents=True, exist_ok=True)
    target = home / 'disc.bin'
    if target.exists():
        if sha1(target) != SHA1:
            raise ValueError('Conflicting working copy; refusing to overwrite')
    else:
        with source.open('rb') as reader, target.open('xb') as writer:
            shutil.copyfileobj(reader, writer)
        if sha1(target) != SHA1:
            raise ValueError('Working copy verification failed')
    cue = home / 'disc.cue'
    cue_text = 'FILE "disc.bin" BINARY\n  TRACK 01 MODE2/2352\n    INDEX 01 00:00:00\n'
    if cue.exists() and cue.read_text() != cue_text:
        raise ValueError('Conflicting working CUE')
    cue.write_text(cue_text, encoding='ascii')
    disc = DiscReader(str(target), raw=True)
    try:
        files = {name: (lba, size) for name, lba, size in enumerate_files(disc)}
        for name in ['SCES_013.31'] + [f'EXE/MAIN{i}.EXE' for i in LANGUAGES.values()]:
            data = disc.read_file_bytes(*files[name])
            if not data.startswith(b'PS-X EXE'):
                raise ValueError(f'Invalid original executable: {name}')
            if name == 'SCES_013.31' and hashlib.sha256(data).hexdigest() != BOOT_SHA256:
                raise ValueError('Unexpected original boot executable')
            destination = home / name
            destination.parent.mkdir(parents=True, exist_ok=True)
            if destination.exists() and destination.read_bytes() != data:
                raise ValueError(f'Conflicting extracted executable: {name}')
            destination.write_bytes(data)
            print('Verified local working copy:', name)
    finally:
        disc.close()


if __name__ == '__main__':
    main()
