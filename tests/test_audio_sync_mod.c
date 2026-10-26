#ifdef NDEBUG
#undef NDEBUG
#endif
#include "audio_sync.h"
#include "mod_plugins.h"
#include <assert.h>
#include <stdio.h>
#include <string.h>
static PSXModActivationCallback activate;
static const char *option;
int psx_mod_register_activation_plugin(const char *id,PSXModActivationCallback fn) {
    assert(!strcmp(id,"psx.low-latency-audio")); activate=fn; return 1;
}
int psx_mod_option_value(const char *pkg,const char *feature,const char *id,char *out,uint32_t size) {
    assert(!strcmp(pkg,"psx.audio.low-latency"));
    assert(!strcmp(feature,"low-latency-audio")); assert(!strcmp(id,"target_ms"));
    if(!option || strlen(option)>=size)return 0;
    strcpy(out,option);return 1;
}
int main(void) {
    assert(activate);
    psx_audio_sync_set_enabled(0);assert(psx_audio_sync_target(180)==180);assert(!psx_audio_sync_enabled());
    option="80";activate();assert(psx_audio_sync_enabled());assert(psx_audio_sync_target(180)==80);
    option="40";activate();assert(psx_audio_sync_target(180)==80);
    option="60";activate();assert(psx_audio_sync_target(180)==80);
    option="70";activate();assert(psx_audio_sync_target(180)==80);
    option="120";activate();assert(psx_audio_sync_target(180)==80);
    option="180";activate();assert(psx_audio_sync_target(180)==80);
    psx_audio_sync_set_enabled(0);assert(psx_audio_sync_target(180)==180);assert(!psx_audio_sync_enabled());
    /* A configured fallback is never overwritten merely by disabling the mod. */
    assert(psx_audio_sync_target(160)==160);
    option=NULL;activate();assert(psx_audio_sync_target(180)==80);
    option="80oops";activate();assert(psx_audio_sync_target(180)==80);
    option="999999999999999999999999999999";activate();assert(psx_audio_sync_target(180)==80);
    option="-1";activate();assert(psx_audio_sync_target(180)==80);
    option="999";activate();assert(psx_audio_sync_target(180)==80);
    psx_audio_sync_set_enabled(0);assert(psx_audio_sync_target(180)==180);assert(!psx_audio_sync_enabled());
    puts("PASS fixed80ms activation, legacy option values ignored, reset and configured OFF fallback");
}
