"""Build SCES-01331 native images using the unmodified shared AOT pipeline."""
import argparse
import hashlib
import json
import os
import re
import shutil
from pathlib import Path
import struct
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT/'eu2'), str(ROOT/'eu'), str(ROOT/'tools'), str(ROOT/'psxrecomp/tools')]
from prepare import LANGUAGES, SHA1
from toolchain import executable
from probe_eu_title_layouts import find_tables
import aot_overlay_pipeline as pipeline


def stage_native(cache,receipt,destination=None):
    destination=destination or ROOT/'build-eu2/native'
    namespace=destination/'cache'/receipt['game_id']/'gcc'/pipeline.compiler.cache_arch_abi()/receipt['cache_tag']
    # Same exact runtime-only memo class handled by the maintained EU1 builder.
    if namespace.is_dir():
        for marker in namespace.iterdir():
            if marker.is_file() and re.fullmatch(r'\.abi_[0-9a-fA-F]{8}\.ok',marker.name):
                marker.unlink()
    pipeline.stage(cache,destination,receipt)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--languages', nargs='+', choices=LANGUAGES, default=list(LANGUAGES))
    parser.add_argument('--workers', type=int, default=3)
    parser.add_argument('--prepare-only', action='store_true')
    parser.add_argument('--reuse-cache',type=Path,help='Re-audit completed pairs before reuse')
    parser.add_argument('--stage-from',type=Path,help='Re-audit and stage a completed native attempt')
    parser.add_argument('--seamless',action='store_true')
    parser.add_argument('--work-dir',type=Path)
    parser.add_argument('--destination',type=Path)
    parser.add_argument('--config',type=Path)
    args = parser.parse_args()
    work = ROOT/('build-eu2-seamless/aot' if args.seamless else 'build-eu2/aot')
    config=ROOT/('eu2/pc.toml' if args.seamless else 'eu2/game.toml')
    destination=ROOT/('build-eu2-launcher/native' if args.seamless else 'build-eu2/native')
    work=(args.work_dir or work).resolve()
    config=(args.config or config).resolve()
    destination=(args.destination or destination).resolve()
    if not all(p.is_relative_to(ROOT) for p in (work,config,destination)):
        parser.error('Build inputs and destinations must remain inside the checkout')
    work.mkdir(parents=True, exist_ok=True)
    temporary = work/'temp'
    temporary.mkdir(exist_ok=True)
    os.environ['TEMP'] = os.environ['TMP'] = str(temporary)
    tempfile.tempdir = str(temporary)
    if args.stage_from:
        attempt=args.stage_from.resolve()
        if not attempt.is_relative_to(work.resolve()):
            raise ValueError('Stage input must belong to this isolated AOT workspace')
        receipt=pipeline.audit(config,ROOT/'build-eu-tools/psxrecomp-game.exe',
            attempt/'cache',work/'runtime-input-inventory.json',attempt/'audit.json')
        stage_native(attempt/'cache',receipt,destination)
        (work/'audit.json').write_text(json.dumps(receipt,indent=2)+'\n')
        print('PASS: staged audited native pairs:',receipt['published_pairs'],flush=True)
        return
    disc = pipeline.Disc(ROOT/'disc/eu2/disc.cue')
    profile = dict(schema='psxrecomp AOT methods v1', game_id='SCES-01331',
        disc_hashes={'sha1': SHA1}, strict_bounds=True, bios_resident=False, checks=[], images=[])
    pipeline.check_disc(profile, disc, ROOT/'disc/eu2/disc.cue')
    for language in args.languages:
        i = LANGUAGES[language]
        name = f'EXE/MAIN{i}.EXE'
        raw = disc.read(name)
        entry, base, size = (struct.unpack_from('<I', raw, p)[0] for p in (16,24,28))
        if not raw.startswith(b'PS-X EXE') or len(raw) != size+2048:
            raise ValueError(f'Invalid executable extent: {name}')
        profile['images'].append(dict(method='fixed_address_extents', file=name,
            extents=[dict(file=name,file_offset=2048,base=hex(base),address=hex(base),
                load_addr=hex(base),size=size,sha256=hashlib.sha256(raw[2048:]).hexdigest())],
            load_addr=hex(base),allow_missing=True,entries=[hex(entry)]))
        tables = find_tables(disc.read(f'SYSTEM/X{i}00.BIN'))
        if len(tables) != 1:
            raise ValueError(f'Ambiguous language overlay base: {language}')
        _, link_base, _ = tables[0]
        # Locate the retail type-F0 load arm independently in each MAIN.
        words = struct.unpack('<%dI' % (size//4), raw[2048:])
        candidates = []
        for n in range(len(words)-6):
            if words[n] != 0x240200F0:
                continue
            for k in range(n+1,n+6):
                if words[k] >> 16 == 0x3C06 and words[k+1] >> 16 == 0x24C6:
                    lo = words[k+1] & 65535
                    value = ((words[k] & 65535) << 16) + lo - (65536 if lo & 32768 else 0)
                    if value == link_base:
                        candidates.append({hex(base+j*4):hex(words[j]) for j in (n,k,k+1)})
        if len(candidates) != 1:
            raise ValueError(f'Unverified original overlay loader: {language}')
        profile['checks'].append(dict(method='words',file=name,base=hex(base),file_offset=2048,
                                      values=candidates[0]))
        names = [f'SYSTEM/D{i}SPSUB{s}.BIN' for s in ('','2','3')]
        names += [f'SYSTEM/I{i}NFO{s}.BIN' for s in ('','2','3')]
        names += [f'SYSTEM/O{i}PTSUB0.BIN']
        # Shared discovery currently emits overlapping producer ranges for
        # the Portuguese game-over image. Preserve retail interpreter fallback;
        # never bypass the compiler's provenance checks to force a native DLL.
        if language != 'pt':
            names += [f'SYSTEM/G{i}OVER.BIN']
        names += [f'SYSTEM/X{i}{area:02d}.BIN' for area in (0,1)]
        for name in names:
            profile['images'].append(dict(method='fixed_address_files',files=[name],
                                           load_addr=hex(link_base),allow_missing=True))
        print(language, 'MAIN', i, 'entry', hex(entry), 'overlay base', hex(link_base), flush=True)
    profile['expected_records'] = len(profile['images'])
    (work/'profile.json').write_text(json.dumps(profile,indent=2))
    inventory = pipeline.prepare(profile,disc,[],work)
    if args.prepare_only:
        return
    compiler = ROOT/'build-eu-tools/psxrecomp-game.exe'
    attempt = Path(tempfile.mkdtemp(prefix='native-',dir=work))
    print('Native audit workspace:', attempt, flush=True)
    selected=inventory
    reuse=None
    if args.reuse_cache:
        reuse=args.reuse_cache.resolve()
        if not reuse.is_relative_to(work.parent.resolve()):
            raise ValueError('Reuse must come from this isolated development workspace')
        stems={p.stem for p in reuse.rglob('*.dll')}
        completed=[job for job in inventory['jobs'] if job['pair_stem'] in stems]
        subset=dict(inventory,jobs=completed)
        subset_path=attempt/'reuse-inventory.json'
        subset_path.write_text(json.dumps(subset,indent=2))
        pipeline.audit(config,compiler,reuse,subset_path,attempt/'reuse-audit.json')
        selected=dict(inventory,jobs=[job for job in inventory['jobs'] if job not in completed])
        print('Re-audited existing recipes:',len(completed),'remaining:',len(selected['jobs']),flush=True)
    cache = pipeline.build(selected,config,compiler,attempt,executable('clang.exe'),args.workers,ROOT)
    if reuse:
        shutil.copytree(reuse,cache,dirs_exist_ok=True)
    receipt = pipeline.audit(config,compiler,cache,work/'runtime-input-inventory.json',attempt/'audit.json')
    stage_native(cache,receipt,destination)
    (work/'audit.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print('PASS: audited native pairs:',receipt['published_pairs'],flush=True)


if __name__ == '__main__':
    main()
