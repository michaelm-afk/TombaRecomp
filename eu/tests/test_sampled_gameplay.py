"""Bounded English/German controller-input smoke test using fresh private cards.

Requires a private debug-tools build and audited native caches. No RAM writes,
state loading, progression cheats, or host audio output. This is not a campaign
or save/load acceptance test.
"""
import argparse
import json
import os
from pathlib import Path
import socket
import struct
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'eu'))
import campaign_test as campaign
from disc_identity import LANGUAGES, main_fingerprints
from session_state import profiles

campaign.ALLOWED.update(('mod_counters', 'resident_status', 'video_info', 'quit'))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--name', default='sample-' + time.strftime('%Y%m%dT%H%M%S'))
    parser.add_argument('--build-dir', default='build-eu-qa/native')
    parser.add_argument('--port', type=int, default=4493)
    args = parser.parse_args()
    if Path(args.name).name != args.name:
        parser.error('--name must be a directory component')
    build = (ROOT / args.build_dir).resolve()
    output = ROOT / 'build-eu-qa' / args.name
    output.mkdir(parents=True, exist_ok=False)
    identity_offset, identities = main_fingerprints(ROOT)
    _, states = profiles(ROOT)
    report = dict(languages=[], no_ram_writes=True, no_states_loaded=True,
                  audio_output='SDL dummy', native_compilation_disabled=True,
                  limitations=['Opening movement/geometry only; no full campaign, area roundtrip, '
                               'physical controller, FMV sync or Memory Card save/load certification.'])
    executable = build / 'TombiRecompEU.exe'
    if not executable.is_file():
        parser.error(f'Missing private QA executable: {executable}')
    for language in ('en', 'de'):
        out = output / language
        out.mkdir()
        env = dict(os.environ)
        env.pop('PYTHONHOME', None)
        env.pop('PYTHONPATH', None)
        for key, path in {
            'TEMP': out / 'temp', 'TMP': out / 'temp',
            'LOCALAPPDATA': out / 'profile/Local', 'APPDATA': out / 'profile/Roaming',
            'XDG_CACHE_HOME': out / 'profile/cache',
            'PSX_RESIDENT_CACHE': ROOT / 'build-eu-qa/resident-cache',
        }.items():
            path.mkdir(parents=True, exist_ok=True)
            env[key] = str(path)
        env.update(SDL_AUDIO_DRIVER='dummy', SDL_AUDIODRIVER='dummy', PSX_OVERLAY_AUTOCOMPILE_OFF='1',
                   PSX_OVERLAY_CACHE_DIR=str(ROOT / 'build-eu-seamless/hook-aot/cache'))
        config = out / 'game.toml'
        config.write_text((ROOT / 'eu/release/game.toml').read_text().replace(
            'internal_resolution = "1080p"', 'internal_resolution = "native"'))
        probe = campaign.Probe(out, args.port)
        game = states[language]['base']
        player = None

        def sample():
            raw = probe.ram(player, 0x1c)
            return dict(frame=probe.rpc('frame')['frame'], state=raw[4], substate=raw[5],
                        position=[n / 65536 for n in struct.unpack_from('<iii', raw, 0x10)])

        def find_player():
            start = game + 0x9000
            data = probe.ram(start, 0x1000)
            matches = []
            for n in range(0, len(data) - 0x1c, 4):
                if data[n+4:n+6] != b'\x01\x00':
                    continue
                x, y = struct.unpack_from('<ii', data, n + 0x10)
                if abs(x - (64 << 16)) < 65536 and abs(y - (-52 << 16)) < 65536:
                    matches.append(start + n)
            return matches[0] if len(matches) == 1 else None

        try:
            with socket.create_connection(('127.0.0.1', args.port), timeout=.3):
                raise RuntimeError('Debug port occupied')
        except OSError:
            pass
        child = None
        try:
            with (out / 'runtime.log').open('w') as log:
                child = subprocess.Popen([str(executable), '--headless', '--game', str(config),
                    '--disc', str(ROOT / 'disc/Tombi! (Europe) (En,Fr,De,It,Nl) (Rev 1).cue'),
                    '--memcard-dir', str(out / 'fresh-cards'), '--debug-port', str(args.port)],
                    cwd=build, env=env, stdout=log, stderr=subprocess.STDOUT)
                deadline = time.monotonic() + 60
                while True:
                    if child.poll() is not None:
                        raise RuntimeError(f'Runtime exited: {child.returncode}')
                    try:
                        probe.rpc('ping')
                        break
                    except OSError:
                        if time.monotonic() > deadline:
                            raise TimeoutError('Runtime startup')
                        time.sleep(.1)
                probe.rpc('turbo', enabled=1)
                probe.wait_frame(350)
                # Exercise selector changes in the English run, then confirm
                # the selected original MAIN fingerprint in both samples.
                steps = []
                if language == 'en':
                    for key in ('right', 'right', 'left', 'left'):
                        steps += [campaign.step([key], 4), campaign.step([], 16)]
                else:
                    for _ in range(LANGUAGES.index(language)):
                        steps += [campaign.step(['right'], 4), campaign.step([], 16)]
                steps += [campaign.step(['cross'], 4), campaign.step([], 16)]
                probe.drive(steps)
                deadline = time.monotonic() + 150
                while True:
                    if time.monotonic() > deadline:
                        raise TimeoutError('Opening did not reach an identifiable playable player')
                    loaded = probe.ram(0x80010000 + identity_offset, 64) == identities[language]
                    if loaded:
                        player = find_player()
                        if player and probe.ram(game + 0x444, 1) == b'\x01':
                            break
                    task = probe.ram(0x801fd848, 8)
                    key = 'cross' if task[:2] in (b'\x01\x00', b'\x02\x00') else 'start'
                    probe.drive([campaign.step([key], 4), campaign.step([], 100)])
                # A visible player can still be in the scripted introduction.
                # Acquire control through ordinary dialogue input, prove movement.
                walk = None
                for _ in range(30):
                    probe.drive([campaign.step([], 120)])
                    settled = sample()
                    probe.drive([campaign.step([], 30)])
                    before = sample()
                    if (before['state'] != 1 or before['substate'] != 0 or
                            abs(before['position'][0] - settled['position'][0]) > .25):
                        probe.drive([campaign.step(['cross'], 4), campaign.step([], 100)])
                        continue
                    probe.drive([campaign.step(['right'], 12), campaign.step([], 30)])
                    after = sample()
                    if abs(after['position'][0] - before['position'][0]) > 1:
                        walk = dict(before=before, after=after)
                        break
                    probe.drive([campaign.step(['cross'], 4), campaign.step([], 100)])
                if walk is None:
                    raise RuntimeError('Walk did not move; no gameplay pass claimed')
                probe.rpc('turbo', enabled=0)
                probe.rpc('input_route_clear')
                for step in (campaign.step(['cross'], 30), campaign.step([], 100)):
                    bits = sum(campaign.BUTTONS[key] for key in step['buttons'])
                    probe.rpc('input_route_append', buttons=0xffff ^ bits, frames=step['frames'])
                probe.rpc('input_route_start')
                jump = []
                deadline = time.monotonic() + 15
                while probe.rpc('input_route_status')['active']:
                    if time.monotonic() > deadline:
                        raise TimeoutError('Jump route')
                    jump.append(sample())
                    time.sleep(.02)
                if not jump or max(s['position'][1] for s in jump) - min(s['position'][1] for s in jump) <= 1:
                    raise RuntimeError('Jump did not occur')
                counters = probe.rpc('mod_counters')
                counts = {item['name']: item['count'] for item in counters['counters']}
                assert counts.get('tombi.geometry.entries', 0) > 0, 'Geometry HLE not exercised'
                assert sum(counts.get('tombi.geometry.' + kind, 0)
                           for kind in ('flat', 'triangle', 'quad')) > 0, 'No geometry HLE batches completed'
                assert counts.get('tombi.seamless.native_entry_seen', 0) > 0, 'Native entry hook not exercised'
                overlays = probe.rpc('overlay_loader_status')
                assert overlays['dispatch_native'] > 0 and overlays['loads'] > 0, 'Prebuilt native overlays did not execute'
                shot = probe.rpc('screenshot_file', path=str(out / 'gameplay.png'))
                result = dict(language=language, result='passed', player=hex(player),
                    original_main_fingerprint_matched=True, selector_changes=steps,
                    walk=walk, jump=jump, counters=counters,
                    resident=probe.rpc('resident_status'),
                    overlay_loader=overlays, screenshot=shot)
                (out / 'result.json').write_text(json.dumps(result, indent=2) + '\n')
                report['languages'].append(result)
                print(f'PASS: {language} original MAIN, walk/jump, geometry and native loading hooks', flush=True)
        except Exception as exc:
            report['error'] = f'{language}: {exc}'
            raise
        finally:
            if child and child.poll() is None:
                try:
                    probe.rpc('quit')
                    child.wait(timeout=10)
                except (OSError, RuntimeError, subprocess.TimeoutExpired):
                    if child.poll() is None:
                        child.terminate()
                        child.wait(timeout=10)
            (out / 'events.json').write_text(json.dumps(probe.events, indent=2) + '\n')
            (output / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
    print(f'Sampled QA evidence: {output}', flush=True)


if __name__ == '__main__':
    main()
