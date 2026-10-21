"""Bind EU loader fields to checked instructions in each original MAIN."""
from pathlib import Path
import json
import struct
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
from disc_identity import main_fingerprints
ROOT = Path(__file__).resolve().parents[1]


def fnv(data):
    value = 2166136261
    for byte in data:
        value = ((value ^ byte) * 16777619) & 0xffffffff
    return value


def generate():
    sys.path.insert(0,str(ROOT/'psxrecomp/tools'))
    from aot_overlay_pipeline import Disc
    disc=Disc(ROOT/'disc/Tombi! (Europe) (En,Fr,De,It,Nl) (Rev 1).cue')
    offset, fingerprints = main_fingerprints(ROOT)
    rows = []
    for index, lang in enumerate(('en', 'fr', 'de', 'it', 'nl')):
        body = (ROOT/f'disc/EXE/MAIN{index}.EXE').read_bytes()[2048:]
        def word(pc): return struct.unpack_from('<I', body, pc-0x80010000)[0]
        def field(pc, upper, expected):
            value = word(pc)
            if value & 0xffff0000 != expected:
                raise ValueError(f'{lang}: unexpected field instruction {pc:08X}')
            lui = word(pc-4)
            if lui >> 26 != 15 or (lui & 65535) != upper >> 16 or \
                    (lui >> 16 & 31) != (value >> 21 & 31):
                raise ValueError(f'{lang}: unverified field address construction {pc:08X}')
            return upper+(value & 65535)-(65536 if value & 32768 else 0)
        row = dict(
            queue=field(0x8004ebec, 0x800a0000, 0x24420000),
            files=field(0x8004ec1c, 0x80080000, 0x24a50000),
            scratch=field(0x8004ed18, 0x800a0000, 0x24420000),
            alternate=field(0x8004ed08, 0x800b0000, 0x24420000),
            errors=field(0x8004eb4c, 0x800a0000, 0xac200000),
            headers=field(0x8004f13c, 0x800a0000, 0x24840000),
            bodies=field(0x8004f174, 0x800a0000, 0x24840000),
            codec_bit=field(0x8003bb5c, 0x800a0000, 0xa0200000),
            codec_flags=field(0x8003bb74, 0x800a0000, 0xa4230000),
            spu_mode=field(0x800772ec, 0x800a0000, 0x8c630000),
            spu_address=field(0x800772f4, 0x800a0000, 0xa4220000))
        # initGameConfig's GAME pointer is already independently derived.
        from session_state import profiles
        _, game_profiles = profiles(ROOT)
        row['game'] = game_profiles[lang]['base']
        row['list_buffer'] = field(0x8004f648,0x800a0000,0x24c60000)
        if field(0x8006c0c4,0x800a0000,0x279c0000) != row['list_buffer']:
            raise ValueError('Loader relocation base differs from original GP')
        loc=body[row['files']-0x80010000:row['files']-0x80010000+8]
        bcd=lambda value: (value>>4)*10+(value&15)
        row['list_lba']=(bcd(loc[0])*60+bcd(loc[1]))*75+bcd(loc[2])-150
        row['list_size']=struct.unpack_from('<I',loc,4)[0]
        if (row['list_lba'],row['list_size']) != disc.files[f'SYS/LD{index}SYS.BIN'] or \
                (row['list_size']+2047)//2048*2048 != 8192:
            raise ValueError('Unverified original system list file extent')
        names=[f'SYS/LD{index}SYS.BIN']+[f'SYS/LD{index}AR{a:02d}.BIN' for a in list(range(15))+[16,17,18,19]]
        for number,name in enumerate(names):
            at=row['files']-0x80010000+number*8
            raw=body[at:at+8]
            extent=((bcd(raw[0])*60+bcd(raw[1]))*75+bcd(raw[2])-150,struct.unpack_from('<I',raw,4)[0])
            if extent!=disc.files[name] or extent[1]>8192:
                raise ValueError(f'Unverified load-list ID {number}: {name}')
        # Checked leaf-call targets and bank configuration table in cdLoadTask.
        checks = {0x8004f1c0: 0x8c348530, 0x8004f008: 0x0c017c3f,
                  0x8004f118: 0x0c01d183, 0x8004f254: 0x0c01d1d8,
                  0x8004f274: 0x0c01d1a4, 0x8004eb08: 0x27bdff98,
                  0x800199e0: 0x0c005c8e, 0x800199e4: 0x24040001}
        for pc, expected in checks.items():
            if word(pc) != expected:
                raise ValueError(f'{lang}: unverified loader ABI {pc:08X}')
        # Runtime guards reject other code/overlay identities before any write.
        for key, start, size in (('loader_hash', 0x4eb08, 0x850),
                                 ('task_hash', 0x198b4, 0x3154),
                                 ('libraries_hash', 0x7460c, 0x2e00),
                                 ('gpu_hash', 0x5f0fc, 0x100),
                                 ('open_hash', 0x171b8, 0xb4),
                                 ('render_hash', 0x5042c, 0x700)):
            row[key] = fnv(body[start-0x10000:start-0x10000+size])
        at=row['files']-0x80010000
        row['files_hash']=fnv(body[at:at+1119*8])
        row['fingerprint'] = fingerprints[lang]
        rows.append(row)
    out = ROOT/'build-eu-seamless/generated'
    out.mkdir(parents=True, exist_ok=True)
    lines = [f'#define TOMBI_MAIN_IDENTITY_ADDRESS 0x{0x80010000+offset:08x}u',
             'static const TombiLoaderProfile eu_profiles[5] = {']
    for row in rows:
        values = ','.join(f'0x{v:08x}u' for k, v in row.items() if k != 'fingerprint')
        fingerprint = ','.join(str(v) for v in row['fingerprint'])
        lines.append('    {'+values+', {'+fingerprint+'}},')
    lines.append('};\n')
    (out/'eu_profiles.h').write_text('\n'.join(lines))
    (out/'profiles.json').write_text(json.dumps([
        {k: v.hex() if isinstance(v, bytes) else hex(v) for k, v in row.items()}
        for row in rows], indent=2)+'\n')
    print('PASS: five instruction-bound EU loader profiles')


if __name__ == '__main__': generate()
