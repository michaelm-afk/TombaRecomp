#include "launcher_model.c"
#include <assert.h>
static int route;
static int verify(const char* path,RecompLauncherCDiscVerify* out){(void)path;out->verdict=route<0?3:1;out->profile_handoff=route>0;return 1;}
int main(void){
 static SystemProfile profile;profile.verify.mode=1;
 LauncherModel* m=calloc(1,sizeof(*m));m->profile=&profile;m->disc_verify_cb=verify;m->rom_present=true;
 route=0;run_verify(m);assert(!m->profile_handoff && m->action==LNG_ACTION_NONE);
 route=-1;run_verify(m);assert(!m->profile_handoff && m->verify.verdict==3);
 route=1;run_verify(m);assert(m->profile_handoff && m->action==LNG_ACTION_QUIT);
 free(m);puts("PASS: same profile, invalid disc and verified handoff model transitions");return 0;
}
void launcher_binds_set_zapper(int a,int b){(void)a;(void)b;}
