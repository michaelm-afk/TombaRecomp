"""Small fresh-start US/EU movement comparison: controller input and RAM reads only."""
from pathlib import Path
import sys,os,time,json,subprocess,shutil,struct,socket,argparse
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'eu'))
from campaign_test import Probe,step

def main():
 parser=argparse.ArgumentParser();parser.add_argument('--name',default='movement-comparison-03');args=parser.parse_args()
 if Path(args.name).name!=args.name:parser.error('name must be a directory component')
 out=ROOT/'build-eu-release-rc3'/args.name;out.mkdir(parents=True,exist_ok=False);results=[]
 for i,(region,source,exe,config,disc,game,player,hz) in enumerate([
 ('eu',ROOT/'build-eu-release-rc3/qa','TombiRecompEU.exe',ROOT/'eu/release/game.toml',ROOT/'disc/Tombi! (Europe) (En,Fr,De,It,Nl) (Rev 1).cue',0x8009C9A0,0x800A6078,50),
 ('us',ROOT/'build-german','Tomba__Recompiled.exe',ROOT/'game.toml',ROOT/'disc/Tomba! (USA).cue',0x8009BCC8,0x800A5398,59.94)]):
  stage=out/region;stage.mkdir();shutil.copy2(source/exe,stage/exe)
  for folder in ['assets','bios','mods/bundled']:
   if (source/folder).exists():shutil.copytree(source/folder,stage/folder)
  env=dict(os.environ);env.pop('PYTHONHOME',None);env.pop('PYTHONPATH',None)
  cache_source=ROOT/('build-eu-seamless/hook-aot/cache' if region=='eu' else 'build-german/cache')
  shutil.copytree(cache_source,stage/'cache',ignore=shutil.ignore_patterns('*.ok','*.json','*.log'))
  env['PSX_OVERLAY_CACHE_DIR']=str(stage/'cache')
  env['PSX_OVERLAY_AUTOCOMPILE_OFF']='1';port=4485+i;probe=Probe(stage,port)
  def sample():
   a=probe.rpc('frame')['frame'];raw=probe.ram(player,0x30);g=probe.ram(game,0x24);b=probe.rpc('frame')['frame']
   return dict(frame_before=a,frame=b,real_seconds=time.monotonic()-probe.started,state=raw[4],substate=raw[5],position=[x/65536 for x in struct.unpack_from('<iii',raw,0x10)],animation=list(struct.unpack_from('<HH',raw,0x2c)),area=list(struct.unpack_from('<HH',g)),health=g[0x10])
  with (stage/'runtime.log').open('w') as log:
   child=subprocess.Popen([str(stage/exe),'--headless','--game',str(config),'--disc',str(disc),'--memcard-dir',str(stage/'fresh-cards'),'--debug-port',str(port)],cwd=stage,env=env,stdout=log,stderr=subprocess.STDOUT)
   try:
    deadline=time.monotonic()+25
    while True:
     try:probe.rpc('ping');break
     except OSError:
      if time.monotonic()>deadline:raise
      time.sleep(.1)
    probe.rpc('turbo',enabled=1)
    if region=='eu':
     probe.wait_frame(350);probe.drive([step(['right'],4),step([],16),step(['right'],4),step([],16),step(['cross'],4),step([],16)])
    deadline=time.monotonic()+100;start_state=None
    while time.monotonic()<deadline:
     s=sample();quests=probe.ram(game+0x444,2);task=probe.ram(0x801fd848,8)
     if s['state']==1 and s['substate']==0 and abs(s['position'][0]-64)<1 and abs(s['position'][1]+52)<1 and quests[0]==1 and task==bytes.fromhex('0100010001000100'):
      start_state=s;break
     key='cross' if task[:2] in [b'\x01\x00',b'\x02\x00'] else 'start'
     probe.drive([step([key],4),step([],100)])
    if start_state is None:
     (stage/'not-ready.json').write_text(json.dumps(dict(last=s,quests=quests.hex(),task=task.hex()),indent=2));raise RuntimeError(region+' did not reach comparable regular start within bounded test')
    # Initial PLAYER_ACTIVE precedes a scripted intro: it is not playable yet.
    # Let it settle and finish the actual dialogue with ordinary Cross presses.
    settled=False
    for attempt in range(30):
     probe.drive([step([],120)]);stable=sample()
     if stable['state']==1 and stable['substate']==0 and abs(stable['position'][0]-64)<1:
      settled=True;break
     probe.drive([step(['cross'],4),step([],100)])
    if not settled:raise RuntimeError(region+' opening scene still holds player control')
    probe.rpc('turbo',enabled=0);probe.drive([step([],int(hz*.2))]);baseline=sample()
    probe.rpc('input_route_clear');probe.rpc('input_route_append',buttons=0xffff^0x20,frames=12);probe.rpc('input_route_append',buttons=0xffff,frames=30);probe.rpc('input_route_start')
    walk=[]
    while probe.rpc('input_route_status')['active']:
     walk.append(sample());time.sleep(.003)
    after_walk=sample()
    assert abs(after_walk['position'][0]-baseline['position'][0])>1, 'Walk did not move: opening/control acquisition problem, not valid speed evidence'
    probe.drive([step([],round(hz*.2))]);before_jump=sample()
    probe.rpc('input_route_clear');probe.rpc('input_route_append',buttons=0xffff^0x4000,frames=30);probe.rpc('input_route_append',buttons=0xffff,frames=100);probe.rpc('input_route_start')
    jump=[]
    while probe.rpc('input_route_status')['active']:
     jump.append(sample());time.sleep(.003)
    assert max(x['position'][1] for x in jump)-min(x['position'][1] for x in jump)>1, 'Jump did not occur; invalid speed evidence'
    result=dict(region=region,hz=hz,regular_start=start_state,baseline=baseline,walk=walk,after_walk=after_walk,before_jump=before_jump,jump=jump,after_jump=sample(),no_ram_writes=True,no_states_loaded=True)
    (stage/'samples.json').write_text(json.dumps(result,indent=2));results.append(result)
    print(region,'PASS comparable new-game start, walk and jump captured (12-frame walk / 30-frame jump hold; compare seconds)',flush=True)
   finally:
    if child.poll() is None:child.terminate()
    child.wait(timeout=10);(stage/'events.json').write_text(json.dumps(probe.events,indent=2))
 (out/'report.json').write_text(json.dumps(results,indent=2))
if __name__=='__main__':main()
