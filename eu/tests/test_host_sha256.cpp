#include "host_sha256.h"
#include "psx_sha256.h"
#include <vector>
#include <array>
#include <cassert>
#include <cstdio>
#include <cstring>
#include <chrono>
int main(int argc,char**argv) {
 for(size_t n:{0u,1u,55u,56u,63u,64u,65u,4096u,1048577u}) {
  std::vector<uint8_t> bytes(n);for(size_t i=0;i<n;++i)bytes[i]=uint8_t(i*71+17);
  std::array<uint8_t,32>a{},b{};psx_sha256_compute(bytes.data(),n,a.data());
  if(n==0){char hex[65]{};for(size_t i=0;i<32;++i)std::snprintf(hex+i*2,3,"%02x",unsigned(a[i]));assert(std::strcmp(hex,"e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855")==0);}
#if defined(_WIN32) && !defined(PSX_DISABLE_NATIVE_SHA256)
  assert(PSXRecompV4::host_sha256_bytes(bytes.data(),n,b.data()));assert(a==b);
  PSXRecompV4::HostSha256 chunks;
  for(size_t offset=0;offset<n;){size_t take=std::min<size_t>(37,n-offset);assert(chunks.update(bytes.data()+offset,take));offset+=take;}
  assert(chunks.finish(b.data()));assert(a==b);
#else
  assert(!PSXRecompV4::host_sha256_bytes(bytes.data(),n,b.data()));
#endif
 }
 if(argc==2){std::array<uint8_t,32> digest{};auto t=std::chrono::steady_clock::now();assert(PSXRecompV4::host_sha256_file(std::filesystem::u8path(argv[1]),digest.data()));
  for(auto b:digest)std::printf("%02x",unsigned(b));std::printf(" %.6f seconds\n",std::chrono::duration<double>(std::chrono::steady_clock::now()-t).count());}
 std::puts("PASS: native SHA-256 equals portable SHA-256, boundary sizes and fragmented updates");
}
