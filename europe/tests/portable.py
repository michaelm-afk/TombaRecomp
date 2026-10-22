"""Exact release executables, imports and bundled Python; headless only."""
import argparse,json,os,shutil,subprocess,time,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'eu/tests'))
from audit_release_imports import imports

def main():
 p=argparse.ArgumentParser();p.add_argument('--package',type=Path,required=True);p.add_argument('--name',default='Europe portable without developer tools');a=p.parse_args()
 if Path(a.name).name!=a.name:p.error('One output component')
 out=ROOT.parent/'release-qa'/a.name;out.mkdir(parents=True,exist_ok=False);app=out/'Windows x64';shutil.copytree(a.package.resolve(),app)
 assert not list(app.rglob('*.mcd')) and not list(app.rglob('settings.toml'))
 system=Path(os.environ['SystemRoot'])/'System32';env=dict(os.environ)
 for k in list(env):
  if k in ['PYTHONHOME','PYTHONPATH'] or k.startswith(('PSX_','TOMBA_','TOMBI_','RECOMP_','LNG_')):env.pop(k,None)
 env.update(PATH=str(system),SDL_AUDIO_DRIVER='dummy',SDL_AUDIODRIVER='dummy')
 binaries=[p for p in app.rglob('*') if p.suffix.lower() in ['.exe','.dll','.pyd']];names={p.name.lower() for p in binaries};missing={}
 for file in binaries:
  for name in imports(file):
   if name.lower() not in names and not (system/name).exists() and not name.lower().startswith(('api-ms-win-','ext-ms-win-')):missing.setdefault(file.relative_to(app).as_posix(),[]).append(name)
 assert not missing,missing
 for region,folder,exe,disc in [('SCES-01330',app,'TombiRecompEU.exe',ROOT/'disc/Tombi! (Europe) (En,Fr,De,It,Nl) (Rev 1).cue'),('SCES-01331',app/'backends/SCES-01331','TombiRecompEU2.exe',ROOT/'disc/eu2/disc.cue')]:
  logpath=out/(region+'.log')
  with logpath.open('w') as log:
   # Explorer/common-launcher handoff inherits the package-root cwd. A neutral
   # cwd missed EU2 accidentally loading the EU1 config before RC2.
   child=subprocess.Popen([str(folder/exe),'--headless','--no-launcher','--disc',str(disc)],cwd=app,env=env,stdout=log,stderr=subprocess.STDOUT)
   try:
    deadline=time.monotonic()+45
    while time.monotonic()<deadline:
     assert child.poll() is None,region+' exited'
     text=logpath.read_text(errors='replace')
     if 'executing from PC=' in text and 'guest video standard PAL' in text and region in text:break
     time.sleep(.2)
    else:raise TimeoutError(region)
    assert f', {region})' in text, 'wrong regional game.toml: '+region
    assert 'does not contain the expected game ID' not in text
    time.sleep(2)
   finally:child.terminate();child.wait(timeout=10)
  for i in [1,2]:
   data=(folder/'saves'/region/f'card{i}.mcd').read_bytes();assert len(data)==131072 and data[:2]==b'MC'
  result=subprocess.run([str(folder/'overlay_toolchain/python/python.exe'),'-I','-c','print("portable-python-ok")'],cwd=out,env=env,capture_output=True,text=True,check=True)
  assert 'portable-python-ok' in result.stdout
 report=dict(result='passed',both_exact_player_executables_boot=True,package_root_working_directory=True,correct_regional_config=True,original_pal=True,regionally_separate_default_cards=True,unresolved_imports=missing,bundled_python_both=True,developer_tools_removed_from_path=True,desktop_automation=False)
 (out/'result.json').write_text(json.dumps(report,indent=2)+'\n');print(out,flush=True)
if __name__=='__main__':main()
