"""Render pipeline.json as PIPELINE.md. Run from this folder: python3 pipeline_manifest.py"""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def render(data):
    out = [f"# {data['title']}", '', 'Generated from `pipeline.json` by `pipeline_manifest.py`; edit the JSON, not this file.', '', data['note'], '']
    for s in data['stages']:
        out += [f"## {s['stage']}", '', '| Module | Functions |', '| --- | --- |']
        out += [f"| `{m['path']}` | {', '.join(f'`{f}`' for f in m['functions'])} |" for m in s['modules']]
        out += ['', 'Entry points:', ''] + [f'- `{e}`' for e in s['entry_points']]
        out += ['', f"Input: {s['input']}", '', f"Output: {s['output']}", '', 'Tests:', ''] + [f'- `{t}`' for t in s['tests']]
        out += ['', 'Checked offline when this map was written:', ''] + ([f'- {c}' for c in s['checked']] or ['- nothing'])
        out += ['', f"Known gap: {s['gap']}", '']
    return '\n'.join(out)


if __name__ == '__main__':
    (HERE / 'PIPELINE.md').write_text(render(json.loads((HERE / 'pipeline.json').read_text())))
