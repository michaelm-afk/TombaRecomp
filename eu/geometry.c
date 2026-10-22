/* EU MAIN overlay adapter for the shared, original Tomba geometry HLE.
 * No US disc, GP, game-state pointer or generated game code is embedded. */
#define TOMBA_GEOMETRY_Y_LIMIT 256u
#define TOMBA_GEOMETRY_FLAT_PC 0x800223F8u
#define TOMBA_GEOMETRY_TRI_PC 0x800226CCu
#define TOMBA_GEOMETRY_QUAD_PC 0x800228D4u
#define TOMBA_GEOMETRY_FLAT_LAST_PC 0x8002243Cu
#define TOMBA_GEOMETRY_QUAD_LAST_PC 0x80022918u
#define func_80024EEC tombi_geometry_hle_0
#define func_800251C0 tombi_geometry_hle_1
#define func_800253C8 tombi_geometry_hle_2
#define tomba_lle_func_80024EEC tombi_geometry_lle_0
#define tomba_lle_func_800251C0 tombi_geometry_lle_1
#define tomba_lle_func_800253C8 tombi_geometry_lle_2
#include "../src/hle/tomba_geometry_hle.c"
#include "eu_geometry_profile.inc"

static int eu_geometry_filter(CPUState *cpu, uint32_t address) {
    psx_mod_counter_add("tombi.geometry.entries",1);
    unsigned kind;
    for (kind=0;kind<3;kind++)
        if ((address&0x1fffffffu)==(eu_geometry_profile[kind].pc&0x1fffffffu)) break;
    if (kind==3 || (cpu->pc && cpu->pc!=address)) {
        psx_mod_counter_add("tombi.geometry.interior",1);return 0;
    }
    /* Full live body, not a shared first-instruction guess. Unknown overlays
     * and modified code always retain the original implementation. */
    uint32_t hash=2166136261u;
    for (uint32_t offset=0;offset<eu_geometry_profile[kind].size;offset+=4) {
        uint32_t word=psx_mod_read_word(eu_geometry_profile[kind].pc+offset);
        for (unsigned byte=0;byte<4;byte++) {
            hash=(hash^(word&255u))*16777619u;word>>=8;
        }
    }
    if (hash!=eu_geometry_profile[kind].hash) {
        psx_mod_counter_add("tombi.geometry.unverified_entry",1);return 0;
    }
    cpu->pc=0;
    void (*batch[])(CPUState*)={tombi_geometry_hle_0,tombi_geometry_hle_1,tombi_geometry_hle_2};
    batch[kind](cpu);
    psx_mod_counter_add(kind==0 ? "tombi.geometry.flat" : kind==1 ? "tombi.geometry.triangle" : "tombi.geometry.quad",1);
    return 1;
}
static void eu_geometry_activate(void) {
    fprintf(stdout,"EU geometry: verified PAL batches enabled%s\n",
#ifdef TOMBA_GEOMETRY_VALIDATE
        " (local differential validation)"
#else
        ""
#endif
    );
    fflush(stdout);
}
PSX_MOD_CONSTRUCTOR(tombi_register_geometry) {
    psx_mod_register_activation_plugin("tombi.geometry",eu_geometry_activate);
    for (unsigned i=0;i<3;i++)
        psx_mod_register_function_filter_plugin("tombi.geometry",eu_geometry_profile[i].pc,eu_geometry_filter);
}
