"""Unique original MIPS instruction windows used to nominate relocated sites."""
import struct


def normalize(raw):
    words = list(struct.unpack('<%dI' % (len(raw)//4), raw))
    for n, word in enumerate(words):
        op = word >> 26
        if op in (2, 3): word &= 0xfc000000
        elif op == 15 and 0x8000 <= word & 65535 <= 0x8020: word &= 0xffff0000
        elif op in (9,32,33,34,35,36,37,38,40,41,42,43,46): word &= 0xffff0000
        words[n] = word
    return struct.pack('<%dI' % len(words), *words)


def match_normalized(original, target, at):
    for radius in (16,32,64,128,256):
        needle = original[at-radius:at+radius]
        positions, start = [], 0
        while True:
            pos = target.find(needle, start)
            if pos < 0: break
            if pos % 4 == 0: positions.append(pos+radius)
            start = pos+1
        if len(positions) == 1: return positions[0], radius
    raise ValueError(f'No unique original instruction correspondence at {at:x}')
