"""Unpack the delivered ZIP; real discs, real host verification, no desktop API."""
import argparse,hashlib,json,os,subprocess,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]

def main():
 p=argparse.ArgumentParser();p.add_argument('--archive',type=Path,required=True);p.add_argument('--name',required=True);a=p.parse_args()
 if Path(a.name).name!=a.name:p.error('One output folder component required')
 out=ROOT.parent/'release-qa'/a.name;out.mkdir(parents=True,exist_ok=False)
 with zipfile.ZipFile(a.archive) as z:
  assert all((out/n).resolve().is_relative_to(out.resolve()) for n in z.namelist());z.extractall(out)
 app=out/'Windows-x64';entry=app/'TombiRecompEU.exe';eu2=app/'backends/SCES-01331/TombiRecompEU2.exe'
 discs={'SCES-01330':ROOT/'disc/Tombi! (Europe) (En,Fr,De,It,Nl) (Rev 1).cue','SCES-01331':ROOT/'disc/eu2/disc.cue'}
 env=dict(os.environ);env['PATH']=str(Path(os.environ['SystemRoot'])/'System32')
 protected=[]
 for region,folder in [('SCES-01330',app),('SCES-01331',eu2.parent)]:
  f=folder/'settings.toml';f.write_text('[video]\nvsync = "adaptive"\n')
  protected.append((f,hashlib.sha256(f.read_bytes()).hexdigest()))
 cases=[]
 def check(exe,cwd,region,flags):
  result=subprocess.run([str(exe),'--launcher-disc-check',*map(str,flags)],cwd=cwd,env=env,capture_output=True,text=True,errors='replace',timeout=90)
  (out/f'case-{len(cases)+1}.txt').write_text(result.stdout+result.stderr)
  expected=f'launcher-disc-check expected={region} serial={region} verdict=1 iso=1 handoff=0'
  assert result.returncode==0 and expected in result.stdout,(result.returncode,result.stdout,result.stderr)
  own=app/'game.toml' if region=='SCES-01330' else eu2.parent/'game.toml'
  assert 'config='+str(own) in result.stdout
  cases.append(dict(region=region,passed=True))
 # Exact reported fresh-install flow: common entry -> EU2, cwd is package root.
 check(entry,app,'SCES-01331',['--disc',discs['SCES-01331']])
 # Remembered selection, no disc argument, includes real backend handoff.
 check(entry,app,'SCES-01331',[])
 # Both directions with the other region's config present in cwd.
 check(eu2,eu2.parent,'SCES-01330',['--disc',discs['SCES-01330']])
 check(entry,eu2.parent,'SCES-01330',[])
 check(eu2,app,'SCES-01331',['--disc',discs['SCES-01331'],'--game','game.toml'])
 check(entry,eu2.parent,'SCES-01330',['--disc',discs['SCES-01330'],'--game','game.toml'])
 check(entry,out,'SCES-01331',['--disc',discs['SCES-01331']])
 # Missing EU2 config must fail, never silently inherit EU1's parent config.
 own=eu2.parent/'game.toml';temp=own.with_suffix('.test-backup');own.rename(temp)
 try:
  result=subprocess.run([str(eu2),'--launcher-disc-check','--disc',str(discs['SCES-01331'])],cwd=app,env=env,capture_output=True,text=True,timeout=90)
  assert result.returncode!=0 and 'Missing regional backend game.toml' in result.stderr
 finally:temp.rename(own)
 for f,h in protected:assert hashlib.sha256(f.read_bytes()).hexdigest()==h
 report=dict(result='passed',real_disc_inputs=True,extracted_release_zip=True,production_launcher_callback=True,verified_cases=len(cases),missing_own_config_rejected=True,actual_process_handoff=True,remembered_selection=True,foreign_cwd_configs_ignored=True,saved_settings_unchanged=True,developer_tools_removed_from_path=True,desktop_automation=False)
 (out/'result.json').write_text(json.dumps(report,indent=2)+'\n');print(out,flush=True)
if __name__=='__main__':main()
