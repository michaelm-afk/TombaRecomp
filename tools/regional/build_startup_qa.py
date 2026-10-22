"""Build private instrumented counterparts; never replaces released programs."""
import argparse
import os
from pathlib import Path
import shutil
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'eu'))
from toolchain import executable


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--region',choices=['us','eu1'],required=True)
    args=parser.parse_args()
    region=args.region
    build=ROOT/'build-startup'/(region+'-qa')/'native'
    build.mkdir(parents=True,exist_ok=True)
    env=dict(os.environ)
    for key in ('TEMP','TMP','CCACHE_DIR'):
        folder=build.parent/key
        folder.mkdir(exist_ok=True)
        env[key]=str(folder)
    command=[executable('cmake.exe'),'-S',str(ROOT/'eu' if region=='eu1' else ROOT),
        '-B',str(build),'-G','Ninja','-DCMAKE_BUILD_TYPE=Release','-DPSX_DEBUG_TOOLS=ON',
        '-DPSX_PGXP_VARIANT=OFF','-DPSXRECOMP_BIOS_STEMS=OpenBIOS','-DBUILD_TESTING=OFF',
        '-DCMAKE_C_COMPILER='+executable('clang.exe'),'-DCMAKE_CXX_COMPILER='+executable('clang++.exe'),
        '-DCMAKE_MAKE_PROGRAM='+executable('ninja.exe'),'-DCMAKE_C_COMPILER_LAUNCHER=',
        '-DCMAKE_CXX_COMPILER_LAUNCHER=','-DPython3_EXECUTABLE='+sys.executable,
        '-DFETCHCONTENT_SOURCE_DIR_PSX_LIBWEBP='+str(ROOT/'build-eu2/native/_deps/psx_libwebp-src')]
    target='tombi-eu-seamless' if region=='eu1' else 'psx-runtime'
    if region=='eu1':command+=['-DTOMBI_SEAMLESS=ON','-DTOMBI_PLAYER_RELEASE=ON']
    for label,argv in [('configure',command),('build',[executable('cmake.exe'),'--build',str(build),'--target',target,'-j','3'])]:
        print(region,label,flush=True)
        with (build.parent/(label+'.log')).open('w') as log:
            subprocess.run(argv,cwd=ROOT,env=env,stdout=log,stderr=subprocess.STDOUT,check=True)
    original=ROOT/'build-startup/comparison'/region
    for folder in ('cache','overlay_toolchain','user-data','tomba'):
        if (original/folder).exists():shutil.copytree(original/folder,build/folder,dirs_exist_ok=True)
    shutil.copy2(original/'game.toml',build/'game.toml')
    print('Prepared private QA counterpart:',build,flush=True)


if __name__=='__main__':main()
