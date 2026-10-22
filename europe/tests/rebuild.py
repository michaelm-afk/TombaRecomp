"""Reconstruct three exact upstream bases, apply all patches, build both backends."""
import argparse,json,subprocess,sys,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
def main():
 p=argparse.ArgumentParser();p.add_argument('--handoff',type=Path,required=True);p.add_argument('--name',required=True);p.add_argument('--check-only',action='store_true');p.add_argument('--reuse-native',action='store_true');a=p.parse_args()
 if Path(a.name).name!=a.name:p.error('One output folder component')
 out=ROOT/'build-europe'/a.name;out.mkdir(parents=True,exist_ok=False);tree=out/'source';tree.mkdir();metadata=json.loads((a.handoff/'SOURCE_BASES.json').read_text())
 def archive(repo,revision,target):
  target.mkdir(parents=True,exist_ok=True);zpath=out/('archive-'+str(len(list(out.glob('archive-*'))))+'.zip')
  subprocess.run(['git','-C',str(repo),'archive','--format=zip','-o',str(zpath),revision],check=True)
  with zipfile.ZipFile(zpath) as z:
   assert all((target/n).resolve().is_relative_to(target.resolve()) for n in z.namelist());z.extractall(target)
  for line in subprocess.check_output(['git','-C',str(repo),'ls-tree','-r',revision]).decode().splitlines():
   if line.startswith('160000') and repo!=ROOT:
    before,path=line.split('\t',1);archive(repo/path,before.split()[2],target/path)
 for name,repo in [('TombaRecomp',ROOT),('psxrecomp',ROOT/'psxrecomp'),('recomp_ui',ROOT/'recomp-ui')]:
  entry=metadata[name];target=tree/entry['apply_in'];archive(repo,entry['base'],target);subprocess.run(['git','-C',str(target),'init','--quiet'],check=True)
  for flag in ['--check','']:
   subprocess.run(['git','-C',str(target),'apply',*([flag] if flag else []),str((a.handoff/entry['patch']).resolve())],check=True)
 if not a.check_only:
  cmd=[sys.executable,'-I','-B','europe/build.py','--eu1-disc',str(ROOT/'disc/Tombi! (Europe) (En,Fr,De,It,Nl) (Rev 1).cue'),'--eu2-disc',str(ROOT/'disc/eu2/disc.cue'),'--runtime-toolchain',str(ROOT/'build-eu2/native/overlay_toolchain'),'--webp-source',str(ROOT/'build-eu2/native/_deps/psx_libwebp-src')]
  if a.reuse_native:cmd+=['--reuse-native-from',str(ROOT)]
  with (out/'build.log').open('w') as log:subprocess.run(cmd,cwd=tree,stdout=log,stderr=subprocess.STDOUT,check=True)
 report=dict(result='passed',three_exact_base_archives=True,all_three_patches_apply=True,both_backends_rebuilt=not a.check_only,native_reused_only_after_new_audit=a.reuse_native)
 (out/'result.json').write_text(json.dumps(report,indent=2)+'\n');print(out,flush=True)
if __name__=='__main__':main()
