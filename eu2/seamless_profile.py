"""Recover EU2 bindings from original instructions, reusing the EU1 loader."""
from pathlib import Path
import hashlib
import json
import re
import struct
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'eu2'))
sys.path[:0]=[str(ROOT/'eu'),str(ROOT/'psxrecomp/tools')]
from session_state import profiles
from seamless_profiles import fnv
from aot_overlay_pipeline import Disc,check_disc
from revisions import source, PROFILES, active

LANGUAGES={'en':0,'es':5,'pt':6,'sv':7,'da':8}


def generate():
    loader=(ROOT/'eu/seamless/loader.c').read_text()
    reviewed=json.loads((source('seamless-contract.json')).read_text())
    if hashlib.sha256(loader.encode()).hexdigest()!=reviewed['loader_source_sha256'] or \
       hashlib.sha256((ROOT/'eu/seamless/profile.h').read_text().encode()).hexdigest()!=reviewed['profile_header_sha256']:
        raise ValueError('Shared loader changed; review the EU2 source contract before rebuilding')
    addresses={int(v,16) for v in re.findall(r'0x(80[0-9a-fA-F]{6})u',loader)}
    addresses|={0x80000000+int(v,16) for v in re.findall(r'phys[!=]=0x([0-9a-fA-F]+)u',loader)}
    addresses|={0x8004ebec,0x8004ec1c,0x8004ed18,0x8004ed08,0x8004eb4c,
        0x8004f13c,0x8004f174,0x8003bb5c,0x8003bb74,0x800772ec,0x800772f4,
        0x8004f648,0x8006c0c4,0x8004f1c0,0x8004f008,0x8004f118,0x8004f254,0x8004f274,
        0x800199e0,0x800199e4,0x8003bafc}
    out=ROOT/'build-eu2-seamless/generated'
    out.mkdir(parents=True,exist_ok=True)
    identity_address,states=profiles(ROOT,disc_dir='disc/eu2',languages=LANGUAGES)
    disc=Disc(ROOT/'disc/eu2/disc.cue')
    check_disc(dict(disc_hashes={'sha1':PROFILES[active()]['sha1']}),disc,ROOT/'disc/eu2/disc.cue')
    mappings=[];bindings=[];contracts=[]
    fields=dict(queue=(0x8004ebec,0x2442),files=(0x8004ec1c,0x24a5),
        scratch=(0x8004ed18,0x2442),alternate=(0x8004ed08,0x2442),errors=(0x8004eb4c,0xac20),
        headers=(0x8004f13c,0x2484),bodies=(0x8004f174,0x2484),codec_bit=(0x8003bb5c,0xa020),
        codec_flags=(0x8003bb74,0xa423),spu_mode=(0x800772ec,0x8c63),spu_address=(0x800772f4,0xa422))
    ranges=(('loader_hash',0x8004eb08,0x850),('task_hash',0x800198b4,0x3154),
        ('libraries_hash',0x8007460c,0x2e00),('gpu_hash',0x8005f0fc,0x100),
        ('open_hash',0x800171b8,0xb4),('render_hash',0x8005042c,0x700))
    for lang,index in LANGUAGES.items():
        exe=(ROOT/f'disc/eu2/EXE/MAIN{index}.EXE').read_bytes()
        body=exe[2048:]
        if body!=disc.read(f'EXE/MAIN{index}.EXE')[2048:]:raise ValueError('Working executable differs from verified disc')
        contract=next(r for r in reviewed['languages'] if r['language']==lang)
        if hashlib.sha256(exe).hexdigest()!=contract['main_sha256']:raise ValueError('Unreviewed original MAIN image')
        mapping={int(pc,16):int(record['address'],16) for pc,record in contract['code'].items()}
        if set(mapping)!={pc for pc in addresses if 0x80017000<=pc<0x80078000}:
            raise ValueError('Loader address set changed; explicit profile review required')
        for pc,new in mapping.items():
            if hashlib.sha256(body[new-0x80010000-32:new-0x80010000+32]).hexdigest()!=contract['code'][hex(pc)]['sha256']:
                raise ValueError('Original hook instruction contract changed')
        def word(pc):return struct.unpack_from('<I',body,pc-0x80010000)[0]
        def field(old,expected):
            pc=mapping[old]
            lo,hi=word(pc),word(pc-4)
            if lo>>16!=expected or hi>>26!=15 or hi>>16&31!=lo>>21&31:
                raise ValueError(f'Unverified field construction {lang} {pc:x}')
            value=((hi&65535)<<16)+(lo&65535)-(65536 if lo&32768 else 0)
            if not 0x80010000<=value<0x80200000:raise ValueError('Field outside RAM')
            return value
        row={name:field(pc,expected) for name,(pc,expected) in fields.items()}
        row['game']=states[lang]['base']
        row['list_buffer']=field(0x8004f648,0x24c6)
        if field(0x8006c0c4,0x279c)!=row['list_buffer']:raise ValueError('List relocation/GP mismatch')
        bcd=lambda v:(v>>4)*10+(v&15)
        table=row['files']-0x80010000
        names=[f'SYS/LD{index}SYS.BIN']+[f'SYS/LD{index}AR{a:02d}.BIN' for a in list(range(15))+[16,17,18,19]]
        for n,name in enumerate(names):
            raw=body[table+n*8:table+n*8+8]
            extent=((bcd(raw[0])*60+bcd(raw[1]))*75+bcd(raw[2])-150,struct.unpack_from('<I',raw,4)[0])
            if extent!=disc.files[name] or extent[1]>8192:raise ValueError(f'Original load-list extent mismatch: {lang} {name}')
            if n==0:row['list_lba'],row['list_size']=extent
        for key,pc,n in ranges:
            offset=mapping[pc]-0x80010000
            row[key]=fnv(body[offset:offset+n])
        row['files_hash']=fnv(body[table:table+1119*8])
        row['fingerprint']=states[lang]['fingerprint']
        # Exact bank-table addressing: LUI at +8, indexed LW at +16.
        bank_pc=mapping[0x8004f1c0]
        high=word(bank_pc-8);low=word(bank_pc)
        if high>>16!=0x3c01 or low>>16!=0x8c34:raise ValueError('SPU table ABI')
        bank=((high&65535)<<16)+(low&65535)-(65536 if low&32768 else 0)
        mapping[0x80078530]=bank
        mapping[0x80099000]=0x80010000+len(body)
        # Independently verify every synchronous leaf-call and the task yield.
        for call,target in ((0x8004f008,0x8005f0fc),(0x8004f118,0x8007460c),
            (0x8004f254,0x80074760),(0x8004f274,0x80074690),(0x800199e0,0x80017238)):
            actual=word(mapping[call])
            if actual!=0x0c000000|((mapping[target]&0x0fffffff)>>2):raise ValueError(f'Leaf call mismatch: {lang} {call:x}')
        if word(mapping[0x800199e4])!=0x24040001:raise ValueError('Yield argument changed')
        mappings.append(mapping);bindings.append(row)
        contracts.append(dict(language=lang,main_sha256=hashlib.sha256(exe).hexdigest(),
            code={hex(pc):dict(address=hex(new),sha256=hashlib.sha256(body[new-0x80010000-32:new-0x80010000+32]).hexdigest())
                  for pc,new in mapping.items() if pc not in (0x80099000,0x80078530)},
            bank_table=hex(bank),game=hex(row['game'])))
        print(lang,'verified loader',hex(mapping[0x8004eb08]),'render',hex(mapping[0x8005042c]),flush=True)
    if contracts!=reviewed['languages']:raise ValueError('Derived EU2 instruction/data contract changed')
    header=[f'#define TOMBI_MAIN_IDENTITY_ADDRESS 0x{identity_address:08x}u',
        'static const TombiLoaderProfile eu_profiles[5] = {']
    for row in bindings:
        header.append('{'+','.join(hex(v)+'u' for k,v in row.items() if k!='fingerprint')+',{'+','.join(str(v) for v in row['fingerprint'])+'}},')
    header.append('};')
    (out/'eu_profiles.h').write_text('\n'.join(header)+'\n')
    code=['static uint32_t eu2_address(uint32_t address) {',
        'if(!s_profile) return 0; unsigned language=(unsigned)(s_profile-eu_profiles);',
        'if(language>=5) return 0; switch(address) {']
    for old in mappings[0]:
        code.append('case '+hex(old)+'u: { static const uint32_t values[5]={'+','.join(hex(m[old])+'u' for m in mappings)+'}; return values[language]; }')
    code+=['default:return address;','}}']
    (out/'eu2_code_map.inc').write_text('\n'.join(code)+'\n')
    entries=sorted({m[old] for m in mappings for old in (0x800171b8,0x80017238,0x8001be1c,0x8005042c)})
    # Keep constructor addresses static. All runtime guest addresses refresh
    # through the original MAIN identity before touching guest state.
    loader=re.sub(r'const uint32_t entries\[\]=\{.*?\};','const uint32_t entries[]={'+','.join(hex(v)+'u' for v in entries)+'};',loader)
    constructor=loader[loader.index('PSX_MOD_CONSTRUCTOR'):]
    loader=loader[:loader.index('PSX_MOD_CONSTRUCTOR')]
    def replace(match):
        value=int(match.group(1),16)
        if value in mappings[0]:return f'eu2_address(0x{value:08x}u)'
        if 0x10000<=value<0x78000 and value+0x80000000 in mappings[0]:
            return f'(eu2_address(0x{value+0x80000000:08x}u)&0x1fffffffu)'
        if 0x80017000<=value<0x80099001:raise ValueError(f'Unmapped loader literal {value:x}')
        return match.group()
    loader=re.sub(r'0x([0-9a-fA-F]+)u\b',replace,loader)
    loader=loader.replace('static const TombiLoaderProfile *s_profile;',
        'static const TombiLoaderProfile *s_profile;\n#include "eu2_code_map.inc"')
    loader=loader.replace('return dispatch(cpu,address&0x1fffffffu);',
        'if(!identify_profile()) return 0;\n    return dispatch(cpu,address&0x1fffffffu);')
    (out/'eu2_loader.c').write_text(loader+constructor)
    (out/'profiles.json').write_text(json.dumps([{k:v.hex() if isinstance(v,bytes) else hex(v) for k,v in r.items()} for r in bindings],indent=2))
    (out/'instruction-contract.json').write_text(json.dumps(contracts,indent=2))
    (out/'hook-entries.json').write_text(json.dumps([hex(v) for v in entries]))
    return entries


if __name__=='__main__':generate()
