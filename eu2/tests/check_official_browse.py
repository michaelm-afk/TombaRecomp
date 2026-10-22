"""Source parity proof; no window, dialog or input simulation."""
import hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
EXPECTED={'src/common/backends/imgui/launcher_imgui.cpp': '3f35d53ca2d8ac1b8f227a38ada853008aebc045beb748f9ff2da66b0b88cdcf', 'src/common/launcher_files.c': '5d41dc8d3b6250b7f3482c235cf48c521784decf91cfc0a582d773592069ce8f', 'src/common/launcher_files.h': '22b19abcfbc710549a6ff56466e11add83798e14d323842b8dd977fce0836778'}
for path,expected in EXPECTED.items():
    actual=hashlib.sha256((ROOT/'recomp-ui'/path).read_bytes().replace(b'\r\n',b'\n')).hexdigest()
    assert actual==expected,path
print('PASS: official picker/UI source parity at e08082d10c38d0c4293455c3d15b3ab35ef1afe3')
