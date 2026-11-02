export PYTHONDONTWRITEBYTECODE=1
cd ~/Projects/PolySentinel-flow-trace
python3 -u tools/walk.py && python3 -u tools/pairs.py && python3 -u tools/bridges.py | head -1 && python3 -u tools/proxy_check.py | tail -3 | cut -c1-200 && python3 -u tools/build_data.py && python3 -u tools/verify.py
echo BUILD_FINISHED
