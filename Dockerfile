# Python 3.10 기본 이미지 사용
FROM python:3.10-slim

# 작업 디렉토리 설정
WORKDIR /app

# 시스템 의존성 설치 (OpenCV용)
RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxrender1 \
    libxext6 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# requirements.txt 복사 및 의존성 설치
# pip 타임아웃 설정 및 PyPI 미러 사용
COPY requirements.txt .
RUN pip install --default-timeout=1000 --no-cache-dir -r requirements.txt

# 애플리케이션 코드 복사
COPY main.py .

# AI 모델 파일 복사
COPY best.pt .

# 포트 노출
EXPOSE 8000

# FastAPI 실행 (Uvicorn 사용)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
