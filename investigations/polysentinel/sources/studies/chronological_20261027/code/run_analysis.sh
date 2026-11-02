#!/bin/sh
set -eu
export PYTHONDONTWRITEBYTECODE=1
python3 code/ana_evaluate.py
python3 code/write_report.py
