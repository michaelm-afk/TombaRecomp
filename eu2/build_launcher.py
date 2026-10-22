"""Build the separate EU2 launcher; retain the first prototype and all player data."""
import argparse
import os
from pathlib import Path
import shutil
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'eu'))
from toolchain import executable


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--disc',type=Path,required=True)
    parser.add_argument('--jobs',type=int,default=3)
    parser.add_argument('--skip-aot',action='store_true',help='Retain already audited candidate cache')
    args=parser.parse_args()
    if args.jobs<1:parser.error('--jobs must be positive')
    build=ROOT/'build-eu2-launcher/native'
    scratch=build.parent/'build-logs'
    scratch.mkdir(parents=True,exist_ok=True)
    env=dict(os.environ)
    for key in ('TEMP','TMP','CCACHE_DIR','SCCACHE_DIR'):
        path=scratch/key;path.mkdir(exist_ok=True);env[key]=str(path)
    cmake=executable('cmake.exe')
    common=['-G','Ninja','-DCMAKE_BUILD_TYPE=Release',
        '-DCMAKE_C_COMPILER='+executable('clang.exe'),
        '-DCMAKE_CXX_COMPILER='+executable('clang++.exe'),
        '-DCMAKE_MAKE_PROGRAM='+executable('ninja.exe'),
        '-DCMAKE_C_COMPILER_LAUNCHER=','-DCMAKE_CXX_COMPILER_LAUNCHER=','-DBUILD_TESTING=OFF']
    configure=[cmake,'-S','eu2','-B',str(build),*common,'-DPSX_DEBUG_TOOLS=ON',
        '-DPSX_PGXP_VARIANT=OFF','-DPSXRECOMP_BIOS_STEMS=OpenBIOS',
        '-DTOMBI_EU2_SEAMLESS=ON','-DPython3_EXECUTABLE='+sys.executable]
    webp=ROOT/'build-eu2/native/_deps/psx_libwebp-src'
    if webp.exists():configure+=['-DFETCHCONTENT_SOURCE_DIR_PSX_LIBWEBP='+str(webp)]
    commands=[
        [sys.executable,'-I','-B','eu2/prepare.py','--disc',str(args.disc.resolve())],
        [cmake,'-S','psxrecomp/recompiler','-B','build-eu-tools',*common],
        [cmake,'--build','build-eu-tools','--target','psxrecomp-game','-j',str(args.jobs)],
        [str(ROOT/'build-eu-tools/psxrecomp-game.exe'),'--config','eu2/game.toml'],
        [sys.executable,'-I','-B','eu/seamless_catalog.py','--variant','eu2'],
        configure,[cmake,'--build',str(build),'--target','tombi-eu2','tombi-eu2-loader-tests','-j',str(args.jobs)],
        [str(build/'tombi-eu2-loader-tests.exe')]]
    if not args.skip_aot:commands.append([sys.executable,'-I','-B','eu2/build_aot.py','--seamless','--workers',str(args.jobs)])
    for index,command in enumerate(commands):
        print(f'EU2 launcher step {index+1}/{len(commands)}',flush=True)
        with (scratch/f'step-{index+1}.log').open('w') as log:
            subprocess.run(command,cwd=ROOT,env=env,stdout=log,stderr=subprocess.STDOUT,check=True)
    # All runtime dependencies remain in the new build. Never copy memory cards.
    toolchain=build/'overlay_toolchain'
    if not toolchain.exists():
        original=ROOT/'build-eu2/native/overlay_toolchain'
        if not original.exists():raise FileNotFoundError('Stage the bundled overlay toolchain first')
        shutil.copytree(original,toolchain)
    text=(ROOT/'eu2/seamless.toml').read_text()
    # Runtime discovers a project root independently of config.parent. Use
    # canonical local paths so both the launcher and compiler fallback agree.
    for old,new in [('exe = "../disc/','exe = "'+(ROOT/'disc').as_posix()+'/'),
                    ('disc = "../disc/','disc = "'+(ROOT/'disc').as_posix()+'/'),
                    ('bios_config = "../psxrecomp/','bios_config = "'+(ROOT/'psxrecomp').as_posix()+'/'),
                    ('seeds = "seeds/','seeds = "'+(ROOT/'eu2/seeds').as_posix()+'/'),
                    ('memcard_dir = "../build-eu2-launcher/manual-cards"','memcard_dir = "../manual-cards"')]:
        text=text.replace(old,new)
    config=build/'game.toml'
    if not config.exists():config.write_text(text)
    print('Ready: build-eu2-launcher/native/Tombi__SCES_01331_Prototype.exe',flush=True)


if __name__=='__main__':main()
