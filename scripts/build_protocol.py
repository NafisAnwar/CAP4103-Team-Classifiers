from pathlib import Path
import json
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.trial_protocol import build_protocol

if __name__ == '__main__':
    print(json.dumps(build_protocol(), indent=2))
