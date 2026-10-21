#include <SDL3/SDL.h>
#include "psx_controller_type.h"
#include <cstdio>

/* SDL-local virtual pads only. Discard device events deliberately: recovery
 * must still notice an obsolete handle and permit a later reconnect. */
int main() {
    if (!SDL_Init(SDL_INIT_GAMEPAD)) return 1;
    SDL_VirtualJoystickDesc desc;
    SDL_INIT_INTERFACE(&desc);
    desc.type = SDL_JOYSTICK_TYPE_GAMEPAD;
    desc.naxes = SDL_GAMEPAD_AXIS_COUNT;
    desc.nbuttons = SDL_GAMEPAD_BUTTON_COUNT;
    desc.name = "Tombi reconnect regression";
    const auto first = SDL_AttachVirtualJoystick(&desc);
    SDL_Gamepad* pad = SDL_OpenGamepad(first);
    if (!first || !pad || !SDL_GamepadConnected(pad)) return 2;
    if (psx_controller_recovery_needed(true, true, true, 1000, 0)) return 3;
    if (!SDL_DetachVirtualJoystick(first)) return 4;
    SDL_PumpEvents();
    SDL_FlushEvents(SDL_EVENT_FIRST, SDL_EVENT_LAST);
    if (!psx_controller_recovery_needed(true, true, SDL_GamepadConnected(pad), 1001, 0)) return 5;
    SDL_CloseGamepad(pad);
    if (psx_controller_recovery_needed(true, false, false, 1100, 1001)) return 6;
    const auto second = SDL_AttachVirtualJoystick(&desc);
    SDL_PumpEvents();
    SDL_FlushEvents(SDL_EVENT_FIRST, SDL_EVENT_LAST);
    if (!psx_controller_recovery_needed(true, false, false, 1501, 1001)) return 7;
    pad = SDL_OpenGamepad(second);
    if (!second || second == first || !pad || !SDL_GamepadConnected(pad)) return 8;
    if (psx_controller_recovery_needed(true, true, true, 1502, 1501)) return 9;
    SDL_CloseGamepad(pad);
    SDL_DetachVirtualJoystick(second);
    SDL_Quit();
    std::puts("PASS: SDL virtual disconnect/reconnect with discarded hotplug events, new instance and bounded retry");
    return 0;
}
