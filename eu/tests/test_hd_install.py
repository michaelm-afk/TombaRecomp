"""Synthetic installer fixtures only: no game textures or game state."""
from pathlib import Path
import subprocess,struct,zlib,json,argparse,time
ROOT=Path(__file__).resolve().parents[2]
def main():
 parser=argparse.ArgumentParser();parser.add_argument('--game-id',default='SCES-01330');parser.add_argument('--binary',type=Path);parser.add_argument('--output-root',type=Path);parser.add_argument('--name',default='hd-install-fixtures-'+str(time.time_ns()));args=parser.parse_args()
 if Path(args.name).name!=args.name:parser.error('name must be a directory component')
 out=(args.output_root or ROOT/'build-eu-release-rc3')/args.name;out.mkdir(parents=True,exist_ok=False)
 binary=args.binary or ROOT/'build-eu-release-rc3/qa/tombi-hd-install-tests.exe';results=[]
 def check(label,path,ok,contains):
  run=subprocess.run([str(binary),str(path),args.game_id],capture_output=True,text=True,errors='replace')
  assert (run.returncode==0)==ok,(label,run.stdout,run.stderr)
  assert contains in run.stdout,(label,run.stdout)
  results.append(dict(case=label,accepted=ok,status=run.stdout.splitlines()[0]));print(label,run.stdout.splitlines()[0],flush=True)
 check('missing',out/'missing',False,'No texture pack installed')
 pack=out/'download/mods/texture-packs'/args.game_id;images=pack/'replacements';images.mkdir(parents=True)
 check('empty',pack,False,'No texture pack installed')
 def chunk(kind,data):return struct.pack('>I',len(data))+kind+data+struct.pack('>I',zlib.crc32(kind+data)&0xffffffff)
 png=b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',64,64,8,6,0,0,0))+chunk(b'IDAT',zlib.compress((b'\0'+b'\x00\xff\xff\xff'*64)*64))+chunk(b'IEND',b'')
 image=images/'texpage-P4-1111111111111111-2222222222222222-64x256-0-0-64x64-P0-15.png';image.write_bytes(png)
 check('game-id-target',pack,True,'Installed')
 check('outer-download-folder',out/'download',True,'Installed')
 check('replacement-directory',images,True,'Installed')
 (pack/'texture-pack.toml').write_text('game_ids = ["SCUS-94236"]\n')
 check('conflicting-metadata',pack,False,'Incompatible')
 (pack/'texture-pack.toml').write_text('game_ids = ["'+args.game_id+'"]\n')
 check('explicit-EU-metadata',pack,True,'Installed')
 image.write_bytes(b'not an image');check('corrupt-image',pack,False,'Invalid image')
 image.write_bytes(png);image.rename(images/'invalid.png');check('invalid-name',pack,False,'Invalid replacement filename')
 other=out/'other-region';(other/'replacements').mkdir(parents=True)
 (other/'texture-pack.toml').write_text('game_ids = ["SCUS-94236"]\n')
 (other/'replacements'/image.name.replace('invalid.png','texpage-P4-1111111111111111-2222222222222222-64x256-0-0-64x64-P0-15.png')).write_bytes(png)
 check('synthetic-US-only-pack',other,False,'Incompatible')
 (out/'report.json').write_text(json.dumps(results,indent=2));print('PASS:',len(results),'installer cases')
if __name__=='__main__':main()
