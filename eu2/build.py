"""Local prototype build entry point. Never publishes or touches original saves."""
import argparse
import os
from pathlib import Path
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'eu'))
from toolchain import executable


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--disc',type=Path,required=True)
    parser.add_argument('--jobs',type=int,default=3)
    parser.add_argument('--skip-aot',action='store_true')
    args=parser.parse_args()
    if args.jobs<1:
        parser.error('--jobs must be positive')
    env=dict(os.environ)
    scratch=ROOT/'build-eu2/temp'
    scratch.mkdir(parents=True,exist_ok=True)
    for key in ('TEMP','TMP','CCACHE_DIR','SCCACHE_DIR'):
        path=scratch/key
        path.mkdir(exist_ok=True)
        env[key]=str(path)
    cmake=executable('cmake.exe')
    common=['-G','Ninja','-DCMAKE_BUILD_TYPE=Release',
        '-DCMAKE_C_COMPILER='+executable('clang.exe'),
        '-DCMAKE_CXX_COMPILER='+executable('clang++.exe'),
        '-DCMAKE_MAKE_PROGRAM='+executable('ninja.exe'),
        '-DCMAKE_C_COMPILER_LAUNCHER=','-DCMAKE_CXX_COMPILER_LAUNCHER=','-DBUILD_TESTING=OFF']
    commands=[
        [sys.executable,'-I','-B','eu2/prepare.py','--disc',str(args.disc.resolve())],
        [cmake,'-S','psxrecomp/recompiler','-B','build-eu-tools',*common],
        [cmake,'--build','build-eu-tools','--target','psxrecomp-game','-j',str(args.jobs)],
        [str(ROOT/'build-eu-tools/psxrecomp-game.exe'),'--config','eu2/game.toml'],
        [cmake,'-S','eu2','-B','build-eu2/native',*common,'-DPSX_DEBUG_TOOLS=ON',
         '-DPSX_PGXP_VARIANT=OFF','-DPSXRECOMP_BIOS_STEMS=OpenBIOS'],
        [cmake,'--build','build-eu2/native','--target','tombi-eu2','-j',str(args.jobs)]]
    if not args.skip_aot:
        commands.append([sys.executable,'-I','-B','eu2/build_aot.py','--workers',str(args.jobs)])
    for index,command in enumerate(commands):
        print(f'Step {index+1}/{len(commands)}: {command[0]}',flush=True)
        with (scratch/f'build-step-{index+1}.log').open('w') as log:
            subprocess.run(command,cwd=ROOT,env=env,stdout=log,stderr=subprocess.STDOUT,check=True)
    print('Local prototype: build-eu2/native/TombiRecompEU2.exe',flush=True)


if __name__=='__main__':
    main()
