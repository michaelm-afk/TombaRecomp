"""Allowlisted local release staging. Refuses to overwrite an existing package.

Run after build_release.py. Never copies player state or original disc assets.
The output is ignored by Git and is not published by this tool.
"""
from pathlib import Path
import hashlib
import json
import re
import shutil
import subprocess
import sys
import zipfile
import argparse

sys.path.insert(0, str(Path(__file__).resolve().parent))
from toolchain import executable

ROOT = Path(__file__).resolve().parents[1]


def copy(source, destination):
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)


def privacy(directory):
    problems = []
    pattern = re.compile(r'(?:[A-Za-z]:[\\/](?:Users|Projects|Emulator)[\\/]|/' + r'Users/)', re.I)
    forbidden = {'.mcd', '.cue', '.bin', '.log', '.dmp', '.pdb'}
    count = size = 0
    for file in sorted(directory.rglob('*')):
        if not file.is_file():
            continue
        rel = file.relative_to(directory).as_posix()
        if file.suffix.lower() in forbidden and rel not in ('windows-x64/bios/openbios.bin', 'bios/openbios.bin'):
            problems.append(rel + ': excluded file type')
        data = file.read_bytes()
        count += 1
        size += len(data)
        # Scan strings, not arbitrary instructions resembling a drive prefix.
        strings = [m.decode('ascii') for m in re.findall(rb'[\x20-\x7e]{6,}', data)]
        strings += [m.decode('utf-16le') for m in re.findall(rb'(?:[\x20-\x7e]\x00){6,}', data)]
        if any(pattern.search(s) for s in strings):
            problems.append(rel + ': personal absolute path')
    if problems:
        raise RuntimeError('\n'.join(problems))
    return dict(files=count, bytes=size, personal_path_scan='passed',
                excluded_extensions_scan='passed', generated_game_source='not staged')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', default='public-final-staging')
    parser.add_argument('--build-dir', default='build-eu-release-final/native')
    args = parser.parse_args()
    out = (ROOT / args.output).resolve()
    build = (ROOT / args.build_dir).resolve()
    if not out.is_relative_to(ROOT) or not build.is_relative_to(ROOT):
        parser.error('paths must remain inside the project')
    if 'PSX_DEBUG_TOOLS:BOOL=ON' in (build / 'CMakeCache.txt').read_text():
        parser.error('private debug-tools build cannot be staged')
    out.mkdir(exist_ok=False)
    player = out / 'windows-x64'
    copy(build / 'TombiRecompEU.exe', player / 'TombiRecompEU.exe')
    copy(ROOT / 'eu/release/game.toml', player / 'game.toml')
    copy(ROOT / 'eu/seeds/boot.txt', player / 'seeds/boot.txt')
    for folder in ('assets', 'bios', 'mods/bundled'):
        shutil.copytree(build / folder, player / folder)
    shutil.copytree(ROOT / 'psxrecomp/runtime/licenses', player / 'licenses')
    copy(ROOT / 'LICENSE', player / 'LICENSE')
    copy(ROOT / 'psxrecomp/LICENSE', player / 'licenses/PSXRecomp-LICENSE')
    copy(ROOT / 'recomp-ui/LICENSE', player / 'licenses/recomp-ui-LICENSE')
    copy(ROOT / 'recomp-ui/src/third_party/imgui/LICENSE.txt', player / 'licenses/ImGui-LICENSE.txt')
    copy(ROOT / 'recomp-ui/assets/common/fonts/NOTICE.md', player / 'licenses/Fonts-NOTICE.md')
    copy(ROOT / 'recomp-ui/assets/common/img/NOTICE.md', player / 'licenses/Images-NOTICE.md')
    for path in (ROOT / 'eu/release/licenses').glob('*'):
        copy(path, player / 'licenses' / path.name)
    tools_root = Path(executable('clang.exe')).parent.parent
    copy(tools_root / 'LICENSE.TXT', player / 'licenses/LLVM-LICENSE.txt')
    copy(tools_root / 'deps/share/licenses/SDL3/LICENSE.txt', player / 'licenses/SDL3-LICENSE.txt')
    for path in (tools_root / 'x86_64-w64-mingw32/share/mingw32').glob('COPYING*'):
        copy(path, player / 'licenses' / path.name)
    zlib = (tools_root / 'deps/include/zlib.h').read_text()
    (player / 'licenses/zlib-NOTICE.txt').write_text(zlib[:zlib.index('*/')+2] + '\n')
    # Only executable/ranges pairs certified by the existing source audit.
    receipt = json.loads((ROOT / 'build-eu-seamless/hook-aot/audit.json').read_text())
    assert receipt['all_pairs_valid'] and receipt['all_guards_match_known_input_bytes']
    namespace = Path('cache/SCES-01330/gcc/win-x64') / receipt['cache_tag']
    source = ROOT / 'build-eu-seamless/hook-aot' / namespace
    staged_hashes = {}
    for pair in receipt['pairs']:
        for name, digest in ((pair['dll'], pair['dll_sha256']),
                             (pair['dll'].removesuffix('.dll') + '.ranges', pair['manifest_sha256'])):
            path = source / name
            assert hashlib.sha256(path.read_bytes()).hexdigest() == digest, name
            copy(path, player / namespace / name)
            if name.endswith('.dll'):
                subprocess.run([executable('llvm-strip.exe'), '--strip-debug', str(player / namespace / name)], check=True)
                staged_hashes[name] = hashlib.sha256((player / namespace / name).read_bytes()).hexdigest()
    receipt['staged_dll_sha256_after_debug_strip'] = staged_hashes
    (player / 'AOT_CACHE_AUDIT.json').write_text(json.dumps(receipt, indent=2) + '\n')
    # Self-contained fallback: no compiler.txt from a developer installation.
    tk = player / 'overlay_toolchain'
    archive = ROOT / 'build-eu-release/python-3.13.1-embed-amd64.zip'
    assert hashlib.sha256(archive.read_bytes()).hexdigest() == '7b7923ff0183a8b8fca90f6047184b419b108cb437f75fc1c002f9d2f8bcec16'
    with zipfile.ZipFile(archive) as bundle:
        bundle.extractall(tk / 'python')
    shutil.copytree(ROOT / 'psxrecomp/overlay_toolchain/tcc', tk / 'tcc',
                    ignore=shutil.ignore_patterns('i386-win32-tcc.exe', 'examples', 'libtcc', 'doc'))
    copy(ROOT / 'build-eu-tools/psxrecomp-game.exe', tk / 'psxrecomp-game.exe')
    for dependency in ('libc++.dll', 'libunwind.dll'):
        copy(Path(executable('clang.exe')).parent / dependency, tk / dependency)
    subprocess.run([executable('llvm-strip.exe'), '--strip-debug', str(tk / 'psxrecomp-game.exe')], check=True)
    copy(ROOT / 'psxrecomp/tools/compile_overlays.py', tk / 'compile_overlays.py')
    helper = tk / 'compile_overlays.py'
    helper.write_text(helper.read_text().replace('C:' + '/' + 'Users/...', '<Windows user path>'))
    copy(ROOT / 'psxrecomp/tools/bios_module_build.py', tk / 'bios_module_build.py')
    copy(ROOT / 'build-eu-tools/psxrecomp-bios.exe', tk / 'psxrecomp-bios.exe')
    subprocess.run([executable('llvm-strip.exe'), '--strip-debug', str(tk / 'psxrecomp-bios.exe')], check=True)
    for path in (ROOT / 'psxrecomp/runtime/include').iterdir():
        if path.name.endswith(('.h', '.c.inc')):
            copy(path, tk / 'include' / path.name)
    trace_header = tk / 'include/audio_trace.h'
    trace_header.write_text(trace_header.read_text().replace(
        'F:' + '/Projects/_audio_round2/ROUND2_PLAN.md', 'the shared audio measurement design'))
    for path in (ROOT / 'psxrecomp/bios').glob('*.toml'):
        copy(path, tk / 'bios' / path.name)
    for path in (ROOT / 'psxrecomp/recompiler/seeds').glob('*.json'):
        copy(path, tk / 'recompiler/seeds' / path.name)
    for path in (ROOT / 'eu/release/docs').glob('*.md'):
        copy(path, out / 'docs' / path.name)
    copy(ROOT / 'eu/release/docs/README.md', player / 'README.md')
    copy(ROOT / 'eu/release/docs/TEST_STATUS.md', player / 'TEST_STATUS.md')
    copy(ROOT / 'psxrecomp/docs/DUCKSTATION_TEXTURE_FORMAT.md', out / 'docs/DUCKSTATION_TEXTURE_FORMAT.md')
    copy(ROOT / 'eu/release/docs/HD_TEXTURE_PACKS.md', player / 'docs/HD_TEXTURE_PACKS.md')
    copy(ROOT / 'psxrecomp/docs/DUCKSTATION_TEXTURE_FORMAT.md', player / 'docs/DUCKSTATION_TEXTURE_FORMAT.md')
    shutil.copytree(ROOT / 'handoff/upstream-bugs-2026-10-21', out / 'upstream-bugs')
    # Developer changes are staged separately by the source handoff step.
    report = privacy(out)
    (out / 'PACKAGE_AUDIT.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report))


if __name__ == '__main__':
    main()
