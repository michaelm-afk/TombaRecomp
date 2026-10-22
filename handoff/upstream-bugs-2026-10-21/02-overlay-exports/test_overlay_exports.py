"""Run the actual dynamic overlay patcher on synthetic, header-free C."""
import argparse
import ast
from pathlib import Path
import re
import subprocess
import tempfile


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('framework', type=Path)
    ap.add_argument('--cc', help='Optional Clang binary for a Windows syntax check')
    ap.add_argument('--work-dir', type=Path)
    args = ap.parse_args()
    source = (args.framework/'tools/compile_overlays.py').read_text(encoding='utf-8')
    node = next(n for n in ast.parse(source).body if isinstance(n, ast.FunctionDef)
                and n.name == 'patch_generated_c')
    namespace = dict(re=re, DISPATCH_PREAMBLE='')
    exec(compile(ast.Module(body=[node], type_ignores=[]), 'actual-patcher', 'exec'), namespace)
    fixture = '''void func_80010000(CPUState* cpu);
void func_80010004(CPUState* cpu);
void func_80020000(CPUState* cpu);
void func_80010000(CPUState* cpu)
{ func_80010004(cpu); func_80020000(cpu); }
void func_80010004(CPUState* cpu)
{}
'''
    result = namespace['patch_generated_c'](fixture, 0x80010000, 8)
    failures = []
    export = '__attribute__((visibility("default")))\n#endif\n'
    for address in ('80010000', '80010004'):
        signature = f'void func_{address}(CPUState* cpu)'
        if export + signature + ';' not in result: failures.append('missing exported declaration: '+address)
        if export + signature + '\n' not in result: failures.append('missing exported definition: '+address)
    if 'void func_80020000' in result: failures.append('external declaration was retained')
    if 'call_by_address(cpu, 0x80020000u)' not in result: failures.append('external dispatch missing')
    if args.cc:
        if args.work_dir: args.work_dir.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=args.work_dir) as directory:
            path = Path(directory)/'synthetic.c'
            path.write_text('typedef struct CPUState CPUState;\n'
                            'void call_by_address(CPUState*, unsigned);\n'+result)
            checked = subprocess.run([args.cc, '--target=x86_64-w64-windows-gnu',
                '-fsyntax-only', str(path)], text=True, capture_output=True)
            if checked.returncode: failures.append(checked.stderr.strip())
    for failure in failures: print('FAIL:', failure)
    print('FAIL' if failures else 'PASS: declaration/definition exports and external dispatch')
    return bool(failures)


if __name__ == '__main__': raise SystemExit(main())
