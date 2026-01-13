# 🚀 FairStay AI 람다 배포 가이드 (ECR + Lambda Container)

Lambda Container Image를 사용하면 **10GB 제한** 안에서 PyTorch, YOLO, OpenCV를 모두 배포할 수 있습니다.

## 📊 아키텍처

```
GitHub (코드 푸시)
  ↓
GitHub Actions (Docker 빌드 - 16GB RAM 서버)
  ↓
Amazon ECR (Docker 이미지 저장)
  ↓
AWS Lambda (Container Image, 10GB 제한)
  ↓
백엔드 Node.js Lambda (Function URL로 호출)
```

## 💰 비용 예상

- **Lambda**: 월 $0-5 (프리티어 100만 요청 + 40만 GB-초 무료)
- **ECR**: 월 $0.5-1 (500MB당 $0.10, 프리티어 500MB/월)
- **총 비용**: **월 $0-6** (Fargate $107에서 95% 절감)

## ⚡ 성능

- **첫 요청 (Cold Start)**: 5-10초
- **이후 요청 (Warm)**: 1-3초
- 15-40초 RunTask 방식 대비 훨씬 빠름

---

## 1️⃣ AWS 액세스 키 생성

### 1-1. IAM 사용자 생성

1. **AWS Console** → **IAM** 이동
2. 왼쪽 메뉴 → **사용자** → **사용자 생성**
3. 사용자 이름: `github-actions-fairstay-ai` 입력
4. **다음** 클릭

### 1-2. 권한 설정

**권한 옵션**: 직접 정책 연결 선택

필요한 권한 (체크박스 선택):
- `AmazonEC2ContainerRegistryFullAccess` - ECR 이미지 푸시/관리
- `AWSLambda_FullAccess` - Lambda 함수 관리 (선택사항, 콘솔로 배포하려면 불필요)

**사용자 생성** 클릭

### 1-3. 액세스 키 생성

1. 생성된 사용자 클릭 → **보안 자격 증명** 탭
2. **액세스 키 만들기** 클릭
3. 사용 사례: **Command Line Interface(CLI)** 선택
4. 체크박스: "위의 권장 사항을 이해했으며..." 체크
5. **다음** → **액세스 키 만들기**

📝 **중요**: 
- **액세스 키 ID** 복사
- **비밀 액세스 키** 복사 (다시 볼 수 없음!)

---

## 2️⃣ GitHub Secrets 설정

### GitHub 리포지토리로 이동

1. **Settings** 탭 클릭
2. 왼쪽 메뉴 → **Secrets and variables** → **Actions**
3. **New repository secret** 클릭

### 다음 3개의 Secret 생성:

| Secret 이름 | 값 | 설명 |
|------------|-----|------|
| `AWS_ACCESS_KEY_ID` | 위에서 복사한 액세스 키 ID | IAM 사용자 액세스 키 |
| `AWS_SECRET_ACCESS_KEY` | 위에서 복사한 비밀 액세스 키 | IAM 사용자 비밀 키 |
| `AWS_REGION` | `ap-northeast-2` | 서울 리전 |

각 Secret 추가:
1. **Name**: Secret 이름 입력
2. **Value**: 해당 값 입력 (붙여넣기)
3. **Add secret** 클릭

---

## 3️⃣ ECR 리포지토리 생성 (이미 완료됨)

✅ **이미 생성됨**: `fairstay-mvp-ai`

확인:
```bash
aws ecr describe-repositories --region ap-northeast-2 --repository-names fairstay-mvp-ai
```

---

## 4️⃣ 코드 수정사항 확인

✅ **모두 완료됨**:
- `lambda_handler.py` 생성 (Mangum 어댑터)
- `requirements.txt`에 `mangum` 추가
- `Dockerfile` Lambda 베이스 이미지로 변경

---

## 5️⃣ GitHub에 푸시하여 자동 배포 트리거

```bash
cd /Users/susie/Desktop/Temp_Laptop3/Solidity_Files/Yn/fairstay_mvp_ai

# 현재 상태 확인
git status

# 변경사항 추가
git add lambda_handler.py requirements.txt Dockerfile

# 커밋
git commit -m "feat: Lambda Container Image로 변경 (ECR + Lambda 배포)"

# 푸시 (GitHub Actions 자동 트리거)
git push origin main
```

### GitHub Actions 확인

1. GitHub 리포지토리 → **Actions** 탭
2. 워크플로우 실행 확인 (5-10분 소요)
3. 단계:
   - ✅ Checkout code
   - ✅ Configure AWS credentials
   - ✅ Login to Amazon ECR
   - ✅ Build Docker image
   - ✅ Push to ECR

---

## 6️⃣ Lambda 함수 생성

### 6-1. Lambda Console로 이동

1. **AWS Console** → **Lambda** 이동
2. **함수 생성** 클릭

### 6-2. 함수 구성

- **옵션**: 컨테이너 이미지 선택
- **함수 이름**: `fairstay-ai-lambda`
- **컨테이너 이미지 URI**: **이미지 찾아보기** 클릭
  - ECR 리포지토리: `fairstay-mvp-ai` 선택
  - 이미지 태그: `latest` 선택
  - **이미지 선택**

### 6-3. 권한

- **실행 역할**: 새 역할 생성 (기본 Lambda 권한)
- 역할 이름: `fairstay-ai-lambda-role` (자동 생성)

**함수 생성** 클릭

---

## 7️⃣ Lambda 함수 설정

### 7-1. 메모리 및 타임아웃 설정

함수 생성 후:

1. **구성** 탭 → **일반 구성** → **편집**
2. 설정:
   - **메모리**: `3008 MB` (최소 권장)
   - **제한 시간**: `5분 0초` (300초)
   - **임시 스토리지**: `512 MB` (기본값)
3. **저장**

### 7-2. 환경 변수 (선택사항)

**구성** → **환경 변수** → **편집**

| 키 | 값 | 설명 |
|-----|-----|------|
| `MODEL_PATH` | `best.pt` | YOLO 모델 파일 경로 |
| `SAVE_DIR` | `/tmp/result` | 결과 이미지 저장 경로 |

---

## 8️⃣ Function URL 생성

### 8-1. Function URL 설정

1. **구성** 탭 → **함수 URL** → **함수 URL 생성**
2. 설정:
   - **인증 유형**: `NONE` (공개 API) 
     - 또는 `AWS_IAM` (백엔드 Lambda에서 서명된 요청)
   - **CORS 구성**:
     - **Allow origin**: `*`
     - **Allow methods**: `GET, POST, OPTIONS`
     - **Allow headers**: `*`
3. **저장**

### 8-2. Function URL 복사

생성된 URL 형식:
```
https://abc123xyz.lambda-url.ap-northeast-2.on.aws/
```

📝 **이 URL을 메모**해두세요 (백엔드 환경변수에 사용)

---

## 9️⃣ Lambda 함수 테스트

### 9-1. Health Check 테스트

Lambda Console에서:

1. **테스트** 탭 → **테스트 이벤트 구성**
2. 이벤트 이름: `health-check`
3. 이벤트 JSON:
```json
{
  "httpMethod": "GET",
  "path": "/health",
  "headers": {},
  "body": null
}
```
4. **저장** → **테스트** 클릭

예상 결과:
```json
{
  "statusCode": 200,
  "body": "{\"status\":\"healthy\",\"message\":\"AI server is running\",\"model_loaded\":true}"
}
```

### 9-2. Function URL로 테스트

터미널에서:

```bash
# Health Check
curl https://YOUR_FUNCTION_URL/health

# Root 엔드포인트
curl https://YOUR_FUNCTION_URL/
```

예상 응답:
```json
{
  "status": "healthy",
  "message": "AI server is running",
  "model_loaded": true
}
```

### 9-3. 이미지 업로드 테스트

```bash
# 테스트 이미지로 crack detection
curl -X POST https://YOUR_FUNCTION_URL/detect-crack \
  -F "file=@/path/to/test-image.jpg"
```

예상 응답:
```json
{
  "file_id": "abc123-...",
  "has_crack": true,
  "confidence": 0.85,
  "result_url": "https://YOUR_FUNCTION_URL/result/abc123-..."
}
```

---

## 🔟 백엔드 통합

### 10-1. 백엔드 Lambda 환경변수 설정

백엔드 Node.js Lambda 함수에서:

1. **구성** → **환경 변수** → **편집**
2. 추가:

| 키 | 값 |
|-----|-----|
| `AI_SERVER_URL` | `https://YOUR_FUNCTION_URL` |

3. **저장**

### 10-2. 백엔드 코드 확인

```typescript
// services/ai.service.ts

const AI_SERVER_URL = process.env.AI_SERVER_URL;

// Health check
export async function checkAIServerHealth() {
  const response = await fetch(`${AI_SERVER_URL}/health`);
  return response.json();
}

// 이미지 분석
export async function analyzeImage(imageFile: Buffer) {
  const formData = new FormData();
  formData.append('file', new Blob([imageFile]), 'image.jpg');
  
  const response = await fetch(`${AI_SERVER_URL}/detect-crack`, {
    method: 'POST',
    body: formData
  });
  
  return response.json();
}
```

---

## 1️⃣1️⃣ 모니터링 및 로그

### CloudWatch Logs

1. Lambda Console → **모니터링** 탭
2. **CloudWatch에서 로그 보기** 클릭
3. 로그 스트림 확인:
   - Cold start 시간
   - 모델 로딩 시간
   - 에러 로그

### 주요 지표

- **호출 횟수**: 총 요청 수
- **오류**: 실패한 요청
- **기간**: 평균 실행 시간
- **제한**: 동시 실행 수

---

## 1️⃣2️⃣ 자동 배포 워크플로우

### 코드 변경 시

```bash
# 코드 수정 후
git add .
git commit -m "fix: 이미지 처리 로직 개선"
git push origin main
```

→ GitHub Actions 자동 실행 (5-10분)
→ ECR에 새 이미지 푸시
→ **Lambda 함수 수동 업데이트 필요**

### Lambda 이미지 업데이트

1. Lambda Console → 함수 선택
2. **이미지** 탭 → **새 이미지 배포** 클릭
3. ECR에서 `latest` 태그 선택
4. **저장**

---

## 🔧 트러블슈팅

### 문제 1: Cold Start 너무 느림 (10초+)

**해결**:
- Lambda **메모리 증가** → 4096 MB 또는 5120 MB
- 메모리가 높을수록 CPU도 증가하여 모델 로딩 빨라짐

### 문제 2: 타임아웃 에러

**해결**:
- Lambda **제한 시간 증가** → 5분 (최대 15분 가능)
- `/tmp` 공간 부족 시 → **임시 스토리지 증가** (512MB → 1024MB)

### 문제 3: 모델 로딩 실패

**로그 확인**:
```
CloudWatch Logs → 에러 메시지 확인
```

**가능한 원인**:
- `best.pt` 파일이 Docker 이미지에 없음
- Lambda 메모리 부족 (최소 3GB 필요)

**해결**:
```bash
# Dockerfile에 best.pt 포함 확인
COPY best.pt ${LAMBDA_TASK_ROOT}/
```

### 문제 4: GitHub Actions 빌드 실패

**로그 확인**:
- GitHub → Actions → 실패한 워크플로우 클릭

**가능한 원인**:
- GitHub Secrets 미설정
- ECR 리포지토리 없음
- 네트워크 타임아웃 (pip install)

**해결**:
```yaml
# deploy.yml에 타임아웃 설정 확인
RUN pip install --default-timeout=1000 ...
```

---

## 📚 참고

### Lambda Container Image 제한

- 최대 이미지 크기: **10 GB**
- 현재 이미지 크기: ~2-3 GB (PyTorch + YOLO + OpenCV)
- ✅ 충분한 여유 공간

### Lambda 리소스 제한

- 최대 메모리: **10,240 MB** (10GB)
- 최대 타임아웃: **15분** (900초)
- 최대 /tmp 스토리지: **10,240 MB** (10GB)

### ECR 이미지 관리

```bash
# 이미지 목록 확인
aws ecr describe-images --repository-name fairstay-mvp-ai --region ap-northeast-2

# 이미지 삭제 (오래된 이미지 정리)
aws ecr batch-delete-image \
  --repository-name fairstay-mvp-ai \
  --image-ids imageTag=TAG_NAME \
  --region ap-northeast-2
```

---

## ✅ 체크리스트

- [ ] AWS 액세스 키 생성 완료
- [ ] GitHub Secrets 설정 완료 (3개)
- [ ] ECR 리포지토리 생성 완료
- [ ] 코드 수정 완료 (lambda_handler.py, Dockerfile, requirements.txt)
- [ ] GitHub에 푸시 → Actions 성공 확인
- [ ] Lambda 함수 생성 완료
- [ ] Lambda 메모리/타임아웃 설정 완료
- [ ] Function URL 생성 완료
- [ ] `/health` 엔드포인트 테스트 성공
- [ ] 백엔드 `AI_SERVER_URL` 환경변수 설정 완료
- [ ] 백엔드 → AI Lambda 호출 테스트 성공

---

## 🎉 완료!

이제 AI 서버가 Lambda Container Image로 배포되었습니다!

- **비용**: 월 $0-6 (프리티어 최대 활용)
- **성능**: 1-10초 응답 (Cold/Warm)
- **관리**: 서버리스, 자동 스케일링
- **CI/CD**: 코드 푸시 → 자동 빌드 → ECR 푸시

**백엔드 통합 후 테스트** 필수!
