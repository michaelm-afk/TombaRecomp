"""Recompile original EU MAIN images with opt-in native entry filters.

Everything is emitted into the separate seamless workspace from original-disc
recipes. Memory cards and the baseline cache/executable are not modified.
"""
import argparse
import json
import os
import re
from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'eu'))
from toolchain import executable
sys.path.insert(0, str(ROOT/'psxrecomp/tools'))
import aot_overlay_pipeline as pipeline


def clear_abi_memos(destination, receipt):
    """Discard only runtime ABI-check memos in this isolated target cache."""
    destination=Path(destination).resolve()
    assert destination == (ROOT/'build-eu-seamless/native').resolve()
    namespace=destination/'cache'/receipt['game_id']/'gcc'/pipeline.compiler.cache_arch_abi()/receipt['cache_tag']
    assert namespace.resolve().is_relative_to(destination)
    if namespace.is_dir():
        for marker in namespace.iterdir():
            if marker.is_file() and re.fullmatch(r'\.abi_[0-9a-fA-F]{8}\.ok',marker.name):
                marker.unlink()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--scope', choices=('startup', 'opening', 'full'), default='opening')
    parser.add_argument('--workers', type=int, default=2)
    args = parser.parse_args()
    if args.workers < 1:
        parser.error('--workers must be positive')
    os.environ.pop('PYTHONPATH', None)
    os.environ.pop('PYTHONHOME', None)
    work = ROOT/'build-eu-seamless/hook-aot'
    # A completed workspace is deliberately reused only through re-auditing.
    inventory_path = ROOT/f'build-eu-prototype/aot-{args.scope}/runtime-input-inventory.json'
    inventory = json.loads(inventory_path.read_text())
    # Render funnels and backdrop builders also live in area overlays.
    # Every recipe needs the same widescreen substitutions as MAIN.
    selected = inventory['jobs']
    assert len([job for job in selected if '-EXE/MAIN' in job['name']]) == 5
    config = ROOT/'eu/seamless/game.toml'
    recompiler = ROOT/'build-eu-tools/psxrecomp-game.exe'
    tag = pipeline.compiler.cache_tag(str(ROOT/'psxrecomp/runtime/include'),str(recompiler),str(config),0)
    cache = work/'cache'
    previous = json.loads((work/'audit.json').read_text()) if (work/'audit.json').is_file() else {}
    if (not (cache/'SCES-01330/gcc/win-x64'/tag).is_dir()
            or previous.get('aot_scope') != args.scope):
        # pipeline.build requires a new directory; a failed attempt is retained
        # for diagnosis and the next attempt gets its own workspace.
        import tempfile
        work.mkdir(parents=True, exist_ok=True)
        attempt = Path(tempfile.mkdtemp(prefix='attempt-',dir=work))
        cache = pipeline.build(dict(inventory, jobs=selected), config, recompiler,
            attempt, executable('clang.exe'),
            args.workers, project_root=ROOT)
        shutil.copytree(cache,work/'cache',dirs_exist_ok=True)
        cache = work/'cache'
        (work/'compiled.ok').write_text('all selected MAIN and area images\n')
    # Never relabel a baseline DLL into this namespace: every area may contain
    # PAL render funnels even when it has no explicit mod entry address.
    receipt = pipeline.audit(config, recompiler, cache, inventory_path, work/'audit.json')
    receipt['aot_scope'] = args.scope
    receipt['required_images'] = inventory['required_images']
    (work/'audit.json').write_text(json.dumps(receipt, indent=2)+'\n')
    clear_abi_memos(ROOT/'build-eu-seamless/native',receipt)
    pipeline.stage(cache, ROOT/'build-eu-seamless/native', receipt)
    print('PASS: isolated native entry-filter cache audited and staged', flush=True)


if __name__ == '__main__':
    main()
