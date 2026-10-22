#!/usr/bin/env python3
"""Fresh-disc controller-only campaign probe. Never writes RAM or loads states."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import socket
import struct
import subprocess
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parent))
from disc_identity import main_fingerprints

ROOT = Path(__file__).resolve().parents[1]
BUTTONS = dict(up=0x10, right=0x20, down=0x40, left=0x80,
               start=8, select=1, cross=0x4000, circle=0x2000,
               square=0x8000, triangle=0x1000)
# Observed German Rev-1 addresses; gated by a disc-derived MAIN fingerprint.
GAME, PLAYER, TASK = 0x8009C9A0, 0x800A6078, 0x801FD800
ALLOWED = {'ping', 'frame', 'turbo', 'read_ram', 'screenshot_file',
           'input_route_clear', 'input_route_append', 'input_route_start',
           'input_route_status', 'overlay_loader_status', 'cdrom_state'}


class Probe:
    def __init__(self, out, port, rpc_timeout=15):
        self.out, self.port = out, port
        self.rpc_timeout = rpc_timeout
        self.started = time.monotonic()
        self.events = []

    def rpc(self, cmd, **kwargs):
        if cmd not in ALLOWED:
            raise ValueError(f'Forbidden campaign-test operation: {cmd}')
        request = dict(id=1, cmd=cmd, **kwargs)
        with socket.create_connection(('127.0.0.1', self.port), timeout=3) as s:
            s.settimeout(self.rpc_timeout)
            s.sendall((json.dumps(request)+'\n').encode())
            reply = json.loads(s.makefile('rb').readline())
        self.events.append(dict(real_seconds=time.monotonic()-self.started,
                                request=request, reply=reply))
        if not reply.get('ok'):
            raise RuntimeError(reply)
        return reply

    def ram(self, address, size):
        return bytes.fromhex(self.rpc('read_ram', addr=hex(address), len=size)['hex'])

    def wait_frame(self, target):
        deadline = time.monotonic()+90
        while self.rpc('frame')['frame'] < target:
            if time.monotonic() > deadline:
                raise TimeoutError('Guest frame target not reached')
            time.sleep(.02)

    def drive(self, steps):
        self.rpc('input_route_clear')
        total = 0
        for step in steps:
            frames = step['frames']
            if not isinstance(frames, int) or not 1 <= frames <= 10000:
                raise ValueError('Invalid frame count')
            bits = 0
            for key in step.get('buttons', []):
                bits |= BUTTONS[key]
            self.rpc('input_route_append', buttons=0xffff ^ bits, frames=frames)
            total += frames
        self.rpc('input_route_start')
        deadline = time.monotonic()+max(30, total/25)
        while self.rpc('input_route_status')['active']:
            if time.monotonic() > deadline:
                raise TimeoutError('Controller route did not finish')
            time.sleep(.02)

    def snapshot(self, label):
        if Path(label).name != label:
            raise ValueError('Checkpoint label must be a filename component')
        frame = self.rpc('frame')['frame']
        data = self.ram(GAME, 0x988)
        player = self.ram(PLAYER, 0x1c)
        task = self.ram(TASK+0x48, 8)
        state = dict(label=label, frame=frame,
            emulated_video_seconds=frame/50,
            real_seconds=time.monotonic()-self.started,
            game_timer_ticks=struct.unpack_from('<I', data, 8)[0],
            area=struct.unpack_from('<H', data, 0)[0],
            section=struct.unpack_from('<H', data, 2)[0],
            health=data[0x10], lives=data[0x20],
            wise_man_event=data[0x445], fog_event=data[0x446],
            tornado=data[0x748], bell=data[0x749],
            inventory_count=struct.unpack_from('<H', data, 0x944)[0],
            player_state=player[4], player_substate=player[5],
            position=[v/65536 for v in struct.unpack_from('<iii', player, 0x10)],
            task_state=list(struct.unpack('<4H', task)))
        try:
            self.rpc('screenshot_file', path=str(self.out/f'{label}.png'))
        except RuntimeError as exc:
            if 'display disabled' not in str(exc):
                raise
            state['screenshot_unavailable'] = 'Guest display temporarily disabled'
        (self.out/f'{label}.json').write_text(json.dumps(state, indent=2)+'\n')
        print(json.dumps(state), flush=True)
        return state


def step(buttons, frames):
    return dict(buttons=buttons, frames=frames)


def ready(state):
    return (state['task_state'] == [1, 1, 1, 1]
            and state['area'] == state['section'] == 0
            and state['wise_man_event'] == 1 and state['player_state'] == 1
            and state['player_substate'] == 0
            and abs(state['position'][0]-64) < 1
            and abs(state['position'][1]+52) < 1)


def check(state, expected):
    actual = state[expected['field']]
    if not isinstance(actual, list):
        actual = [actual]
    return len(actual) == len(expected['ranges']) and all(
        lo <= value <= hi for value, (lo, hi) in zip(actual, expected['ranges']))


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--name', required=True, help='New output directory name')
    ap.add_argument('--port', type=int, default=4392)
    ap.add_argument('--route', type=Path, default=ROOT/'eu/routes/regular_de.json')
    ap.add_argument('--explore-seconds', type=int, default=0,
                    help='Accept controller-only next-phase.json attempts after the tested prefix')
    args = ap.parse_args()
    if Path(args.name).name != args.name:
        ap.error('--name must be a directory name, not a path')
    out = ROOT/'build-eu-prototype'/args.name
    out.mkdir()  # Refuse reuse: every run starts with new, empty card paths.
    route = json.loads(args.route.read_text())
    report = dict(status='incomplete', controller_only=True,
        fresh_start=True, loaded_debug_states=False, language='de',
        route_sha256=hashlib.sha256(args.route.read_bytes()).hexdigest(),
        phases=[], targets={'fog_cleared': False, 'bell_received': False,
                            'regular_hut_exit': False, 'memory_card_roundtrip': False})
    probe = Probe(out, args.port)
    child = None
    try:
        try:
            with socket.create_connection(('127.0.0.1', args.port), timeout=.3):
                raise RuntimeError('Debug port occupied')
        except OSError:
            pass
        build = ROOT/'build-eu-prototype/native'
        env = dict(os.environ, PSX_OVERLAY_BACKEND='gcc',
            PSX_FAST_FORWARD_SPEED='max', PSX_OVERLAY_AUTOCOMPILE_OFF='1',
            PSX_OVERLAY_CACHE_DIR=str(build/'cache'))
        with (out/'runtime.log').open('w') as log:
            child = subprocess.Popen([str(build/'Tombi_EU_Prototype.exe'),
                '--headless', '--game', str(ROOT/'eu/game.toml'), '--disc',
                str(ROOT/'disc/Tombi! (Europe) (En,Fr,De,It,Nl) (Rev 1).cue'),
                '--memcard-dir', str(out/'saves'), '--debug-port', str(args.port)],
                cwd=build, env=env, stdout=log, stderr=subprocess.STDOUT)
            deadline = time.monotonic()+40
            while True:
                if child.poll() is not None:
                    raise RuntimeError(f'Runtime exited: {child.returncode}')
                try:
                    probe.rpc('ping')
                    break
                except OSError:
                    if time.monotonic() > deadline:
                        raise
                    time.sleep(.1)
            probe.rpc('turbo', enabled=1)
            probe.wait_frame(350)
            probe.drive([step(['right'], 4), step([], 16), step(['right'], 4),
                         step([], 16), step(['cross'], 4), step([], 16)])
            offset, identities = main_fingerprints(ROOT)
            deadline = time.monotonic()+180
            while True:
                if time.monotonic() > deadline:
                    raise TimeoutError('Regular opening dialogue not completed')
                loaded = probe.ram(0x80010000+offset, 64) == identities['de']
                if loaded:
                    state = probe.snapshot('opening-progress')
                    if ready(state):
                        break
                    # Title is task state0=2; state0=1 is the actual game.
                    key = 'cross' if state['task_state'][0] in (1, 2) else 'start'
                else:
                    key = 'start'
                probe.drive([step([key], 4), step([], 100)])
            probe.drive([step([], 90)])
            state = probe.snapshot('intro-ready')
            if not ready(state) or state['bell'] or state['tornado']:
                raise AssertionError('Unexpected regular opening state')
            report['phases'].append(dict(name='intro-ready', result='passed', end=state))
            for phase in route['phases']:
                before = state
                probe.drive(phase['steps'])
                state = probe.snapshot(phase['id'])
                passed = check(state, phase['expect'])
                report['phases'].append(dict(name=phase['id'],
                    result='passed' if passed else 'failed', end=state,
                    real_seconds=state['real_seconds']-before['real_seconds'],
                    emulated_video_seconds=(state['frame']-before['frame'])/50))
                if not passed:
                    raise AssertionError(f"Route checkpoint failed: {phase['id']}")
            until = time.monotonic()+args.explore_seconds
            while time.monotonic() < until and not (out/'stop').exists():
                incoming = out/'next-phase.json'
                if not incoming.exists():
                    time.sleep(.1)
                    continue
                phase = json.loads(incoming.read_text(encoding='utf-8-sig'))
                incoming.unlink()
                before = probe.snapshot('before-'+phase['id'])
                phase_started = time.monotonic()
                probe.drive(phase['steps'])
                state = probe.snapshot(phase['id'])
                passed = check(state, phase['expect'])
                attempt = dict(name=phase['id'], phase=phase,
                    result='passed' if passed else 'controller-checkpoint-missed',
                    before=before, end=state,
                    real_seconds=time.monotonic()-phase_started,
                    emulated_video_seconds=(state['frame']-before['frame'])/50)
                report.setdefault('exploration_attempts', []).append(attempt)
                (out/(phase['id']+'-attempt.json')).write_text(json.dumps(attempt, indent=2)+'\n')
            report['targets']['fog_cleared'] = state['fog_event'] == 255
            report['targets']['bell_received'] = state['bell'] > 0
            report['obstacle'] = route['next_unverified_action']
            report['loader'] = probe.rpc('overlay_loader_status')
            report['cdrom'] = probe.rpc('cdrom_state')
            # A tested prefix must never masquerade as the full campaign test.
            print('INCOMPLETE: '+report['obstacle'], flush=True)
            return 2
    except Exception as exc:
        report['error'] = str(exc)
        print('FAILED/INCOMPLETE:', exc, flush=True)
        return 1
    finally:
        if child and child.poll() is None:
            child.terminate()
            child.wait(timeout=10)
        report['real_seconds'] = time.monotonic()-probe.started
        (out/'report.json').write_text(json.dumps(report, indent=2)+'\n')
        (out/'rpc-events.json').write_text(json.dumps(probe.events, indent=2)+'\n')


if __name__ == '__main__':
    raise SystemExit(main())
