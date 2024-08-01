# Python 3.10 이미지를 기반으로 함
FROM python:3.10-slim

# 작업 디렉토리 설정
WORKDIR /app

RUN mkdir /app/code_exec

# 필요한 파일 복사
COPY . /app/code_exec

WORKDIR /app/code_exec

# 필요한 패키지 설치
RUN pip install --no-cache-dir -r requirements.txt

# 애플리케이션 실행
CMD ["gunicorn", "-k", "uvicorn.workers.UvicornWorker", "--access-logfile", "./gunicorn-access.log", "code_exec_server:app", "--bind", "0.0.0.0:8081", "--workers", "2", "--timeout", "300"]
