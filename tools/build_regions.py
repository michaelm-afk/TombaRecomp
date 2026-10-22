#!/usr/bin/env python3
"""Build Windows US/EU candidates and audited AOT caches, serially.

Use --plan to inspect commands, or --check to validate inputs without building.
This does not publish a release or certify gameplay/feature parity.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
DISCS = {
    'us': ('Tomba! (USA)', 280193760,
           'c259ec7ff6ef4163913991f4e4db2eff71702818', 'SCUS-94236'),
    'eu': ('Tombi! (Europe) (En,Fr,De,It,Nl) (Rev 1)', 492370032,
           '2505d958b4439d04844cadd3f968fc7432a48e00', 'SCES-01330'),
}


def data_track(path: Path) -> Path:
    path = path.resolve(strict=True)
    if path.suffix.lower() in ('.bin', '.img'):
        return path
    if path.suffix.lower() != '.cue':
        raise ValueError(f'Use a raw BIN/IMG or single-track MODE2/2352 CUE: {path}')
    text = path.read_text(encoding='utf-8-sig')
    files = re.findall(r'^\s*FILE\s+"([^"]+)"\s+BINARY\s*$', text, re.I | re.M)
    tracks = re.findall(r'^\s*TRACK\s+(\d+)\s+(\S+)', text, re.I | re.M)
    indexes = re.findall(r'^\s*INDEX\s+(\d+)\s+(\S+)', text, re.I | re.M)
    if (len(files) != 1 or len(tracks) != 1 or
            int(tracks[0][0]) != 1 or tracks[0][1].upper() != 'MODE2/2352' or
            len(indexes) != 1 or int(indexes[0][0]) != 1 or indexes[0][1] != '00:00:00'):
        raise ValueError(f'Expected an original single-track MODE2/2352 dump: {path}')
    return (path.parent / files[0]).resolve(strict=True)


def sha1(path: Path) -> str:
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha1').hexdigest()


def checked_track(region: str, source: Path) -> Path:
    track = data_track(source)
    _, size, expected, serial = DISCS[region]
    actual = sha1(track)
    if track.stat().st_size != size or actual != expected:
        hint = ' SCES-01331 is not supported by this EU handoff.' if region == 'eu' else ''
        raise ValueError(f'{region.upper()} requires {serial}: expected SHA1 {expected}; '
                         f'got {actual} ({track.stat().st_size} bytes).{hint}')
    return track


def stage_disc(region: str, source: Path) -> None:
    name = DISCS[region][0]
    destination = ROOT / 'disc' / (name + '.bin')
    destination.parent.mkdir(parents=True, exist_ok=True)
    if not destination.exists():
        temporary = destination.with_suffix('.bin.partial')
        with source.open('rb') as reader, temporary.open('xb') as writer:
            shutil.copyfileobj(reader, writer)
        if sha1(temporary) != DISCS[region][2]:
            raise ValueError(f'Disc copy verification failed: {temporary}')
        temporary.rename(destination)
    cue = destination.with_suffix('.cue')
    if not cue.exists():
        cue.write_text(f'FILE "{destination.name}" BINARY\n'
                       '  TRACK 01 MODE2/2352\n    INDEX 01 00:00:00\n', encoding='ascii')


def build_plan(regions, jobs, tool, bash, scope, qa=False):
    python = [sys.executable, '-I', '-B']
    compiler = ('clang.exe', 'clang++.exe') if 'eu' in regions else ('gcc.exe', 'g++.exe')
    cmake = tool('cmake.exe')
    common = ['-G', 'Ninja', '-DCMAKE_BUILD_TYPE=Release',
              '-DCMAKE_C_COMPILER=' + tool(compiler[0]),
              '-DCMAKE_CXX_COMPILER=' + tool(compiler[1]),
              '-DCMAKE_MAKE_PROGRAM=' + tool('ninja.exe')]
    steps = []
    def add(label, command, cwd=ROOT, extra=None):
        steps.append((label, list(map(str, command)), cwd, extra or {}))
    add('Build tool configuration', [cmake, '-S', 'psxrecomp/recompiler', '-B', 'build-eu-tools',
                                     *common, '-DBUILD_TESTING=OFF', '-DPSXRECOMP_ENABLE_CHD=OFF'])
    add('Build emitters', [cmake, '--build', 'build-eu-tools', '--target',
                          'psxrecomp-game', 'psxrecomp-bios', '-j', jobs])
    add('Generate OpenBIOS', [bash, 'tools/regen_bios.sh', '--config', 'bios/OpenBIOS.toml'],
        ROOT / 'psxrecomp', {'PSXRECOMP_BIOS_BUILD': '../build-eu-tools'})
    runtime = ['-DPSX_DEBUG_TOOLS=OFF', '-DPSX_PGXP_VARIANT=OFF',
               '-DPSXRECOMP_BIOS_STEMS=OpenBIOS', '-DBUILD_TESTING=OFF']
    emitter = ROOT / 'build-eu-tools/psxrecomp-game.exe'
    if 'us' in regions:
        native = ROOT / 'build-regions/us/native'
        add('US code generation', [emitter, '--config', 'game.toml'])
        add('US configuration', [cmake, '-S', ROOT, '-B', native, *common, *runtime])
        add('US native executable', [cmake, '--build', native, '--target', 'psx-runtime', '-j', jobs])
        add('US original-disc AOT and audit', [*python, 'tools/build_us_aot.py',
            'release', '--profile', 'aot/overlays.json', '--game-toml', 'game.toml',
            '--runtime-config', 'game.toml', '--recompiler', emitter,
            '--runtime-build-dir', native, '--runtime-target', 'psx-runtime',
            '--work-dir', ROOT / 'build-regions/us/aot', '--stage', native,
            '--gcc', tool(compiler[0]), '--workers', jobs])
    if 'eu' in regions:
        add('EU original-disc verification and extraction', [*python, 'eu/prepare.py',
            '--disc', ROOT / 'disc' / (DISCS['eu'][0] + '.cue')])
        add('EU boot code generation', [emitter, '--config', 'eu/game.toml'])
        add('EU baseline configuration', [cmake, '-S', 'eu', '-B', 'build-eu-prototype/native',
            *common, *runtime])
        # The baseline must produce its codegen hash before compiling overlays.
        add('EU baseline executable', [cmake, '--build', 'build-eu-prototype/native',
            '--target', 'tombi-eu', '-j', jobs])
        add('EU original-disc AOT and audit', [*python, 'eu/build_aot.py',
            '--scope', scope, '--workers', jobs])
        add('EU resident catalog', [*python, 'eu/seamless_catalog.py'])
        add('EU native HLE entry hooks and audit', [*python, 'eu/build_seamless_hooks.py',
            '--scope', scope, '--workers', jobs])
        final = [*python, 'eu/build_release.py', '--jobs', jobs]
        if qa:
            final += ['--debug-tools', '--build-dir', 'build-eu-qa/native']
        add('EU private QA executable' if qa else 'EU release executable', final)
    return steps


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--region', choices=('us', 'eu', 'both'), default='both')
    parser.add_argument('--us-disc', type=Path)
    parser.add_argument('--eu-disc', type=Path)
    parser.add_argument('--jobs', type=int, default=3)
    parser.add_argument('--eu-aot-scope', choices=('opening', 'full'), default='opening',
                        help='opening is release-qualified; full is experimental and may fail code-safety audit')
    parser.add_argument('--qa', action='store_true', help='Build an EU private debug-tools candidate for automation')
    parser.add_argument('--toolchain-bin', type=Path,
                        default=os.environ.get('TOMBI_TOOLCHAIN_BIN'))
    parser.add_argument('--bash', default='C:/Program Files/Git/bin/bash.exe')
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('--plan', action='store_true', help='Print commands; write nothing')
    mode.add_argument('--check', action='store_true', help='Verify disc/tool inputs; write nothing')
    args = parser.parse_args()
    if args.jobs < 1:
        parser.error('--jobs must be positive')
    if args.toolchain_bin:
        args.toolchain_bin = args.toolchain_bin.resolve()
    regions = ('us', 'eu') if args.region == 'both' else (args.region,)
    path = os.pathsep.join(filter(None, [str(args.toolchain_bin or ''), os.environ.get('PATH', '')]))
    def tool(name):
        found = shutil.which(name, path=path)
        return str(Path(found).resolve()) if found else name
    steps = build_plan(regions, args.jobs, tool, args.bash, args.eu_aot_scope, args.qa)
    if args.plan:
        for label, command, cwd, extra in steps:
            print(f'[{label}] cwd={cwd}')
            if extra:
                print('  env: ' + json.dumps(extra))
            print('  ' + subprocess.list2cmdline(command))
        return
    if os.name != 'nt':
        parser.error('This entry point targets Windows; the supplied EU build helpers use Windows native modules.')
    sources = {}
    # Validate the entire selection before copying discs or starting any build.
    for region in regions:
        source = getattr(args, region + '_disc') or ROOT / 'disc' / (DISCS[region][0] + '.cue')
        sources[region] = checked_track(region, source)
        canonical = ROOT / 'disc' / (DISCS[region][0] + '.bin')
        if canonical.exists():
            checked_track(region, canonical)
        cue = canonical.with_suffix('.cue')
        if cue.exists():
            if data_track(cue) != canonical.resolve():
                raise ValueError(f'Existing canonical CUE references a different file: {cue}')
    required = ['cmake.exe', 'ninja.exe']
    required += ['clang.exe', 'clang++.exe'] if 'eu' in regions else ['gcc.exe', 'g++.exe']
    for name in required:
        if not shutil.which(name, path=path):
            raise ValueError(f'Missing developer tool: {name}')
    if not Path(args.bash).is_file():
        raise ValueError(f'Git Bash not found: {args.bash}; pass --bash')
    for relative in ('psxrecomp/lib/recomp-net/CMakeLists.txt',
                     'psxrecomp/lib/retcomm-rbengine/CMakeLists.txt'):
        if not (ROOT / relative).is_file():
            raise ValueError(f'Missing dependency {relative}; initialize pinned submodules recursively.')
    print('PASS: selected discs and developer tools verified; no files changed.', flush=True)
    if args.check:
        return
    scratch = ROOT / 'build-regions/temp'
    scratch.mkdir(parents=True, exist_ok=True)
    env = dict(os.environ, PATH=path, TEMP=str(scratch), TMP=str(scratch),
               TMPDIR=scratch.as_posix(), PYTHONDONTWRITEBYTECODE='1',
               XDG_CACHE_HOME=str(scratch / 'cache'), CCACHE_DIR=str(scratch / 'ccache'),
               SCCACHE_DIR=str(scratch / 'sccache'),
               APPDATA=str(scratch / 'profile/Roaming'),
               LOCALAPPDATA=str(scratch / 'profile/Local'))
    for key in ('XDG_CACHE_HOME', 'CCACHE_DIR', 'SCCACHE_DIR', 'APPDATA', 'LOCALAPPDATA'):
        Path(env[key]).mkdir(parents=True, exist_ok=True)
    env.pop('PYTHONHOME', None)
    env.pop('PYTHONPATH', None)
    if args.toolchain_bin:
        env['TOMBI_TOOLCHAIN_BIN'] = str(args.toolchain_bin.resolve())
    for region, source in sources.items():
        stage_disc(region, source)
    for label, command, cwd, extra in steps:
        print(f'[{label}]', flush=True)
        subprocess.run(command, cwd=cwd, env=dict(env, **extra), check=True)
    print('Candidates built. EU packaging: eu/stage_release.py; gameplay validation remains separate.')


if __name__ == '__main__':
    try:
        main()
    except (OSError, ValueError, subprocess.CalledProcessError) as exc:
        print(f'build_regions: {exc}', file=sys.stderr)
        raise SystemExit(1)
