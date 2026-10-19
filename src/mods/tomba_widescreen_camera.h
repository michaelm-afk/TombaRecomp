#ifndef TOMBA_WIDESCREEN_CAMERA_H
#define TOMBA_WIDESCREEN_CAMERA_H
#include <stdint.h>

/* SCUS-94236: the starting grassland is area 0, sector 0. The camera's
 * follow point is 16.16, with a native left limit in whole world pixels.
 * Return a screen-space origin shift, never a world-camera displacement.
 * Parallax layers must receive the same screen shift as terrain and actors.
 * Use visible reveal, excluding the culling guard/envelope.
 * Other sectors (including centered rooms) keep their original camera. */
static inline int32_t tomba_widescreen_camera_shift(unsigned area,
        unsigned sector, int left, int32_t point, int reveal) {
    if (area != 0 || sector != 0 || reveal <= 0) return 0;
    int64_t available = (int64_t)(point >> 16) - left;
    if (available < 0) available = 0;
    return available < reveal ? (int32_t)(available - reveal) : 0;
}
#endif
