#!/usr/bin/env python3
"""Build/audit original-disc native EU variants with the shared AOT pipeline.

Preparation is deliberately limited to the declared five language families;
no runtime captures, US binaries or historical generated code are inputs.
"""
import argparse,hashlib,json,os,re,shutil,struct,sys,tempfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'eu'))
from toolchain import executable
sys.path[:0]=[str(ROOT/'psxrecomp/tools'),str(ROOT/'tools')]
import aot_overlay_pipeline as pipeline
from probe_eu_title_layouts import find_tables

def stage_native(cache,receipt):
    destination=ROOT/'build-eu-prototype/native'
    namespace=destination/'cache'/receipt['game_id']/'gcc'/pipeline.compiler.cache_arch_abi()/receipt['cache_tag']
    # Runtime-generated ABI-check memo is not a published game artifact.
    # Remove only that exact metadata class so the expanded cache is checked
    # anew. Every executable/ranges file still needs the full original audit.
    if namespace.exists():
        for marker in namespace.iterdir():
            if marker.is_file() and re.fullmatch(r'\.abi_[0-9a-fA-F]{8}\.ok',marker.name):
                marker.unlink()
    pipeline.stage(cache,destination,receipt)

def main():
    # Child tools use this interpreter too; unrelated media-player Python
    # extensions on the host must not override its standard library.
    os.environ.pop('PYTHONPATH', None)
    os.environ.pop('PYTHONHOME', None)
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--scope',choices=['startup','opening','full'],default='startup')
    ap.add_argument('--prepare-only',action='store_true')
    ap.add_argument('--workers',type=int,default=1)
    ap.add_argument('--reuse-from',type=Path,help='Previous native-* directory; re-audited before reuse')
    ap.add_argument('--stage-from',type=Path,help='Re-audit and stage an already completed native-* build')
    args=ap.parse_args()
    if args.stage_from:
        native=args.stage_from.resolve()
        receipt=pipeline.audit(ROOT/'eu/game.toml',ROOT/'build-eu-tools/psxrecomp-game.exe',
            native/'cache',native.parent/'runtime-input-inventory.json',native/'audit.json')
        stage_native(native/'cache',receipt)
        print(f'PASS: staged {receipt["published_pairs"]} audited EU native pairs',flush=True)
        return
    home=ROOT/'eu';work=ROOT/'build-eu-prototype'/('aot-'+args.scope);work.mkdir(exist_ok=True)
    cue=ROOT/'disc/Tombi! (Europe) (En,Fr,De,It,Nl) (Rev 1).cue'
    disc=pipeline.Disc(cue)
    profile=dict(schema='psxrecomp AOT methods v1',game_id='SCES-01330',
        disc_hashes={'sha1':'2505d958b4439d04844cadd3f968fc7432a48e00'},
        strict_bounds=True,bios_resident=False,checks=[],images=[])
    pipeline.check_disc(profile,disc,cue)
    entries=disc.files
    # MAIN payload addresses/entry points come from their actual headers.
    for language in range(5):
        name=f'EXE/MAIN{language}.EXE';raw=disc.read(name)
        entry,base,size=(struct.unpack_from('<I',raw,p)[0] for p in (0x10,0x18,0x1C))
        body=raw[2048:2048+size]
        profile['images'].append(dict(method='fixed_address_extents',file=name,
            extents=[dict(file=name,file_offset=2048,base=hex(base),address=hex(base),load_addr=hex(base),size=size,
                          sha256=hashlib.sha256(body).hexdigest())],
            load_addr=hex(base),allow_missing=True,entries=[hex(entry)]))
    seen=set()
    for language in range(5):
        xfile=f'SYSTEM/X{language}00.BIN'
        tables=find_tables(disc.read(xfile))
        if len(tables)!=1:raise ValueError(f'Ambiguous actual EU link base: {xfile}')
        _,base,_=tables[0]
        mainfile=f'EXE/MAIN{language}.EXE';main=disc.read(mainfile)
        # Loader's type-F0 arm: compare F0 then form a2 = the exact link base.
        words={0x8004F614:0x240200F0,0x8004F624:0x3C06800F,
               0x8004F628:0x24C60000|(base&0xFFFF)}
        for address,word in words.items():
            if struct.unpack_from('<I',main,address-0x80010000+2048)[0]!=word:
                raise ValueError(f'Unverified EU loader: {mainfile} {address:X}')
        profile['checks'].append(dict(method='words',file=mainfile,base='0x80010000',
            file_offset=2048,values={hex(k):hex(v) for k,v in words.items()}))
        names=[f'SYSTEM/D{language}SPSUB{s}.BIN' for s in ('','2','3')]
        names += [f'SYSTEM/I{language}NFO{s}.BIN' for s in ('','2','3')]
        names += [f'SYSTEM/O{language}PTSUB0.BIN',f'SYSTEM/G{language}OVER.BIN']
        areas={'startup':[0], 'opening':[0,1],
               'full':[0,1,2,3,4,5,6,8,9,10,11,13,14,16,17,18,19]}[args.scope]
        names += [f'SYSTEM/X{language}{area:02d}.BIN' for area in areas]
        for name in names:
            raw=disc.read(name);key=(base,hashlib.sha256(raw).hexdigest())
            if key in seen:continue
            seen.add(key)
            profile['images'].append(dict(method='fixed_address_files',files=[name],
                load_addr=hex(base),allow_missing=True))
    profile['expected_records']=len(profile['images'])
    profile_path=work/'profile.json';profile_path.write_text(json.dumps(profile,indent=2)+'\n')
    # Every recipe is recovered from declared original sources using the
    # framework's supported missing-image discovery and original-byte audit.
    inventory=pipeline.prepare(profile,disc,[],work)
    print(f'Verified {len(inventory["jobs"])} original EU recipes',flush=True)
    if args.prepare_only:return
    compiler=ROOT/'build-eu-tools/psxrecomp-game.exe'
    gcc=executable('clang.exe')
    attempt=Path(tempfile.mkdtemp(prefix='native-',dir=work))
    print(f'Native build/audit directory: {attempt}',flush=True)
    reuse=None
    selected=inventory
    if args.reuse_from:
        reuse=args.reuse_from.resolve()
        previous_inventory=reuse.parent/'runtime-input-inventory.json'
        previous=json.loads(previous_inventory.read_text())
        pipeline.audit(home/'game.toml',compiler,reuse/'cache',previous_inventory,attempt/'reuse-audit.json')
        keys={job['recipe_sha256'] for job in previous['jobs']}
        selected=dict(inventory,jobs=[job for job in inventory['jobs'] if job['recipe_sha256'] not in keys])
        print(f'Re-audited cache reuse: compiling {len(selected["jobs"])} additional recipes',flush=True)
    # --project-root is the overlay compiler's BIOS-address-profile search root.
    # Its CWD/config remain eu/, so no US annotations or game seeds are read.
    cache=pipeline.build(selected,home/'game.toml',compiler,attempt,gcc,args.workers,ROOT)
    if reuse:
        for source in (reuse/'cache').rglob('*'):
            if not source.is_file():continue
            target=cache/source.relative_to(reuse/'cache')
            if target.exists() and source.read_bytes()!=target.read_bytes():
                raise ValueError(f'Conflicting reused native artifact: {target}')
            target.parent.mkdir(parents=True,exist_ok=True)
            shutil.copy2(source,target)
    receipt=pipeline.audit(home/'game.toml',compiler,cache,work/'runtime-input-inventory.json',attempt/'audit.json')
    receipt['profile_sha256']=hashlib.sha256(profile_path.read_bytes()).hexdigest()
    receipt['required_images']=inventory['required_images']
    stage_native(cache,receipt)
    print(f'PASS: staged {receipt["published_pairs"]} audited EU native pairs',flush=True)

if __name__=='__main__':main()
