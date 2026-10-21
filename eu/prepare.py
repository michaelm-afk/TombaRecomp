#!/usr/bin/env python3
"""Verify the owner's exact EU Rev-1 data track and extract local EXEs only."""
import argparse
import hashlib
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'psxrecomp/tools'))
import extract_overlays as iso

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--disc', type=Path, required=True)
    args = parser.parse_args()
    path = args.disc.resolve()
    if path.suffix.lower() == '.cue':
        text = path.read_text(encoding='utf-8-sig')
        files = re.findall(r'FILE\s+"([^"]+)"\s+BINARY', text, re.I)
        if len(files) != 1 or not re.search(r'TRACK\s+01\s+MODE2/2352', text, re.I):
            raise ValueError('Prototype preparation requires the original single-track MODE2/2352 dump')
        path = path.parent / files[0]
    with path.open('rb') as stream:
        digest = hashlib.file_digest(stream, 'sha1').hexdigest()
    if digest != '2505d958b4439d04844cadd3f968fc7432a48e00':
        raise ValueError('Unsupported EU data track; original images are never modified')
    disc = iso.DiscReader(str(path), raw=True)
    try:
        files = {name: (lba, size) for name, lba, size in iso.enumerate_files(disc)}
        for name in ['SCES_013.30'] + [f'EXE/MAIN{i}.EXE' for i in range(5)]:
            data = disc.read_file_bytes(*files[name])
            if not data.startswith(b'PS-X EXE'):
                raise ValueError(f'Invalid executable: {name}')
            if name == 'SCES_013.30' and hashlib.sha256(data).hexdigest() != \
                    '08436f44ca2ddf9f9a9ece58f7fbbb9b88f6ab3cef6ede5b36300f51e4356df0':
                raise ValueError('Unexpected EU boot program')
            target = ROOT / 'disc' / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
            print(f'Verified EU source -> local {target.relative_to(ROOT)}')
    finally:
        disc.close()

if __name__ == '__main__':
    main()
