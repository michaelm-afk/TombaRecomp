#define STB_IMAGE_IMPLEMENTATION
#define STBI_ONLY_PNG
#define STBI_ONLY_JPEG
#define STBI_NO_STDIO
#include "../../psxrecomp/runtime/third_party/stb_image.h"
#include "gpu_hd_textures.h"
#include <cstdio>
int main(int argc,char**argv){if(argc!=3)return 2;char root[4096]{},status[2048]{};int ok=gpu_hd_textures_validate_install(argv[1],argv[2],root,sizeof root,status,sizeof status);std::printf("%s\n%s\n",status,root);return ok?0:1;}
