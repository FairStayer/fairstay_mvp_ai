#!/bin/bash

# FairStay AI Lambda 배포 스크립트
# 이 스크립트는 Docker 이미지를 빌드하고 AWS ECR에 푸시한 후 Lambda 함수를 업데이트합니다.

set -e  # 오류 발생 시 스크립트 중단

# 설정
AWS_REGION="ap-northeast-2"
AWS_ACCOUNT_ID="897722707561"
ECR_REPOSITORY="fairstay-ai"
LAMBDA_FUNCTION_NAME="fairstay-ai"
IMAGE_TAG="latest"

# 색상 출력
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}FairStay AI Lambda 배포 시작${NC}"
echo -e "${GREEN}========================================${NC}"

# 1. AWS CLI 설치 확인
echo -e "\n${YELLOW}[1/7] AWS CLI 확인 중...${NC}"
if ! command -v aws &> /dev/null; then
    echo -e "${RED}AWS CLI가 설치되어 있지 않습니다.${NC}"
    echo "설치 방법: https://aws.amazon.com/cli/"
    exit 1
fi
echo -e "${GREEN}✓ AWS CLI 설치 확인됨${NC}"

# 2. Docker 실행 확인
echo -e "\n${YELLOW}[2/7] Docker 확인 중...${NC}"
if ! docker info &> /dev/null; then
    echo -e "${RED}Docker가 실행되고 있지 않습니다.${NC}"
    echo "Docker Desktop을 실행해주세요."
    exit 1
fi
echo -e "${GREEN}✓ Docker 실행 확인됨${NC}"

# 3. ECR 로그인
echo -e "\n${YELLOW}[3/7] ECR에 로그인 중...${NC}"
aws ecr get-login-password --region $AWS_REGION | \
    docker login --username AWS --password-stdin \
    ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ ECR 로그인 성공${NC}"
else
    echo -e "${RED}✗ ECR 로그인 실패${NC}"
    exit 1
fi

# 4. Docker 이미지 빌드
echo -e "\n${YELLOW}[4/7] Docker 이미지 빌드 중...${NC}"
docker build --platform linux/amd64 -t ${ECR_REPOSITORY}:${IMAGE_TAG} .

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Docker 이미지 빌드 성공${NC}"
else
    echo -e "${RED}✗ Docker 이미지 빌드 실패${NC}"
    exit 1
fi

# 5. Docker 이미지 태그
echo -e "\n${YELLOW}[5/7] Docker 이미지 태그 지정 중...${NC}"
docker tag ${ECR_REPOSITORY}:${IMAGE_TAG} \
    ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${ECR_REPOSITORY}:${IMAGE_TAG}

echo -e "${GREEN}✓ Docker 이미지 태그 지정 완료${NC}"

# 6. ECR에 푸시
echo -e "\n${YELLOW}[6/7] ECR에 이미지 푸시 중...${NC}"
docker push ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${ECR_REPOSITORY}:${IMAGE_TAG}

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ ECR에 이미지 푸시 성공${NC}"
else
    echo -e "${RED}✗ ECR에 이미지 푸시 실패${NC}"
    exit 1
fi

# 7. Lambda 함수 업데이트 (선택사항)
echo -e "\n${YELLOW}[7/7] Lambda 함수 업데이트 확인${NC}"
read -p "Lambda 함수를 자동으로 업데이트하시겠습니까? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${YELLOW}Lambda 함수 업데이트 중...${NC}"
    aws lambda update-function-code \
        --function-name ${LAMBDA_FUNCTION_NAME} \
        --image-uri ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${ECR_REPOSITORY}:${IMAGE_TAG} \
        --region ${AWS_REGION}
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ Lambda 함수 업데이트 성공${NC}"
    else
        echo -e "${RED}✗ Lambda 함수 업데이트 실패${NC}"
        echo -e "${YELLOW}수동으로 AWS Console에서 업데이트해주세요.${NC}"
    fi
else
    echo -e "${YELLOW}Lambda 함수는 AWS Console에서 수동으로 업데이트해주세요.${NC}"
fi

# 완료 메시지
echo -e "\n${GREEN}========================================${NC}"
echo -e "${GREEN}배포 완료!${NC}"
echo -e "${GREEN}========================================${NC}"
echo -e "\n${YELLOW}다음 단계:${NC}"
echo -e "1. AWS Lambda Console에서 함수 상태 확인"
echo -e "2. Function URL로 테스트 실행"
echo -e "3. Backend Lambda에 AI_SERVER_URL 환경 변수 설정\n"

echo -e "${YELLOW}이미지 URI:${NC}"
echo -e "${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${ECR_REPOSITORY}:${IMAGE_TAG}"
