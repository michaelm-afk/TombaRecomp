"""Compile a separate portable EU2 player; keep private cards and builds intact."""
import argparse
import os
from pathlib import Path
import shutil
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'eu2'))
sys.path.insert(0,str(ROOT/'eu'))
from toolchain import executable
from revisions import source, active, write_standalone_catalog

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--jobs',type=int,default=3)
    parser.add_argument('--build-dir',default='build-eu2-release/native')
    parser.add_argument('--webp-source',type=Path)
    parser.add_argument('--debug-tools',action='store_true',help='Private QA build; never package as a player release')
    parser.add_argument('--validate-geometry',action='store_true',help='Private debug build; never stage as a player release')
    args=parser.parse_args()
    build=(ROOT/args.build_dir).resolve()
    if args.jobs<1 or not build.is_relative_to(ROOT):parser.error('Invalid private build destination/jobs')
    build.mkdir(parents=True,exist_ok=True)
    env=dict(os.environ)
    for key in ('PYTHONPATH','PYTHONHOME'):env.pop(key,None)
    for key in ('TEMP','TMP','CCACHE_DIR','SCCACHE_DIR','XDG_CACHE_HOME','LOCALAPPDATA','APPDATA'):
        path=build.parent/'build-temp'/key;path.mkdir(parents=True,exist_ok=True);env[key]=str(path)
    cmake=executable('cmake.exe')
    mapping='-ffile-prefix-map='+ROOT.as_posix()+'=. -fmacro-prefix-map='+ROOT.as_posix()+'=.'
    argv=[cmake,'-S',str(ROOT/'eu2'),'-B',str(build),'-G','Ninja',
        '-DCMAKE_BUILD_TYPE=Release','-DTOMBI_EU2_SEAMLESS=ON','-DTOMBI_EU2_PLAYER_RELEASE=ON',
        '-DTOMBI_EU2_GEOMETRY_VALIDATE=OFF',
        '-DPSX_DEBUG_TOOLS=OFF','-DPSX_PGXP_VARIANT=OFF','-DPSXRECOMP_BIOS_STEMS=OpenBIOS',
        '-DPython3_EXECUTABLE='+sys.executable,'-DBUILD_TESTING=OFF',
        '-DCMAKE_C_COMPILER='+executable('clang.exe'),'-DCMAKE_CXX_COMPILER='+executable('clang++.exe'),
        '-DCMAKE_MAKE_PROGRAM='+executable('ninja.exe'),'-DCMAKE_C_COMPILER_LAUNCHER=',
        '-DCMAKE_CXX_COMPILER_LAUNCHER=','-DCMAKE_C_FLAGS='+mapping,'-DCMAKE_CXX_FLAGS='+mapping]
    webp=args.webp_source or ROOT/'build-eu2/native/_deps/psx_libwebp-src'
    if args.debug_tools or args.validate_geometry:
        argv += ['-DTOMBI_EU2_PLAYER_RELEASE=OFF','-DPSX_DEBUG_TOOLS=ON',
                 '-DTOMBI_EU2_GEOMETRY_VALIDATE='+('ON' if args.validate_geometry else 'OFF')]
    if webp.is_dir():argv+=['-DFETCHCONTENT_SOURCE_DIR_PSX_LIBWEBP='+str(webp.resolve())]
    for label,command in [('configure',argv),('build',[cmake,'--build',str(build),'--target','tombi-eu2','-j',str(args.jobs)])]:
        print(label,build,flush=True)
        with (build.parent/(label+'.log')).open('w') as log:
            subprocess.run(command,cwd=ROOT,env=env,stdout=log,stderr=subprocess.STDOUT,check=True,
                           creationflags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0)
    # Direct QA launches and production packages use the same reviewed wide
    # configuration. Never relabel the handoff's narrow native modules.
    shutil.copy2(source('release/game.toml'),build/'game.toml')
    (build/'disc-revision.txt').write_text(active()+'\n',encoding='ascii')
    write_standalone_catalog(build)
    (build/'seeds').mkdir(exist_ok=True)
    shutil.copy2(ROOT/'eu2/seeds/boot.txt',build/'seeds/boot.txt')
    print('Player build complete:',build/'TombiRecompEU2.exe',flush=True)

if __name__=='__main__':main()
