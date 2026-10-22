"""Read-only local disc audit. Writes metadata only to an explicit output folder."""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'psxrecomp/tools'))
from extract_overlays import DiscReader, enumerate_files, parse_cue


def hashes(path):
    digests = {name: hashlib.new(name) for name in ('md5', 'sha1', 'sha256')}
    with path.open('rb') as stream:
        while chunk := stream.read(4 * 1024 * 1024):
            for digest in digests.values():
                digest.update(chunk)
    return {name: digest.hexdigest() for name, digest in digests.items()}


def audit(cue):
    binary, raw = parse_cue(str(cue))
    binary = Path(binary)
    disc = DiscReader(str(binary), raw=raw)
    result = dict(cue=cue.name, image=binary.name, size=binary.stat().st_size,
                  hashes=hashes(binary), files=[])
    try:
        for name, lba, size in enumerate_files(disc):
            data = disc.read_file_bytes(lba, size)
            row = dict(name=name, lba=lba, size=size,
                       sha256=hashlib.sha256(data).hexdigest())
            if name.upper() == 'SYSTEM.CNF':
                result['system_cnf'] = data.decode('ascii', errors='replace').rstrip('\0')
            if data.startswith(b'PS-X EXE'):
                row['exe'] = dict(zip(('entry_pc', 'gp', 'load_address', 'text_size'),
                                     (hex(x) for x in struct.unpack_from('<4I', data, 16))))
                row['exe']['stack_base'] = hex(struct.unpack_from('<I', data, 48)[0])
            result['files'].append(row)
    finally:
        disc.close()
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--workspace', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    workspace, out = args.workspace.resolve(), args.out.resolve()
    # Never permit audit output inside any original input tree.
    for original in workspace.iterdir():
        if original.name.upper() in ('ROMS', 'SAVES') or 'windows-x64' in original.name:
            if out == original or original in out.parents:
                raise ValueError('Output must be separate from original inputs')
    out.mkdir(parents=True, exist_ok=True)
    inventory = []
    for folder in workspace.iterdir():
        if folder.name.upper() not in ('ROMS','SAVES') and 'windows-x64' not in folder.name:
            continue
        print('Inventory:', folder.name, flush=True)
        for path in ([folder] if folder.is_file() else folder.rglob('*')):
            if path.is_file():
                (out / 'inventory-progress.txt').write_text(path.relative_to(workspace).as_posix(), encoding='utf-8')
                row = dict(path=path.relative_to(workspace).as_posix(), size=path.stat().st_size)
                # Disc/save integrity is the baseline. Native release modules are
                # inventoried by size; some host scanners block their raw reads.
                if folder.name.upper() in ('ROMS', 'SAVES') or folder.is_file():
                    row['sha256'] = hashes(path)['sha256']
                inventory.append(row)
    (out / 'original-files.json').write_text(json.dumps(inventory, indent=2), encoding='utf-8')
    for cue in sorted((workspace / 'ROMS').rglob('*.cue')):
        result = audit(cue)
        target = out / (cue.parent.name.split()[-1] + '.json')
        target.write_text(json.dumps(result, indent=2), encoding='utf-8')
        print(target.name, result['hashes'], result.get('system_cnf'),
              'files=', len(result['files']), flush=True)


if __name__ == '__main__':
    main()
