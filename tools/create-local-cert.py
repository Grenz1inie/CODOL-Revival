"""Prepare certificates for an explicit instance; never changes OS trust stores."""
import argparse
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from games.codol.versions.v3_3_3_3.client.bootstrap import prepare_certificates

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--runtime', required=True, type=Path, help='selected runtime/instances/<instance> directory')
    args = parser.parse_args()
    print('Local certificates ready in', prepare_certificates(args.runtime))
