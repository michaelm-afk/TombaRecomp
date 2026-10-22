"""Export only committed public-base source deltas for the common EU package."""
import argparse,json,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
BASES={'TombaRecomp':('ec11a7e8afa1a15d4599483f0c80f0a3b1389bff',ROOT,'https://github.com/mstan/TombaRecomp.git'),'psxrecomp':('847762995c0fa1af65f0e43604bb2a3e23d92bff',ROOT/'psxrecomp','https://github.com/mstan/psxrecomp.git'),'recomp_ui':('e08082d10c38d0c4293455c3d15b3ab35ef1afe3',ROOT/'recomp-ui','https://github.com/mstan/recomp-ui.git')}
def main():
 p=argparse.ArgumentParser();p.add_argument('--output',default='dist/TombiRecomp-Europe-Developer');a=p.parse_args();out=(ROOT/a.output).resolve()
 if not out.is_relative_to(ROOT):p.error('Output must stay in checkout')
 out.mkdir(parents=True,exist_ok=False);metadata={}
 for name,(base,repo,url) in BASES.items():
  head=subprocess.check_output(['git','-C',str(repo),'rev-parse','HEAD']).decode().strip();patch=name+'-Europe.patch'
  cmd=['git','-C',str(repo),'diff','--binary','--no-ext-diff',base,head]
  if name=='TombaRecomp':cmd+=['--','.',':(exclude)psxrecomp',':(exclude)recomp-ui']
  (out/patch).write_bytes(subprocess.check_output(cmd));metadata[name]=dict(url=url,base=base,revision=head,patch=patch,apply_in='.' if name=='TombaRecomp' else repo.name)
 (out/'SOURCE_BASES.json').write_text(json.dumps(metadata,indent=2)+'\n')
 for source,target in [('europe/DEVELOPER.md','README.md'),('europe/README_EN.md','DISC_SELECTION_EN.md'),('europe/FEATURES.md','FEATURES.md'),('europe/MANUAL_TESTS_DE.md','MANUAL_TESTS_DE.md'),('europe/FINAL_REPORT.json','TEST_REPORT.json'),('eu2/handoff/DEFAULTS_COMPARISON_DE.md','DEFAULTS_COMPARISON_DE.md'),('eu2/handoff/WIDESCREEN.md','EU2_WIDESCREEN.md'),('docs/regional/FMV_SKIP_EU2_REVIEW.json','EU2_FMV_REVIEW.json'),('LICENSE','LICENSE'),('psxrecomp/LICENSE','LICENSE.psxrecomp'),('recomp-ui/LICENSE','LICENSE.recomp-ui')]:
  (out/target).write_bytes((ROOT/source).read_bytes())
 (out/'RC2_DISC_VERIFICATION.md').write_bytes((ROOT/'europe/RC2_DISC_VERIFICATION.md').read_bytes())
 print(out,flush=True)
if __name__=='__main__':main()
