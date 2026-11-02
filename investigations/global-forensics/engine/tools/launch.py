"""Start a long job in its own Unix session, so it survives this session, with idle sleep held for exactly its lifetime. Usage: launch.py <log> <cmd...>"""
import subprocess
import sys
log = open(sys.argv[1], 'ab')
p = subprocess.Popen(sys.argv[2:], stdin=subprocess.DEVNULL, stdout=log, stderr=log, start_new_session=True, env={**__import__('os').environ, 'PYTHONDONTWRITEBYTECODE': '1', 'TMPDIR': '/Volumes/PHI-Data/global-forensics/tmp'})
subprocess.Popen(['caffeinate', '-is', '-w', str(p.pid)], stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
print(p.pid)
