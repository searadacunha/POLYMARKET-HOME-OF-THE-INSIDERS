"""Lossless in-place compression of immutable legacy reports, with a manifest."""
import gzip
import hashlib
import json
from pathlib import Path


def compress_reports(root):
    root = Path(root)
    manifest = root/'evidence/restoration_20261029/report_compression.jsonl'
    manifest.parent.mkdir(parents=True, exist_ok=True)
    saved = 0
    for source in sorted((root/'reports').iterdir()):
        if source.is_symlink() or source.suffix not in ('.html', '.json'):
            continue
        # Daily summaries are mutable; z1 files are already compact exports.
        if source.name.startswith(('quotidien-', 'revue-')) or '-z1.' in source.name:
            continue
        raw = source.read_bytes()
        packed = gzip.compress(raw, mtime=0)
        if len(packed) >= len(raw):
            continue
        dest = source.with_name(source.name+'.gz')
        if dest.exists():
            if dest.is_symlink() or gzip.decompress(dest.read_bytes()) != raw:
                raise ValueError('Conflicting archive: '+str(dest))
        else:
            with dest.open('xb') as f:
                f.write(packed)
                f.flush()
                import os
                os.fsync(f.fileno())
        if gzip.decompress(dest.read_bytes()) != raw or source.read_bytes() != raw:
            raise ValueError('Verification failed: '+str(source))
        with manifest.open('a') as f:
            f.write(json.dumps(dict(source=str(source), archive=str(dest), bytes=len(raw),
                                   compressed_bytes=dest.stat().st_size,
                                   sha256=hashlib.sha256(raw).hexdigest()))+'\n')
            f.flush()
            import os
            os.fsync(f.fileno())
        source.unlink()
        saved += len(raw)-dest.stat().st_size
    return saved


if __name__ == '__main__':
    print(compress_reports(Path(__file__).resolve().parents[1]))
