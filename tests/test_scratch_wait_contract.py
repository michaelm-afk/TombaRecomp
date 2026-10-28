"""Compare the actual SCUS-94236 scratchpad wait block and load timing."""
import argparse
from pathlib import Path
import re
import subprocess
import tempfile


def function(text, name):
    match = re.search(r'^(?:static inline )?\w+ '+name+r'\([^;]*?\)\s*\{', text, re.M)
    if not match:
        raise ValueError('Missing runtime function '+name)
    depth = 1
    end = match.end()
    while depth:
        depth += (text[end] == '{') - (text[end] == '}')
        end += 1
    return text[match.start():end]


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--framework', type=Path, required=True)
    p.add_argument('--generated', type=Path, required=True)
    p.add_argument('--cc', required=True)
    a = p.parse_args()
    a.framework = a.framework.resolve()
    a.generated = a.generated.resolve()
    blocks = []
    for path in a.generated.glob('*full*.c'):
        text = path.read_text()
        start = text.find('\nblock_80016588:')
        if start >= 0:
            blocks.append(text[start:text.index('\nblock_800165A0:', start)])
    if not blocks:
        print('SKIP: regenerate the supported original executable first')
        return 77
    assert len(blocks) == 1
    memory = (a.framework/'runtime/src/memory.c').read_text()
    with tempfile.TemporaryDirectory(prefix='tomba-scratch-wait-') as temp:
        work = Path(temp)
        (work/'poll.inc').write_text('static void actual_poll(CPUState *cpu) {\n'+blocks[0]+
            '\nblock_800165A0: cpu->pc=0x800165A0u;\n}\n')
        (work/'load.inc').write_text('\n'.join(function(memory, name) for name in
            ('psx_mmio_read_wait', 'psx_cyc_readmem', 'psx_cyc_load_timing',
             'psx_cyc_load_half_slow')))
        exe = work/'poll.exe'
        includes = [work, a.framework/'runtime/include', a.framework/'runtime/tests']
        sources = [Path(__file__).with_name('scratch_wait_contract.c'),
                   a.framework/'runtime/src/psx_cycles.c', a.framework/'runtime/src/psx_icache.c']
        if Path(a.cc).name.lower() in ('cl', 'cl.exe'):
            cmd = [a.cc, '/nologo', '/std:c11', '/O2', '/DPSX_ENABLE_BLOCK_CYCLES=1',
                   '/DPSX_NO_DEBUG_TOOLS=1', *['/I'+str(x) for x in includes],
                   *map(str, sources), '/Fe:'+str(exe)]
        else:
            cmd = [a.cc, '-std=c11', '-O2', '-DPSX_ENABLE_BLOCK_CYCLES=1',
                   '-DPSX_NO_DEBUG_TOOLS=1', *['-I'+str(x) for x in includes],
                   *map(str, sources), '-o', str(exe)]
        subprocess.run(cmd, cwd=work, check=True)
        subprocess.run([str(exe)], cwd=work, check=True, timeout=30)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
