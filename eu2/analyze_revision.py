"""Reproduce Rev1 loader and complete geometry contracts from original discs."""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT/'eu2'), str(ROOT/'eu'), str(ROOT/'psxrecomp/tools')]
from revisions import active, source
from correspondence import normalize, match_normalized
import importlib.util
spec=importlib.util.spec_from_file_location('eu_geometry',ROOT/'eu/geometry_profile.py')
geometry_module=importlib.util.module_from_spec(spec);spec.loader.exec_module(geometry_module)
ROUTINES=geometry_module.ROUTINES
from session_state import profiles


def sha(raw): return hashlib.sha256(raw).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write-contract', action='store_true')
    args = parser.parse_args()
    if active() != 'rev1': raise ValueError('This correspondence targets the exact Rev1 disc')
    reference = (ROOT/'disc/EXE/MAIN0.EXE').read_bytes()
    from aot_overlay_pipeline import Disc, check_disc
    cue=ROOT/'disc/Tombi! (Europe) (En,Fr,De,It,Nl) (Rev 1).cue'
    donor=Disc(cue)
    check_disc(dict(disc_hashes={'sha1':'2505d958b4439d04844cadd3f968fc7432a48e00'}),donor,cue)
    assert reference == donor.read('EXE/MAIN0.EXE')
    target_disc=Disc(ROOT/'disc/eu2/disc.cue')
    body = reference[2048:]
    normalized = normalize(body)
    keys = json.loads((ROOT/'eu2/seamless-contract.json').read_text())
    result = {k:v for k,v in keys.items() if k!='languages'}
    result['languages'] = []
    _, states = profiles(ROOT, disc_dir='disc/eu2', languages={'en':0,'es':5,'pt':6,'sv':7,'da':8})
    geometry = dict(enabled=False, languages={}, evidence='Complete hash-qualified EU1 geometry bodies; identical internal continuations')
    for language, index in {'en':0,'es':5,'pt':6,'sv':7,'da':8}.items():
        raw = (ROOT/f'disc/eu2/EXE/MAIN{index}.EXE').read_bytes()
        assert raw == target_disc.read(f'EXE/MAIN{index}.EXE')
        target = raw[2048:]
        norm = normalize(target)
        code = {}
        for pc in keys['languages'][0]['code']:
            offset, radius = match_normalized(normalized, norm, int(pc,16)-0x80010000)
            code[pc] = dict(address=hex(0x80010000+offset), sha256=sha(target[offset-32:offset+32]))
        # Derive the original indexed SPU table load, independently of symbols.
        at = int(code['0x8004f1c0']['address'],16)-0x80010000
        high, low = struct.unpack_from('<I',target,at-8)[0], struct.unpack_from('<I',target,at)[0]
        assert high>>16 == 0x3c01 and low>>16 == 0x8c34
        bank = ((high&65535)<<16)+(low&65535)-(65536 if low&32768 else 0)
        result['languages'].append(dict(language=language,main_sha256=sha(raw),code=code,
            bank_table=hex(bank),game=hex(states[language]['base'])))
        routines=[]
        for pc,size,digest in ROUTINES:
            assert sha(body[pc-0x80010000:pc-0x80010000+size]) == digest
            offset,radius=match_normalized(normalized,norm,pc-0x80010000)
            candidate=target[offset:offset+size]
            # Rev1 bodies are byte-identical, including every internal jump.
            assert sha(candidate)==digest, (language,hex(pc))
            routines.append(dict(pc=hex(0x80010000+offset),size=size,sha256=digest,verified_internal_relocations=[]))
        geometry['languages'][language]=dict(game=hex(states[language]['base']),routines=routines)
        print(language,'verified',len(code),'loader sites and three complete geometry bodies')
    for name,data in [('seamless-contract.json',result),('geometry-evidence.json',geometry)]:
        destination=source(name)
        if args.write_contract: destination.write_text(json.dumps(data,indent=2)+'\n',encoding='utf-8',newline='\n')
        else: assert json.loads(destination.read_text())==data, name
    print('PASS: Rev1 original loader/geometry correspondence')


if __name__=='__main__': main()
