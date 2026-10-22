"""Export committed EU2 changes against exact public source bases, never game data."""
import argparse,json,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
BASE='ec11a7e8afa1a15d4599483f0c80f0a3b1389bff'
UI='e08082d10c38d0c4293455c3d15b3ab35ef1afe3'
FRAMEWORK='847762995c0fa1af65f0e43604bb2a3e23d92bff'

def git(repo,*args):return subprocess.check_output(['git','-C',str(repo),*args])
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',default='dist/SCES01331-developer');a=p.parse_args()
    out=(ROOT/a.output).resolve()
    if not out.is_relative_to(ROOT):p.error('Output must stay inside project')
    out.mkdir(parents=True,exist_ok=False)
    head=git(ROOT,'rev-parse','HEAD').decode().strip();uihead=git(ROOT/'recomp-ui','rev-parse','HEAD').decode().strip()
    patch=git(ROOT,'diff','--binary','--no-ext-diff',BASE,head,'--','.',':(exclude)psxrecomp',':(exclude)recomp-ui')
    (out/'TombaRecomp-EU2.patch').write_bytes(patch)
    (out/'recomp-ui-memory-card-safety.patch').write_bytes(git(ROOT/'recomp-ui','diff','--binary','--no-ext-diff',UI,uihead))
    metadata=dict(TombaRecomp=dict(url='https://github.com/mstan/TombaRecomp.git',base=BASE,revision=head),
        psxrecomp=dict(url='https://github.com/mstan/psxrecomp.git',base=FRAMEWORK,revision=FRAMEWORK,changes=False),
        recomp_ui=dict(url='https://github.com/mstan/recomp-ui.git',base=UI,revision=uihead,apply_in='recomp-ui'))
    (out/'SOURCE_BASES.json').write_text(json.dumps(metadata,indent=2)+'\n')
    for src,name in [('eu2/handoff/README.md','README.md'),('eu2/handoff/TEST_REPORT.md','TEST_REPORT.md'),
                     ('eu2/handoff/WIDESCREEN.md','WIDESCREEN.md'),
                     ('eu2/handoff/PC_MODS.md','PC_MODS.md'),
                     ('eu2/handoff/MANUAL_TESTS_DE.md','MANUAL_TESTS_DE.md'),
                     ('eu2/handoff/CLOSEOUT_RESULTS.json','CLOSEOUT_RESULTS.json'),('LICENSE','LICENSE'),
                     ('recomp-ui/LICENSE','LICENSE.recomp-ui'),('psxrecomp/LICENSE','LICENSE.psxrecomp')]:
        (out/name).write_bytes((ROOT/src).read_bytes())
    print(out,flush=True)

if __name__=='__main__':main()
