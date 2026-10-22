"""Run the shared US AOT pipeline with Python isolated-mode imports."""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'psxrecomp/tools'))
from aot_overlay_pipeline import main

if __name__ == '__main__':
    sys.exit(main())
