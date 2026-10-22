/* New-card creation must never truncate an existing native progress image. */
#include "memcard_format.h"
#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
int main(int argc,char** argv) {
    assert(argc==2);
    char path[4096];
    snprintf(path,sizeof path,"%s/new-card.mcd",argv[1]);
    assert(recompui_memcard_format_file(NULL)==-1);
    assert(recompui_memcard_format_file("")==-1);
    assert(recompui_memcard_format_file(path)==0);
    unsigned char* before=malloc(RECOMPUI_MEMCARD_SIZE);
    unsigned char* after=malloc(RECOMPUI_MEMCARD_SIZE);
    assert(before && after);
    FILE* file=fopen(path,"r+b"); assert(file);
    assert(fread(before,1,RECOMPUI_MEMCARD_SIZE,file)==RECOMPUI_MEMCARD_SIZE);
    assert(before[0]=='M' && before[1]=='C');
    for(unsigned i=0;i<64;i++) {
        unsigned checksum=0;
        for(unsigned j=0;j<128;j++) checksum^=before[i*128+j];
        assert(!checksum);
    }
    before[8192]=0x42; before[8193]=0x19; /* synthetic progress payload */
    rewind(file); assert(fwrite(before,1,RECOMPUI_MEMCARD_SIZE,file)==RECOMPUI_MEMCARD_SIZE);
    assert(fclose(file)==0);
    assert(recompui_memcard_format_file(path)==-1);
    file=fopen(path,"rb"); assert(file);
    assert(fread(after,1,RECOMPUI_MEMCARD_SIZE,file)==RECOMPUI_MEMCARD_SIZE);
    assert(fgetc(file)==EOF); fclose(file);
    assert(!memcmp(before,after,RECOMPUI_MEMCARD_SIZE));
    free(before);free(after);
    puts("PASS: valid blank card created; existing native progress is preserved");
    return 0;
}
