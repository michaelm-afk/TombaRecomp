"""Build a separate relocatable EU release candidate; never stage private state."""
import os
from pathlib import Path
import subprocess
import sys
import argparse

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'eu'))
from toolchain import executable
from geometry_profile import generate as geometry
from seamless_profiles import generate as loader
from boot_profile import generate as boot

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--build-dir', default='build-eu-release-final/native')
    parser.add_argument('--debug-tools',action='store_true',help='Private QA only; never stage this binary')
    args=parser.parse_args()
    geometry();loader();boot()
    target=(ROOT/args.build_dir).resolve()
    if not target.is_relative_to(ROOT):parser.error('build directory must stay inside the project')
    target.mkdir(parents=True,exist_ok=True)
    env=dict(os.environ)
    for key in ('PYTHONPATH','PYTHONHOME'):env.pop(key,None)
    cmake=executable('cmake.exe')
    command=[cmake,'-S',str(ROOT/'eu'),'-B',str(target),'-G','Ninja',
        '-DCMAKE_BUILD_TYPE=Release','-DTOMBI_SEAMLESS=ON','-DTOMBI_PLAYER_RELEASE=ON',
        '-DPython3_EXECUTABLE='+sys.executable,
        '-DTOMBI_GEOMETRY_VALIDATE=OFF','-DPSX_DEBUG_TOOLS='+('ON' if args.debug_tools else 'OFF'),'-DPSX_PGXP_VARIANT=OFF',
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
    for label,args in [('configure',command),('build',[cmake,'--build',str(target),'--target','tombi-eu-seamless','-j','3'])]:
        log=target.parent/(label+'.log');print(f'{label}: {log}',flush=True)
        with log.open('w') as output:
            subprocess.run(args,cwd=ROOT,env=env,stdout=output,stderr=subprocess.STDOUT,check=True)
    print('Release candidate built; staging/privacy/first-run checks still required.',flush=True)

if __name__=='__main__':main()
