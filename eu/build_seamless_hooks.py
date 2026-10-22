"""Recompile original EU MAIN images with opt-in native entry filters.

Everything is emitted into the separate seamless workspace. The baseline
cache, executable and memory cards are read-only inputs.
"""
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
    os.environ.pop('PYTHONPATH', None)
    os.environ.pop('PYTHONHOME', None)
    work = ROOT/'build-eu-seamless/hook-aot'
    # A completed workspace is deliberately reused only through re-auditing.
    inventory_path = ROOT/'build-eu-prototype/aot-opening/runtime-input-inventory.json'
    inventory = json.loads(inventory_path.read_text())
    selected = [job for job in inventory['jobs'] if '-EXE/MAIN' in job['name']]
    assert len(selected) == 5
    config = ROOT/'eu/seamless/game.toml'
    recompiler = ROOT/'build-eu-tools/psxrecomp-game.exe'
    tag = pipeline.compiler.cache_tag(str(ROOT/'psxrecomp/runtime/include'),str(recompiler),str(config),0)
    cache = work/'cache'
    if not (cache/'SCES-01330/gcc/win-x64'/tag).is_dir():
        # pipeline.build requires a new directory; a failed attempt is retained
        # for diagnosis and the next attempt gets its own workspace.
        import tempfile
        work.mkdir(parents=True, exist_ok=True)
        attempt = Path(tempfile.mkdtemp(prefix='attempt-',dir=work))
        cache = pipeline.build(dict(inventory, jobs=selected), config, recompiler,
            attempt, executable('clang.exe'),
            2, project_root=ROOT)
        shutil.copytree(cache,work/'cache',dirs_exist_ok=True)
        cache = work/'cache'
        (work/'compiled.ok').write_text('five MAIN images\n')
    baseline = ROOT/'build-eu-prototype/native/cache'
    original = pipeline.audit(ROOT/'eu/game.toml', recompiler, baseline,
        inventory_path, work/'baseline-audit.json')
    # Only MAIN contains the opted-in entry addresses. Unaffected overlays
    # retain the same emitter and ABI; prove absence of those entries before
    # copying their audited pairs into the new config namespace.
    tag = pipeline.compiler.cache_tag(str(ROOT/'psxrecomp/runtime/include'),str(recompiler),str(config),0)
    destination = cache/'SCES-01330/gcc/win-x64'/tag
    assert destination.is_dir()
    import tomllib
    hooks = {int(x,0)&0x1fffffff for x in tomllib.loads(config.read_text())['recompiler']['mod_function_entry_funcs']}
    abi = pipeline.compiler.overlay_abi_tag(str(ROOT/'psxrecomp/runtime/include'),0)
    for source in baseline.rglob('*.dll'):
        target = destination/source.name
        if target.exists():
            continue
        entries = pipeline.compiler.load_shard_func_ids(str(source),abi)
        assert entries and not any((entry[0]&0x1fffffff) in hooks for entry in entries), source
        for suffix in ('.dll','.ranges','.resident'):
            member = source.with_suffix(suffix)
            if member.exists():
                shutil.copy2(member,target.with_suffix(suffix))
    receipt = pipeline.audit(config, recompiler, cache, inventory_path, work/'audit.json')
    clear_abi_memos(ROOT/'build-eu-seamless/native',receipt)
    pipeline.stage(cache, ROOT/'build-eu-seamless/native', receipt)
    print('PASS: isolated native entry-filter cache audited and staged', flush=True)


if __name__ == '__main__':
    main()
