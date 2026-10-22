"""Bind the existing EU geometry adapter/HLE to complete original EU2 bodies."""
import argparse,hashlib,json,re,struct
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
import sys
sys.path.insert(0, str(ROOT/'eu2'))
LANGUAGES={'en':0,'es':5,'pt':6,'sv':7,'da':8}
from revisions import source as revision_source, active

def generate(references=False):
    evidence=json.loads((revision_source('geometry-evidence.json') if active()=='rev1' else ROOT/'docs/regional/eu2-geometry-evidence.json').read_text())
    rows=[];first=None
    for lang,index in LANGUAGES.items():
        body=(ROOT/f'disc/eu2/EXE/MAIN{index}.EXE').read_bytes()[2048:]
        current=[]
        for r in evidence['languages'][lang]['routines']:
            pc=int(r['pc'],16);raw=body[pc-0x80010000:pc-0x80010000+r['size']]
            if hashlib.sha256(raw).hexdigest()!=r['sha256']:raise ValueError('Unreviewed EU2 geometry body')
            h=2166136261
            for b in raw:h=((h^b)*16777619)&0xffffffff
            current.append((pc,r['size'],h))
        if first is None:first=body;rows=current
        if current!=rows:raise ValueError('Language-specific geometry requires a separate reviewed adapter')
    out=ROOT/'build-eu2-seamless/generated';out.mkdir(parents=True,exist_ok=True)
    (out/'eu_geometry_profile.inc').write_text('static const struct { uint32_t pc,size,hash; } eu_geometry_profile[] = {\n'+',\n'.join('{%su,%su,%su}'%tuple(hex(v) for v in r) for r in rows)+'\n};\n')
    adapter=(ROOT/'eu/geometry.c').read_text()
    for pc in (0x800223F8,0x800226CC,0x800228D4,0x8002243C,0x80022918):adapter=adapter.replace(f'0x{pc:08X}u',f'0x{pc-(0 if active()=="rev1" else 0x4c):08X}u')
    # Shared include owns all geometry math and validation. Only original store
    # provenance PCs and the generated complete-body contracts differ.
    (out/'eu2_geometry.c').write_text(adapter.replace('../src/hle/tomba_geometry_hle.c',str(ROOT/'src/hle/tomba_geometry_hle.c').replace('\\','/')))
    if references:
        candidates=list((ROOT/'build-eu2-seamless/aot').glob('native-*/jobs/000/cache/**/*_patched.c'))
        if not candidates:raise ValueError('Build audited EU2 native overlays before differential validation')
        source=max(candidates,key=lambda p:p.stat().st_mtime).read_text(encoding='latin-1');chunks=[]
        for kind,(pc,size,_) in enumerate(rows):
            symbol=f'func_{pc:08X}';m=re.search(r'\nvoid '+symbol+r'\(CPUState\* cpu\)\n\{.*?\n\}',source,re.S)
            if not m:raise ValueError('Original translated geometry body missing')
            chunk=m.group(0)
            chunk=re.sub(r'^    if \(psx_mod_function_entry\(cpu, 0x'+f'{pc:08X}'+r'u\)\) return;.*\n','',chunk,flags=re.M)
            if 'psx_mod_function_entry' in chunk:raise ValueError('Reference must not reenter HLE')
            instructions={int(a,16):int(b,16) for a,b in re.findall(r'/\* 0x([0-9A-F]{8}): 0x([0-9A-F]{8}) \*/',chunk)}
            for address,w in instructions.items():
                if not pc<=address<pc+size or struct.unpack_from('<I',first,address-0x80010000)[0]!=w:raise ValueError('Reference instruction mismatch')
            for address in range(pc,pc+size,4):
                if address not in instructions:
                    w=struct.unpack_from('<I',first,address-0x80010000)[0]
                    if not (w>>26 in (1,2,3,4,5,6,7) or (w>>26==0 and w&63 in (8,9))):raise ValueError('Incomplete reference metadata')
            chunks.append(chunk.replace(symbol,f'tombi_geometry_lle_{kind}'))
        (out/'eu2_geometry_reference.c').write_text('/* Private original-code reference; never distribute. */\n#include "psx_runtime.h"\n#include "gpu.h"\n#include "ws_cull_edge.h"\nextern void debug_server_cyc_observe(uint32_t);\n'+'\n'.join(chunks))
    (out/'geometry-binding.json').write_text(json.dumps(dict(languages=list(LANGUAGES),routines=rows,source='shared EU adapter and shared Tomba HLE',references=references),indent=2))
    print('PASS: complete geometry/store-PC bindings for five EU2 MAINs',flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--references',action='store_true');generate(p.parse_args().references)
