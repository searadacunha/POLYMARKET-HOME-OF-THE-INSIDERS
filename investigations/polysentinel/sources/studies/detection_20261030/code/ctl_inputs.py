import gzip
import hashlib
import json
from pathlib import Path
import tempfile
from unittest.mock import patch
import ana_replay
import ana_labels
import budget

def controls():
    with tempfile.TemporaryDirectory() as temp:
        root=Path(temp);(root/'data').mkdir()
        raw=gzip.compress(b'{"id":"fixture"}\n',mtime=0)
        path=root/'data/replay_input.jsonl.gz';path.write_bytes(raw)
        manifest=root/'data/input_manifest.json'
        manifest.write_text(json.dumps(dict(input_sha256=hashlib.sha256(raw).hexdigest(),counts={'kept':1})))
        with patch.object(ana_replay,'STUDY',root):
            assert len(ana_replay.verified_input())==1
            path.write_bytes(gzip.compress(b'{"id":"changed"}\n',mtime=0))
            try:ana_replay.verified_input()
            except ValueError:pass
            else:raise AssertionError('changed source accepted')
            path.write_bytes(raw);manifest.unlink()
            try:ana_replay.verified_input()
            except FileNotFoundError:pass
            else:raise AssertionError('missing manifest accepted')
        out=root/'never-written'
        with patch.object(budget,'STUDY',root),patch.object(budget,'CAP',1):
            try:budget.write_bytes(out,b'x')
            except RuntimeError:pass
            else:raise AssertionError('cap failed open')
            assert not out.exists()
        out.write_bytes(b'preserved')
        with patch.object(budget,'STUDY',root):
            try:budget.write_bytes(out,b'replaced')
            except FileExistsError:pass
            else:raise AssertionError('existing output overwritten')
            assert out.read_bytes()==b'preserved'
        (root/'derived').mkdir()
        with patch.object(ana_labels,'STUDY',root):
            for files in ({},{'derived/replay.json.gz':'absent'}):
                (root/'derived/pre_label_seal.json').write_text(json.dumps({'files':files}))
                try:ana_labels.main()
                except ValueError as error:assert 'both complete' in str(error)
                else:raise AssertionError('incomplete seal accepted')
    return dict(status='PASS',fixtures=7,cases=['completed_input','changed_input_refused','missing_manifest_refused','cap_prevents_write','existing_output_preserved','empty_seal_refused','partial_seal_refused'])

if __name__=='__main__':print(json.dumps(controls(),indent=2))
