import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

def load_config(root=None):
    root = Path(root or ROOT).resolve()
    config = json.loads((root / 'config.json').read_text())
    if config['host'] != '127.0.0.1' or config.get('paid_llm'):
        raise ValueError('Écoute locale et appels payants désactivés obligatoires')
    for key in ('request_concurrency', 'request_attempts', 'request_timeout', 'trade_interval', 'catalog_interval'):
        if not isinstance(config[key], (int, float)) or config[key] <= 0:
            raise ValueError(f'Configuration invalide: {key}')
    if config['request_concurrency'] > 4:
        raise ValueError('Maximum 4 requêtes simultanées')
    config['root'] = str(root)
    return config
