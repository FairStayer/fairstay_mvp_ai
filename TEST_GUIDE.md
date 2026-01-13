# 🧪 테스트 가이드

## 테스트 코드 설명

`test_api.py`는 FairStay AI 서버의 모든 엔드포인트를 자동으로 테스트합니다.

## 테스트 항목

### 1. **Root Endpoint** (GET `/`)
- 서버 기본 health check
- 응답 형식 검증

### 2. **Health Check** (GET `/health`)
- 백엔드가 사용하는 health check
- 모델 로딩 상태 확인
- 필수 필드: `status`, `model_loaded`

### 3. **Detect Crack - 'file' 필드** (POST `/detect-crack`)
- 백엔드가 사용하는 필드명 (`file`)
- Crack 패턴 이미지 전송
- 응답 구조 검증:
  - `file_id`: 결과 이미지 ID
  - `image_url`: 결과 이미지 경로
  - `has_crack`: Crack 감지 여부
  - `confidence`: 신뢰도 점수
  - `crack_count`: 감지된 crack 개수
  - `bounding_boxes`: 각 crack의 위치 정보

### 4. **Detect Crack - 'image' 필드** (POST `/detect-crack`)
- 대체 필드명 (`image`) 테스트
- Crack 없는 이미지 전송
- 서버 호환성 검증

### 5. **Get Result Image** (GET `/result/{file_id}`)
- 처리된 이미지 다운로드
- Content-Type 검증 (image/jpeg)
- 로컬 파일 저장

### 6. **Invalid Image**
- 잘못된 이미지 파일 업로드
- 에러 핸들링 검증 (400 Bad Request)

### 7. **Missing File**
- 파일 없이 요청 전송
- 에러 핸들링 검증 (400/422)

---

## 사용 방법

### 1. 로컬 서버 테스트

```bash
# FastAPI 서버 실행
python main.py

# 새 터미널에서 테스트 실행
python test_api.py
```

### 2. Lambda Function URL 테스트

```bash
# 환경변수로 설정
export AI_SERVER_URL=https://abc123.lambda-url.ap-northeast-2.on.aws
python test_api.py

# 또는 직접 인자로 전달
python test_api.py https://abc123.lambda-url.ap-northeast-2.on.aws
```

### 3. 도움말

```bash
python test_api.py --help
```

---

## 필요한 패키지 설치

```bash
pip install requests pillow numpy
```

---

## 테스트 결과 예시

```
🚀 FairStay AI API Testing Suite
Testing server: http://localhost:8000

============================================================
Test 1: Root Endpoint (GET /)
============================================================

ℹ️  Status Code: 200
ℹ️  Response: {
  "message": "Welcome to FairStay AI",
  "status": "ok"
}
✅ Root endpoint working correctly

============================================================
Test 2: Health Check (GET /health)
============================================================

ℹ️  Status Code: 200
ℹ️  Response: {
  "status": "healthy",
  "model_loaded": true,
  "model_path": "best.pt",
  "save_dir": "/tmp/result"
}
✅ Health check passed - Model loaded successfully

============================================================
Test 3: Detect Crack (POST /detect-crack) - 'file' field
============================================================

ℹ️  Sending POST request with test image...
ℹ️  Status Code: 200
ℹ️  Response: {
  "file_id": "abc-123-xyz",
  "image_url": "/result/abc-123-xyz",
  "has_crack": true,
  "confidence": 0.8523,
  "crack_count": 2,
  "bounding_boxes": [...]
}
✅ Crack detection successful
ℹ️    - File ID: abc-123-xyz
ℹ️    - Image URL: /result/abc-123-xyz
ℹ️    - Has Crack: True
ℹ️    - Confidence: 0.8523
ℹ️    - Crack Count: 2

...

============================================================
Test Results Summary
============================================================

PASS - Root Endpoint
PASS - Health Check
PASS - Detect Crack (file field)
PASS - Detect Crack (image field)
PASS - Get Result Image
PASS - Invalid Image
PASS - Missing File

Total: 7/7 tests passed
🎉 All tests passed!
```

---

## CI/CD에서 사용

GitHub Actions에서 Lambda 배포 후 자동 테스트:

```yaml
# .github/workflows/deploy.yml에 추가

- name: Test Lambda Function
  run: |
    pip install requests pillow numpy
    python test_api.py ${{ secrets.LAMBDA_FUNCTION_URL }}
```

---

## 주의사항

### Lambda Cold Start
- 첫 테스트는 5-10초 소요 가능
- Cold start 시 타임아웃 증가 권장:
  ```python
  response = requests.post(..., timeout=60)
  ```

### 결과 이미지 저장
- 테스트 실행 후 `test_result_*.jpg` 파일 생성됨
- Crack detection 결과를 시각적으로 확인 가능
- `.gitignore`에 추가 권장:
  ```
  test_result_*.jpg
  ```

### Lambda /tmp 제한
- Lambda `/tmp`는 512MB 제한 (설정 가능)
- 많은 요청 시 이미지 파일 축적 가능
- 주기적으로 정리하거나 Lambda 재시작

---

## 트러블슈팅

### Connection refused
```
❌ Request failed: HTTPConnectionPool(host='localhost', port=8000): Max retries exceeded
```
→ FastAPI 서버가 실행 중인지 확인

### Timeout
```
❌ Request failed: HTTPSConnectionPool(...): Read timed out.
```
→ Lambda Cold start 또는 모델 로딩 중
→ `timeout=60` 이상 설정

### 400 Bad Request
```
❌ Expected status 200, got 400
```
→ `main.py`의 필드명 확인 (`file` vs `image`)
→ 백엔드 코드와 일치하는지 확인

---

## 백엔드 통합 테스트

백엔드에서 AI 서버 호출 테스트:

```typescript
// backend/test/ai.test.ts
import { analyzeImage, checkAIServerHealth } from '../services/ai.service';

describe('AI Service Integration', () => {
  it('should check AI server health', async () => {
    const isHealthy = await checkAIServerHealth();
    expect(isHealthy).toBe(true);
  });

  it('should analyze image and return results', async () => {
    const imageUrl = 'https://example.com/test-image.jpg';
    const result = await analyzeImage(imageUrl);
    
    expect(result).toHaveProperty('processedImageUrl');
    expect(result).toHaveProperty('damages');
    expect(Array.isArray(result.damages)).toBe(true);
  });
});
```
