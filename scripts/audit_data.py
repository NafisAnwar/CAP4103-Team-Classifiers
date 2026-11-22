from pathlib import Path
import json
import sys
import argparse

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.datasets import audit_datasets

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--rebuild', action='store_true', help='Intentionally replace audited manifests; rebuild the protocol afterward')
    summary, counts = audit_datasets(rebuild=parser.parse_args().rebuild)  # an old protocol lock will reject changed audit files
    print(json.dumps(summary, indent=2))
    print(json.dumps(counts, indent=2))
