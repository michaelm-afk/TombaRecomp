"""Verify original EU geometry bodies; optional local-only LLE test references.

Never embeds original machine/generated code in the tracked project. SHA-256
contracts are common to all five EU MAIN images, independently checked here.
"""
import hashlib
import json
from pathlib import Path
import re
import struct

ROOT = Path(__file__).resolve().parents[1]
ROUTINES = (
    (0x8002235c, 724, '54daa3092828b289d6a3de30de16f57c927d63aa27666464d1e3cb1c00c2d424'),
    (0x80022630, 520, '1286a4d0c55df2bf2b6bf5d0313480560d00a35243a659599b7e197c51f400e4'),
    (0x80022838, 644, '2fb503d7fc2018bdca649ea9377422c28e7ef1e0aa08f8c7c86c9e455bb1a146'),
)

def fnv(data):
    result = 2166136261
    for b in data: result = ((result ^ b) * 16777619) & 0xffffffff
    return result

def generate(references=False):
    bodies=[]
    for i in range(5):
        exe=(ROOT/f'disc/EXE/MAIN{i}.EXE').read_bytes()
        assert struct.unpack_from('<I',exe,0x18)[0] == 0x80010000
        body=exe[2048:];bodies.append(body)
        for pc,size,sha in ROUTINES:
            raw=body[pc-0x80010000:pc-0x80010000+size]
            assert hashlib.sha256(raw).hexdigest()==sha,(i,hex(pc))
    out=ROOT/'build-eu-seamless/generated';out.mkdir(parents=True,exist_ok=True)
    rows=[]
    for pc,size,sha in ROUTINES:
        raw=bodies[0][pc-0x80010000:pc-0x80010000+size]
        rows.append(f'{{0x{pc:08x}u,{size}u,0x{fnv(raw):08x}u}}')
    (out/'eu_geometry_profile.inc').write_text(
        '/* Generated hashes only; no game code. */\n'
        'static const struct { uint32_t pc, size, hash; } eu_geometry_profile[] = {\n'+
        ',\n'.join(rows)+'\n};\n')
    if references:
        # Extract only the three original functions from a previously audited
        # local MAIN translation. Reference C remains an excluded build output.
        candidates=sorted((ROOT/'build-eu-seamless/hook-aot').glob('attempt-*/jobs/000/cache/**/*_patched.c'),
                          key=lambda p:p.stat().st_mtime,reverse=True)
        if not candidates: raise RuntimeError('Build/audit original MAIN overlays first')
        source=candidates[0].read_text(encoding='latin-1')
        chunks=[]
        for kind,(pc,size,_) in enumerate(ROUTINES):
            symbol=f'func_{pc:08X}'
            match=re.search(r'\nvoid '+symbol+r'\(CPUState\* cpu\)\n\{.*?\n\}',source,re.S)
            assert match,symbol
            chunk=match.group(0)
            # A fresh cache may already contain the opt-in HLE entry. The
            # reference must execute the original body without re-entering it.
            chunk=re.sub(r'^    if \(psx_mod_function_entry\(cpu, 0x'+f'{pc:08X}'+r'u\)\) return;  /\* trusted opt-in game-mod hook \*/\n',
                         '',chunk,flags=re.M)
            instructions={int(a,16):int(b,16) for a,b in re.findall(r'/\* 0x([0-9A-F]{8}): 0x([0-9A-F]{8}) \*/',chunk)}
            for address,word in instructions.items():
                assert pc<=address<pc+size
                assert struct.unpack_from('<I',bodies[0],address-0x80010000)[0]==word
            # The emitter records ordinary instruction words; branch/jump
            # terminators are represented by C control flow without that
            # comment. Reject any missing non-control instruction metadata.
            for address in range(pc,pc+size,4):
                if address in instructions: continue
                word=struct.unpack_from('<I',bodies[0],address-0x80010000)[0]
                assert word>>26 in (1,2,3,4,5,6,7) or (word>>26==0 and word&63 in (8,9)),hex(address)
            assert 'psx_mod_function_entry' not in chunk, 'Unexpected reference hook form'
            chunks.append(chunk.replace(symbol,f'tombi_geometry_lle_{kind}'))
        (out/'eu_geometry_reference.c').write_text(
            '/* LOCAL GENERATED GAME CODE: NEVER COMMIT OR DISTRIBUTE. */\n'
            '#include "psx_runtime.h"\n#include "ws_cull_edge.h"\n'
            'extern void debug_server_cyc_observe(uint32_t pc);\n'+ '\n'.join(chunks))
    (out/'geometry-contract.json').write_text(json.dumps(dict(
        mains=5,routines=[dict(pc=hex(pc),size=size,sha256=sha) for pc,size,sha in ROUTINES],
        reference_generated=references),indent=2)+'\n')
    print('PASS: complete EU geometry contracts in all five languages',flush=True)

if __name__=='__main__':
    import argparse
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--references',action='store_true')
    generate(ap.parse_args().references)
