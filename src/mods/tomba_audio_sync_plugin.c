/* Host output policy only; shared by the official regional players. */
#include "audio_sync.h"
#include "mod_plugins.h"
static void activate_audio_sync(void) { psx_audio_sync_set_enabled(1); }
PSX_MOD_CONSTRUCTOR(tomba_register_audio_sync_plugin) {
    (void)psx_mod_register_activation_plugin("psx.low-latency-audio", activate_audio_sync);
}
