"""Build a separate relocatable EU release candidate; never stage private state."""
import os
from pathlib import Path
import subprocess
import sys
import argparse
import json
import re
import shutil

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'eu'))
from toolchain import executable
from geometry_profile import generate as geometry
from seamless_profiles import generate as loader
from boot_profile import generate as boot

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--build-dir', default='build-eu-release-final/native')
    parser.add_argument('--jobs', type=int, default=3)
    parser.add_argument('--debug-tools',action='store_true',help='Private QA only; never stage this binary')
    parser.add_argument('--geometry-validation',action='store_true',
        help='Private QA: compare HLE with verified original MAIN translations')
    args=parser.parse_args()
    if args.jobs < 1:parser.error('--jobs must be positive')
    if args.geometry_validation and not args.debug_tools:
        parser.error('--geometry-validation requires --debug-tools')
    geometry(references=args.geometry_validation);loader();boot()
    target=(ROOT/args.build_dir).resolve()
    if not target.is_relative_to(ROOT):parser.error('build directory must stay inside the project')
    target.mkdir(parents=True,exist_ok=True)
    env=dict(os.environ)
    for key in ('PYTHONPATH','PYTHONHOME'):env.pop(key,None)
    cmake=executable('cmake.exe')
    command=[cmake,'-S',str(ROOT/'eu'),'-B',str(target),'-G','Ninja',
        '-DCMAKE_BUILD_TYPE=Release','-DTOMBI_SEAMLESS=ON','-DTOMBI_PLAYER_RELEASE=ON',
        '-DPython3_EXECUTABLE='+sys.executable,
        '-DTOMBI_GEOMETRY_VALIDATE='+('ON' if args.geometry_validation else 'OFF'),
        '-DPSX_DEBUG_TOOLS='+('ON' if args.debug_tools else 'OFF'),'-DPSX_PGXP_VARIANT=OFF',
        '-DPSXRECOMP_BIOS_STEMS=OpenBIOS',
        '-DCMAKE_C_COMPILER='+executable('clang.exe'),
        '-DCMAKE_CXX_COMPILER='+executable('clang++.exe'),
        '-DCMAKE_MAKE_PROGRAM='+executable('ninja.exe')]
    # Optional local dependency reuse; nothing from this cache is distributed.
    cache=ROOT/'build-eu-prototype/native/CMakeCache.txt'
    if cache.exists():
        for line in cache.read_text().splitlines():
            if line.startswith(('FETCHCONTENT_SOURCE_DIR_PSX_LIBWEBP:','FETCHCONTENT_SOURCE_DIR_PSX_LIBCHDR:')):
                key,value=line.split('=',1)
                if value and Path(value).is_dir():command.append('-D'+key.split(':')[0]+'='+value)
    for label,argv in [('configure',command),('build',[cmake,'--build',str(target),'--target','tombi-eu-seamless','-j',str(args.jobs)])]:
        log=target.parent/(label+'.log');print(f'{label}: {log}',flush=True)
        with log.open('w') as output:
            subprocess.run(argv,cwd=ROOT,env=env,stdout=output,stderr=subprocess.STDOUT,check=True)
    # Direct launches use the executable's cache root. Install the audited
    # native pairs there as well as in the separate hook-build workspace.
    sys.path.insert(0,str(ROOT/'psxrecomp/tools'))
    import aot_overlay_pipeline as pipeline
    work=ROOT/'build-eu-seamless/hook-aot'
    receipt=json.loads((work/'audit.json').read_text())
    if not receipt['all_pairs_valid'] or not receipt['all_guards_match_known_input_bytes']:
        raise RuntimeError('EU native cache has not passed the original-disc audit')
    namespace=target/'cache'/receipt['game_id']/'gcc'/pipeline.compiler.cache_arch_abi()/receipt['cache_tag']
    if not namespace.resolve().is_relative_to(target):
        raise RuntimeError('Invalid native cache namespace')
    if namespace.is_dir():
        for marker in namespace.iterdir():
            if marker.is_file() and re.fullmatch(r'\.abi_[0-9a-fA-F]{8}\.ok',marker.name):
                marker.unlink()
    pipeline.stage(work/'cache',target,receipt)
    shutil.copy2(ROOT/'eu/release/game.toml',target/'game.toml')
    (target/'seeds').mkdir(exist_ok=True)
    shutil.copy2(ROOT/'eu/seeds/boot.txt',target/'seeds/boot.txt')
    print(f'Candidate built with {receipt["published_pairs"]} audited native pairs beside the executable; portable packaging/acceptance remain separate.',flush=True)

if __name__=='__main__':main()
