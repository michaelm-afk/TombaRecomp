"""Independent combined-directory/ZIP completeness, privacy and manifest audit."""
import argparse,hashlib,json,re,tomllib,zipfile
from pathlib import Path

EU2_REVISIONS = {
 '2eba3dfdd25f5d270d47f5fe408391971aa25ee09c6aac9874bba4e3bf6f32cc':
  (492306528,65,{'0x8005E618','0x8005E630'}),
 '48a55fabd29e185dfc7d2afa94490d6092694cbed75ec8511f363b19076c5c2e':
  (492370032,66,{'0x8005E61C','0x8005E634'}),
}

def audit(path,kind):
 if path.is_file():
  with zipfile.ZipFile(path) as z:
   names=[n for n in z.namelist() if not n.endswith('/')]
   assert len(names)==len(set(names))
   prefix=names[0].split('/')[0]+'/'
   if not all(n.startswith(prefix) for n in names):prefix=''
   data={n[len(prefix):]:z.read(n) for n in names}
 else:data={p.relative_to(path).as_posix():p.read_bytes() for p in path.rglob('*') if p.is_file()}
 pattern=re.compile(r'[A-Za-z]:[\\/]+(?:Users|Projects|Emulator)[\\/]+|/[U]sers/',re.I)
 for name,value in data.items():
  assert not name.startswith('/') and '..' not in Path(name).parts,name
  assert not pattern.search(value.decode('latin1')) and not pattern.search(value.decode('utf-16le',errors='ignore')),name+': personal path'
  assert Path(name).suffix.lower() not in ['.mcd','.mcr','.cue','.iso','.log','.pdb','.dmp'],name
  if Path(name).suffix.lower()=='.bin':assert name in ['bios/openbios.bin','backends/SCES-01331/bios/openbios.bin'],name
  assert Path(name).name.lower() not in ['settings.toml','state.toml','europe-selection.toml','disc.cfg','bios.cfg','overlay_captures.json'],name
 report=dict(result='passed',kind=kind,files_excluding_self=sum(n!='PACKAGE_AUDIT.json' for n in data),payload_bytes=sum(len(v) for n,v in data.items() if n!='PACKAGE_AUDIT.json'),personal_paths=False,personal_cards=False,original_roms=False)
 if kind=='player':
  required=['TombiRecompEU.exe','game.toml','regional-launch.toml','README_EN.md','FEATURES.md','MANUAL_TESTS_DE.md','bios/openbios.bin','backends/SCES-01331/TombiRecompEU2.exe','backends/SCES-01331/game.toml','backends/SCES-01331/bios/openbios.bin']
  assert all(p in data for p in required)
  catalog=tomllib.loads(data['regional-launch.toml'].decode());assert {p['id'] for p in catalog['profile']}=={'SCES-01330','SCES-01331'}
  counts={}
  for region,prefix,exe in [('SCES-01330','','TombiRecompEU.exe'),('SCES-01331','backends/SCES-01331/','TombiRecompEU2.exe')]:
   config=tomllib.loads(data[prefix+'game.toml'].decode());assert config['game']['id']==region
   assert config['video']['vsync']=='off' and config['audio']['spu_hq']
   assert config['runtime']['memcard_dir']=='saves/'+region
   manifests=[tomllib.loads(value.decode()) for name,value in data.items() if name.startswith(prefix+'mods/bundled/') and name.endswith('/manifest.toml')]
   assert manifests
   for manifest in manifests:
    assert manifest['id'] not in ['psx.enhancement.cd-speed','psx.enhancement.fast-loading','tomba.enhancement.fast-loading','tomba.enhancement.frame-interpolation'],manifest['id']
    assert any(t['game_id'] in [region,'*'] for t in manifest['target']),manifest['id']
    for plugin in manifest.get('plugin',[]):assert plugin['id'].encode() in data[prefix+exe],plugin['id']
   wide=next(m for m in manifests if m['id']=='tomba.enhancement.widescreen')
   assert wide['name']=='Widescreen' and not wide['feature'][0]['default_enabled']
   assert config['widescreen']['adaptive_view'] and config['widescreen']['native_wide']
   if region=='SCES-01331':
    assert not any(m['id']=='tomba.enhancement.skip-fmv' for m in manifests)
    profile=next(p for p in catalog['profile'] if p['id']==region)
    size,expected_pairs,sprite_tags=EU2_REVISIONS[profile['sha256']]
    assert profile['size']==size
    assert set(config['widescreen']['sprite_tag_funcs'])==sprite_tags
    assert profile['size'] in config['prepare_disc']['known_sizes']
    assert all(t.get('disc_sha256',profile['sha256'])==profile['sha256'] for m in manifests for t in m['target'] if t['game_id']==region)
   geometry=next(m for m in manifests if m['id']=='tombi.enhancement.geometry');assert geometry['feature'][0]['default_enabled']
   cache=[n for n in data if n.startswith(prefix+'cache/'+region+'/') and n.endswith('.dll')]
   counts[region]=len(cache);assert len(cache)==(66 if region=='SCES-01330' else expected_pairs)
   assert all(n[:-4]+'.ranges' in data for n in cache)
  report.update(native_pairs=counts,regional_mod_targets=True,declared_plugin_strings_present=True,defaults_match_eu1=True,only_openbios=True)
 else:
  required=['TombaRecomp-Europe.patch','psxrecomp-Europe.patch','recomp_ui-Europe.patch','SOURCE_BASES.json','README.md','TEST_REPORT.json']
  assert all(n in data and data[n] for n in required)
  metadata=json.loads(data['SOURCE_BASES.json']);assert len(metadata)==3
  report['source_patches']=3
 report['files_sha256']={n:hashlib.sha256(v).hexdigest() for n,v in sorted(data.items()) if n!='PACKAGE_AUDIT.json'}
 if path.is_file():
  expected=json.loads(data['PACKAGE_AUDIT.json'])['files_sha256']
  assert report['files_sha256']==expected,'Archive differs from the complete staged manifest'
 return report

def main():
 p=argparse.ArgumentParser();p.add_argument('--path',type=Path,required=True);p.add_argument('--kind',choices=['player','developer'],required=True);p.add_argument('--output',type=Path);a=p.parse_args();report=audit(a.path,a.kind)
 if a.output:a.output.write_text(json.dumps(report,indent=2)+'\n')
 print(json.dumps({k:v for k,v in report.items() if k!='files_sha256'}),flush=True)
if __name__=='__main__':main()
