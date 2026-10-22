"""Private controller-only card probe. Always copies input cards; never edits originals.

Interactive JSON input: {"drive":[{"buttons":["cross"],"frames":4},...]},
{"sample":"label"}, {"quit":true}. No RAM writes or state loading.
"""
import hashlib,json,os,shutil,socket,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'eu'))
from campaign_test import Probe,ALLOWED,step
from session_state import profiles,decode
ALLOWED.update(('quit','mod_counters','resident_status'))

def main():
    build=ROOT/'build-eu2-launcher/native'
    out=ROOT/'build-eu2-closeout'/('card-probe-'+time.strftime('%Y%m%dT%H%M%S'))
    cards=out/'cards';cards.mkdir(parents=True)
    source=ROOT/'build-eu2-launcher/manual-cards'
    original={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in source.glob('*.mcd')}
    for name in original:shutil.copy2(source/name,cards/name)
    (out/'original-hashes.json').write_text(json.dumps(original,indent=2))
    probe=Probe(out,4498)
    try:
        with socket.create_connection(('127.0.0.1',probe.port),timeout=.2):
            raise RuntimeError('Private test port occupied; refusing to control another session')
    except OSError:pass
    identity,states=profiles(ROOT,disc_dir='disc/eu2',languages={'en':0,'es':5,'pt':6,'sv':7,'da':8})
    env=dict(os.environ,PSX_OVERLAY_AUTOCOMPILE_OFF='1',PSX_INTERNAL_RESOLUTION='native',
        PSX_RESIDENT_CACHE=str(ROOT/'build-eu2-launcher/resident-cache'),SDL_AUDIO_DRIVER='dummy',SDL_AUDIODRIVER='dummy')
    with (out/'runtime.log').open('w') as log:
        child=subprocess.Popen([str(build/'Tombi__SCES_01331_Prototype.exe'),'--headless','--no-launcher',
            '--game',str(build/'game.toml'),'--disc',str(ROOT/'disc/eu2/disc.cue'),
            '--memcard-dir',str(cards),'--debug-port','4498'],cwd=build,env=env,stdout=log,stderr=subprocess.STDOUT)
        try:
            deadline=time.monotonic()+60
            while True:
                try:
                    if probe.rpc('frame')['frame']>=350:break
                except (OSError,RuntimeError):pass
                if time.monotonic()>deadline:raise TimeoutError('Boot')
                time.sleep(.1)
            probe.drive([step(['down'],4),step([],16),step(['cross'],4),step([],1000)])
            deadline=time.monotonic()+45
            while probe.ram(0x801fd848,4)!=b'\x04\x00\x03\x00':
                if time.monotonic()>deadline:raise TimeoutError('Original title menu')
                probe.drive([step(['start'],4),step([],50)])
            probe.rpc('screenshot_file',path=str(out/'title-menu.png'))
            probe.drive([step(['right'],4),step([],20)])
            probe.rpc('screenshot_file',path=str(out/'load-choice.png'))
            probe.drive([step(['cross'],4),step([],200)])
            probe.rpc('screenshot_file',path=str(out/'before-title.png'))
            print('READY '+str(out),flush=True)
            for line in sys.stdin:
                req=json.loads(line)
                if req.get('quit'):break
                if 'drive' in req:probe.drive(req['drive'])
                if 'sample' in req:
                    label=req['sample']
                    if Path(label).name!=label:raise ValueError('Invalid label')
                    probe.rpc('screenshot_file',path=str(out/(label+'.png')))
                    language=next((k for k,v in states.items() if probe.ram(identity,64)==v['fingerprint']),None)
                    r=dict(frame=probe.rpc('frame')['frame'],language=language,counters=probe.rpc('mod_counters'))
                    if language:r['state']=decode(probe.ram(states[language]['base'],0x988),probe.ram(0x1f8001c0,64),probe.ram(0x801fd848,8))
                    (out/(label+'.json')).write_text(json.dumps(r,indent=2))
                    print(json.dumps({k:v for k,v in r.items() if k!='state'}),flush=True)
                    if 'state' in r:print(json.dumps({k:v for k,v in r['state'].items() if k not in ('quests','items')}),flush=True)
                else:print('OK',flush=True)
        finally:
            try:probe.rpc('quit');child.wait(timeout=10)
            except Exception:child.terminate();child.wait(timeout=10)
            (out/'events.json').write_text(json.dumps(probe.events,indent=2))
            assert all(hashlib.sha256((source/n).read_bytes()).hexdigest()==h for n,h in original.items()),'Original cards changed'

if __name__=='__main__':main()
