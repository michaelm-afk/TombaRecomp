"""Noninteractive relocated player checks. Never opens a desktop window."""
import argparse,hashlib,json,os,shutil,subprocess,time
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'eu/tests'))
from audit_release_imports import imports

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--package',type=Path,required=True)
    p.add_argument('--name',required=True)
    a=p.parse_args()
    if Path(a.name).name!=a.name:p.error('Name must be one folder component')
    out=ROOT.parent/'release-qa'/a.name
    out.mkdir(parents=True,exist_ok=False)
    build=out/'relocated player';shutil.copytree(a.package.resolve(),build)
    assert not (build/'settings.toml').exists() and not list(build.rglob('*.mcd'))
    env=dict(os.environ)
    for k in list(env):
        if k in ('PYTHONHOME','PYTHONPATH') or k.startswith(('PSX_','TOMBA_','TOMBI_','RECOMP_','LNG_')):env.pop(k,None)
    system=Path(os.environ['SystemRoot'])/'System32'
    env.update(PATH=str(system),SDL_AUDIO_DRIVER='dummy',SDL_AUDIODRIVER='dummy')
    files=[f for f in build.rglob('*') if f.suffix.lower() in ('.exe','.dll','.pyd')]
    names={f.name.lower() for f in files};missing={}
    for f in files:
        for name in imports(f):
            if name.lower() not in names and not (system/name).exists() and not name.lower().startswith(('api-ms-win-','ext-ms-win-')):missing.setdefault(f.relative_to(build).as_posix(),[]).append(name)
    assert not missing,missing
    with (out/'runtime.log').open('w') as log:
        child=subprocess.Popen([str(build/'TombiRecompEU2.exe'),'--headless','--no-launcher','--game',str(build/'game.toml'),'--disc',str(ROOT/'disc/eu2/disc.cue')],cwd=out,env=env,stdout=log,stderr=subprocess.STDOUT)
        try:
            deadline=time.monotonic()+30
            while time.monotonic()<deadline:
                assert child.poll() is None,'Player exited unexpectedly'
                text=(out/'runtime.log').read_text(errors='replace')
                if 'executing from PC=' in text and 'guest video standard PAL' in text:break
                time.sleep(.2)
            else:raise TimeoutError('Portable boot')
            time.sleep(2)
        finally:
            child.terminate();child.wait(timeout=10)
    r=subprocess.run([str(build/'overlay_toolchain/python/python.exe'),'-I','-c','print("portable-python-ok")'],cwd=out,env=env,capture_output=True,text=True,check=True)
    assert 'portable-python-ok' in r.stdout
    config=(build/'game.toml').read_text()
    assert 'memcard_dir = "saves/SCES-01331"' in config
    result=dict(result='passed',relocated_outside_checkout=True,no_host_developer_tools_on_path=True,headless_boot=True,original_pal=True,imports_unresolved=missing,bundled_python=True,no_personal_cards_or_settings_copied=True,portable_default_cards='saves/SCES-01331',manual_pending=['GUI dialog selection and settings persistence','ordinary save and restart/load on test card'])
    (out/'result.json').write_text(json.dumps(result,indent=2)+'\n')
    print(out,flush=True)
if __name__=='__main__':main()
