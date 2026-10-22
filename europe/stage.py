"""One European distribution; reuse the same audited backend packaging path."""
import argparse,json,shutil,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--runtime-toolchain',type=Path);p.add_argument('--output',default='dist/TombiRecomp-Europe-Windows-x64');p.add_argument('--eu1-build',type=Path,default=ROOT/'build-europe/eu1/native');p.add_argument('--eu2-build',type=Path,default=ROOT/'build-eu2-parity/player/native');p.add_argument('--eu1-audit',type=Path,default=ROOT/'build-eu-seamless/hook-aot/audit.json');p.add_argument('--eu2-audit',type=Path,default=ROOT/'build-eu2-parity/aot/audit.json');p.add_argument('--eu2-cache',type=Path,default=ROOT/'build-eu2-parity/qa/native');a=p.parse_args()
 out=(ROOT/a.output).resolve()
 if not out.is_relative_to(ROOT):p.error('Stage output must stay in checkout')
 for region,build,audit,cache,target in [('eu1',a.eu1_build,a.eu1_audit,a.eu1_build,out),('eu2',a.eu2_build,a.eu2_audit,a.eu2_cache,out/'backends/SCES-01331')]:
  extra=['--runtime-toolchain',str(a.runtime_toolchain.resolve())] if a.runtime_toolchain else []
  subprocess.run([sys.executable,'-I','-B',str(ROOT/'eu2/stage_release.py'),'--region',region,'--output',str(target),'--build-dir',str(build),'--audit',str(audit),'--cache-root',str(cache),*extra],cwd=ROOT,check=True)
 shutil.copy2(ROOT/'europe/regional-launch.toml',out/'regional-launch.toml')
 config=out/'game.toml';config.write_text(config.read_text().replace('memcard_dir = "saves"','memcard_dir = "saves/SCES-01330"'))
 for source,target in [('README_EN.md','README_EN.md'),('FEATURES.md','FEATURES.md'),('MANUAL_TESTS_DE.md','MANUAL_TESTS_DE.md')]:shutil.copy2(ROOT/'europe'/source,out/target)
 subprocess.run([sys.executable,'-I','-B',str(ROOT/'europe/audit.py'),'--path',str(out),'--kind','player','--output',str(out/'PACKAGE_AUDIT.json')],cwd=ROOT,check=True)
 # Per-backend audit hashes precede the final catalog/docs additions; the
 # independent combined archive audit is authoritative for the final package.
 print(out,flush=True)
if __name__=='__main__':main()
