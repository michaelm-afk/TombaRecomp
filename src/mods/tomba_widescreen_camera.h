#ifndef TOMBA_WIDESCREEN_CAMERA_H
#define TOMBA_WIDESCREEN_CAMERA_H
#include <stdint.h>

/* SCUS-94236: the starting grassland is area 0, sector 0. The camera's
 * follow point is 16.16, with a native left limit in whole world pixels.
 * Return a presentation point; never feed it back into native following.
 * World X and screen X are 1:1 here. Keep the original left edge at the
 * expanded viewport edge; ordinary following takes over beyond that edge.
 * The 32px culling guard is not visible and must not move the camera.
 * Other sectors (including centered rooms) keep their original camera. */
static inline int32_t tomba_widescreen_camera_point(unsigned area,
        unsigned sector, int left, int32_t point, int cull_margin) {
    if (area != 0 || sector != 0 || cull_margin <= 32) return point;
    int64_t minimum = ((int64_t)left + cull_margin - 32) * 65536;
    if (minimum > INT32_MAX) minimum = INT32_MAX;
    return point < minimum ? (int32_t)minimum : point;
}
#endif
