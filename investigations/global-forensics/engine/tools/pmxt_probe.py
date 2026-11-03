"""Schema and row groups of one hourly archive file, read by HTTP ranges, so the file itself is never downloaded."""
import io
import json
import sys
import urllib.request

import pyarrow.parquet as pq

UA = {'User-Agent': 'phi-global-forensics/0.1 read-only'}


class RangeFile(io.RawIOBase):
    """Enough of a file for pyarrow: size from HEAD, reads by Range. Counts the bytes really fetched."""

    def __init__(self, url):
        self.url, self.pos, self.fetched = url, 0, 0
        with urllib.request.urlopen(urllib.request.Request(url, method='HEAD', headers=UA), timeout=60) as r:
            self.size = int(r.headers['Content-Length'])

    def seekable(self):
        return True

    def readable(self):
        return True

    def tell(self):
        return self.pos

    def seek(self, offset, whence=0):
        self.pos = {0: offset, 1: self.pos + offset, 2: self.size + offset}[whence]
        return self.pos

    def read(self, n=-1):
        if n is None or n < 0:
            n = self.size - self.pos
        if n == 0 or self.pos >= self.size:
            return b''
        end = min(self.size, self.pos + n) - 1
        request = urllib.request.Request(self.url, headers={**UA, 'Range': f'bytes={self.pos}-{end}'})
        for attempt in range(5):
            try:
                with urllib.request.urlopen(request, timeout=120) as r:
                    data = r.read()
                self.pos += len(data)
                self.fetched += len(data)
                return data
            except OSError:
                if attempt == 4:
                    raise


if __name__ == '__main__':
    f = RangeFile(sys.argv[1])
    p = pq.ParquetFile(f)
    print(p.schema_arrow)
    meta = p.metadata
    print('rows', meta.num_rows, 'row groups', meta.num_row_groups, 'size', f.size, 'fetched for footer', f.fetched)
    rg = meta.row_group(0)
    for i in range(rg.num_columns):
        c = rg.column(i)
        print(c.path_in_schema, c.compression, c.total_compressed_size, (str(c.statistics.min)[:70], str(c.statistics.max)[:70]) if c.statistics and c.statistics.has_min_max else None)
    t = p.read_row_group(0, columns=[n for n in p.schema_arrow.names]).slice(0, 2).to_pylist()
    print(json.dumps(t, default=str)[:1500])
    print('fetched total', f.fetched)
