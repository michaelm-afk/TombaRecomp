"""Check PE import dependencies without rejecting legacy TinyCC TLS metadata."""
from pathlib import Path
import json
import os
import struct
import argparse

ROOT = Path(__file__).resolve().parents[2]


def imports(path):
    data = path.read_bytes()
    pe = struct.unpack_from('<I', data, 60)[0]
    count = struct.unpack_from('<H', data, pe + 6)[0]
    optional = pe + 24
    size = struct.unpack_from('<H', data, pe + 20)[0]
    magic = struct.unpack_from('<H', data, optional)[0]
    assert magic in (0x10b, 0x20b), path
    directory = optional + (112 if magic == 0x20b else 96)
    rva, _ = struct.unpack_from('<II', data, directory + 8)
    sections = []
    for index in range(count):
        offset = optional + size + index * 40
        virtual_size, va, raw_size, pointer = struct.unpack_from('<IIII', data, offset + 8)
        sections.append((va, max(virtual_size, raw_size), pointer))

    def file_offset(address):
        for va, length, pointer in sections:
            if va <= address < va + length:
                return pointer + address - va
        raise ValueError((path, address))

    if not rva:
        return []
    offset = file_offset(rva)
    result = []
    while any(data[offset:offset + 20]):
        name = file_offset(struct.unpack_from('<I', data, offset + 12)[0])
        result.append(data[name:data.index(0, name)].decode('ascii'))
        offset += 20
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--package', default='public-final-staging/windows-x64')
    args = parser.parse_args()
    root = ROOT / args.package
    files = [p for p in root.rglob('*') if p.suffix.lower() in ('.exe', '.dll', '.pyd')]
    bundled = {p.name.lower() for p in files}
    system = Path(os.environ['SystemRoot']) / 'System32'
    missing, names = {}, set()
    for path in files:
        for name in imports(path):
            names.add(name)
            if name.lower() in bundled or (system / name).exists() or name.lower().startswith(('api-ms-win-', 'ext-ms-win-')):
                continue
            missing.setdefault(path.relative_to(root).as_posix(), []).append(name)
    result = dict(pe_files=len(files), import_names=sorted(names), unresolved_non_system_imports=missing)
    (ROOT / 'build-eu-release-final/import-audit.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(dict(pe_files=len(files), unresolved_non_system_imports=missing)))
    assert not missing


if __name__ == '__main__':
    main()
