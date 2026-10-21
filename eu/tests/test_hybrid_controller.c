#include "mod_plugins.h"
#include <assert.h>
#include <string.h>

static void (*activate)(void);
static PSXModControllerPresentationCallback policy;

int psx_mod_register_activation_plugin(const char *id, void (*callback)(void)) {
    assert(strcmp(id, "tomba.hybrid-controller") == 0);
    activate = callback;
    return 1;
}

int psx_mod_set_controller_presentation_policy(uint32_t player,
    PSXModControllerPresentationCallback callback, uint32_t initial, int capable) {
    assert(player == 0 && initial == PSX_MOD_CONTROLLER_ANALOG && capable == 1);
    policy = callback;
    return 1;
}

int main(void) {
    assert(activate);
    activate();
    assert(policy);
    PSXModControllerInput input = {0};
    assert(policy(&input) == PSX_MOD_CONTROLLER_ANALOG);
    input.dpad_active = 1;
    assert(policy(&input) == PSX_MOD_CONTROLLER_DIGITAL);
    input.dpad_active = 0;
    assert(policy(&input) == PSX_MOD_CONTROLLER_DIGITAL);
    input.stick_active = 1;
    assert(policy(&input) == PSX_MOD_CONTROLLER_ANALOG);
    input.dpad_active = 1;
    assert(policy(&input) == PSX_MOD_CONTROLLER_ANALOG);
    activate();
    assert(policy(0) == PSX_MOD_CONTROLLER_ANALOG);
    return 0;
}
