"""Bounded private boot probe; controller input and reads only, fresh cards."""
import argparse
import json
import os
from pathlib import Path
import socket
import subprocess
import struct
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'eu'))
from campaign_test import Probe, step, ALLOWED
from session_state import profiles
ALLOWED.update(('quit','mod_counters','resident_status','host_launch_timings','video_info','geom_correction','spu_status'))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--language', choices=['en', 'es', 'pt', 'sv', 'da','fr','de','it','nl'], default='en')
    parser.add_argument('--region',choices=['eu1','eu2'],default='eu2')
    parser.add_argument('--seconds', type=int, default=45)
    parser.add_argument('--play', action='store_true')
    parser.add_argument('--start', action='store_true')
    parser.add_argument('--opengl', action='store_true')
    parser.add_argument('--build-dir',default='build-eu2/native')
    parser.add_argument('--executable',help='Backend filename in the private test directory')
    parser.add_argument('--config',default='eu2/game.toml')
    parser.add_argument('--seamless',choices=['on','off'])
    parser.add_argument('--cd-fallback',action='store_true')
    parser.add_argument('--geometry',action='store_true')
    parser.add_argument('--pgxp',action='store_true')
    args = parser.parse_args()
    build = (ROOT/args.build_dir).resolve()
    if not (build.is_relative_to(ROOT) or build.is_relative_to(ROOT.parent/'release-qa')):parser.error('Build must stay inside private QA roots')
    out = build.parent / ('smoke-' + args.language + '-' + time.strftime('%Y%m%dT%H%M%S'))
    out.mkdir(parents=True)
    executable = build / ('TombiRecompEU.exe' if args.region=='eu1' else 'TombiRecompEU2.exe')
    if args.executable:
        if Path(args.executable).name!=args.executable:parser.error('Executable must be a filename')
        executable=build/args.executable
    env = dict(os.environ, SDL_AUDIO_DRIVER='dummy', SDL_AUDIODRIVER='dummy',
               PSX_OVERLAY_AUTOCOMPILE_OFF='1',PSX_INTERNAL_RESOLUTION='native')
    env['PSX_RESIDENT_CACHE']=str(build.parent/'resident-cache')
    if args.cd_fallback:env['TOMBI_SEAMLESS_TEST_CD_LISTS']='1'
    for key in ('TEMP', 'TMP', 'LOCALAPPDATA', 'APPDATA', 'XDG_CACHE_HOME'):
        folder = out / key
        folder.mkdir()
        env[key] = str(folder)
    probe = Probe(out, 4497, rpc_timeout=10)
    languages={'en':0,'fr':1,'de':2,'it':3,'nl':4} if args.region=='eu1' else {'en':0,'es':5,'pt':6,'sv':7,'da':8}
    if args.language not in languages:parser.error('Language does not belong to region')
    disc=ROOT/('disc/Tombi! (Europe) (En,Fr,De,It,Nl) (Rev 1).cue' if args.region=='eu1' else 'disc/eu2/disc.cue')
    identity_address, states = profiles(ROOT, disc_dir='disc' if args.region=='eu1' else 'disc/eu2',languages=languages)
    try:
        with socket.create_connection(('127.0.0.1', probe.port), timeout=.2):
            raise RuntimeError('Debug port occupied')
    except OSError:
        pass
    mod_state=build/'mods/state.toml'
    previous_state=mod_state.read_bytes() if mod_state.exists() else None
    if args.seamless:
        mod_state.parent.mkdir(exist_ok=True)
        mod_state.write_text('format_version = 2\n[[feature]]\npackage_id = "tombi.eu2.experimental.seamless"\n'
            'id = "resident-assets"\nenabled = '+('true' if args.seamless=='on' else 'false')+'\n')
        if args.region=='eu1':mod_state.write_text(mod_state.read_text().replace('tombi.eu2.experimental.seamless','tombi.experimental.seamless'))
    if args.geometry:
        mod_state.parent.mkdir(exist_ok=True)
        with mod_state.open('a' if args.seamless else 'w') as state:
            if not args.seamless:state.write('format_version = 2\n')
            state.write('\n[[feature]]\npackage_id = "tombi.enhancement.geometry"\nid = "geometry"\nenabled = true\n')
    if args.pgxp:
        mod_state.parent.mkdir(exist_ok=True)
        with mod_state.open('a' if args.seamless or args.geometry else 'w') as state:
            if not args.seamless and not args.geometry:state.write('format_version = 2\n')
            state.write('\n[[feature]]\npackage_id = "psx.enhancement.pgxp"\nid = "pgxp"\nenabled = true\n')
    process_started=time.monotonic()
    result=None
    with (out / 'runtime.log').open('w') as log:
        child = subprocess.Popen([str(executable), '--hidden-window' if args.opengl else '--headless', '--game', str(ROOT/args.config),
            '--disc', str(disc), '--memcard-dir', str(out/'fresh-cards'),
            '--debug-port', str(probe.port)], cwd=build, env=env, stdout=log, stderr=subprocess.STDOUT)
        try:
            deadline = time.monotonic() + args.seconds
            while time.monotonic() < deadline:
                if child.poll() is not None:
                    raise RuntimeError(f'Runtime exited {child.returncode}')
                try:
                    reply = probe.rpc('frame')
                    print('frame', reply, flush=True)
                    if reply['frame'] >= 350:
                        break
                except (OSError, RuntimeError):
                    pass
                time.sleep(.2)
            else:
                raise TimeoutError('Boot frame deadline')
            probe.rpc('screenshot_file', path=str(out/'selector.png'))
            steps = []
            navigation={'en':(), 'es':('right',), 'pt':('right','right'),
                        'sv':('down',), 'da':('down','right'),
                        'fr':('right',),'de':('right','right'),'it':('down',),'nl':('down','right')}
            for key in navigation[args.language]:
                steps += [step([key], 4), step([], 16)]
            steps += [step(['cross'], 4), step([], 16)]
            probe.drive(steps)
            if args.play or args.start:
                game = states[args.language]['base']
                def initial_player():
                    start=game+0x9000
                    data=probe.ram(start,0x1000)
                    matches=[]
                    for n in range(0,len(data)-0x1c,4):
                        # State 5 is the original opening dialogue; state 1
                        # is normal control. State-0 coordinate copies are not
                        # the live player and must not satisfy this check.
                        if data[n+4] not in (1,5) or data[n+5]!=0:
                            continue
                        x,y=struct.unpack_from('<ii',data,n+0x10)
                        if abs(x-(64<<16))<65536 and abs(y-(-52<<16))<65536:
                            matches.append(start+n)
                    return matches[0] if len(matches)==1 else None
                fingerprint = states[args.language]['fingerprint']
                deadline = time.monotonic()+150
                loaded = False
                while time.monotonic()<deadline:
                    loaded = probe.ram(identity_address,64)==fingerprint
                    if loaded:
                        break
                    probe.drive([step(['start'],4),step([],100)])
                if not loaded:
                    raise TimeoutError('Selected original MAIN not reached')
                print('Original language MAIN matched:',args.language,flush=True)
                # Open the original title menu and choose its default New Game.
                for n in range(18):
                    probe.drive([step(['start'] if n%2==0 else ['cross'],4),step([],100)])
                deadline=time.monotonic()+120
                while probe.ram(game+0x444,1)!=b'\x01' or initial_player() is None:
                    if time.monotonic()>deadline:
                        raise TimeoutError('Regular New Game initialization not reached')
                    probe.drive([step(['start'],4),step([],100),step(['cross'],4),step([],100)])
                probe.rpc('screenshot_file',path=str(out/'gameplay-candidate.png'))
                (out/'state.json').write_text(json.dumps(dict(game=hex(game),
                    identity_matched=loaded,game_bytes=probe.ram(game,0x988).hex()),indent=2))
                if args.play:
                    player = None
                    for _ in range(30):
                        probe.drive([step(['cross'],4),step([],100)])
                        start = game+0x9000
                        data = probe.ram(start,0x1000)
                        matches=[]
                        for n in range(0,len(data)-0x1c,4):
                            if data[n+4:n+6] != b'\x01\x00':
                                continue
                            x,y=struct.unpack_from('<ii',data,n+0x10)
                            if abs(x-(64<<16))<65536 and abs(y-(-52<<16))<65536:
                                matches.append(start+n)
                        if len(matches)==1:
                            player=matches[0]
                            break
                    if player is None:
                        raise RuntimeError('No unique initial player; no movement pass claimed')
                    def sample():
                        raw=probe.ram(player,0x1c)
                        return dict(frame=probe.rpc('frame')['frame'],state=raw[4],substate=raw[5],
                            position=[v/65536 for v in struct.unpack_from('<iii',raw,0x10)])
                    walk=None
                    for _ in range(30):
                        probe.drive([step([],120)])
                        before=sample()
                        probe.drive([step(['right'],12),step([],30)])
                        after=sample()
                        if before['state']==1 and before['substate']==0 and abs(after['position'][0]-before['position'][0])>1:
                            walk=dict(before=before,after=after)
                            break
                        probe.drive([step(['cross'],4),step([],100)])
                    if walk is None:
                        raise RuntimeError('Regular walk not demonstrated')
                    probe.rpc('screenshot_file',path=str(out/'walk.png'))
                    (out/'movement.json').write_text(json.dumps(dict(player=hex(player),walk=walk),indent=2))
                    print('Regular walk demonstrated:',walk,flush=True)
            overlays=None
            for n in range(4):
                time.sleep(2)
                probe.rpc('screenshot_file', path=str(out/f'after-{n}.png'))
                overlays=probe.rpc('overlay_loader_status')
                print('Native dispatches:',overlays['dispatch_native'],'loads:',overlays['loads'],flush=True)
            if args.play or args.start:
                if not overlays['loads'] or not overlays['dispatch_native']:
                    raise RuntimeError('Original MAIN reached, but prebuilt native execution not demonstrated')
                result=dict(language=args.language,
                    original_main_matched=loaded,native_dispatches=overlays['dispatch_native'],
                    native_loads=overlays['loads'],interpreter_fallbacks=overlays['dispatch_interp_fallback'],
                    renderer='opengl-requested' if args.opengl else 'software-headless',
                    new_game_initialized=True,initial_player_detected=True,regular_walk_demonstrated=args.play,
                    runtime_autocompile_disabled=True,seamless=args.seamless,
                    gameplay_checkpoint_seconds=time.monotonic()-process_started)
            counters=probe.rpc('mod_counters')
            counts={item['name']:item['count'] for item in counters['counters']}
            if args.geometry:
                assert all(counts.get('tombi.geometry.'+kind,0)>=200 for kind in ('flat','triangle','quad')),counts
                assert not counts.get('tombi.geometry.unverified_entry',0),counts
            if args.seamless=='on':
                if not counts.get('tomba.seamless.batches',0) or not counts.get('tombi.seamless.native_entry_seen',0):
                    raise RuntimeError('Seamless native batches not demonstrated')
                if args.cd_fallback and not (counts.get('tomba.seamless.fallbacks',0)+counts.get('tombi.seamless.preflight_fallbacks',0)):
                    raise RuntimeError('Controlled original-CD fallback not demonstrated')
            if args.seamless=='off' and counts.get('tomba.seamless.batches',0):
                raise RuntimeError('Disabled seamless executed a batch')
            for filename,cmd in [('mod-counters.json','mod_counters'),('resident.json','resident_status'),('host-timings.json','host_launch_timings')]:
                (out/filename).write_text(json.dumps(probe.rpc(cmd),indent=2))
            (out/'video.json').write_text(json.dumps(probe.rpc('video_info'),indent=2))
            precision=probe.rpc('geom_correction')
            (out/'precision.json').write_text(json.dumps(precision,indent=2))
            if args.pgxp:
                # geometry_vertex_hits counts the legacy position fallback;
                # exact packet dataflow is the primary precision source.
                assert precision['pgxp']['dataflow_hit']>0 and precision['pgxp']['tri_precise']>0 and precision['perspective_triangles']>0,precision
            (out/'audio.json').write_text(json.dumps(probe.rpc('spu_status'),indent=2))
            if result:
                result['result']='passed'
                (out/'result.json').write_text(json.dumps(result,indent=2))
            (out/'events.json').write_text(json.dumps(probe.events, indent=2))
        finally:
            try:
                probe.rpc('quit')
                child.wait(timeout=5)
            except Exception:
                child.terminate()
                child.wait(timeout=10)
            (out/'events.json').write_text(json.dumps(probe.events, indent=2))
            if args.seamless or args.geometry or args.pgxp:
                if previous_state is None:mod_state.unlink(missing_ok=True)
                else:mod_state.write_bytes(previous_state)
    print(out, flush=True)


if __name__ == '__main__':
    main()
