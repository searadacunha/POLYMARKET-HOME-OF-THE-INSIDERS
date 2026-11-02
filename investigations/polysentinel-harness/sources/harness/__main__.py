"""Usage: python -m harness {run,status,context,digest,propose,demo} --root DIR"""
import argparse
import json
import sys

from .paths import assert_isolated
from .runner import isolate_environment, passage


def main():
    parser = argparse.ArgumentParser(prog='harness', description=__doc__)
    parser.add_argument('command', choices=('run', 'status', 'context', 'digest', 'propose', 'demo'))
    parser.add_argument('--root', required=True)
    parser.add_argument('--seconds', type=float, default=240, help='run: length of this passage')
    parser.add_argument('--query', default='', help='context: what the next run is about')
    parser.add_argument('--budget', type=int, default=6000, help='context: characters')
    parser.add_argument('--file', help='propose: JSON with statement, feature, threshold')
    args = parser.parse_args()
    root = assert_isolated(args.root)
    isolate_environment(root)
    if args.command == 'run':
        print(json.dumps(passage(root, args.seconds), ensure_ascii=False))
        return 0
    if args.command == 'demo':
        from .demo import build
        print(json.dumps(build(root), ensure_ascii=False))
        return 0
    from . import memory
    from .recover import enqueue
    from .store import Harness
    h = Harness(root)
    try:
        if args.command == 'status':
            print(json.dumps(h.status(), ensure_ascii=False, indent=1))
        elif args.command == 'digest':
            print(h.digest())
        elif args.command == 'context':
            print(memory.context_pack(h, args.query, args.budget)['text'])
        elif args.command == 'propose':
            item = json.loads(open(args.file).read())
            spec = dict(feature=item['feature'], threshold=item['threshold'], direction=item.get('direction', 1))
            new, status, duplicate = memory.propose(h, 'population', item['statement'], spec, 'operator')
            if not duplicate:
                enqueue(h, f'population:{new}', 'population_test', dict(hypothesis=new), .2, why='proposed by the operator')
            print(json.dumps(dict(id=new, status=status, duplicate=duplicate)))
    finally:
        h.close()
    return 0


if __name__ == '__main__':
    sys.exit(main())
