#include "memcard.h"
#include <assert.h>
#include <stdio.h>
#include <string.h>
int main(int argc,char**argv){
 assert(argc==3);unsigned char a[128],b[128],out[128];memset(a,0x31,128);memset(b,0x42,128);
 memcard_init(argv[1]);assert(memcard_write_sector(0,1023,a)==0);memcard_flush(0);
 memcard_init(argv[2]);assert(memcard_read_sector(0,1023,out)==0);assert(memcmp(out,a,128)!=0);
 assert(memcard_write_sector(0,1023,b)==0);memcard_flush(0);
 memcard_init(argv[1]);assert(memcard_read_sector(0,1023,out)==0);assert(memcmp(out,a,128)==0);
 memcard_init(argv[2]);assert(memcard_read_sector(0,1023,out)==0);assert(memcmp(out,b,128)==0);
 puts("PASS: independent card directories, write/flush/reinitialize/read for both regions");return 0;
}
