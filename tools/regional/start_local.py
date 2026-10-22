"""Verify and start a private regional test copy, preserving player originals."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'tools'),str(ROOT/'psxrecomp/tools')]
from build_regions import data_track
from extract_overlays import DiscReader,enumerate_files


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--region',choices=['eu1','eu2'],required=True)
    parser.add_argument('--launcher',action='store_true')
    args=parser.parse_args()
    if args.region=='eu1':
        build=ROOT/'build-startup/comparison/eu1'
        executable=build/'TombiRecompEU.exe'
        disc=ROOT/'disc/Tombi! (Europe) (En,Fr,De,It,Nl) (Rev 1).cue'
        config=build/'game.toml'
        sha='2505d958b4439d04844cadd3f968fc7432a48e00'
        size=492370032
        boot='SCES_013.30'
        destination=build/'user-data'/boot
        cards=ROOT/'build-startup/eu1-manual-cards'
    else:
        build=ROOT/'build-eu2-launcher/native'
        executable=build/'TombiRecompEU2.exe'
        disc=ROOT/'disc/eu2/disc.cue'
        config=build/'game.toml'
        sys.path.insert(0,str(ROOT/'eu2'))
        from revisions import active, PROFILES
        profile=PROFILES[active()]
        sha=profile['sha1']
        size=profile['size']
        boot='SCES_013.31'
        destination=ROOT/'disc/eu2'/boot
        cards=ROOT/'build-eu2-launcher/manual-cards'
    if not executable.is_file():
        raise FileNotFoundError('Separate test build has not been prepared: '+str(executable))
    track=data_track(disc)
    started=time.monotonic()
    with track.open('rb') as stream:
        actual=hashlib.file_digest(stream,'sha1').hexdigest()
    if actual!=sha or track.stat().st_size!=size:
        raise ValueError('Wrong disc or modified track; launch refused')
    reader=DiscReader(str(track),raw=True)
    try:
        catalog={name:(lba,n) for name,lba,n in enumerate_files(reader)}
        raw=reader.read_file_bytes(*catalog[boot])
    finally:
        reader.close()
    if not raw.startswith(b'PS-X EXE'):
        raise ValueError('Invalid original boot executable')
    if destination.exists() and destination.read_bytes()!=raw:
        raise ValueError('Conflicting local boot program; refusing overwrite')
    destination.parent.mkdir(parents=True,exist_ok=True)
    if not destination.exists():
        destination.write_bytes(raw)
    diagnostics=build/'diagnostics'
    diagnostics.mkdir(exist_ok=True)
    timestamp=time.strftime('%Y%m%dT%H%M%S')
    result=dict(region=args.region,launcher=args.launcher,verified_sha1=actual,
                disc_verification_seconds=time.monotonic()-started)
    env=dict(os.environ,PSX_LAUNCHER_BOOT_TIMING='1',PSX_FRAME_REPORT_MS='1000')
    env['PSX_RESIDENT_CACHE']=str(build.parent/(args.region+'-resident-cache') if args.region=='eu1' else build.parent/'resident-cache')
    command=[str(executable),'--game',str(config),'--disc',str(disc),'--memcard-dir',str(cards),
             '--launcher' if args.launcher else '--no-launcher']
    print('Disc verified. Test cards:',cards,flush=True)
    print('Runtime log:',diagnostics/(timestamp+'.log'),flush=True)
    with (diagnostics/(timestamp+'.log')).open('w') as log:
        result['exit_code']=subprocess.call(command,cwd=build,env=env,stdout=log,stderr=subprocess.STDOUT)
    (diagnostics/(timestamp+'.json')).write_text(json.dumps(result,indent=2))
    raise SystemExit(result['exit_code'])


if __name__=='__main__':main()
