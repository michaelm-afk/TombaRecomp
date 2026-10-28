/* Retail instructions are extracted privately by test_scratch_wait_contract.py. */
#define main shared_detector_fixture_main
#include "test_idle_skip_store_counter.c"
#undef main
#include <stdlib.h>
#include "psx_icache.h"

uint32_t g_debug_last_store_pc;
volatile uint32_t g_psx_last_fn_entry;
int g_psx_precise_slice=0, g_psx_load_delay=1;
volatile int g_ds_recording=0;
uint8_t *g_psx_ram;
uint32_t g_psx_ram_mask=0x1FFFFFu;
int psx_load_delay_enabled(void) { return 1; }
int psx_slice_block_impl(CPUState *c,uint32_t p,uint32_t n,int e) {
    (void)c;(void)p;(void)n;(void)e;abort();
}
uint16_t psx_read_half(uint32_t addr) {
    if (addr != 0x1F8001E8u) abort();
    return (uint16_t)s_counter;
}
static inline void psx_load_charge_cycles(uint32_t cycles) { psx_cpu_charge(cycles); }
#include "load.inc"
static uint32_t deliveries;
void psx_check_interrupts_at(CPUState *cpu,uint32_t pc) {
    psx_cyc_batch_flush();
    psx_idle_note_check(cpu,pc);
    if (!deliveries && psx_get_cycle_count()>=s_event_at) { s_counter++;deliveries++; }
}
#include "poll.inc"

typedef struct Result {
    uint32_t regs[32],hi,lo,pc,counter,events;
    uint8_t absorb[33],which,ld,ld_absorb,fudge;
    uint64_t cycles,skips;
} Result;
static Result actual_run(int native,uint16_t initial,uint16_t target,
                         uint32_t event,uint32_t scale,uint32_t warm) {
    CPUState cpu={0};
    for(int i=1;i<32;i++)cpu.gpr[i]=0x13570000u+(uint32_t)i;
    cpu.gpr[3]=target;cpu.ld_which_t=cpu.read_fudge=0x20;
    psx_cycles_reset_for_boot();psx_cycles_resync_after_restore(&cpu);psx_icache_reset();
    psx_guest_cycle_scale_set(scale);g_psx_gcs_frac=0;
    g_idle_skip_enabled=native;g_idle_skip_ext=native;
    g_idle_skip_count=0;g_guest_store_count=g_mmio_access_count=0;
    const uint32_t site=0x80016588u;
    psx_idle_skip_set_store_counter_sites(&site,1);
    psx_idle_skip_set_host_writer(host_write);
    psx_idle_skip_set_store_tracker(&g_psx_track_last_store,&g_guest_last_store_addr,&g_guest_last_store_val);
    psx_idle_skip_set_audited_only(native);
    s_event_at=event;s_counter=initial;deliveries=0;
    if(warm)psx_advance_cycles(warm);
    actual_poll(&cpu);
    Result r={0};memcpy(r.regs,cpu.gpr,sizeof r.regs);
    r.hi=cpu.hi;r.lo=cpu.lo;r.pc=cpu.pc;r.counter=s_counter;r.events=deliveries;
    memcpy(r.absorb,cpu.read_absorb,sizeof r.absorb);
    r.which=cpu.read_absorb_which;r.ld=cpu.ld_which_t;r.ld_absorb=cpu.ld_absorb;r.fudge=cpu.read_fudge;
    r.cycles=psx_get_cycle_count();r.skips=g_idle_skip_count;
    if(native && g_psx_track_last_store)abort();
    return r;
}
int main(void) {
    unsigned cases=0,accelerated=0;
    const uint32_t events[]={1,127,4096,200003};
    for(uint32_t scale=1;scale<=2;scale++)for(uint32_t warm=0;warm<=3;warm++)
    for(unsigned j=0;j<sizeof events/sizeof *events;j++) {
        Result a=actual_run(0,10,11,events[j],scale,warm);
        Result b=actual_run(1,10,11,events[j],scale,warm);
        uint64_t skipped=b.skips;a.skips=b.skips=0;
        if(memcmp(&a,&b,sizeof a)) {
            fprintf(stderr,"poll mismatch event=%u scale=%u warm=%u cycles=%llu/%llu\n",
                events[j],scale,warm,(unsigned long long)a.cycles,(unsigned long long)b.cycles);
            return 1;
        }
        cases++;if(skipped)accelerated++;
    }
    if(!accelerated)return 1;
    printf("PASS: %u actual scratch-wait comparisons; %u accelerated; exact GPR/pipeline/continuation/event/cycle outputs\n",cases,accelerated);
    return 0;
}
