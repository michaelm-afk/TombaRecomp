"""Export reviewed source deltas only, from committed revisions.

No Git history, agent configuration, generated game sources or local state.
"""
from pathlib import Path
import json
import shutil
import subprocess
import argparse

ROOT = Path(__file__).resolve().parents[1]
BASES = {
    'TombaRecomp': '1b7bafa5afc3dfd08a4889f2361f9a177e6b0f52',
    'psxrecomp': '03e635e86dceb540b7b6421ada7ee32cc28ca62b',
    'recomp-ui': '7e884a227accea91ddb378671bd49aaeeea13371',
}
GAME_PATHS = [
    'eu/CMakeLists.txt', 'eu/VERSION', 'eu/game.toml', 'eu/pc.toml',
    'eu/prepare.py', 'eu/build_aot.py', 'eu/build_seamless_hooks.py',
    'eu/boot.c', 'eu/boot_profile.py', 'eu/tests/test_controller_reconnect.cpp',
    'eu/tests/test_language_confirmation.cpp', 'eu/tests/test_selector_runtime.py',
    'eu/tests/test_hd_install.cpp', 'eu/tests/test_hd_install.py',
    'eu/tests/test_host_sha256.cpp', 'eu/tests/measure_startup_phases.py',
    'eu/tests/compare_movement.py',
    'eu/build_release.py', 'eu/toolchain.py', 'eu/disc_identity.py',
    'eu/session_state.py', 'eu/campaign_test.py', 'eu/routes/regular_de.json',
    'eu/geometry.c', 'eu/geometry_profile.py', 'eu/seamless_catalog.py',
    'eu/seamless_profiles.py', 'eu/seeds', 'eu/seamless', 'eu/mods',
    'eu/tests/test_hybrid_controller.c', 'eu/release',
    'eu/stage_release.py', 'eu/create_source_handoff.py',
    'eu/tests/audit_release_imports.py', 'eu/tests/test_portable_release.py',
    'handoff/upstream-bugs-2026-10-21',
    'src/hle/tomba_geometry_hle.c', 'src/mods/tomba_seamless_prepare.cpp',
    'tools/seamless_asset_probe.py', 'tools/probe_eu_title_layouts.py',
    'tools/probe_eu_languages.py', 'tests/test_seamless_prepare.cpp',
]


def git(repo, *args):
    return subprocess.check_output(['git', '-C', str(repo), *args])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', default='public-final-staging/source')
    args = parser.parse_args()
    out = (ROOT / args.output).resolve()
    if not out.is_relative_to(ROOT): parser.error('output must remain in project')
    out.mkdir(exist_ok=False)
    metadata = {}
    for name, base in BASES.items():
        repo = ROOT if name == 'TombaRecomp' else ROOT / name
        selected = GAME_PATHS if name == 'TombaRecomp' else ['.']
        head = git(repo, 'rev-parse', 'HEAD').decode().strip()
        patch = git(repo, 'diff', '--binary', '--no-ext-diff', '--unified=0',
                    base, head, '--', *selected)
        (out / (name + '.patch')).write_bytes(patch)
        metadata[name] = dict(base=base, revision=head,
                             apply_in='project root' if name == 'TombaRecomp' else name,
                             patch_bytes=len(patch))
    (out / 'SOURCE_BASES.json').write_text(json.dumps(metadata, indent=2) + '\n')
    shutil.copy2(ROOT / 'eu/release/docs/DEVELOPER.md', out / 'README.md')
    shutil.copy2(ROOT / 'LICENSE', out / 'LICENSE')
    print(json.dumps(metadata, indent=2))


if __name__ == '__main__':
    main()
