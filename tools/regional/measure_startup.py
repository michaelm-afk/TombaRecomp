"""Bounded release startup probes on private copies, same GL/native conditions."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import time

ROOT=Path(__file__).resolve().parents[2]


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--mode',choices=['direct','launcher'],required=True)
    parser.add_argument('--repeat',type=int,default=2)
    parser.add_argument('--regions',nargs='+',choices=['us','eu1','eu2'],default=['us','eu1','eu2'])
    parser.add_argument('--timeout',type=int,default=60)
    parser.add_argument('--without-cache',action='store_true',help='Diagnostic only; retain all disc/ABI checks')
    parser.add_argument('--eu2-launcher',action='store_true',help='Use separate EU2 launcher candidate')
    args=parser.parse_args()
    cases=[('us',ROOT/'build-startup/comparison/us','TombaRecomp.exe',
        ROOT/'disc/Tomba! (USA).cue'),
        ('eu1',ROOT/'build-startup/comparison/eu1','TombiRecompEU.exe',
        ROOT/'disc/Tombi! (Europe) (En,Fr,De,It,Nl) (Rev 1).cue'),
        ('eu2',ROOT/'build-eu2/native','TombiRecompEU2.exe',ROOT/'disc/eu2/disc.cue')]
    output=ROOT/'build-startup'/('measure-'+args.mode+'-'+time.strftime('%Y%m%dT%H%M%S'))
    output.mkdir(parents=True)
    reports=[]
    for name,build,exe,disc in cases:
        if name not in args.regions:continue
        if name=='eu2' and args.eu2_launcher:
            build=ROOT/'build-eu2-launcher/native'
        if args.without_cache:
            import shutil
            isolated=ROOT/'build-startup'/('no-native-cache-'+name)
            if not isolated.exists():
                shutil.copytree(build,isolated,ignore=shutil.ignore_patterns('cache','diagnostics'))
            build=isolated
        for n in range(args.repeat):
            out=output/f'{name}-{n}'
            out.mkdir()
            env=dict(os.environ,PSX_LAUNCHER_BOOT_TIMING='1',PSX_FRAME_REPORT_MS='100',
                SDL_AUDIO_DRIVER='dummy',SDL_AUDIODRIVER='dummy',PSX_INTERNAL_RESOLUTION='native',
                PSX_OVERLAY_AUTOCOMPILE_OFF='1',PSX_RESIDENT_CACHE=str(output/name/'resident-cache'))
            for key in ('TEMP','TMP','LOCALAPPDATA','APPDATA','XDG_CACHE_HOME'):
                folder=output/name/key
                folder.mkdir(parents=True,exist_ok=True)
                env[key]=str(folder)
            config=build/'game.toml' if name!='eu2' or args.eu2_launcher else ROOT/'eu2/game.toml'
            command=[str(build/exe),'--game',str(config),'--disc',str(disc),
                '--memcard-dir',str(out/'fresh-cards'),'--renderer','opengl']
            if args.mode=='launcher':
                command+=['--launcher']
                env['LNG_TEST_HIDDEN']='1'
                env['LNG_SCRIPT']='wait:20;shot:'+str(out/'launcher.png')+';quit'
            else:
                command+=['--no-launcher','--hidden-window']
            lines=[]
            started=time.monotonic()
            # Native Windows CRT output is observed through a regular file,
            # never a redirected pipe shared by concurrent startup workers.
            log=(out/'runtime.log').open('w')
            proc=subprocess.Popen(command,cwd=build,env=env,stdout=log,stderr=subprocess.STDOUT)
            observed=0
            def poll_log():
                nonlocal observed
                current=(out/'runtime.log').read_text(errors='replace').splitlines()
                for line in current[observed:]:
                    lines.append(dict(seconds=round(time.monotonic()-started,5),text=line))
                observed=len(current)
            reason='deadline'
            try:
                until=started+args.timeout
                while time.monotonic()<until:
                    poll_log()
                    if proc.poll() is not None:
                        reason='process-exit'
                        break
                    if args.mode=='direct' and any('frame report every' in r['text'] for r in lines):
                        reason='first-vblank-observed'
                        break
                    time.sleep(.03)
            finally:
                if proc.poll() is None:
                    proc.terminate()
                proc.wait(timeout=10)
                log.close()
                poll_log()
            def marker(text):
                return next((r['seconds'] for r in lines if text in r['text']),None)
            report=dict(region=name,run=n,mode=args.mode,application_warm=n>0,
                main_enter_s=marker('host:main_enter'),launcher_ready_s=marker('rui:model+binds_ready'),
                gl_ready_s=marker('GL GPU pipeline ready'),guest_start_s=marker('executing from PC='),
                first_vblank_s=marker('frame report every'),stop_reason=reason,
                limitation='First vblank is not first playable gameplay; launcher wait/input excluded from direct cases.',
                codegen_lines=[r for r in lines if 'compiling' in r['text'].lower()],
                log=(out/'runtime.json').relative_to(ROOT).as_posix())
            (out/'runtime.json').write_text(json.dumps(lines,indent=2))
            reports.append(report)
            (output/'report.json').write_text(json.dumps(reports,indent=2))
            print(json.dumps(report),flush=True)


if __name__=='__main__':main()
