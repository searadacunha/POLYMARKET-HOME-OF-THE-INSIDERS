# Same read-only audit; receipt links and sidecar basename resolved explicitly.
from pathlib import Path
source=Path('/tmp/signal-claims-a.XiQCuR/ops_recount.py').read_text()
source=source.replace("previous=h", "previous=hashlib.sha256((folder/'receipt.json').read_bytes()).hexdigest()")
source=source.replace("(P/rel).read_bytes()", "(P/'tools/prospective_eval'/rel if rel=='sidecar.py' else P/rel).read_bytes()")
exec(compile(source,'ops_recount_receipt_links_and_sidecar_path','exec'))
