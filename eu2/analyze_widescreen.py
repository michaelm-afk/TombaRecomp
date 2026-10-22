"""Reproduce reviewed EU2 instruction/data correspondence; no boot-disc override."""
from pathlib import Path
import argparse
import sys,struct,json,hashlib,importlib.util
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'psxrecomp/tools'),str(ROOT/'eu')]
from aot_overlay_pipeline import Disc
from session_state import profiles
sys.path.insert(0,str(ROOT/'eu2'))
from revisions import source, active
spec=importlib.util.spec_from_file_location('eu_wide',ROOT/'eu/widescreen_profile.py');wide=importlib.util.module_from_spec(spec);spec.loader.exec_module(wide)
old=Disc(ROOT/'disc/Tombi! (Europe) (En,Fr,De,It,Nl) (Rev 1).cue')
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--reference-disc',type=Path,default=ROOT/'disc/eu2/disc.cue')
parser.add_argument('--revision',choices=['original','rev1'],default='original')
parser.add_argument('--write-contract',action='store_true',help='Write a newly reviewed contract instead of checking it')
args=parser.parse_args()
new=Disc(args.reference_disc)
LANGUAGES={'en':0,'es':5,'pt':6,'sv':7,'da':8}
# Isolated static-analysis copies only. These do not qualify the boot disc.
ref_dir='build-eu2-bindings/reference' if args.revision=='original' else 'build-eu2-bindings/reference-rev1'
refs=ROOT/ref_dir;(refs/'EXE').mkdir(parents=True,exist_ok=True)
for lang,i in LANGUAGES.items():(refs/f'EXE/MAIN{i}.EXE').write_bytes(new.read(f'EXE/MAIN{i}.EXE'))
identity,states=profiles(ROOT,disc_dir=ref_dir,languages=LANGUAGES)
def words(body):return struct.unpack('<%dI'%(len(body)//4),body)
def normalize(raw):
 out=[]
 for w in words(raw):
  op=w>>26
  if op in (2,3):w &= 0xfc000000
  elif op==15 and 0x8000<=w&65535<=0x8020:w&=0xffff0000
  elif op in (9,32,33,34,35,36,37,38,40,41,42,43,46):w&=0xffff0000
  out.append(w)
 return struct.pack('<%dI'%len(out),*out)
def match(original,target,at):
 a,b=normalize(original),normalize(target)
 for radius in (16,32,64,128,256):
  needle=a[at-radius:at+radius];positions=[];start=0
  while True:
   pos=b.find(needle,start)
   if pos<0:break
   if pos%4==0:positions.append(pos+radius)
   start=pos+1
  if len(positions)==1:return positions[0],radius
 raise ValueError(f'No unique instruction correspondence at offset {at:x}')
def sha(raw):return hashlib.sha256(raw).hexdigest()
def pair(body,pc):
 hi,lo=struct.unpack_from('<II',body,pc-0x80010000-4)
 assert hi>>26==15 and hi>>16&31==lo>>21&31
 assert lo>>26 in (9,37)
 return ((hi&65535)<<16)+(lo&65535)-(65536 if lo&32768 else 0)
oldbody=old.read('EXE/MAIN0.EXE')[2048:]
code=dict(wide.CODE);code[0x8002cef8]=0x8002a3d4
rows=[]
for lang,i in LANGUAGES.items():
 raw=new.read(f'EXE/MAIN{i}.EXE');body=raw[2048:]
 expected=json.loads((source('seamless-contract.json',args.revision)).read_text())
 assert sha(raw)==next(r['main_sha256'] for r in expected['languages'] if r['language']==lang),'Unreviewed EU2 MAIN'
 mappings={};checks={};proof={}
 allpcs=set(code.values())|set(wide.FIELDS.values())|{0x8003a45c,0x8003b3cc,0x8004c5c4,0x80020318,0x8004f624,0x8004f628}
 pcmap={}
 for pc in sorted(allpcs):
  at,radius=match(oldbody,body,pc-0x80010000);newpc=0x80010000+at;pcmap[pc]=newpc
  checks[hex(newpc)]=sha(body[at-16:at+16])
  proof[hex(pc)]=dict(address=hex(newpc),window_bytes=radius*2,normalized_sha256=sha(normalize(oldbody[pc-0x80010000-radius:pc-0x80010000+radius])))
 for key,pc in code.items():mappings[key]=pcmap[pc]
 for key,pc in wide.FIELDS.items():mappings[key]=pair(body,pcmap[pc])
 assert mappings[0x8009bcc8]==states[lang]['base']
 mappings[0x8009bcca]=mappings[0x8009bcc8]+2
 # Area bank table 1: unique complete 64-byte scratchpad-slot table.
 table=oldbody[0x7b73c-0x10000:0x7b73c-0x10000+64]
 hits=[n for n in range(0,len(body)-64,4) if body[n:n+64]==table];assert len(hits)==1
 mappings[0x8007eefc]=0x80010000+hits[0]
 # Pointer table: all entries relocate by the same table block displacement.
 reference=list(struct.unpack_from('<16I',oldbody,0x7b90c-0x10000))
 delta=mappings[0x8007eefc]-0x8007b73c
 values=struct.pack('<16I',*(v+delta for v in reference))
 hits=[n for n in range(0,len(body)-64,4) if body[n:n+64]==values];assert len(hits)==1
 mappings[0x8007f0cc]=0x80010000+hits[0]
 # Full instruction windows for area-0 scene guards and area-1 residency guards.
 newbase=pair(body,pcmap[0x8004f628]);oldbase=pair(oldbody,0x8004f628)
 overlays={};overlay_checks={}
 for area in (0,1):
  a=old.read(f'SYSTEM/X0{area:02d}.BIN');b=new.read(f'SYSTEM/X{i}{area:02d}.BIN')
  area_checks={}
  for key,pc in wide.OVERLAY.items():
   if (key in (0x801168f4,0x801169ec)) != (area==0):continue
   oldpc=oldbase+(pc-0x800e8050);at,radius=match(a,b,oldpc-oldbase)
   target=newbase+at;mappings[key]=target
   area_checks[hex(target)]=sha(b[at-16:at+16])
   if key==0x801169ec:
    w=struct.unpack_from('<I',b,at)[0]
    assert w==(0x0c000000|((mappings[0x8002cef8]&0x0fffffff)>>2))
   else:assert struct.unpack_from('<I',b,at)[0]=={0x801168f4:0x27bdffe8,0x80115e2c:0x28420b6e,0x80115f14:0x28620b6d}[key]
  overlays[str(area)]=dict(file=f'SYSTEM/X{i}{area:02d}.BIN',base=hex(newbase),sha256=sha(b),checks=area_checks)
 row=dict(language=lang,main=f'EXE/MAIN{i}.EXE',main_sha256=sha(raw),identity_address=hex(identity),identity=states[lang]['fingerprint'].hex(),mapping={hex(k):hex(v) for k,v in sorted(mappings.items())},checks=checks,correspondence=proof,overlays=overlays)
 rows.append(row)
 print(lang,'verified',len(mappings),'code/data/overlay bindings; camera',hex(mappings[0x800a38b8]),'GAME',hex(mappings[0x8009bcc8]),'overlay',hex(newbase))
contract=dict(schema=1,source_policy_sha256=wide.SOURCES,main_identity_bytes=64,languages=rows)
destination=source('widescreen-contract.json',args.revision)
if args.write_contract:destination.write_text(json.dumps(contract,indent=2)+'\n',encoding='utf-8',newline='\n')
else:assert json.loads(destination.read_text(encoding='utf-8'))==contract,'Derived EU2 bindings differ from reviewed contract'
print('PASS: full correspondence contract reproduced; static images do not qualify a boot disc')
