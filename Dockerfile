# AWS Lambda Python 3.10 베이스 이미지 사용
FROM public.ecr.aws/lambda/python:3.10

# 시스템 의존성 설치 (OpenCV용)
RUN yum install -y mesa-libGL && yum clean all

# requirements.txt 복사 및 의존성 설치
COPY requirements.txt ${LAMBDA_TASK_ROOT}/
RUN pip install --default-timeout=1000 --no-cache-dir -r ${LAMBDA_TASK_ROOT}/requirements.txt

# 애플리케이션 코드 복사
COPY main.py ${LAMBDA_TASK_ROOT}/
COPY lambda_handler.py ${LAMBDA_TASK_ROOT}/

# AI 모델 파일 복사
COPY best.pt ${LAMBDA_TASK_ROOT}/

# Lambda 핸들러 설정
CMD ["lambda_handler.handler"]
