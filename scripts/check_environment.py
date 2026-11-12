from importlib.metadata import version
from pathlib import Path
import json
import platform
import sys

root = Path(__file__).resolve().parents[1]
packages = {name: version(name) for name in ['numpy', 'scipy', 'scikit-learn', 'matplotlib']}
print(json.dumps({'python': platform.python_version(), 'executable': sys.executable,
                  'project_root': str(root), 'isolated_environment': sys.prefix != sys.base_prefix,
                  'packages': packages}, indent=2))
if not (root / 'ppa3_legacy/main.py').is_file():
    raise SystemExit('Missing legacy program')
