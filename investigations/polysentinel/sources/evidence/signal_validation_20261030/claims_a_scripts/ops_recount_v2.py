# Same read-only audit, with receipt hashes as links (the stored chain convention).
from pathlib import Path
source=Path('/tmp/signal-claims-a.XiQCuR/ops_recount.py').read_text()
source=source.replace("previous=h", "previous=hashlib.sha256((folder/'receipt.json').read_bytes()).hexdigest()")
exec(compile(source,'ops_recount_receipt_links','exec'))
