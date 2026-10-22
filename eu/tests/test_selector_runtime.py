"""Short controller-only selector regression; private debug build and fresh cards."""
import sys, os, time, subprocess, json, hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'eu'))
from campaign_test import Probe, step
from disc_identity import main_fingerprints

def main():
 out=ROOT/'build-eu-release-rc2/selector-smoke';out.mkdir(exist_ok=False)
 build=ROOT/'build-eu-release-rc2/qa';env=dict(os.environ)
 env.pop('PYTHONHOME',None);env.pop('PYTHONPATH',None)
 env['PSX_OVERLAY_CACHE_DIR']=str(ROOT/'build-eu-seamless/hook-aot/cache')
 env['PSX_OVERLAY_AUTOCOMPILE_OFF']='1'
 probe=Probe(out,4497);started=time.monotonic()
 with (out/'runtime.log').open('w') as log:
  proc=subprocess.Popen([str(build/'TombiRecompEU.exe'),'--headless','--game',str(ROOT/'eu/release/game.toml'),'--disc',str(ROOT/'disc/Tombi! (Europe) (En,Fr,De,It,Nl) (Rev 1).cue'),'--memcard-dir',str(out/'cards'),'--debug-port','4497'],cwd=build,env=env,stdout=log,stderr=subprocess.STDOUT)
  try:
   deadline=time.monotonic()+30
   while True:
    try:probe.rpc('ping');break
    except OSError:
     if time.monotonic()>deadline:raise
     time.sleep(.1)
   probe.rpc('turbo',enabled=1);probe.wait_frame(1400)
   assert probe.ram(0x80010E50,4)==bytes.fromhex('88ffbd27'), 'selector left without confirmation'
   timer=int.from_bytes(probe.ram(0x800AF064,4),'little');assert 1<=timer<=1000,timer
   probe.drive([step(['right'],4),step([],16),step(['right'],4),step([],16),step(['cross'],4),step([],16)])
   offset,identities=main_fingerprints(ROOT);deadline=time.monotonic()+30
   while probe.ram(0x80010000+offset,64)!=identities['de']:
    if time.monotonic()>deadline:raise TimeoutError('German MAIN not reached after Cross')
    time.sleep(.1)
   frame=probe.rpc('frame')['frame']
   report=dict(result='passed',idle_frames_checked=1400,emulated_idle_seconds=28,final_frame=frame,real_seconds=round(time.monotonic()-started,3),german_main_loaded_after_manual_cross=True,inputs_only=True,no_progress_or_inventory_writes=True)
   (out/'report.json').write_text(json.dumps(report,indent=2));print(json.dumps(report))
  finally:
   if proc.poll() is None:proc.terminate()
   proc.wait(timeout=10)
   (out/'events.json').write_text(json.dumps(probe.events,indent=2))
if __name__=='__main__':main()
