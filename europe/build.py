"""Reproducible common European build; original discs are read-only inputs."""
import argparse,json,os,re,shutil,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'eu'),str(ROOT/'psxrecomp/tools')]
from toolchain import executable
import aot_overlay_pipeline as pipeline

def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('--eu1-disc',type=Path,required=True);p.add_argument('--eu2-disc',type=Path,required=True)
 p.add_argument('--runtime-toolchain',type=Path,required=True);p.add_argument('--webp-source',type=Path)
 p.add_argument('--reuse-native-from',type=Path,help='Re-audit already proved original-disc native pairs, do not trust old receipts')
 p.add_argument('--output',default='dist/TombiRecomp-Europe-Windows-x64');a=p.parse_args()
 work=ROOT/'build-europe';logs=work/'build-steps';logs.mkdir(parents=True,exist_ok=True)
 env=dict(os.environ)
 for key in ['TEMP','TMP','CCACHE_DIR','SCCACHE_DIR']:
  folder=work/key;folder.mkdir(exist_ok=True);env[key]=str(folder)
 def run(command):
  n=len(list(logs.glob('step-*.log')))+1;print('European build step',n,flush=True)
  with (logs/f'step-{n}.log').open('w') as log:subprocess.run(list(map(str,command)),cwd=ROOT,env=env,stdout=log,stderr=subprocess.STDOUT,check=True)
 py=[sys.executable,'-I','-B']
 run([*py,'eu/prepare.py','--disc',a.eu1_disc.resolve()])
 cue=ROOT/'disc/Tombi! (Europe) (En,Fr,De,It,Nl) (Rev 1).cue'
 if not cue.exists():
  source=a.eu1_disc.resolve()
  if source.suffix.lower()=='.cue':
   files=re.findall(r'FILE\s+"([^"]+)"\s+BINARY',source.read_text(encoding='utf-8-sig'),re.I)
   if len(files)!=1:raise ValueError('A single original EU1 data track is required')
   source=source.parent/files[0]
  shutil.copyfile(source,ROOT/'disc/eu1.bin')
  cue.write_text('FILE "eu1.bin" BINARY\n  TRACK 01 MODE2/2352\n    INDEX 01 00:00:00\n')
 run([*py,'eu2/prepare.py','--disc',a.eu2_disc.resolve()])
 cmake=executable('cmake.exe');mapping='-ffile-prefix-map='+ROOT.as_posix()+'=. -fmacro-prefix-map='+ROOT.as_posix()+'=.'
 run([cmake,'-S','psxrecomp/recompiler','-B','build-eu-tools','-G','Ninja','-DCMAKE_BUILD_TYPE=Release','-DCMAKE_C_COMPILER='+executable('clang.exe'),'-DCMAKE_CXX_COMPILER='+executable('clang++.exe'),'-DCMAKE_MAKE_PROGRAM='+executable('ninja.exe'),'-DCMAKE_C_FLAGS='+mapping,'-DCMAKE_CXX_FLAGS='+mapping])
 run([cmake,'--build','build-eu-tools','--target','psxrecomp-game','psxrecomp-bios','-j','3'])
 # Native preparation precedes runtime configuration on a clean checkout.
 # Use the framework's canonical hash generator before auditing any cache.
 run([cmake,'-DOUT='+str(ROOT/'psxrecomp/runtime/include/overlay_codegen_hash.h'),'-DPSXRECOMP_CODEGEN_HASH_ROOT='+str(ROOT/'psxrecomp'),'-P',ROOT/'psxrecomp/runtime/hash_codegen.cmake'])
 for config in ['eu/game.toml','eu2/game.toml']:run([ROOT/'build-eu-tools/psxrecomp-game.exe','--config',config])
 run([*py,'eu/seamless_catalog.py']);run([*py,'eu/seamless_catalog.py','--variant','eu2'])
 run([*py,'eu/build_aot.py','--scope','opening','--prepare-only'])
 run([*py,'eu2/build_aot.py','--seamless','--prepare-only','--work-dir','build-eu2-parity/aot'])
 if a.reuse_native_from:
  source=a.reuse_native_from.resolve()
  for config,cache,inventory,receipt in [('eu/seamless/game.toml','build-eu-seamless/hook-aot/cache','build-eu-prototype/aot-opening/runtime-input-inventory.json','build-eu-seamless/hook-aot/audit.json'),('eu2/pc.toml','build-eu2-parity/qa/native/cache','build-eu2-parity/aot/runtime-input-inventory.json','build-eu2-parity/aot/audit.json')]:
   target=ROOT/cache;shutil.copytree(source/cache,target,dirs_exist_ok=True)
   pipeline.audit(ROOT/config,ROOT/'build-eu-tools/psxrecomp-game.exe',target,ROOT/inventory,ROOT/receipt)
  eu2=json.loads((ROOT/'build-eu2-parity/aot/audit.json').read_text())
  pipeline.stage(ROOT/'build-eu2-parity/qa/native/cache',ROOT/'build-europe/eu2/native',eu2)
 else:
  run([*py,'eu/build_seamless_hooks.py','--scope','opening','--workers','3'])
  run([*py,'eu2/build_aot.py','--seamless','--work-dir','build-eu2-parity/aot','--destination','build-europe/eu2/native','--workers','3'])
 webp=['--webp-source',a.webp_source.resolve()] if a.webp_source else []
 run([*py,'eu/build_release.py','--build-dir','build-europe/eu1/native',*webp])
 run([*py,'eu2/build_release.py','--build-dir','build-europe/eu2/native',*webp])
 run([*py,'europe/stage.py','--output',a.output,'--eu2-build','build-europe/eu2/native','--eu2-cache','build-europe/eu2/native','--runtime-toolchain',a.runtime_toolchain.resolve()])
 report=dict(result='passed',source_build=True,both_backends_rebuilt=True,native_reuse_reaudited=bool(a.reuse_native_from),private_cards_used=False)
 (work/'build-result.json').write_text(json.dumps(report,indent=2)+'\n');print('PASS: common European build and staging',flush=True)
if __name__=='__main__':main()
