"""Offline reconstruction with archived dependencies; the original frozen collector is untouched."""
import argparse
import importlib.util
import os
import sys
from pathlib import Path

CODE = Path(__file__).resolve().parent
VENDOR = CODE / 'vendor'
sys.path.insert(0, str(VENDOR))
from polysentinel import collect

if Path(collect.__file__).resolve() != VENDOR / 'polysentinel/collect.py':
    raise RuntimeError('Normalizer must load from the frozen vendor copy')
spec = importlib.util.spec_from_file_location('original_collector', CODE / 'col_historical.py')
original = importlib.util.module_from_spec(spec)
spec.loader.exec_module(original)
original.ROOT = VENDOR
if original.normalize_trade is not collect.normalize_trade:
    raise RuntimeError('Unexpected normalizer imported')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('mode', choices=('self-check', 'validate-export'))
    args = parser.parse_args()
    if args.mode == 'self-check':
        original.self_check()
    else:
        if not os.environ.get('ETUDE_REPRO_DIR') or not CODE.is_relative_to(Path(os.environ['ETUDE_REPRO_DIR']).resolve()):
            raise RuntimeError('Reconstruction only in a fresh repro.py copy, never over frozen input')
        original.validate_export()
