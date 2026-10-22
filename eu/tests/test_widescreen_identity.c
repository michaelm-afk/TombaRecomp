/* Real PAL profile selector against owned MAIN files, including bad input. */
#ifdef NDEBUG
#undef NDEBUG
#endif
#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "eu_widescreen.h"

static unsigned char image[1024*1024];
static size_t image_size;
static int started;
int psx_mod_game_started(void) { return started; }
uint32_t psx_mod_read_word(uint32_t pc) {
    size_t at = pc-0x80010000u+2048;
    assert(at+4 <= image_size);
    return (uint32_t)image[at] | (uint32_t)image[at+1]<<8 |
           (uint32_t)image[at+2]<<16 | (uint32_t)image[at+3]<<24;
}
int main(int argc, char **argv) {
    assert(argc==2);
    for (unsigned language=0; language<5; ++language) {
        char path[4096];
        snprintf(path,sizeof path,"%s/EXE/MAIN%u.EXE",argv[1],language);
        FILE *file=fopen(path,"rb"); assert(file);
        image_size=fread(image,1,sizeof image,file); assert(!ferror(file)); fclose(file);
        started=0; assert(!eu_ws_refresh()); assert(!eu_ws_address(0x8009bcc8u));
        started=1; assert(eu_ws_refresh());
        uint32_t original=psx_mod_read_word(0x80017848u);
        uint32_t game=0x800a0000u+(int16_t)original;
        assert(eu_ws_address(0x8009bcc8u)==game);
        assert(eu_ws_address(0x8009bccau)==game+2);
        assert(eu_ws_address(0x800a38b8u)==game+0x7bf0u);
        /* Corrupt every candidate identity so no prior language can survive. */
        memset(image+2048,0,image_size-2048);
        assert(!eu_ws_refresh()); assert(!eu_ws_address(0x800a5970u));
    }
    puts("PASS: PAL profile/language replacement, pre-game and unknown-image rejection");
}
