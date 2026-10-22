"""Real backend routing/persistence probes; no SDL window or input simulation."""
import argparse,hashlib,json,os,shutil,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--package',type=Path,required=True);p.add_argument('--name',default='European portable with spaces');p.add_argument('--blank-card',type=Path,default=ROOT/'build-eu2-parity/format-new.mcd');p.add_argument('--check-play-gate',action='store_true');a=p.parse_args()
 if Path(a.name).name!=a.name:p.error('One output folder component required')
 out=ROOT.parent/'release-qa'/a.name;out.mkdir(parents=True,exist_ok=False);app=out/'Windows x64';shutil.copytree(a.package.resolve(),app)
 entry=app/'TombiRecompEU.exe';eu2=app/'backends/SCES-01331/TombiRecompEU2.exe'
 discs={'SCES-01330':ROOT/'disc/Tombi! (Europe) (En,Fr,De,It,Nl) (Rev 1).cue','SCES-01331':ROOT/'disc/eu2/disc.cue'}
 protected=[]
 blank=a.blank_card.read_bytes()
 assert len(blank)==128*1024 and blank[:2]==b'MC'
 for region,folder in [('SCES-01330',app),('SCES-01331',eu2.parent)]:
  s=folder/'settings.toml';s.write_text('# synthetic QA settings '+region+'\n[video]\nvsync = "adaptive"\n')
  card=folder/'saves'/region/'card1.mcd';card.parent.mkdir(parents=True,exist_ok=True);card.write_bytes(blank)
  mods=folder/'mods/state.toml';mods.write_text('format_version = 2\n')
  protected.extend((q,hashlib.sha256(q.read_bytes()).hexdigest()) for q in (s,card,mods))
 cases=[]
 def check(exe,flags,ok,text='',cwd=None):
  result=subprocess.run([str(exe),*map(str,flags)],cwd=cwd or out,capture_output=True,text=True,errors='replace',timeout=60,creationflags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0)
  assert (result.returncode==0)==ok,(flags,result.returncode,result.stdout,result.stderr)
  assert text in result.stdout,(flags,result.stdout,result.stderr)
  (out/f'case-{len(cases)+1}.txt').write_text(result.stdout+result.stderr)
  cases.append(dict(case=len(cases)+1,passed=True))
 check(entry.with_name(entry.name.lower()),['--regional-probe','--disc',discs['SCES-01330']],True,'profile=SCES-01330')
 for region,disc in discs.items():check(entry,['--regional-probe','--disc',disc],True,'profile='+region)
 for region,disc in discs.items():
  check(entry,['--regional-select-only','--disc',disc],True,'profile='+region)
  check(entry,['--regional-probe'],True,'profile='+region)
 check(entry,['--regional-exec-probe'],True,'entered=SCES-01331')
 check(eu2,['--regional-exec-probe','--disc',discs['SCES-01330']],True,'entered=SCES-01330')
 check(entry,['--regional-ui-route-probe','--disc',discs['SCES-01331']],True,'entered=SCES-01331')
 check(eu2,['--regional-ui-route-probe','--disc',discs['SCES-01330']],True,'entered=SCES-01330')
 if a.check_play_gate:
  for exe,region,cwd in [(entry,'SCES-01331',app),(eu2,'SCES-01330',eu2.parent),(entry,'SCES-01331',eu2.parent),(eu2,'SCES-01330',app)]:
   expected=f'launcher-disc-check expected={region} serial={region} verdict=1 iso=1 handoff=0'
   check(exe,['--launcher-disc-check','--disc',discs[region],'--game','game.toml'],True,expected,cwd)
  own=eu2.parent/'game.toml';temp=own.with_suffix('.test-backup');own.rename(temp)
  try:check(eu2,['--launcher-disc-check','--disc',discs['SCES-01331']],False)
  finally:temp.rename(own)
 bad=out/'unknown.bin';bad.write_bytes(b'not a PlayStation disc')
 check(entry,['--regional-probe','--disc',bad],False)
 altered=out/'wrong-hash.bin';shutil.copyfile(ROOT/'disc/eu2/disc.bin',altered)
 with altered.open('r+b') as f:f.seek(-1,2);value=f.read(1);f.seek(-1,2);f.write(bytes([value[0]^1]))
 check(entry,['--regional-probe','--disc',altered],False)
 absent=eu2.with_suffix('.unavailable');eu2.rename(absent)
 try:check(entry,['--regional-probe','--disc',discs['SCES-01331']],False)
 finally:absent.rename(eu2)
 for path,digest in protected:assert hashlib.sha256(path.read_bytes()).hexdigest()==digest,path
 (app/'europe-selection.toml').write_text('disc = "missing-disc.cue"\n')
 check(entry,['--regional-probe'],False)
 report=dict(result='passed',production_play_gate=a.check_play_gate,cases=len(cases),serial_and_full_sha256=True,both_regions=True,cold_restart_selection=True,cold_restart_both_regions=True,actual_process_handoff_both_directions=True,production_ui_handoff_path=True,spaces_in_package_path=True,corrupted_same_size_disc_rejected=True,missing_backend_rejected=True,settings_mod_state_cards_preserved=True,desktop_automation=False)
 (out/'result.json').write_text(json.dumps(report,indent=2)+'\n');print(out,flush=True)
if __name__=='__main__':main()
