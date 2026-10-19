#include "mod_plugins.h"
#include "cpu_state.h"
#include "tomba_widescreen_hud.h"
#include "tomba_widescreen_sprites.h"
#include "tomba_widescreen_view.h"
#include "tomba_widescreen_camera.h"
#include "tomba_widescreen_scripts.h"

/*
 * Tomba's game-specific widescreen hooks remain part of generated/runtime
 * code, but their player-facing activation belongs to the mod catalog rather
 * than generic recomp-ui Settings.  The renderer is native-wide: it grows the
 * compositor surface and its cull margin, rather than stretching the 320px
 * framebuffer. Start from a 16:9 window, then let Fit follow every resize
 * without an upper aspect-ratio limit. Fixed views use this same renderer.
 */
#define PKG "tomba.enhancement.widescreen"
#define FEATURE "widescreen"
static int tomba_widescreen_enabled;
extern void tomba_widescreen_residency_activate(void);

/* The shared camera builder has assembled its translation vector and camera
 * X, and is about to transform that vector. Anchor those two presentation
 * values together. Leave the native follow point and its velocity untouched,
 * so narrowing the window and moving away from the edge need no recovery. */
static void tomba_widescreen_anchor_camera(CPUState* cpu, uint32_t address) {
    (void)address;
    if (!tomba_widescreen_enabled) return;
    if (cpu->gpr[31] != 0x8002A1E4u || cpu->gpr[4] != 0x1F8000C0u ||
        cpu->gpr[5] != 0x1F800060u || cpu->gpr[6] != 0x1F800068u) return;
    unsigned area = psx_mod_read_half(0x8009BCC8u);
    unsigned sector = psx_mod_read_half(0x8009BCCAu);
    if (area != 0 || sector != 0) return;
    /* Overlay addresses are reused; require the original area-0 handler. */
    if (psx_mod_read_word(0x801168F4u) != 0x27BDFFE8u ||
        psx_mod_read_word(0x801169ECu) != 0x0C00B3BEu) return;
    const uint32_t camera = 0x800A38B8u;
    if (psx_mod_read_byte(camera + 4) != 1) return;
    uint32_t follow = psx_mod_read_word(camera + 0x34);
    if (follow != 0x1F8000ECu) return;
    int32_t original = (int32_t)psx_mod_read_word(follow);
    int left = (int16_t)psx_mod_read_half(camera + 0x2C);
    int32_t anchored = tomba_widescreen_camera_point(area, sector, left,
        original, psx_mod_widescreen_x_margin());
    if (anchored != original) {
        /* SVECTOR X is the negated integer follow point. The guest consumes
         * this temporary vector immediately; no persistent bias is stored. */
        if ((int16_t)psx_mod_read_half(0x1F800060u) !=
                (int16_t)-(original >> 16)) return;
        psx_mod_write_half(0x1F800060u, (uint16_t)-(anchored >> 16));
        psx_mod_write_word(camera + 8,
            psx_mod_read_word(camera + 8) + (uint32_t)(anchored - original));
    }
}

static void tomba_widescreen_tag_hud(CPUState* cpu, uint32_t address) {
    (void)address;
    if (!tomba_widescreen_enabled) return;
    psx_mod_tag_hud_primitive(cpu->gpr[4],
        tomba_hud_edge(cpu->gpr[31], cpu->gpr[29], psx_mod_read_word));
    psx_mod_tag_world_primitive(cpu->gpr[4], tomba_is_world_sprite(cpu->gpr[31]));
}

static void tomba_widescreen_activate(void) {
    char aspect[16];
    tomba_widescreen_enabled = 1;
    tomba_widescreen_residency_activate();
    tomba_widescreen_scripts_activate();
    psx_mod_set_adaptive_backdrop_preload(1);

    if (!psx_mod_option_value(PKG, FEATURE, "aspect", aspect, sizeof aspect))
        strcpy(aspect, "Fit");

    TombaWidescreenView view = tomba_widescreen_view(aspect);
    (void)psx_mod_set_fixed_display_aspect(view.numerator, view.denominator);
    if (view.fit)
        (void)psx_mod_set_adaptive_display_aspect(0u, 0u);
}

PSX_MOD_CONSTRUCTOR(tomba_register_widescreen_plugin) {
    (void)psx_mod_register_function_entry_plugin(
        "tomba.widescreen", 0x800636A4u, tomba_widescreen_anchor_camera);
    (void)psx_mod_register_function_entry_plugin(
        "tomba.widescreen", 0x8005E08Cu, tomba_widescreen_tag_hud);
    (void)psx_mod_register_activation_plugin(
        "tomba.widescreen", tomba_widescreen_activate);
    (void)psx_mod_register_vblank_plugin(
        "tomba.widescreen", tomba_widescreen_scripts_tick);
    (void)psx_mod_register_savestate_plugin(
        "tomba.widescreen", tomba_widescreen_scripts_tick);
}
