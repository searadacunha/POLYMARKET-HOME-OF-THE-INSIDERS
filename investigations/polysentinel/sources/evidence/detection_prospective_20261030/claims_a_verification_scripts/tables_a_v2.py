from pathlib import Path
source=Path('/private/tmp/claims_b.iRPZCf/tables_a.py').read_text()
exec(compile(source.replace("else 'inconnu / aucun'", "else 'aucun dans ce scénario'"),'/private/tmp/claims_b.iRPZCf/tables_a.py','exec'))
