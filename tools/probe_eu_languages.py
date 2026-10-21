#!/usr/bin/env python3
"""Compare the owner's US/EU WFM interfaces; emit metadata, never game bytes.

Run from the project root. The images are opened read-only. Generated catalog
entries contain offsets, lengths and hashes only. See the psx_tomba audit note
for format references and checks against the actual discs.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
import hashlib
import json
from pathlib import Path
import struct
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
sys.path.insert(0, str(ROOT / 'psxrecomp/tools'))
import extract_overlays as iso
from seamless_asset_probe import decode_gam

LANGUAGES = [('en', 'B', 0), ('fr', 'F', 1), ('de', 'G', 2),
             ('it', 'I', 3), ('nl', 'H', 4)]
US_SHA1 = 'c259ec7ff6ef4163913991f4e4db2eff71702818'
EU_SHA1 = '2505d958b4439d04844cadd3f968fc7432a48e00'


def digest(data):
    return hashlib.sha256(data).hexdigest()


def interface(data):
    if len(data) < 144 or data[:4] != b'WFM3':
        raise ValueError('not a WFM3 bank')
    table, count, glyphs = struct.unpack_from('<IHH', data, 8)
    if not count or not glyphs or 144 + glyphs * 2 > table:
        raise ValueError('invalid glyph table')
    if table + count * 2 > len(data):
        raise ValueError('dialogue table outside bank')
    for off in struct.unpack_from(f'<{glyphs}H', data, 144):
        if off + 8 > table:
            raise ValueError('glyph header outside glyph region')
        w, h = struct.unpack_from('<HH', data, off)
        if not w or not h or off + 8 + w * h * 2 > table:
            raise ValueError('glyph pixels outside glyph region')
    offsets = struct.unpack_from(f'<{count}H', data, table)
    if any(table + off + 2 > len(data) or off % 2 for off in offsets):
        raise ValueError('dialogue offset outside bank')
    # The 64 group indices are part of the engine/script interface. Glyph IDs,
    # pixel counts and string lengths deliberately are NOT that interface.
    return count, data[16:144]


def wfm_extent(data):
    """Bound an embedded WFM by its glyphs and dialogue streams, not its BIN."""
    interface(data)
    table, count, glyphs = struct.unpack_from('<IHH', data, 8)
    offsets = struct.unpack_from(f'<{count}H', data, table)
    starts = sorted(set(table + off for off in offsets))
    end = table + count * 2
    arity = {0xfff2: 1, 0xfff3: 0, 0xfff4: 0, 0xfff5: 0, 0xfff6: 2,
             0xfff7: 1, 0xfff8: 2, 0xfff9: 1, 0xfffa: 2,
             0xfffb: 0, 0xfffc: 0, 0xfffd: 0}
    for i, start in enumerate(starts):
        limit = starts[i + 1] if i + 1 < len(starts) else len(data)
        pos = start
        while pos + 2 <= limit:
            token = struct.unpack_from('<H', data, pos)[0]
            pos += 2
            if token in (0xfffe, 0xffff):
                break
            pos += arity.get(token, 0) * 2
            if pos > limit:
                raise ValueError('truncated WFM control arguments')
        end = max(end, pos)
    return end


def scan(path, expected_sha1):
    with path.open('rb') as stream:
        if hashlib.file_digest(stream, 'sha1').hexdigest() != expected_sha1:
            raise ValueError(f'unsupported disc: {path}')
    canonical_hash = hashlib.sha256()
    # This probe supports exactly the verified raw Mode-2 images above.
    with path.open('rb') as stream:
        while raw := stream.read(2352 * 4096):
            if len(raw) % 2352:
                raise ValueError('partial raw sector')
            for i in range(0, len(raw), 2352):
                canonical_hash.update(raw[i + 24:i + 24 + 2048])
    reader = iso.DiscReader(str(path), raw=True)
    files, banks, sizes = {}, [], set()
    try:
        for name, lba, size in iso.enumerate_files(reader):
            if name.endswith('.STR'):
                continue
            original = reader.read_file_bytes(lba, size)
            files[name] = (lba, original)
            if name.startswith('SYS/'):
                for pos in range(0, len(original) - 19, 4):
                    r = original[pos:pos + 20]
                    if r[:3] == b'\0\0\xff' and r[3] in (0xd0, 0xd1) and r[16:] == b'\xff' * 4:
                        sizes.add(struct.unpack_from('<I', r, 8)[0])
            data = original
            if data.startswith(b'GAM\0'):
                try:
                    data = decode_gam(data)
                except ValueError:
                    continue
            starts, pos = [], 0
            while (pos := data.find(b'WFM3', pos)) >= 0:
                starts.append(pos)
                pos += 4
            for i, start in enumerate(starts):
                chunk = data[start:starts[i + 1] if i + 1 < len(starts) else len(data)]
                shape = interface(chunk)
                if name.startswith('SYSTEM/'):
                    chunk = chunk[:wfm_extent(chunk)]
                banks.append(dict(name=name, offset=start, data=chunk, shape=shape,
                                  canonical_offset=lba * 2048 + start))
    finally:
        reader.close()
    return files, banks, sizes, canonical_hash.hexdigest(), path.stat().st_size // 2352 * 2048


def compare(us_path, eu_path):
    _, us, sizes, us_hash, _ = scan(us_path, US_SHA1)
    _, eu, _, eu_hash, eu_size = scan(eu_path, EU_SHA1)
    rows, seen = [], set()
    for source in us:
        # Each area-bank length is independently recorded in the US LDARs.
        # Limit the chunk before checking which length belongs to this shape.
        possible = []
        for size in sorted(sizes):
            if size > len(source['data']):
                continue
            try:
                if interface(source['data'][:size]) == source['shape']:
                    possible.append(size)
            except ValueError:
                pass
        if source['name'].startswith('SYSTEM/'):
            # Menu banks have their own guarded pointer stores in DSPSUB.
            size = {205: 22164, 200: 21332}[source['shape'][0]]
            interface(source['data'])
        elif possible:
            size = min(possible)
        else:
            raise ValueError(f'no bounded US load record: {source["name"]}')
        key = (size, source['shape'])
        if key in seen:
            continue
        seen.add(key)
        targets = []
        for code, suffix, index in LANGUAGES:
            candidates = [b for b in eu if b['shape'] == source['shape'] and
                          (b['name'].endswith(suffix + '.WFM') or
                           b['name'] == f'SYSTEM/D{index}SPSUB.BIN')]
            if not candidates:
                raise ValueError(f'no {code} bank for {source["name"]}')
            candidates.sort(key=lambda b: (b['name'], b['offset']))
            target = candidates[0]
            # Menus use their bounded WFM slice, never their executable container.
            hashes = {digest(b['data']) for b in candidates}
            if size and len(hashes) != 1:
                raise ValueError(f'ambiguous {code} bank for {source["name"]}')
            targets.append(dict(language=code, path=target['name'],
                                offset=target['canonical_offset'],
                                size=len(target['data']), sha256=digest(target['data'])))
        rows.append(dict(source=source['name'], source_offset=source['offset'],
                         source_size=size, menu=source['name'].startswith('SYSTEM/'),
                         dialogues=source['shape'][0],
                         groups_sha256=digest(source['shape'][1]), targets=targets))
    # The loader dispatch is keyed by the exact US subresource length. Never
    # generate an ambiguous length-to-language mapping.
    installed = [r for r in rows if r['source_size']]
    if len({r['source_size'] for r in installed}) != len(installed):
        raise ValueError('US bank lengths are not unique')
    return dict(us_canonical_sha256=us_hash, donor_sha256=eu_hash, donor_size=eu_size,
                languages=[x[0] for x in LANGUAGES], banks=rows)


def catalog(report):
    lines = ['/* Metadata only; generated by tools/probe_eu_languages.py. */',
             'static const LanguageBank language_banks[] = {']
    for row in report['banks']:
        if not row['source_size']:
            continue
        values = ', '.join('{%du, %du}' % (t['offset'], t['size']) for t in row['targets'])
        lines.append('    {%du, {%s}}, /* %s */' % (row['source_size'], values, row['source']))
    lines += ['};', '']
    return '\n'.join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--us-bin', type=Path, required=True)
    parser.add_argument('--eu-bin', type=Path, required=True)
    parser.add_argument('--report', type=Path, required=True)
    parser.add_argument('--catalog', type=Path)
    args = parser.parse_args()
    report = compare(args.us_bin, args.eu_bin)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    if args.catalog:
        args.catalog.write_text(catalog(report), encoding='utf-8')
    print(f'{len(report["banks"])} distinct WFM interfaces compatible across five languages')
    print(f'Donor: {report["donor_size"]} canonical bytes, SHA-256 {report["donor_sha256"]}')


if __name__ == '__main__':
    main()
