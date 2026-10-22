"""Fresh relocated exact-player UI/import tests, no system development tools."""
import argparse,json,os,shutil,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'eu/tests'))
from audit_release_imports import imports

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--package',type=Path,required=True);p.add_argument('--name',default='portable-fresh');a=p.parse_args()
    if Path(a.name).name!=a.name:p.error('Invalid output name')
    # Outside the source checkout: repo-root discovery must not influence the
    # portable card/config paths in this acceptance test.
    out=ROOT.parent/'release-qa'/a.name;out.mkdir(parents=True,exist_ok=False)
    original=a.package.resolve();build=out/'relocated player';shutil.copytree(original,build)
    assert not (build/'settings.toml').exists() and not list(build.rglob('*.mcd'))
    env=dict(os.environ)
    for k in list(env):
        if k in ('PYTHONHOME','PYTHONPATH') or k.startswith(('PSX_','TOMBA_','TOMBI_','RECOMP_','LNG_')):env.pop(k,None)
    env.update(PATH=str(Path(os.environ['SystemRoot'])/'System32'),LNG_TEST_HIDDEN='1',SDL_AUDIO_DRIVER='dummy',SDL_AUDIODRIVER='dummy')
    system=Path(os.environ['SystemRoot'])/'System32';files=[f for f in build.rglob('*') if f.suffix.lower() in ('.exe','.dll','.pyd')];names={f.name.lower() for f in files}
    missing={}
    for f in files:
        for name in imports(f):
            if name.lower() not in names and not (system/name).exists() and not name.lower().startswith(('api-ms-win-','ext-ms-win-')):missing.setdefault(f.relative_to(build).as_posix(),[]).append(name)
    assert not missing,missing
    results=[]
    for label,argv,script in [
        ('first-no-disc',[],'wait:30;shot:'+str(out/'first-no-disc.png')+';quit'),
        ('owned-disc',['--disc',str(ROOT/'disc/eu2/disc.cue')],'wait:40;shot:'+str(out/'owned-disc.png')+';quit'),
        ('card-browser',['--disc',str(ROOT/'disc/eu2/disc.cue')],'wait:40;click:1180,1500;wait:5;shot:'+str(out/'card-browser.png')+';quit')]:
        env['LNG_SCRIPT']=script
        with (out/(label+'.log')).open('w') as log:
            r=subprocess.run([str(build/'TombiRecompEU2.exe'),'--launcher','--hidden-window',*argv],cwd=out,env=env,stdout=log,stderr=subprocess.STDOUT,timeout=180)
        assert r.returncode==0,(label,r.returncode)
        text=(out/(label+'.log')).read_text(errors='replace');assert 'loaded game config '+str(build/'game.toml') in text
        assert (out/(label+'.png')).exists(),label
        results.append(dict(case=label,exit_code=r.returncode))
    r=subprocess.run([str(build/'overlay_toolchain/python/python.exe'),'-I','-c','import json;print(json.dumps({"portable":True}))'],cwd=out,env=env,capture_output=True,text=True,check=True)
    assert '"portable": true' in r.stdout
    report=dict(result='passed',cases=results,unresolved_imports=missing,system_developer_tools_removed_from_path=True,fresh_configuration=True,private_cards_or_settings_copied=False,bundled_python=True,limitations=['Screenshots require visual review','No physical OS native file-dialog automation'])
    (out/'result.json').write_text(json.dumps(report,indent=2));print(out,flush=True)

if __name__=='__main__':main()
