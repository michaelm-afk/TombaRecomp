/* EU Rev-1 resident-loader adapter, ported from the US planner. No clock, CD latency, scheduler or audio
 * pacing changes. A request is completed only after its real resource writes.
 * The shipped binary prepares the asset pack once from the owner's disc. */
#include "mod_plugins.h"
#include "cpu_state.h"
#include "interrupts.h"
#include "bios_hle.h"
#include "gpu.h"
#include "spu.h"
#include "memcard.h"
#include "psx_cycles.h"
#include "tomba_seamless_assets.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

typedef TombaAsset Asset;
static const Asset *assets;
static uint32_t asset_count;
static unsigned batches, fallbacks, frame;
static unsigned last_batch_frame;
static int trace;
/* Regression-only host switch: exercise genuine CD fallbacks without
 * changing game data, code, inventory or progress. No launcher setting. */
static int diagnostic_cd_lists;
static unsigned fallbacks_at_frame_start, yield_budget;
#include "profile.h"
#include "eu_profiles.h"
static const TombiLoaderProfile *s_profile;


static uint32_t r32(uint32_t a) { return psx_mod_read_word(a); }
static uint16_t r16(uint32_t a) { return psx_mod_read_half(a); }
static uint8_t r8(uint32_t a) { return psx_mod_read_byte(a); }
static void w32(uint32_t a, uint32_t v) { psx_mod_write_word(a, v); }
static void w16(uint32_t a, uint16_t v) { psx_mod_write_half(a, v); }
static void w8(uint32_t a, uint8_t v) { psx_mod_write_byte(a, v); }

static uint32_t u32(const unsigned char *p) {
    return (uint32_t)p[0] | (uint32_t)p[1]<<8 | (uint32_t)p[2]<<16 | (uint32_t)p[3]<<24;
}
static int ram(uint32_t a, uint32_t n) {
    return a >= 0x80010000u && a <= 0x80200000u && n <= 0x80200000u-a;
}
/* Data the original code produces with CPU stores (decompressor output,
 * clears, card reads) takes the CPU store path. */
static void copy_to_ram(uint32_t a, const unsigned char *p, uint32_t n) {
    if (!psx_mod_host_write_ram(a, p, n)) {
        fprintf(stderr,"EU seamless: unexpected RAM service failure %08X/%u\n",a,n);
        abort();
    }
}
/* Disc sectors arrive as the CD-ROM DMA delivers them. */
static void deliver_sectors(uint32_t a, const unsigned char *p, uint32_t n, uint32_t lba) {
    if (((a | n) & 3u) || !psx_mod_dma_write_ram(a, p, n, (int)lba)) copy_to_ram(a, p, n);
}
static unsigned bcd(unsigned x) { return (x >> 4)*10 + (x & 15); }
static const Asset *find_asset(unsigned id) {
    if (id >= 1119) return NULL;
    uint32_t p = s_profile->files + id*8;
    uint32_t lba = (bcd(r8(p))*60 + bcd(r8(p+1)))*75 + bcd(r8(p+2));
    if (lba < 150) return NULL;
    lba -= 150;
    for (unsigned i = 0; i < asset_count; ++i)
        if (assets[i].lba == lba && assets[i].size == r32(p+4)) return assets+i;
    return NULL;
}

/* Only synchronous leaf services use host calls. Coroutine-capable task
 * bodies execute on their original stack through the normal scheduler. */
static uint32_t guest(CPUState *cpu, uint32_t pc, uint32_t ra,
                      uint32_t a0, uint32_t a1, uint32_t a2) {
    return psx_mod_call_guest(cpu, pc, ra, a0, a1, a2, cpu->gpr[7]);
}

typedef struct { const Asset *asset; uint32_t queue, desc, dest, scratch, raw_dest; unsigned mode, type; } Request;

static int plan_request(unsigned index, Request *r) {
    r->queue=s_profile->queue+index*8;
    r->desc=r32(r->queue); r->dest=r32(r->queue+4);
    if (!ram(r->desc,20)) return 0;
    r->asset=find_asset(r16(r->desc));
    if (!r->asset) return 0;
    uint32_t flags=r32(r->desc+16);
    if(flags & ~31u) return 0;
    r->mode=flags&15; r->type=r8(r->desc+3);
    r->scratch=(flags&16) ? s_profile->alternate : s_profile->scratch;
    if (r->mode>4) return 0;
    r->raw_dest=(r->mode==0 || r->mode==3) ? r->scratch : r->dest;
    if (!ram(r->raw_dest,r->asset->raw_len)) return 0;
    if (r->mode==1 || r->mode==3) {
        if (!r->asset->decoded_len || !ram(r->mode==1 ? r->scratch : r->dest,r->asset->decoded_len)) return 0;
    }
    if (r->mode==0 && (r->type&0xF0)!=0x10 && (r->type&0xF0)!=0x90) return 0;
    if (r->mode==1 || (r->mode==0 && (r->type&0xF0)==0x10)) {
        unsigned width=r16(r->desc+12), height=r16(r->desc+14);
        if (!width || width>1024 || !height || height>512 ||
            r16(r->desc+8)+width>1024 || r16(r->desc+10)+height>512 || (r->scratch&3) ||
            width*height*2 >(r->mode==1 ? r->asset->decoded_len : r->asset->raw_len)) return 0;
    }
    /* Sound tables are offsets into the raw bank. Validate before any write. */
    if ((r->type&0xF0)==0x90 && r->mode!=3 && r->mode!=1) {
        /* This adapter owns synchronous DMA-style banks only. A custom
         * transfer callback or PIO transfer has additional semantics. */
        if(r32((s_profile->spu_mode-12)) || r32((s_profile->spu_mode+16)) || r32(s_profile->spu_mode)!=3) return 0;
        const unsigned char *p=r->asset->raw;
        unsigned n=r->asset->size, slot=r->type&15;
        if(slot==15) slot=0;
        /* SPU DMA reads whole words from word-aligned guest addresses. */
        if(n<36 || !ram(r->dest,n) || r->dest!=r->raw_dest || (r->dest&3)) return 0;
        uint32_t samples=u32(p), headers=u32(p+4);
        if(samples>n-4 || headers>n-32) return 0;
        unsigned sh=u32(p+headers), ss=u32(p+samples);
        if(sh<4 || ss<4 || sh%4 || ss%4 || sh>n-headers || ss>n-samples) return 0;
        unsigned nh=sh/4-1, ns=ss/4-1;
        if(!nh || ns<nh || slot+ns>44 || slot+nh>44) return 0;
        for(unsigned i=0;i<=ns;i++) if(u32(p+samples+4*i)>n-samples) return 0;
        for(unsigned i=0;i<nh;i++) if(u32(p+headers+4*i)>n-headers-32) return 0;
        for(unsigned i=0;i<ns;i++) if(u32(p+samples+4*i)>u32(p+samples+4*(i+1))) return 0;
        /* This is a sound-bank configuration index, not the four-bit handle
         * slot above. The EU table has 75 entries; its base is verified in cdLoadTask.
         * Restricting it to 0..15 sent most later music changes back to CD. */
        if(r16(r->desc+14)>=75) return 0;
        uint32_t spu_addr=r32(0x80078530u+r16(r->desc+14)*8);
        if((spu_addr&7) || spu_addr<0x1010 || spu_addr>=0x80000) return 0;
        for(unsigned i=0;i<nh;i++) {
            uint32_t src=samples+u32(p+samples+4*i);
            uint32_t end=samples+u32(p+samples+4*(i+1==nh ? ns : i+1));
            uint32_t len=(end-src+63)&~63u;
            if(end-src>0x7EFF0 || src>r->asset->raw_len || len>r->asset->raw_len-src ||
               len>0x80000-spu_addr || (src&3)) return 0;
            spu_addr+=end-src;
        }
    }
    return 1;
}

static void install_sound(CPUState *cpu, const Request *r) {
    unsigned slot=r->type&15;
    if(slot==15) slot=0;
    uint32_t samples=r->dest+r32(r->dest), headers=r->dest+r32(r->dest+4);
    unsigned nh=(r32(headers)>>2)-1, ns=(r32(samples)>>2)-1;
    for(unsigned i=0;i<nh;i++) {
        int handle=(int16_t)r16(0x1F8003A8u+2*(slot+i));
        if(handle!=-1) guest(cpu,0x8007460Cu,0x8004F120u,(uint32_t)handle,0,0);
    }
    for(unsigned i=0;i<nh;i++) w32(s_profile->headers+4*(slot+i),headers+r32(headers+4*i));
    for(unsigned i=0;i<ns;i++) w32(s_profile->bodies+4*(slot+i),samples+r32(samples+4*i));
    uint32_t spu_addr=r32(0x80078530u+r16(r->desc+14)*8);
    for(unsigned i=0;i<nh;i++) {
        uint32_t src=r32(s_profile->bodies+4*(slot+i));
        uint32_t end=(i+1==nh) ? samples+r32(samples+4*ns) : r32(s_profile->bodies+4*(slot+i+1));
        /* Same sample writes as SpuWrite's 64-byte DMA blocks, completed
         * synchronously. Preserve library transfer state and use the SPU's
         * write path (including IRQ checks), without pumping DMA wait loops. */
        uint32_t bytes=(end-src+63)&~63u;
        w16(s_profile->spu_address,(uint16_t)(spu_addr>>3));
        w32((s_profile->spu_mode+40),0); w32((s_profile->spu_mode+44),src); w32((s_profile->spu_mode+48),bytes/64);
        if(!psx_mod_spu_upload(spu_addr,src,bytes,1)) abort();
        w32((s_profile->spu_mode+12),1);
        uint32_t handle=guest(cpu,0x80074760u,0x8004F25Cu,r32(s_profile->headers+4*(slot+i)),0xFFFFFFFFu,spu_addr);
        w16(0x1F8003A8u+2*(slot+i),(uint16_t)handle);
        guest(cpu,0x80074690u,0x8004F27Cu,(uint32_t)(int32_t)(int16_t)handle,0,0);
        spu_addr+=end-src;
    }
}

static int install_batch(CPUState *cpu) {
    unsigned begin=r32(0x1F8002A0u), end=r32(0x1F80029Cu), count=0;
    Request requests[128];
    if(begin>=128 || end>=128 || begin==end || r16(0x801FD8E0u)) {
        ++fallbacks; psx_mod_counter_add("tomba.seamless.fallbacks",1);
        fprintf(stdout,"seamless: queue fallback frame=%u begin=%u end=%u busy=%u\n",
                frame,begin,end,r16(0x801FD8E0u));
        return 0;
    }
    for(unsigned i=begin;i!=end;i=(i+1)&127) {
        if(!plan_request(i,requests+count)) {
            uint32_t desc=r32(s_profile->queue+i*8);
            fprintf(stdout,"EU seamless: request fallback frame=%u queue=%u desc=%08X\n",frame,i,desc);
            ++fallbacks; psx_mod_counter_add("tomba.seamless.fallbacks",1); return 0;
        }
        ++count;
    }
    /* Validate every planned write before touching RAM, GPU or SPU. Never
     * replace MAIN/kernel/TCB memory or overwrite the live descriptor ring.
     * Reused scratch/destination buffers between resources are intentional. */
    for(unsigned i=0;i<count;i++) {
        const Request *r=requests+i;
        uint32_t address[2]={r->raw_dest,r->mode==1 ? r->scratch : r->dest};
        uint32_t size[2]={r->asset->raw_len,
            (r->mode==1 || r->mode==3) ? r->asset->decoded_len : 0};
        for(unsigned k=0;k<2;k++) if(size[k]) {
            uint32_t a=address[k], end_address=a+size[k];
            /* Only the 20 verified SYS/LDn{SYS,ARxx}.BIN extents may replace
             * the original GP/list window below the padded MAIN image end.
             * The immutable file table is hashed by validate_code(). */
            unsigned id=r16(r->desc);
            int load_list=!diagnostic_cd_lists && id<20 && r->mode==2 && k==0 && (r->type&0xF0)==0xF0 &&
                a==s_profile->list_buffer && size[k]<=8192 &&
                (id || (r->asset->lba==s_profile->list_lba && r->asset->size==s_profile->list_size));
            if((a<0x80099000u && !load_list) || end_address>0x801FD800u) {
                if(trace) fprintf(stdout,"EU seamless: protected span id=%u mode=%u dest=%08X bytes=%u\n",r16(r->desc),r->mode,a,size[k]);
                goto preflight_fallback;
            }
            if(a<s_profile->queue+1024 && end_address>s_profile->queue) goto preflight_fallback;
            /* Resource DMA/decode must never overwrite live language-specific
             * state. Sound bookkeeping is updated only by install_sound. */
            const uint32_t live[][2]={{s_profile->game,0x988},
                {s_profile->headers,44*4},{s_profile->bodies,44*4},
                {s_profile->codec_bit,8},{s_profile->errors,4}};
            for(unsigned j=0;j<sizeof(live)/sizeof(live[0]);j++)
                if(a<live[j][0]+live[j][1] && end_address>live[j][0]) goto preflight_fallback;
            for(unsigned j=0;j<count;j++)
                if(a<requests[j].desc+20 && end_address>requests[j].desc) goto preflight_fallback;
        }
    }
    double start=tomba_seamless_now_ms(); uint64_t start_cycles=psx_get_cycle_count();
    /* A raw bank/overlay can reuse a previous frame's packet arena too.
     * Drain submitted work before the first RAM write, not only before a
     * texture upload after its scratch data has already been replaced. */
    guest(cpu,0x8005F0FCu,0x8000FB00u,0,0,0);
    w8(0x1F8001CEu,0); w32(s_profile->errors,0);
    for(unsigned i=0;i<count;i++) {
        const Request *r=requests+i; const Asset *a=r->asset;
        double file_start=trace ? tomba_seamless_now_ms() : 0; unsigned file_frame=frame;
        w32(0x1F800288u,r->queue); w32(0x1F80028Cu,r->desc);
        w32(0x1F800290u,r->raw_dest); w32(0x1F800294u,a->raw_len/2048);
        deliver_sectors(r->raw_dest,a->raw,a->raw_len,a->lba);
        if(r->mode==1 || r->mode==3) {
            copy_to_ram(r->mode==1 ? r->scratch : r->dest,a->decoded,a->decoded_len);
            w32(0x1F800070u,a->declared); w32(0x1F800074u,a->decoded_len);
            w16(s_profile->codec_flags,(uint16_t)a->codec_state); w8(s_profile->codec_bit,(uint8_t)(a->codec_state>>16));
        }
        if(r->mode==1 || (r->mode==0 && (r->type&0xF0)==0x10)) {
            /* Drain earlier PsyQ commands before installing this rectangle.
             * The native GP0 upload consumes the data before scratch reuse. */
            guest(cpu,0x8005F0FCu,0x8004F010u,0,0,0);
            if(!psx_mod_psyq_load_image(r16(r->desc+8),r16(r->desc+10),
                                          r16(r->desc+12),r16(r->desc+14),r->scratch)) abort();
        } else if((r->type&0xF0)==0x90 && r->mode!=3) install_sound(cpu,r);
        w32(0x1F8002A0u,(begin+i+1)&127);
        if(trace) fprintf(stdout,"seamless: file id=%u mode=%u type=%02X frames=%u..%u ms=%.3f\n",r16(r->desc),r->mode,r->type,file_frame,frame,tomba_seamless_now_ms()-file_start);
    }
    /* An interrupt may append new requests during a synchronous guest leaf.
     * Leave those queued and let the original task service the remainder. */
    if(r32(0x1F80029Cu)!=end) return 0;
    w8(0x1F8001CEu,1);
    ++batches;
    psx_mod_counter_add("tomba.seamless.batches",1);
    psx_mod_counter_add("tomba.seamless.files",count);
    last_batch_frame=frame;
    fprintf(stdout,"seamless: batch=%u frame=%u files=%u ms=%.3f cycles=%llu area=%u/%u fallbacks=%u\n",batches,frame,count,tomba_seamless_now_ms()-start,(unsigned long long)(psx_get_cycle_count()-start_cycles),r16(s_profile->game),r16((s_profile->game+2)),fallbacks);
    fflush(stdout);
    cpu->gpr[2]=1;
    return 1;
preflight_fallback:
    ++fallbacks;
    psx_mod_counter_add("tombi.seamless.preflight_fallbacks",1);
    return 0;
}

static uint32_t code_hash(uint32_t address, unsigned bytes) {
    uint32_t value=2166136261u;
    for(unsigned i=0;i<bytes;i++) value=(value^r8(address+i))*16777619u;
    return value;
}

static int identify_profile(void) {
    for(unsigned n=0;n<5;n++) {
        unsigned i;
        for(i=0;i<64;i++)
            if(r8(TOMBI_MAIN_IDENTITY_ADDRESS+i)!=eu_profiles[n].fingerprint[i]) break;
        if(i==64) { s_profile=eu_profiles+n; return 1; }
    }
    s_profile=NULL;
    return 0;
}

static int validate_code(void) {
    if(!identify_profile()) return 0;
    const TombiLoaderProfile *p=s_profile;
    int valid=code_hash(0x8004EB08u,0x850)==p->loader_hash &&
        code_hash(0x800198B4u,0x3154)==p->task_hash &&
        code_hash(0x8007460Cu,0x2e00)==p->libraries_hash &&
        code_hash(0x8005F0FCu,0x100)==p->gpu_hash &&
        code_hash(0x800171B8u,0xb4)==p->open_hash &&
        code_hash(0x8005042Cu,0x700)==p->render_hash &&
        code_hash(p->files,1119*8)==p->files_hash;
    if(!valid) psx_mod_counter_add("tombi.seamless.code_rejected",1);
    return valid;
}

static int loading_yield_allowed(CPUState *cpu,unsigned main,unsigned state,unsigned phase,unsigned step) {
    if(r32(0x1F8001D4u)!=0x801FD800u || main!=1 ||
       cpu->gpr[31]!=0x800199E8u || cpu->gpr[4]!=1 || yield_budget>=8 ||
       !r8(0x1F8001CEu) || r8(0x1F8001CCu) || r16(0x801FD8E0u) ||
       fallbacks!=fallbacks_at_frame_start) return 0;
    return (state==0 && phase<=3) || (state==1 &&
        (phase==0 || phase==7 || (phase>=1 && phase<=6 && phase!=3 && step==0)));
}

/* MAIN routines only. No menu/area-overlay PC is treated as a universal
 * function, and original memory-card code/SIO transfers are never hooked. */
static int dispatch(CPUState *cpu, uint32_t phys) {
    if(!assets || !psx_mod_game_started()) return 0;
    if(phys==0x171B8u) {
        if(cpu->gpr[4]!=2 || cpu->gpr[5]!=0x8004EB08u || !validate_code()) return 0;
        /* Logo/title packet lifetimes cross the loader call. Keep that path
         * original until its overlay-specific submission contract is ported.
         * A DrawSync alone cannot drain packets not yet submitted. */
        if(r16(0x801FD848u)!=1) return 0;
        return install_batch(cpu);
    }
    /* Never run coroutine-capable task bodies through a nested host call.
     * Their original execution may sleep on an unsupported CD request. */
    if(phys!=0x17238u && phys!=0x1BE1Cu && phys!=0x5042Cu) return 0;
    if(r32(0x1F8001D4u)!=0x801FD800u) return 0;
    unsigned main=r16(0x801FD848u), state=r16(0x801FD84Au);
    unsigned phase=r16(0x801FD84Cu), step=r16(0x801FD84Eu);
    if(main!=1) return 0;
    if(trace && phys==0x17238u && cpu->gpr[31]==0x800199E8u && identify_profile()) {
        static unsigned previous[7], seen;
        unsigned current[]={main,state,phase,step,r16(s_profile->game),r16(s_profile->game+2),r8(0x1F8001CEu)};
        if(!seen || memcmp(previous,current,sizeof(current))) {
            memcpy(previous,current,sizeof(current));seen=1;
            fprintf(stdout,"EU seamless: state frame=%u task=%u/%u/%u/%u area=%u/%u complete=%u\n",
                frame,main,state,phase,step,current[4],current[5],current[6]);
            fflush(stdout);
        }
    }
    if(phys==0x5042Cu) {
        if(state!=1 || phase!=7 || step) return 0;
        if(cpu->gpr[31]<0x8001A64Cu || cpu->gpr[31]>=0x8001BE58u) return 0;
        return validate_code();
    }
    if(phys==0x1BE1Cu) {
        /* Cosmetic animation only; the original caller still performs its
         * normal completion handoff. Pending reads retain the real screen. */
        if(!r8(0x1F8001CEu) || fallbacks!=fallbacks_at_frame_start) return 0;
        if(!validate_code()) return 0;
        psx_mod_counter_add("tombi.seamless.loading_screen_skipped",1);
        return 1;
    }
    /* The sole accelerated yield is gameTask's own sleepTask(1), verified
     * from its original JAL and delay slot. Internal waits and other tasks
     * always execute their original scheduler calls. No guest registers or
     * coroutine continuation are saved/restored by host glue. */
    if(!loading_yield_allowed(cpu,main,state,phase,step) || !validate_code()) return 0;
    ++yield_budget;
    psx_mod_counter_add("tombi.seamless.loading_yields_skipped",1);
    return 1;
}

static void tick(void) {
    ++frame;
    yield_budget=0;
    fallbacks_at_frame_start=fallbacks;
}
static void activate(void) {
    trace=getenv("TOMBI_SEAMLESS_TRACE")!=NULL;
    diagnostic_cd_lists=getenv("TOMBI_SEAMLESS_TEST_CD_LISTS")!=NULL;
    assets=tomba_seamless_prepare(&asset_count);
    fprintf(stdout,"EU seamless: resident assets=%u; original cards and clock pacing retained\n",asset_count);
}
static int function_filter(CPUState *cpu, uint32_t address) {
    static unsigned seen;
    if(assets && !(seen&1u)) {
        seen|=1u;
        psx_mod_counter_add("tombi.seamless.native_entry_seen",1);
    }
    return dispatch(cpu,address&0x1fffffffu);
}
PSX_MOD_CONSTRUCTOR(tombi_register_seamless) {
    /* Native intra-image calls bypass the global dispatcher. Opt-in entry
     * filters keep their contract identical to interpreted function calls. */
    const uint32_t entries[]={0x800171B8u,0x80017238u,0x8001BE1Cu,0x8005042Cu};
    for(unsigned i=0;i<sizeof(entries)/sizeof(entries[0]);i++)
        psx_mod_register_function_filter_plugin("tombi.seamless",entries[i],function_filter);
    psx_mod_register_activation_plugin("tombi.seamless",activate);
    psx_mod_register_vblank_plugin("tombi.seamless",tick);
}
