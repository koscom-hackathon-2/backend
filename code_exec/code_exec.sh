#!/bin/sh

# 파이썬, pip 설치되어 있어야 함
# 파이썬 버전: 3.10.13

pip install -r requirements.txt
pkill -9 gunicorn

PORT=8081

# 포트 사용 중인 프로세스 확인 및 종료
# PID=$(sudo lsof -t -i :$PORT)
# if [ -n "$PID" ]; then
#   echo "Killing process $PID using port $PORT"
#   sudo kill -9 $PID
# fi

gunicorn -k uvicorn.workers.UvicornWorker --access-logfile ./gunicorn-access.log code_exec_server:app --bind 0.0.0.0:$PORT --workers 2 --timeout 300
