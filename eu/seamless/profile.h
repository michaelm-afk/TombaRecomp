#pragma once
#include <stdint.h>
typedef struct {
    uint32_t queue, files, scratch, alternate, errors, headers, bodies;
    uint32_t codec_bit, codec_flags, spu_mode, spu_address, game, list_buffer, list_lba, list_size;
    uint32_t loader_hash, task_hash, libraries_hash, gpu_hash, open_hash, render_hash, files_hash;
    uint8_t fingerprint[64];
} TombiLoaderProfile;
