#include "mod_plugins.h"
#include <stdio.h>

/*
 * Compatibility tombstones: old installed manifests/state.toml can still name
 * these IDs. Never let them restore temporal blending or force VSync off.
 * Keep registration so upgrades do not invalidate the other selected mods.
 * Tomba has no qualified geometry-interpolation implementation yet.
 */
static void tomba_frame_rate_set(unsigned frames_per_second) {
    (void)frames_per_second;
    fprintf(stderr, "Tomba: temporal frame blending is disabled; using stock frames\n");
}

static void tomba_frame_rate_60_activate(void) {
    tomba_frame_rate_set(60u);
}

static void tomba_frame_rate_120_activate(void) {
    tomba_frame_rate_set(120u);
}

static void tomba_frame_rate_144_activate(void) {
    tomba_frame_rate_set(144u);
}

static void tomba_frame_rate_165_activate(void) {
    tomba_frame_rate_set(165u);
}

static void tomba_frame_rate_display_activate(void) {
    tomba_frame_rate_set(0u);
}

PSX_MOD_CONSTRUCTOR(tomba_register_frame_interpolation_plugin) {
    (void)psx_mod_register_activation_plugin(
        "tomba.framerate.60", tomba_frame_rate_60_activate);
    (void)psx_mod_register_activation_plugin(
        "tomba.framerate.120", tomba_frame_rate_120_activate);
    (void)psx_mod_register_activation_plugin(
        "tomba.framerate.144", tomba_frame_rate_144_activate);
    (void)psx_mod_register_activation_plugin(
        "tomba.framerate.165", tomba_frame_rate_165_activate);
    (void)psx_mod_register_activation_plugin(
        "tomba.framerate.uncapped", tomba_frame_rate_display_activate);
}
