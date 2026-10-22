"""Verify EU2 geometry correspondence; emits hashes, never original bodies."""
import hashlib
import json
from pathlib import Path
import struct
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'eu'))
from geometry_profile import ROUTINES
from session_state import profiles


def main():
    languages={'en':0,'es':5,'pt':6,'sv':7,'da':8}
    identity_address,states=profiles(ROOT,disc_dir='disc/eu2',languages=languages)
    result=dict(enabled=False,identity_address=hex(identity_address),languages={},
        evidence='Complete function comparison against hash-verified EU1 bodies; internal J relocation checked')
    for language,index in languages.items():
        original=(ROOT/'disc/EXE/MAIN0.EXE').read_bytes()[2048:]
        body=(ROOT/f'disc/eu2/EXE/MAIN{index}.EXE').read_bytes()[2048:]
        row=dict(game=hex(states[language]['base']),routines=[])
        for old,size,sha in ROUTINES:
            old_offset=old-0x80010000
            donor=original[old_offset:old_offset+size]
            if hashlib.sha256(donor).hexdigest()!=sha:
                raise ValueError('Unverified EU1 comparison source')
            # Reference symbols nominate these candidates; full bytes qualify them.
            new={0x8002235c:0x80022310,0x80022630:0x800225e4,0x80022838:0x800227ec}[old]
            offset=new-0x80010000
            candidate=body[offset:offset+size]
            relocations=[]
            for n in range(0,size,4):
                a=struct.unpack_from('<I',donor,n)[0]
                b=struct.unpack_from('<I',candidate,n)[0]
                if a==b:
                    continue
                if a>>26 != 2 or b>>26 != 2:
                    raise ValueError(f'Unexplained geometry difference: {language} {new+n:x}')
                at=((old+n+4)&0xf0000000)|((a&0x3ffffff)<<2)
                bt=((new+n+4)&0xf0000000)|((b&0x3ffffff)<<2)
                if not old<=at<old+size or at-old!=bt-new:
                    raise ValueError('Geometry jump is not an identical internal continuation')
                relocations.append(dict(offset=hex(n),target_offset=hex(bt-new)))
            row['routines'].append(dict(pc=hex(new),size=size,sha256=hashlib.sha256(candidate).hexdigest(),
                                       verified_internal_relocations=relocations))
        result['languages'][language]=row
    output=ROOT/'docs/regional/eu2-geometry-evidence.json'
    output.write_text(json.dumps(result,indent=2))
    print('PASS: all 15 complete geometry bodies; no runtime hooks enabled')


if __name__=='__main__':main()
