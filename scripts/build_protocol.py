from pathlib import Path
import json
import sys
import argparse

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.trial_protocol import build_protocol

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--rebuild', action='store_true', help='Intentionally replace the current protocol and lock')
    print(json.dumps(build_protocol(rebuild=parser.parse_args().rebuild), indent=2))  # never overwrite a study by accident
