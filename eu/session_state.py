"""Read-only EU Rev-1 state profiles derived from the owner's MAIN files."""
from pathlib import Path
import struct

from disc_identity import LANGUAGES, main_fingerprints

GAME_SIZE = 0x988


def profiles(root, *, disc_dir='disc', languages=None):
    languages = dict(zip(LANGUAGES, range(5))) if languages is None else languages
    offset, fingerprints = main_fingerprints(root, disc_dir=disc_dir, languages=languages)
    result = {}
    for language, i in languages.items():
        payload = (Path(root)/disc_dir/f'EXE/MAIN{i}.EXE').read_bytes()[2048:]
        words = struct.unpack('<%dI' % (len(payload)//4), payload)
        candidates = []
        # initGameConfig: saved pointer -> a0, memset(a0, 0, sizeof(GAME)).
        # Validate the MIPS argument construction, not another region's symbols.
        for n, word in enumerate(words):
            if word != 0x24060988 or n < 8:
                continue
            for j in range(n-8, n-2):
                lui, addiu = words[j:j+2]
                reg = (lui >> 16) & 31
                if lui >> 26 != 15 or not reg:
                    continue
                if addiu >> 26 != 9 or (addiu >> 21) & 31 != reg or (addiu >> 16) & 31 != reg:
                    continue
                if ((reg << 21) | 0x2021) not in words[j+2:n]:
                    continue
                lo = (addiu & 0xffff) - (0x10000 if addiu & 0x8000 else 0)
                base = ((lui & 0xffff) << 16) + lo
                if 0x80090000 <= base <= 0x800b0000:
                    candidates.append(base)
        if len(set(candidates)) != 1:
            raise ValueError(f'Unverified GAME address for {language}: {candidates}')
        result[language] = dict(base=candidates[0], fingerprint=fingerprints[language])
    return 0x80010000+offset, result


def decode(game, scratch, task):
    if len(game) != GAME_SIZE or len(scratch) != 64 or len(task) != 8:
        raise ValueError('Incomplete state sample')
    u16 = lambda at: struct.unpack_from('<H', game, at)[0]
    count = u16(0x944)
    if count > 256:
        raise ValueError('GAME not initialized or being replaced')
    return dict(
        area=u16(0), section=u16(2), plane=game[4], spawn=u16(0x22),
        current_area=u16(0x948), current_section=u16(0x94a), current_spawn=u16(0x94c),
        health=game[0x10], lives=game[0x20], progress_state=game[0x94f],
        inventory=list(game[0x844:0x844+count]),
        quests=list(game[0x444:0x544]), items=list(game[0x744:0x844]),
        menu_mode=struct.unpack_from('<H', scratch, 6)[0],
        movie_state=scratch[12], movie_id=scratch[13], load_complete=scratch[14],
        pause_flags=struct.unpack_from('<H', scratch, 0x30)[0],
        task=list(struct.unpack('<4H', task)))


def changes(previous, current):
    events = []
    for key in ('quests', 'items'):
        delta = [dict(index=i, old=a, new=b)
                 for i, (a, b) in enumerate(zip(previous[key], current[key])) if a != b]
        if delta:
            events.append(dict(kind=key+'_changed', changes=delta))
    fields = {k: dict(old=previous[k], new=v) for k, v in current.items()
              if k not in ('quests', 'items') and previous[k] != v}
    if fields:
        kind = 'area_changed' if any(k in fields for k in
            ('area', 'section', 'current_area', 'current_section')) else 'state_changed'
        events.append(dict(kind=kind, changes=fields))
    return events
