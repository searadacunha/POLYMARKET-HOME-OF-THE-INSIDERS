"""One quota perimeter, including SQLite sidecars, evidence, caches and exports."""
import json
import os
from pathlib import Path
import shutil

def storage_usage(root):
    root=Path(root);logical=allocated=accounted=0
    for folder,dirs,files in os.walk(root,followlinks=False):
        dirs[:]=[d for d in dirs if d not in ('.venv','.git') and not (Path(folder)/d).is_symlink()]
        for name in files:
            p=Path(folder)/name
            try:
                if p.is_symlink():continue
                s=p.stat()
            except FileNotFoundError:continue
            physical=s.st_blocks*512
            logical+=s.st_size;allocated+=physical;accounted+=max(s.st_size,physical)
    return dict(project_data_bytes=logical,allocated_bytes=allocated,quota_accounted_bytes=accounted,
                free_bytes=shutil.disk_usage(root).free)

def reserve_bytes(config):
    # Raw/normalized/WAL allowance plus 35 MB of bounded logs/metrics and heartbeat.
    return 3*config.get('response_max_bytes',8_000_000)+36_000_000

def resource_blockers(config, metrics):
    margin = reserve_bytes(config)
    used = metrics.get('quota_accounted_bytes', metrics['project_data_bytes'])
    reasons = []
    if metrics['free_bytes'] - margin < config['min_free_bytes']:
        reasons.append(dict(code='volume_free_space', free_bytes=metrics['free_bytes'],
                            required_bytes=config['min_free_bytes'] + margin,
                            deficit_bytes=config['min_free_bytes'] + margin - metrics['free_bytes']))
    if used + margin >= config['data_quota_bytes']:
        reasons.append(dict(code='project_quota', used_bytes=used, margin_bytes=margin,
                            quota_bytes=config['data_quota_bytes']))
    return reasons

def require_capacity(root,config,extra_bytes):
    usage=storage_usage(root)
    if usage['free_bytes']-extra_bytes<config.get('min_free_bytes',0):
        raise RuntimeError('Réserve disque insuffisante')
    if usage['quota_accounted_bytes']+extra_bytes>config.get('data_quota_bytes',5_000_000_000):
        raise RuntimeError('Quota de données atteint')
    return usage

def guard_export(path,size):
    root=Path(path).parent.parent
    config_file=root/'config.json'
    if config_file.is_file():
        config=json.loads(config_file.read_text())
        require_capacity(root,config,size+8192)
