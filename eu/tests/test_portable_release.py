"""Short exact-binary relocation smoke; never modifies the staged package.

No gameplay progression, input injection, original cards or saved settings.
Private output contains local paths and must not be redistributed.
"""
from pathlib import Path
import hashlib
import json
import os
import shutil
import subprocess
import time
import argparse

ROOT = Path(__file__).resolve().parents[2]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--name', default='portable smoke final')
    parser.add_argument('--package', default='public-final-staging/windows-x64')
    args = parser.parse_args()
    if Path(args.name).name != args.name:
        parser.error('name must be one directory name')
    out = ROOT / 'build-eu-release-final' / args.name
    out.mkdir(exist_ok=False)
    build = out / 'relocated game'
    shutil.copytree(ROOT / args.package, build)
    assert not (build / 'settings.toml').exists()
    assert not (build / 'mods/state.toml').exists()
    assert not list(build.rglob('*.mcd'))
    game = build / 'TombiRecompEU.exe'
    original = ROOT / 'disc/Tombi! (Europe) (En,Fr,De,It,Nl) (Rev 1).bin'
    disc = out / 'owned disc copy.bin'
    shutil.copy2(original, disc)
    before = hashlib.sha256(original.read_bytes()).hexdigest()
    cue = out / 'owned disc copy.cue'
    cue.write_text('FILE "owned disc copy.bin" BINARY\n  TRACK 01 MODE2/2352\n    INDEX 01 00:00:00\n')
    env = dict(os.environ)
    for key in list(env):
        if key in ('PYTHONHOME', 'PYTHONPATH') or key.startswith(('PSX_', 'TOMBA_', 'TOMBI_', 'RECOMP_')):
            env.pop(key, None)
    env['PATH'] = str(Path(os.environ['SystemRoot']) / 'System32')
    results = []
    for label, args, seconds in (
        ('no-disc', ['--headless'], 5),
        ('own-disc', ['--headless', '--disc', str(cue)], 12),
        ('fresh-launcher', ['--launcher'], 7),
    ):
        started = time.monotonic()
        with (out / (label + '.log')).open('wb') as log:
            proc = subprocess.Popen([str(game), *args], cwd=out, env=env,
                                    stdout=log, stderr=subprocess.STDOUT)
            try:
                code = proc.wait(timeout=seconds)
                alive = False
            except subprocess.TimeoutExpired:
                alive = True
                proc.terminate()
                code = proc.wait(timeout=5)
        text = (out / (label + '.log')).read_text(errors='replace')
        results.append(dict(case=label, real_seconds=round(time.monotonic()-started, 3),
                            alive_at_timeout=alive, exit_code=code,
                            log_bytes=len(text), game_config_anchored='game.toml' in text))
        assert 'loaded game config ' + str(build / 'game.toml') in text, label
        if label == 'no-disc':
            assert not alive and 'no disc image selected; exiting' in text
        elif label == 'own-disc':
            assert alive and 'disc region PAL (serial SCES-01330)' in text
            assert 'text image guard armed' in text
        else:
            assert alive, 'Launcher process exited before smoke timeout'
    embedded = build / 'overlay_toolchain/python/python.exe'
    result = subprocess.run([str(embedded), '-I', '-c', 'import json, pathlib; print(json.dumps({"portable":True}))'],
                            cwd=out, env=env, capture_output=True, text=True, check=True)
    assert '"portable": true' in result.stdout
    assert hashlib.sha256(original.read_bytes()).hexdigest() == before
    report = dict(results=results, original_disc_unchanged=True,
                  bundled_python_without_host_tools=True,
                  no_personal_cards_or_settings_used=True,
                  limitation='Process/config smoke only; not visual UI or gameplay acceptance.')
    (out / 'report.json').write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
