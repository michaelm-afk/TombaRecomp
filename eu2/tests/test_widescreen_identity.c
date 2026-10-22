/* Original MAIN selection, language replacement and real PAL HUD return sites. */
#ifdef NDEBUG
#undef NDEBUG
#endif
#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include "eu_widescreen.h"
#include "tomba_widescreen_hud.h"
#include "tomba_widescreen_sprites.h"

static unsigned char image[1024*1024];
static size_t image_size;
static int started;
static uint32_t registered[8];
static unsigned registrations;
int psx_mod_game_started(void) { return started; }
uint32_t psx_mod_read_word(uint32_t pc) {
    size_t at = pc-0x80010000u+2048;
    assert(at+4 <= image_size);
    return (uint32_t)image[at] | (uint32_t)image[at+1]<<8 |
           (uint32_t)image[at+2]<<16 | (uint32_t)image[at+3]<<24;
}
static void write_word(uint32_t pc, uint32_t value) {
    size_t at = pc-0x80010000u+2048;
    assert(at+4 <= image_size);
    for (unsigned i=0;i<4;i++) image[at+i]=(unsigned char)(value>>(8*i));
}
int psx_mod_register_function_entry_plugin(
    const char* id,uint32_t pc,PSXModFunctionEntryCallback callback) {
    (void)id;(void)callback;
    assert(registrations<8); registered[registrations++]=pc; return 1;
}
static void unused(CPUState* cpu,uint32_t pc) { (void)cpu;(void)pc; }
static uint32_t field(uint32_t pc) {
    uint32_t high=psx_mod_read_word(pc-4), low=psx_mod_read_word(pc);
    assert(high>>26==15 && (high>>16&31)==(low>>21&31));
    return ((high&65535u)<<16)+(int16_t)low;
}
int main(int argc,char** argv) {
    assert(argc==2 || argc==3);
    /* Registration runs before MAIN exists and covers distinct entries once. */
    eu_ws_register_entry("test",0x8005e08cu,unused);
    assert(registrations==2);
    assert((registered[0]==0x8005e630u && registered[1]==0x8005e618u) ||
           (registered[1]==0x8005e630u && registered[0]==0x8005e618u));
    const unsigned mains[5]={0,5,6,7,8};
    for (unsigned language=0;language<5;language++) {
        char path[4096];
        snprintf(path,sizeof path,"%s/EXE/MAIN%u.EXE",argv[1],mains[language]);
        FILE* file=fopen(path,"rb"); assert(file);
        image_size=fread(image,1,sizeof image,file); assert(!ferror(file)); fclose(file);
        started=0; assert(!eu_ws_refresh()); assert(!eu_ws_address(0x8009bcc8u));
        started=1; assert(eu_ws_refresh());
        /* Derive fields from original LUI/low instructions, independently of
         * the generated table. These early sites are common across EU2 MAINs. */
        assert(eu_ws_address(0x8009bcc8u)==field(0x80017848u));
        assert(eu_ws_address(0x8009bccau)==field(0x80017848u)+2);
        assert(eu_ws_address(0x800a38b8u)==field(0x80017e1cu));
        assert(!eu_ws_address(0x80001234u));
        const unsigned spanish=language==1;
        const uint32_t shade=spanish?0x8005e618u:0x8005e630u;
        assert(eu_ws_address(0x8005e08cu)==shade);
        const uint32_t ap=spanish?0x80058aa8u:0x80058ac0u;
        const uint32_t parent=spanish?0x8005874cu:0x80058764u;
        const uint32_t sp=0x80090000u;
        write_word(sp+0x2c,parent);
        assert(tomba_hud_edge(ap,sp,psx_mod_read_word)==1);
        write_word(sp+0x2c,parent+4);
        assert(!tomba_hud_edge(ap,sp,psx_mod_read_word));
        /* The other language's return address must not tag a primitive. */
        write_word(sp+0x2c,parent);
        assert(!tomba_hud_edge(spanish?0x80058ac0u:0x80058aa8u,sp,psx_mod_read_word));
        write_word(sp+0x2c,0x8004e4d4u);
        assert(!tomba_hud_edge(0x8004e830u,sp,psx_mod_read_word));
        const uint32_t world=spanish?0x800543b4u:0x800543ccu;
        assert(tomba_is_world_sprite(world));
        assert(!tomba_is_world_sprite(ap));
        assert(!tomba_is_world_sprite(0x8004a170u));
        /* A replaced or corrupt MAIN must clear the prior language mapping. */
        memset(image+2048,0,image_size-2048);
        assert(!eu_ws_refresh()); assert(!eu_ws_address(0x800a5970u));
        assert(!eu_ws_code_key(ap));
        assert(!tomba_hud_edge(ap,sp,psx_mod_read_word));
    }
    if(argc==3) {
        /* The other PAL group's real MAINs are also unsupported here. */
        for(unsigned language=0;language<5;language++) {
            char path[4096];
            snprintf(path,sizeof path,"%s/EXE/MAIN%u.EXE",argv[2],language);
            FILE* file=fopen(path,"rb"); assert(file);
            image_size=fread(image,1,sizeof image,file); assert(!ferror(file)); fclose(file);
            started=1; assert(!eu_ws_refresh()); assert(!eu_ws_address(0x8009bcc8u));
        }
    }
    puts("PASS: original EU2 language/field/HUD bindings, registration and foreign/unknown-image rejection");
    return 0;
}
