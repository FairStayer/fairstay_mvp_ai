# AWS Lambda Python 3.10 기본 이미지 사용
FROM public.ecr.aws/lambda/python:3.10

# 작업 디렉토리 설정
WORKDIR ${LAMBDA_TASK_ROOT}

# 시스템 의존성 설치 (OpenCV용)
RUN yum install -y \
    libGL \
    libglib2.0-0 \
    libSM \
    libXrender \
    libXext \
    && yum clean all

# requirements.txt 복사 및 의존성 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 애플리케이션 코드 복사
COPY main.py .
COPY lambda_handler.py .

# AI 모델 파일 복사 (best.pt가 프로젝트에 있는 경우)
# COPY best.pt .

# Lambda 핸들러 설정
CMD ["lambda_handler.handler"]
