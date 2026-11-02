"""Dedicated per-user LaunchAgent; bootout removes supervision on stop."""
import os
import plistlib
import subprocess
import time
from pathlib import Path

LABEL='org.example.polysentinel'

def plist_path():return Path.home()/'Library/LaunchAgents'/f'{LABEL}.plist'
def domain():return f'gui/{os.getuid()}'

def status():
    r=subprocess.run(['launchctl','print',f'{domain()}/{LABEL}'],capture_output=True,text=True)
    fields={}
    if r.returncode==0:
        for line in r.stdout.splitlines():
            key,sep,value=line.strip().partition(' = ')
            if sep and key in ('state','pid','runs','last exit code'):fields[key]=value
    return dict(loaded=r.returncode==0,label=LABEL,**fields)

def install(config):
    root=Path(config['root'])
    (root/'logs').mkdir(parents=True,exist_ok=True)
    payload=dict(Label=LABEL,ProgramArguments=[str(root/'.venv/bin/python'),'-m','polysentinel','run'],
                 WorkingDirectory=str(root),RunAtLoad=True,KeepAlive=True,ThrottleInterval=30,
                 ExitTimeOut=20,ProcessType='Standard',Nice=5,
                 EnvironmentVariables={'PYTHONUNBUFFERED':'1','PYTHONNOUSERSITE':'1','PATH':'/usr/bin:/bin:/usr/sbin:/sbin'},
                 StandardOutPath=str(root/'logs/launchd.stdout.log'),StandardErrorPath=str(root/'logs/launchd.stderr.log'))
    p=plist_path();p.parent.mkdir(parents=True,exist_ok=True)
    if p.exists():
        existing=plistlib.loads(p.read_bytes())
        if existing.get('Label')!=LABEL or existing.get('WorkingDirectory')!=str(root):
            raise RuntimeError('LaunchAgent existant différent ; conservé sans remplacement')
    p.write_bytes(plistlib.dumps(payload));p.chmod(0o600)
    return p

def start(config):
    if status()['loaded']:return status()
    p=install(config)
    subprocess.run(['launchctl','enable',f'{domain()}/{LABEL}'],check=True,capture_output=True,text=True)
    subprocess.run(['launchctl','bootstrap',domain(),str(p)],check=True,capture_output=True,text=True)
    return status()

def stop():
    if status()['loaded']:
        subprocess.run(['launchctl','bootout',f'{domain()}/{LABEL}'],check=True,capture_output=True,text=True)
    subprocess.run(['launchctl','disable',f'{domain()}/{LABEL}'],check=True,capture_output=True,text=True)
    deadline=time.monotonic()+20
    result=status()
    while result['loaded'] and time.monotonic()<deadline:
        time.sleep(.2)
        result=status()
    if result['loaded']:raise RuntimeError('Arrêt demandé, processus encore présent après 20 s')
    return result

def uninstall():
    result=stop();p=plist_path()
    if p.exists():
        dest=p.with_suffix('.plist.disabled')
        if dest.exists():raise RuntimeError('Sauvegarde .disabled existe déjà ; plist conservé')
        p.rename(dest)
    result['data_preserved']=True
    return result
