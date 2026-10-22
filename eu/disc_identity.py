"""Derive a five-way language fingerprint from the owner's extracted MAIN files."""
from pathlib import Path

LANGUAGES = ('en', 'fr', 'de', 'it', 'nl')


def main_fingerprints(root: Path, *, disc_dir='disc', languages=None):
    languages = dict(zip(LANGUAGES, range(5))) if languages is None else languages
    bodies = [(root / disc_dir / f'EXE/MAIN{i}.EXE').read_bytes()[2048:]
              for i in languages.values()]
    # Require five distinct fingerprints; a shared startup prefix is useless.
    # The runtime test also requires the selected bytes to remain unchanged.
    for offset in range(0, min(map(len, bodies)) - 64, 16):
        chunks = [body[offset:offset + 64] for body in bodies]
        if len(set(chunks)) == len(languages):
            return offset, dict(zip(languages, chunks))
    raise ValueError('No unique five-language MAIN fingerprint in verified sources')


if __name__ == '__main__':
    import hashlib
    offset, fingerprints = main_fingerprints(Path(__file__).resolve().parents[1])
    print(f'Guest fingerprint address: {0x80010000 + offset:08X}')
    for language, data in fingerprints.items():
        print(language, hashlib.sha256(data).hexdigest())
