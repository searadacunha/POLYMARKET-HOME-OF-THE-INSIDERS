"""External watchdog: runs a command in its own process group, stops it on any ceiling.

Usage: guard.py --nom NAME [--rss-mo 400] [--swap-mo 100] [--ecrit-mo 250] [--libre-go 14] \
           [--avant-go 15] --dossier DIR [--dossier DIR] -- command...
"""
import argparse
import json
import os
import signal
import subprocess
import sys
import time
from pathlib import Path

ETUDE = Path(__file__).resolve().parent.parent
PROJET = ETUDE.parent.parent
HEARTBEAT = PROJET / 'metrics/heartbeat.json'


def swap_mo():
    sortie = subprocess.run(['/usr/sbin/sysctl', '-n', 'vm.swapusage'], capture_output=True, text=True, check=True).stdout
    return float(sortie.split('used = ')[1].split('M')[0])


def libre_go():
    s = os.statvfs('/')
    return s.f_bavail * s.f_frsize / 1e9


def taille_mo(dossiers):
    total = 0
    for dossier in dossiers:
        for racine, _, fichiers in os.walk(dossier):
            for nom in fichiers:
                try:
                    total += os.lstat(os.path.join(racine, nom)).st_size
                except FileNotFoundError:
                    pass
    return total / 1e6


def rss_groupe_mo(pgid):
    sortie = subprocess.run(['/bin/ps', '-o', 'rss=', '-g', str(pgid)], capture_output=True, text=True).stdout
    return sum(int(x) for x in sortie.split()) / 1024


def battement_age():
    try:
        return time.time() - json.loads(HEARTBEAT.read_text())['at']
    except (OSError, ValueError, KeyError):
        return float('inf')


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--nom', required=True)
    p.add_argument('--rss-mo', type=float, default=400)
    p.add_argument('--swap-mo', type=float, default=100)
    p.add_argument('--ecrit-mo', type=float, default=250)
    p.add_argument('--libre-go', type=float, default=14)
    p.add_argument('--avant-go', type=float, default=15)
    p.add_argument('--dossier', action='append', required=True)
    p.add_argument('commande', nargs=argparse.REMAINDER)
    a = p.parse_args()
    commande = a.commande[1:] if a.commande[:1] == ['--'] else a.commande
    rapport = ETUDE / f'data/guard_{a.nom}.json'
    depart = dict(libre_go=libre_go(), swap_mo=swap_mo(), ecrit_mo=taille_mo(a.dossier), debut=time.time())
    etat = dict(nom=a.nom, commande=commande, depart=depart, plafonds=vars(a) | {'commande': None}, pics=dict(rss_mo=0, swap_delta_mo=0, ecrit_delta_mo=0, libre_min_go=depart['libre_go']))
    if depart['libre_go'] < a.avant_go:
        etat.update(motif=f"Refus: {depart['libre_go']:.2f} Go libres < {a.avant_go} Go", code=None, fin=time.time())
        rapport.write_text(json.dumps(etat, indent=1))
        print(etat['motif'], file=sys.stderr)
        return 3
    fils = subprocess.Popen(commande, start_new_session=True)
    pgid = fils.pid
    motif = None
    derniere_taille = 0
    while fils.poll() is None:
        time.sleep(2)
        rss = rss_groupe_mo(pgid)
        swap = swap_mo() - depart['swap_mo']
        libre = libre_go()
        ages = battement_age()
        etat['pics'].update(rss_mo=max(etat['pics']['rss_mo'], rss), swap_delta_mo=max(etat['pics']['swap_delta_mo'], swap),
                            libre_min_go=min(etat['pics']['libre_min_go'], libre))
        if time.time() - derniere_taille > 20:
            derniere_taille = time.time()
            etat['pics']['ecrit_delta_mo'] = max(etat['pics']['ecrit_delta_mo'], taille_mo(a.dossier) - depart['ecrit_mo'])
            rapport.write_text(json.dumps(etat, indent=1))
        if rss > a.rss_mo:
            motif = f'RSS {rss:.0f} Mo > {a.rss_mo}'
        elif swap > a.swap_mo:
            motif = f'swap +{swap:.0f} Mo > {a.swap_mo}'
        elif etat['pics']['ecrit_delta_mo'] > a.ecrit_mo:
            motif = f"écritures +{etat['pics']['ecrit_delta_mo']:.0f} Mo > {a.ecrit_mo}"
        elif libre < a.libre_go:
            motif = f'disque {libre:.2f} Go < {a.libre_go}'
        elif ages > 180:
            motif = f'battement collecteur vieux de {ages:.0f} s'
        if motif:
            os.killpg(pgid, signal.SIGTERM)
            limite = time.time() + 20
            while fils.poll() is None and time.time() < limite:
                time.sleep(.5)
            if fils.poll() is None:
                os.killpg(pgid, signal.SIGKILL)
            break
    code = fils.wait()
    etat['pics']['ecrit_delta_mo'] = max(etat['pics']['ecrit_delta_mo'], taille_mo(a.dossier) - depart['ecrit_mo'])
    etat.update(motif=motif, code=code, fin=time.time(), duree_s=time.time() - depart['debut'])
    rapport.write_text(json.dumps(etat, indent=1))
    print(json.dumps(dict(nom=a.nom, motif=motif, code=code, duree_s=round(etat['duree_s']), pics=etat['pics'])))
    return 2 if motif else code


if __name__ == '__main__':
    sys.exit(main())
