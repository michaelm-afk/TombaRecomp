#include "mod_plugins.h"
#include <stdio.h>
#include <string.h>

/* Link the real compatibility callbacks. Any call to an interpolation setter
 * is a link failure: stale installed manifests must have no such route. */
static unsigned count;
static PSXModActivationCallback callbacks[5];
int psx_mod_register_activation_plugin(const char* id, PSXModActivationCallback cb) {
    static const char* ids[] = {"tomba.framerate.60", "tomba.framerate.120",
        "tomba.framerate.144", "tomba.framerate.165", "tomba.framerate.uncapped"};
    if (count >= 5 || strcmp(id, ids[count]) != 0 || !cb) return 0;
    callbacks[count++] = cb;
    return 1;
}
int main(void) {
    if (count != 5) return 1;
    for (unsigned i = 0; i < count; ++i) callbacks[i]();
    puts("all five legacy frame-blending activations are inert");
    return 0;
}
