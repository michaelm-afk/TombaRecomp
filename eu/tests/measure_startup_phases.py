"""Short isolated launch-phase probes; application-cold is not OS-cold."""
from pathlib import Path
import sys,os,json,time,subprocess,shutil,socket,threading,argparse
ROOT=Path(__file__).resolve().parents[2]
def rpc(port,cmd,**kw):
 with socket.create_connection(('127.0.0.1',port),timeout=2) as s:
  s.settimeout(8);s.sendall((json.dumps(dict(id=1,cmd=cmd,**kw))+'\n').encode());return json.loads(s.makefile('rb').readline())
def main():
 parser=argparse.ArgumentParser();parser.add_argument('--name',default='startup-phases');parser.add_argument('--eu-build',default='build-eu-release-rc2/qa');parser.add_argument('--eu-only',action='store_true');args=parser.parse_args()
 if Path(args.name).name!=args.name:parser.error('name must be a directory component')
 out=ROOT/'build-eu-release-rc3'/args.name;out.mkdir(parents=True,exist_ok=False);reports=[]
 for i,(name,source,exe,config,disc) in enumerate([
  ('eu',ROOT/'public-rc2/windows-x64','TombiRecompEU.exe',ROOT/'eu/release/game.toml',ROOT/'disc/Tombi! (Europe) (En,Fr,De,It,Nl) (Rev 1).cue'),
  ('us',ROOT/'build-german','Tomba__Recompiled.exe',ROOT/'game.toml',ROOT/'disc/Tomba! (USA).cue')]):
  if args.eu_only and name!='eu':continue
  stage=out/name;stage.mkdir()
  shutil.copy2(ROOT/args.eu_build/'TombiRecompEU.exe' if name=='eu' else source/exe,stage/exe)
  for folder in ('assets','bios','mods/bundled','cache'):
   if (source/folder).exists():shutil.copytree(source/folder,stage/folder,ignore=shutil.ignore_patterns('*.json','*.log','*.ok'))
  env=dict(os.environ);env.pop('PYTHONHOME',None);env.pop('PYTHONPATH',None);env['PSX_LAUNCHER_BOOT_TIMING']='1'
  for temperature in ['application-cold','warm']:
   label=name+'-'+temperature;lines=[];start=time.monotonic();port=4490+i
   proc=subprocess.Popen([str(stage/exe),'--headless','--game',str(config),'--disc',str(disc),'--memcard-dir',str(stage/'private-cards'),'--debug-port',str(port)],cwd=stage,env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,errors='replace')
   def read():
    for line in proc.stdout:lines.append(dict(seconds=round(time.monotonic()-start,5),text=line.rstrip()))
   reader=threading.Thread(target=read,daemon=True);reader.start()
   try:
    until=time.monotonic()+90
    while True:
     if proc.poll() is not None:raise RuntimeError(label+' exited')
     try:
      f=rpc(port,'frame')
      if f.get('frame',0)>=20:break
     except OSError:pass
     if time.monotonic()>until:raise TimeoutError(label)
     time.sleep(.05)
    timings=rpc(port,'host_launch_timings',count=256)
    marker=next((e['seconds'] for e in lines if 'executing from PC=' in e['text']),None)
    report=dict(case=label,before_guest_seconds=marker,observed_frame=f,host_timings=timings,codegen_messages=[e for e in lines if any(t in e['text'].lower() for t in ['compiling','codegen','compiled'])])
    reports.append(report);print(json.dumps({k:v for k,v in report.items() if k!='host_timings'}),flush=True)
   finally:
    if proc.poll() is None:proc.terminate()
    proc.wait(timeout=10);reader.join(timeout=2);(out/(label+'.json')).write_text(json.dumps(lines,indent=2))
 (out/'report.json').write_text(json.dumps(reports,indent=2))
if __name__=='__main__':main()
