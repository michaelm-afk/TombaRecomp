"""Allowlisted offline EU2 player packaging; no personal state or Sony BIOS."""
import argparse,hashlib,json,shutil,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'eu'))
from stage_release import copy,privacy
from toolchain import executable
sys.path.insert(0,str(ROOT/'psxrecomp/tools'))
import aot_overlay_pipeline as pipeline

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output',default='dist/SCES01331-windows-x64')
    p.add_argument('--build-dir',default='build-eu2-release/native')
    p.add_argument('--runtime-toolchain',type=Path)
    p.add_argument('--audit',type=Path,default=ROOT/'build-eu2-seamless/aot/audit.json')
    p.add_argument('--cache-root',type=Path,default=ROOT/'build-eu2-launcher/native')
    p.add_argument('--region',choices=['eu1','eu2'],default='eu2')
    args=p.parse_args();out=(ROOT/args.output).resolve();build=(ROOT/args.build_dir).resolve()
    if not out.is_relative_to(ROOT) or not build.is_relative_to(ROOT):p.error('Paths must remain inside project')
    build_config=(build/'CMakeCache.txt').read_text()
    assert 'PSX_DEBUG_TOOLS:BOOL=OFF' in build_config
    assert 'TOMBI_EU2_GEOMETRY_VALIDATE:BOOL=ON' not in build_config
    assert 'TOMBI_GEOMETRY_VALIDATE:BOOL=ON' not in build_config
    out.mkdir(parents=True,exist_ok=False)
    home='eu' if args.region=='eu1' else 'eu2'
    binary='TombiRecompEU.exe' if args.region=='eu1' else 'TombiRecompEU2.exe'
    copy(build/binary,out/binary)
    copy(ROOT/home/'release/game.toml',out/'game.toml')
    copy(ROOT/home/'seeds/boot.txt',out/'seeds/boot.txt')
    for folder in ('assets','bios','mods/bundled'):shutil.copytree(build/folder,out/folder)
    shutil.copytree(ROOT/'psxrecomp/runtime/licenses',out/'licenses')
    for source,name in [('LICENSE','LICENSE'),('psxrecomp/LICENSE','licenses/PSXRecomp-LICENSE'),
        ('recomp-ui/LICENSE','licenses/recomp-ui-LICENSE'),('psxrecomp/bios/OpenBIOS.LICENSE','licenses/OpenBIOS-LICENSE'),
        ('recomp-ui/src/third_party/imgui/LICENSE.txt','licenses/ImGui-LICENSE.txt'),
        ('recomp-ui/assets/common/fonts/NOTICE.md','licenses/Fonts-NOTICE.md'),
        ('recomp-ui/assets/common/img/NOTICE.md','licenses/Images-NOTICE.md')]:copy(ROOT/source,out/name)
    for f in (ROOT/'eu/release/licenses').glob('*'):copy(f,out/'licenses'/f.name)
    tools=Path(executable('clang.exe')).parent.parent
    for source,name in [(tools/'LICENSE.TXT','LLVM-LICENSE.txt'),(tools/'deps/share/licenses/SDL3/LICENSE.txt','SDL3-LICENSE.txt')]:copy(source,out/'licenses'/name)
    for f in (tools/'x86_64-w64-mingw32/share/mingw32').glob('COPYING*'):copy(f,out/'licenses'/f.name)
    zlib=(tools/'deps/include/zlib.h').read_text()
    (out/'licenses/zlib-NOTICE.txt').write_text(zlib[:zlib.index('*/')+2]+'\n')
    # Embedded Python/TinyCC are runtime fallback dependencies, not a system
    # tool installation. No debug executables, host compiler.txt or state files.
    tk=out/'overlay_toolchain';source=args.runtime_toolchain or ROOT/'build-eu2/native/overlay_toolchain'
    for folder in ('python','tcc','include','bios','recompiler'):
        shutil.copytree(source/folder,tk/folder,ignore=shutil.ignore_patterns('__pycache__','examples','doc','libtcc','i386-win32-tcc.exe'))
    for name in ('compile_overlays.py','bios_module_build.py','psxrecomp-game.exe','psxrecomp-bios.exe','libc++.dll','libunwind.dll','libwinpthread-1.dll'):
        copy(source/name,tk/name)
    for name in ('psxrecomp-game.exe','psxrecomp-bios.exe'):
        if (ROOT/'build-eu-tools'/name).exists():copy(ROOT/'build-eu-tools'/name,tk/name)
    receipt=json.loads(args.audit.read_text())
    assert receipt['all_pairs_valid'] and receipt['all_guards_match_known_input_bytes']
    assert receipt['game_id']==('SCES-01330' if args.region=='eu1' else 'SCES-01331')
    expected_tag=pipeline.compiler.cache_tag(str(ROOT/'psxrecomp/runtime/include'),
        str(ROOT/'build-eu-tools/psxrecomp-game.exe'),str(ROOT/home/'release/game.toml'),0)
    assert receipt['cache_tag']==expected_tag,'Rebuild the native cache for this exact widescreen configuration'
    namespace=Path('cache')/receipt['game_id']/'gcc/win-x64'/receipt['cache_tag']
    cache=args.cache_root/namespace
    for pair in receipt['pairs']:
        for name,digest in [(pair['dll'],pair['dll_sha256']),(pair['dll'].removesuffix('.dll')+'.ranges',pair['manifest_sha256'])]:
            data=(cache/name).read_bytes();assert hashlib.sha256(data).hexdigest()==digest,name
            copy(cache/name,out/namespace/name)
    for f in out.rglob('*'):
        if f.suffix.lower() in ('.exe','.dll','.pyd') and 'tcc' not in f.parts:
            subprocess.run([executable('llvm-strip.exe'),'--strip-debug',str(f)],check=True)
    for language in ('DE','EN'):
        source=ROOT/home/'release'/('README_'+language+'.txt')
        if source.exists():copy(source,out/source.name)
    (out/'AOT_CACHE_AUDIT.json').write_text(json.dumps(dict(game_id=receipt['game_id'],cache_tag=receipt['cache_tag'],pairs=receipt['published_pairs'],all_pairs_valid=True,all_guards_match_known_input_bytes=True,full_static_coverage_proven=False),indent=2))
    report=privacy(out)
    report['files_sha256']={f.relative_to(out).as_posix():hashlib.sha256(f.read_bytes()).hexdigest() for f in out.rglob('*') if f.is_file()}
    (out/'PACKAGE_AUDIT.json').write_text(json.dumps(report,indent=2))
    print('PASS: staged player package',out,flush=True)

if __name__=='__main__':main()
