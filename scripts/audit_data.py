from pathlib import Path
import json
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.datasets import audit_datasets

if __name__ == '__main__':
    summary, counts = audit_datasets()
    print(json.dumps(summary, indent=2))
    print(json.dumps(counts, indent=2))
