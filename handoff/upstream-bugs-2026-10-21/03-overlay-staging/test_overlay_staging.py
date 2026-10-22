"""Exercise the actual stage function with hashes, synthetic bytes and locked writes."""
import argparse
import ast
import hashlib
import json
from pathlib import Path
import shutil
import tempfile
from types import SimpleNamespace
from unittest.mock import patch


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('framework', type=Path)
    ap.add_argument('--work-dir', type=Path)
    args = ap.parse_args()
    source = (args.framework/'tools/aot_overlay_pipeline.py').read_text(encoding='utf-8')
    node = next(n for n in ast.parse(source).body if isinstance(n, ast.FunctionDef) and n.name == 'stage')
    def require(condition, message):
        if not condition: raise ValueError(message)
    digest = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
    ns = dict(Path=Path, shutil=shutil, compiler=SimpleNamespace(cache_arch_abi=lambda:'test-abi'),
              require=require, digest=digest,
              write_json=lambda p,v:p.write_text(json.dumps(v)))
    exec(compile(ast.Module(body=[node], type_ignores=[]), 'actual-stage', 'exec'), ns)
    stage = ns['stage']
    if args.work_dir: args.work_dir.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=args.work_dir) as directory:
        root = Path(directory)
        cache = root/'cache'; target = root/'target'
        source_leaf = cache/'TEST/gcc/test-abi/cg'
        source_leaf.mkdir(parents=True)
        name = '00010000_12345678.dll'
        (source_leaf/name).write_bytes(b'synthetic non-executable DLL fixture')
        (source_leaf/Path(name).with_suffix('.ranges')).write_bytes(b'synthetic manifest')
        receipt = dict(game_id='TEST', cache_tag='cg', pairs=[dict(dll=name,
            dll_sha256=digest(source_leaf/name),
            manifest_sha256=digest(source_leaf/Path(name).with_suffix('.ranges')))])
        stage(cache,target,receipt)
        with patch.object(shutil,'copy2',side_effect=PermissionError('simulated mapped DLL')):
            try: stage(cache,target,receipt)
            except PermissionError:
                print('FAIL: identical audited target was unnecessarily replaced')
                return 1
            target_file = target/'cache/TEST/gcc/test-abi/cg'/name
            target_file.write_bytes(b'different destination')
            try: stage(cache,target,receipt)
            except PermissionError: pass
            else: raise AssertionError('Changed targets must still be copied')
        (source_leaf/name).write_bytes(b'changed after audit')
        try: stage(cache,target,receipt)
        except ValueError as exc: assert 'Audited artifact changed' in str(exc)
        else: raise AssertionError('Changed source was accepted')
        (source_leaf/name).write_bytes(b'synthetic non-executable DLL fixture')
        stage(cache,target,receipt)
        (target_file.parent/'unaudited.extra').write_bytes(b'extra')
        try: stage(cache,target,receipt)
        except ValueError as exc: assert 'unaudited' in str(exc)
        else: raise AssertionError('Extra file was accepted')
    print('PASS: identical locked targets, changed targets and audit boundaries')
    return 0


if __name__ == '__main__': raise SystemExit(main())
