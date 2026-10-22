"""Resolve developer tools without embedding a developer's machine paths."""
import os
from pathlib import Path
import shutil

def executable(name):
    directory=os.environ.get('TOMBI_TOOLCHAIN_BIN')
    candidate=Path(directory)/name if directory else None
    if candidate and candidate.is_file():return str(candidate.resolve())
    found=shutil.which(name)
    if found:return found
    raise RuntimeError(f'{name} not found. Add the Windows toolchain to PATH or set TOMBI_TOOLCHAIN_BIN.')
