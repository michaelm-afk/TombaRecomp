"""Reconstruct pinned source archives + patches and build in an isolated folder.

Uses only local Git objects and an explicitly supplied legal disc/dependency cache.
Does not modify the normal checkout, manual build or cards.
"""
import argparse,json,os,shutil,subprocess,sys,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'eu'))
from toolchain import executable

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--handoff',type=Path,required=True);p.add_argument('--disc',type=Path,required=True);p.add_argument('--name',default='clean-rebuild');p.add_argument('--check-only',action='store_true');a=p.parse_args()
    if Path(a.name).name!=a.name:p.error('Name must be a folder component')
    out=ROOT/'build-eu2-closeout'/a.name;out.mkdir(parents=True,exist_ok=False);tree=out/'source';tree.mkdir()
    metadata=json.loads((a.handoff/'SOURCE_BASES.json').read_text())
    def archive(repo,revision,target):
        target.mkdir(parents=True,exist_ok=True)
        bundle=out/('archive-'+str(len(list(out.glob('archive-*'))))+'.zip')
        subprocess.run(['git','-C',str(repo),'archive','--format=zip','-o',str(bundle),revision],check=True)
        with zipfile.ZipFile(bundle) as z:
            assert all((target/n).resolve().is_relative_to(target.resolve()) for n in z.namelist());z.extractall(target)
        listing=subprocess.check_output(['git','-C',str(repo),'ls-tree','-r',revision]).decode()
        for line in listing.splitlines():
            if line.startswith('160000'):
                before,path=line.split('\t',1);rev=before.split()[2]
                # Main submodules are reconstructed with their reviewed patch below.
                if repo==ROOT:continue
                archive(repo/path,rev,target/path)
    archive(ROOT,metadata['TombaRecomp']['base'],tree)
    archive(ROOT/'psxrecomp',metadata['psxrecomp']['base'],tree/'psxrecomp')
    archive(ROOT/'recomp-ui',metadata['recomp_ui']['base'],tree/'recomp-ui')
    for folder,patch in [(tree,'TombaRecomp-EU2.patch'),(tree/'recomp-ui','recomp-ui-memory-card-safety.patch')]:
        # An archive nested below the working checkout must not inherit the
        # parent's repository discovery: give each patch root its own repo.
        subprocess.run(['git','-C',str(folder),'init','--quiet'],check=True)
        for flag in ('--check',''):
            cmd=['git','-C',str(folder),'apply']+([flag] if flag else [])+[str((a.handoff/patch).resolve())]
            subprocess.run(cmd,check=True)
    if a.check_only:
        (out/'result.json').write_text(json.dumps(dict(result='passed',exact_final_patch_application=True,source_archives_from_exact_bases=True),indent=2))
        print('PASS: exact final patches reconstruct clean source',flush=True)
        return
    env=dict(os.environ)
    for key in ('TEMP','TMP','CCACHE_DIR','SCCACHE_DIR'):
        path=out/key;path.mkdir();env[key]=str(path)
    cmake=executable('cmake.exe');mapping='-ffile-prefix-map='+tree.as_posix()+'=. -fmacro-prefix-map='+tree.as_posix()+'=.'
    common=['-G','Ninja','-DCMAKE_BUILD_TYPE=Release','-DBUILD_TESTING=OFF',
        '-DCMAKE_C_COMPILER='+executable('clang.exe'),'-DCMAKE_CXX_COMPILER='+executable('clang++.exe'),
        '-DCMAKE_MAKE_PROGRAM='+executable('ninja.exe'),'-DCMAKE_C_COMPILER_LAUNCHER=',
        '-DCMAKE_CXX_COMPILER_LAUNCHER=','-DCMAKE_C_FLAGS='+mapping,'-DCMAKE_CXX_FLAGS='+mapping]
    commands=[
        [sys.executable,'-I','-B','eu2/prepare.py','--disc',str(a.disc.resolve())],
        [cmake,'-S','psxrecomp/recompiler','-B','build-eu-tools',*common],
        [cmake,'--build','build-eu-tools','--target','psxrecomp-game','psxrecomp-bios','-j','3'],
        [str(tree/'build-eu-tools/psxrecomp-game.exe'),'--config','eu2/game.toml'],
        [sys.executable,'-I','-B','eu/seamless_catalog.py','--variant','eu2'],
        [sys.executable,'-I','-B','eu2/build_release.py','--webp-source',str(ROOT/'build-eu2/native/_deps/psx_libwebp-src')],
        [sys.executable,'-I','-B','eu2/build_aot.py','--seamless','--workers','3'],
        [sys.executable,'-I','-B','eu2/stage_release.py','--runtime-toolchain',str(ROOT/'build-eu2/native/overlay_toolchain')]]
    for n,cmd in enumerate(commands):
        print('Clean rebuild',n+1,'/',len(commands),flush=True)
        with (out/f'step-{n+1}.log').open('w') as log:subprocess.run(cmd,cwd=tree,env=env,stdout=log,stderr=subprocess.STDOUT,check=True)
    (out/'result.json').write_text(json.dumps(dict(result='passed',patch_apply_check=True,source_archives_from_exact_bases=True,rebuilt_player_and_aot=True,dependency_reuse=['pinned libwebp sources','bundled Python/TinyCC runtime dependencies'],no_personal_cards_used=True),indent=2))
    print('PASS: isolated source rebuild and staging',tree/'dist/SCES01331-windows-x64',flush=True)

if __name__=='__main__':main()
