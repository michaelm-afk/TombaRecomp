"""Exercise the actual shared launcher UI, PLAY, and original EU2 selector."""
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import time

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'eu'))
from campaign_test import Probe, ALLOWED
ALLOWED.update(('quit','host_launch_timings','video_info','mod_counters'))


def main():
    build=ROOT/'build-eu2-launcher/native'
    out=build.parent/('launcher-qa-'+time.strftime('%Y%m%dT%H%M%S'))
    out.mkdir(parents=True)
    probe=Probe(out,4495,rpc_timeout=20)
    try:
        with socket.create_connection(('127.0.0.1',probe.port),timeout=.2):
            raise RuntimeError('Test port occupied')
    except OSError:pass
    preserved={path:path.read_bytes() if path.exists() else None for path in
        (build/'settings.toml',build/'keybinds.ini',build/'mods/state.toml')}
    # Native SDL event coordinates on this Windows/DPI QA host, observed in
    # the captured 2478x1900 dashboard. Runtime input_scale handles UI units.
    script='wait:30;view:settings;wait:3;shot:'+str(out/'settings.png')+';view:controller;wait:3;shot:'+str(out/'controller.png')+';view:dashboard;wait:3;shot:'+str(out/'dashboard.png')+';click:2190,1765;wait:300;quit'
    env=dict(os.environ,LNG_TEST_HIDDEN='1',LNG_SCRIPT=script,PSX_LAUNCHER_BOOT_TIMING='1',
        PSX_OVERLAY_AUTOCOMPILE_OFF='1',PSX_INTERNAL_RESOLUTION='native',
        PSX_RESIDENT_CACHE=str(build.parent/'resident-cache'),SDL_AUDIO_DRIVER='dummy',SDL_AUDIODRIVER='dummy')
    with (out/'runtime.log').open('w') as log:
        child=subprocess.Popen([str(build/'Tombi__SCES_01331_Prototype.exe'),'--launcher','--hidden-window',
            '--game',str(build/'game.toml'),'--disc',str(ROOT/'disc/eu2/disc.cue'),
            '--memcard-dir',str(out/'fresh-cards'),'--debug-port',str(probe.port)],cwd=build,env=env,stdout=log,stderr=subprocess.STDOUT)
        try:
            deadline=time.monotonic()+60
            while True:
                if child.poll() is not None:raise RuntimeError('Launcher exited before guest selector')
                try:
                    if probe.rpc('frame')['frame']>=1000:break
                except (OSError,RuntimeError):pass
                if time.monotonic()>deadline:raise TimeoutError('PLAY did not reach original selector')
                time.sleep(.2)
            probe.rpc('screenshot_file',path=str(out/'selector.png'))
            report=dict(result='passed',launcher_play_to_guest=True,original_selector_reached=True,
                host_timings=probe.rpc('host_launch_timings'),video=probe.rpc('video_info'),counters=probe.rpc('mod_counters'))
            (out/'result.json').write_text(json.dumps(report,indent=2))
            print('PASS: shared launcher Settings/Controller/PLAY to original EU2 selector:',out,flush=True)
        finally:
            if child.poll() is None:
                try:probe.rpc('quit');child.wait(timeout=10)
                except (OSError,RuntimeError,subprocess.TimeoutExpired):child.terminate();child.wait(timeout=10)
            (out/'events.json').write_text(json.dumps(probe.events,indent=2))
            for path,previous in preserved.items():
                if previous is None:path.unlink(missing_ok=True)
                else:path.write_bytes(previous)


if __name__=='__main__':main()
