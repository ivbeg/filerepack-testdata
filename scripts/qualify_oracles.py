"""Run every declared independent oracle profile; strict lanes reject missing readers."""
import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from frbench.common import write_json  # noqa: E402
from frbench.conformance import run  # noqa: E402


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=ROOT)
    parser.add_argument('--strict', action='store_true')
    parser.add_argument('--output', type=Path, default=Path('results/conformance.json'))
    args = parser.parse_args()
    result = run(args.root, args.strict)
    write_json(args.output, result)
    raise SystemExit(bool(result['failed'] or (args.strict and result['skipped'])))


if __name__ == '__main__':
    main()
