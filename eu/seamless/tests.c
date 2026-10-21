/* Explicitly synthetic unit fixtures; no card or gameplay progress is loaded. */
#include "mod_plugins.h"
#undef PSX_MOD_CONSTRUCTOR
#define PSX_MOD_CONSTRUCTOR(name) static void name(void)
#include "loader.c"
#include <assert.h>

static uint8_t memory[0x200000], scratchpad[1024], bank[8192];
static unsigned writes, dmas, leaves;
uint64_t psx_cycle_count;
uint64_t psx_get_cycle_count(void) { return psx_cycle_count; }
static uint8_t *ptr(uint32_t a) {
    a&=0x1fffffffu;
    if(a<sizeof memory) return memory+a;
    assert(a>=0x1f800000 && a<0x1f800400);
    return scratchpad+(a-0x1f800000);
}
uint8_t psx_mod_read_byte(uint32_t a) { return *ptr(a); }
uint16_t psx_mod_read_half(uint32_t a) { return r8(a)|(uint16_t)r8(a+1)<<8; }
uint32_t psx_mod_read_word(uint32_t a) { return r16(a)|(uint32_t)r16(a+2)<<16; }
void psx_mod_write_byte(uint32_t a,uint8_t v) { *ptr(a)=v; ++writes; }
void psx_mod_write_half(uint32_t a,uint16_t v) { w8(a,(uint8_t)v); w8(a+1,(uint8_t)(v>>8)); }
void psx_mod_write_word(uint32_t a,uint32_t v) { w16(a,(uint16_t)v);w16(a+2,(uint16_t)(v>>16)); }
int psx_mod_host_write_ram(uint32_t a,const void *p,uint32_t n) { memcpy(ptr(a),p,n);++writes;return 1; }
int psx_mod_dma_write_ram(uint32_t a,const void *p,uint32_t n,int lba) {
    assert(leaves && lba==(int)assets[0].lba);memcpy(ptr(a),p,n);++dmas;++writes;return 1;
}
uint32_t psx_mod_call_guest(CPUState *cpu,uint32_t f,uint32_t ra,uint32_t a,uint32_t b,uint32_t c,uint32_t d) {
    (void)cpu;(void)ra;(void)a;(void)b;(void)c;(void)d;
    assert(f==0x8005f0fc);++leaves;return 0;
}
int psx_mod_spu_upload(uint32_t a,uint32_t b,uint32_t c,int d) { (void)a;(void)b;(void)c;(void)d;assert(0);return 0; }
int psx_mod_psyq_load_image(uint32_t a,uint32_t b,uint32_t c,uint32_t d,uint32_t e) { (void)a;(void)b;(void)c;(void)d;(void)e;assert(0);return 0; }
void psx_mod_counter_add(const char *name,uint32_t count) { (void)name;(void)count; }
double tomba_seamless_now_ms(void) { return 0; }

static void setup(unsigned lang) {
    memset(memory,0,sizeof memory);memset(scratchpad,0,sizeof scratchpad);
    memset(bank,0x37,sizeof bank);
    static Asset asset;
    asset=(Asset){.lba=0,.size=8,.raw=bank,.raw_len=2048};
    assets=&asset;asset_count=1;s_profile=eu_profiles+lang;
    w8(s_profile->files+1,2);w32(s_profile->files+4,8);
    w32(0x1f8002a0,126);w32(0x1f80029c,1);
    for(unsigned i=0;i<3;i++) {
        unsigned index=(126+i)&127, desc=0x8009b000+i*32;
        w32(s_profile->queue+index*8,desc);
        w32(s_profile->queue+index*8+4,0x80100000+i*4096);
        w32(desc+16,2);
    }
    writes=dmas=leaves=0;
    fallbacks_at_frame_start=fallbacks;yield_budget=0;
}

int main(void) {
    CPUState cpu={0};
    for(unsigned lang=0;lang<5;lang++) {
        setup(lang);
        assert(install_batch(&cpu));
        assert(dmas==3 && r32(0x1f8002a0)==1 && r8(0x1f8001ce)==1);
        for(unsigned i=0;i<3;i++) assert(!memcmp(ptr(0x80100000+i*4096),bank,2048));
        setup(lang);
        w32(0x8009b020+16,0x80000002u);writes=0;
        assert(!install_batch(&cpu) && !writes && !dmas && !leaves);
        setup(lang);
        w32(s_profile->queue+127*8+4,s_profile->game);writes=0;
        assert(!install_batch(&cpu) && !writes && !dmas && !leaves);
        setup(lang);
        w32(s_profile->queue+127*8+4,s_profile->bodies);writes=0;
        assert(!install_batch(&cpu) && !writes && !dmas && !leaves);
        setup(lang);
        w32(s_profile->queue+127*8+4,s_profile->codec_bit);writes=0;
        assert(!install_batch(&cpu) && !writes && !dmas && !leaves);
        setup(lang);
        w32(s_profile->queue+127*8+4,0x801fd700);writes=0;
        assert(!install_batch(&cpu) && !writes && !dmas && !leaves);
        setup(lang);
        w32(s_profile->queue+127*8+4,0x80040000);writes=0;
        assert(!install_batch(&cpu) && !writes && !dmas && !leaves);
        setup(lang);
        w32(s_profile->queue+127*8+4,s_profile->queue);writes=0;
        assert(!install_batch(&cpu) && !writes && !dmas && !leaves);
        setup(lang);
        for(unsigned i=0;i<64;i++) w8(TOMBI_MAIN_IDENTITY_ADDRESS+i,eu_profiles[lang].fingerprint[i]);
        writes=0;
        assert(identify_profile() && s_profile==eu_profiles+lang);
        assert(!validate_code() && !writes); /* matching language != matching code */
        setup(lang);
        /* Same WVD bounds as the US planner, under each actual EU layout. */
        Asset *asset=(Asset*)assets;
        asset->size=2048;w32(s_profile->files+4,2048);
        memset(bank,0,sizeof bank);
        uint32_t values[][2]={{0,0x100},{4,0x40},{0x40,8},{0x44,40},{0x100,8},{0x104,16}};
        for(unsigned j=0;j<6;j++) {
            unsigned a=values[j][0];uint32_t v=values[j][1];
            for(unsigned k=0;k<4;k++) bank[a+k]=(uint8_t)(v>>(8*k));
        }
        w8(0x8009b003,0x93);w32(s_profile->spu_mode,3);
        for(unsigned j=0;j<75;j++) w32(0x80078530+j*8,0x48250);
        Request request;
        for(unsigned j=0;j<75;j++) {
            w16(0x8009b00e,(uint16_t)j);
            assert(plan_request(126,&request));
        }
        w16(0x8009b00e,75);assert(!plan_request(126,&request));
        w16(0x8009b00e,0);w32(s_profile->spu_mode-12,1);
        assert(!plan_request(126,&request));
        setup(lang);
        w8(0x8009b003,0x10);w32(0x8009b010,0);
        w16(0x8009b00c,32);w16(0x8009b00e,32);
        assert(plan_request(126,&request));
        w16(0x8009b008,1000);assert(!plan_request(126,&request));
        w16(0x8009b008,0);w16(0x8009b00a,500);assert(!plan_request(126,&request));
        w16(0x8009b00a,0);
        w16(0x8009b00c,1025);assert(!plan_request(126,&request));
        setup(lang);
        /* Only the original file-0 system-list extent can replace the GP
         * list window below the executable image's padded end. */
        asset=(Asset*)assets;
        asset->lba=s_profile->list_lba;asset->size=s_profile->list_size;asset->raw_len=8192;
        unsigned lba=asset->lba+150, minute=lba/(75*60), second=lba/75%60, sector=lba%75;
        w8(s_profile->files,(uint8_t)((minute/10)*16+minute%10));
        w8(s_profile->files+1,(uint8_t)((second/10)*16+second%10));
        w8(s_profile->files+2,(uint8_t)((sector/10)*16+sector%10));
        w32(s_profile->files+4,asset->size);
        w8(0x8009b003,0xf8);
        w32(0x1f80029c,127);w32(s_profile->queue+126*8+4,s_profile->list_buffer);
        assert(install_batch(&cpu));
        assert(!memcmp(ptr(s_profile->list_buffer),bank,8192));
        w32(0x1f8002a0,126);w32(s_profile->queue+126*8+4,s_profile->list_buffer+4);
        writes=leaves=0;assert(!install_batch(&cpu) && !writes && !leaves);
        w32(s_profile->queue+126*8+4,s_profile->list_buffer);
        memcpy(ptr(s_profile->files+20*8),ptr(s_profile->files),8);
        w16(0x8009b000,20);writes=leaves=0;
        assert(!install_batch(&cpu) && !writes && !leaves); /* not an allowed list ID */
        w16(0x8009b000,0);diagnostic_cd_lists=1;writes=leaves=0;
        assert(!install_batch(&cpu) && !writes && !leaves); /* controlled real-loader fallback */
        diagnostic_cd_lists=0;
        setup(lang);
        w32(s_profile->queue+126*8+4,s_profile->list_buffer);writes=0;
        assert(!install_batch(&cpu) && !writes && !leaves); /* wrong extent */
        setup(lang);
        w32(0x1f8001d4,0x801fd800);w8(0x1f8001ce,1);
        cpu.gpr[31]=0x800199e8;cpu.gpr[4]=1;
        assert(loading_yield_allowed(&cpu,1,1,7,0));
        assert(!loading_yield_allowed(&cpu,1,1,1,1)); /* running gameplay */
        assert(loading_yield_allowed(&cpu,1,1,4,0)); /* one-shot init */
        assert(!loading_yield_allowed(&cpu,2,2,0,0)); /* original card menu */
        cpu.gpr[31]=0x80012340;assert(!loading_yield_allowed(&cpu,1,1,7,0));
        cpu.gpr[31]=0x800199e8;yield_budget=8;assert(!loading_yield_allowed(&cpu,1,1,7,0));
        yield_budget=0;++fallbacks;assert(!loading_yield_allowed(&cpu,1,1,7,0));
        fallbacks_at_frame_start=fallbacks;w8(0x1f8001ce,0);assert(!loading_yield_allowed(&cpu,1,1,7,0));
        w8(0x1f8001ce,1);w16(0x801fd8e0,1);assert(!loading_yield_allowed(&cpu,1,1,7,0));
        w16(0x801fd8e0,0);w8(0x1f8001cc,1);assert(!loading_yield_allowed(&cpu,1,1,7,0));
        w8(0x1f8001cc,0);w32(0x1f8001d4,0x801fd880);assert(!loading_yield_allowed(&cpu,1,1,7,0));
    }
    puts("PASS: five profiles, atomic batches, memory guards, WVD/VRAM, original system-list window, bounded root-yield acceleration and protected internal waits");
    return 0;
}
