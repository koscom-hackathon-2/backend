#!/bin/sh

# 파이썬, pip 설치되어 있어야 함
# 파이썬 버전: 3.10.13

pip install -r requirements.txt
pkill -9 gunicorn
gunicorn -k uvicorn.workers.UvicornWorker --access-logfile ./gunicorn-access.log code_exec_server:app --bind 0.0.0.0:8081 --workers 2 --daemon --timeout 300