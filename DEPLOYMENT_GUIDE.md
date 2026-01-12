# FairStay AI 배포 가이드 (GitHub Actions + ECR + ECS Fargate)

## 🎯 배포 개요

**로컬 컴퓨터 RAM 부족 문제 해결!**
- GitHub Actions에서 자동 빌드 (무료, RAM 16GB)
- ECR에 Docker 이미지 푸시
- ECS Fargate에서 컨테이너 실행
- ALB로 HTTP 엔드포인트 제공

**총 소요 시간: 약 30-40분 (자동 빌드 5-7분 포함)**

---

## 📋 전체 단계

1. **AWS Access Key 생성** (5분)
2. **GitHub Secrets 설정** (2분)
3. **Git Push (자동 빌드 시작)** (1분)
4. **GitHub Actions 빌드 확인** (5-7분 대기)
5. **AWS VPC 및 네트워크 설정** (Console, 10분)
6. **ECS Cluster 생성** (Console, 5분)
7. **Task Definition 생성** (Console, 10분)
8. **Application Load Balancer 생성** (Console, 15분)
9. **ECS Service 생성** (Console, 10분)
10. **Backend Lambda 환경 변수 설정** (Console, 2분)
11. **테스트 및 검증** (5분)

---

## 🔑 Step 1: AWS Access Key 생성

### 1-1. IAM 사용자 확인

**AWS Console → IAM → Users**

기존 사용자가 있으면 그대로 사용, 없으면 새로 생성:
- User name: `github-actions-user`
- 권한: `AmazonEC2ContainerRegistryFullAccess`, `AmazonECS_FullAccess`

### 1-2. Access Key 생성

1. IAM → Users → (사용자 선택)
2. **Security credentials** 탭
3. **Create access key**
4. Use case: **Command Line Interface (CLI)** 선택
5. **Next** → **Create access key**

**⚠️ 중요: Access Key 정보 저장!**
```
Access key ID: AKIA...
Secret access key: wJa...
```

**이 정보는 한 번만 표시됩니다!** 메모장에 복사해두세요!

---

## 🔐 Step 2: GitHub Secrets 설정

### 2-1. GitHub 저장소 페이지 이동

```
https://github.com/FairStayer/fairstay_mvp_ai
```

### 2-2. Secrets 설정

**Settings → Secrets and variables → Actions → New repository secret**

**추가할 Secret 2개:**

#### Secret 1:
- **Name**: `AWS_ACCESS_KEY_ID`
- **Value**: `AKIA...` (Step 1에서 복사한 Access Key ID)
- **Add secret** 클릭

#### Secret 2:
- **Name**: `AWS_SECRET_ACCESS_KEY`
- **Value**: `wJa...` (Step 1에서 복사한 Secret Access Key)
- **Add secret** 클릭

---

## 🚀 Step 3: Git Push (자동 빌드 시작)

### 3-1. 변경 사항 커밋 & 푸시

터미널에서 실행:

```bash
cd /Users/susie/Desktop/Temp_Laptop3/Solidity_Files/Yn/fairstay_mvp_ai

# 현재 상태 확인
git status

# 모든 변경사항 추가
git add .

# 커밋
git commit -m "Add GitHub Actions deployment with best.pt model"

# GitHub에 푸시 (자동 빌드 시작!)
git push origin main
```

### 3-2. 빌드 자동 시작 확인

푸시 직후:
```
https://github.com/FairStayer/fairstay_mvp_ai/actions
```

페이지에서 **노란색 점** 표시 확인! (빌드 진행 중)

---

## ⏳ Step 4: GitHub Actions 빌드 확인

### 4-1. 빌드 로그 확인

**Actions 탭 → 최신 워크플로우 클릭**

진행 상태:
```
✓ Checkout code
✓ Configure AWS credentials
✓ Login to Amazon ECR
🔄 Build, tag, and push image to Amazon ECR (5-7분 소요)
```

### 4-2. 빌드 완료 대기

**예상 소요 시간: 5-7분**

빌드 단계:
1. OpenCV 설치 (1분)
2. PyTorch 다운로드 (3-4분)
3. 기타 패키지 설치 (1분)
4. ECR 푸시 (1분)

### 4-3. 빌드 성공 확인

녹색 체크 표시 ✅ 와 함께 다음 메시지 확인:
```
✅ Deployment completed successfully!
🐳 Image: 897722707561.dkr.ecr.ap-northeast-2.amazonaws.com/fairstay-mvp-ai:latest
```

**이제 이미지가 ECR에 업로드되었어요!**

---

## 🌐 Step 5: VPC 및 네트워크 설정 (Console)

### 5-1. VPC 생성

**AWS Console → VPC → VPC 생성**

| 설정 | 값 |
|------|-----|
| **이름** | `fairstay-mvp-vpc` |
| **IPv4 CIDR** | `10.0.0.0/16` |

**[VPC 생성]**

### 5-2. Public Subnet 2개 생성

**VPC → 서브넷 → 서브넷 생성**

#### Subnet 1:
| 설정 | 값 |
|------|-----|
| **VPC** | `fairstay-mvp-vpc` |
| **서브넷 이름** | `fairstay-public-subnet-1` |
| **가용 영역** | `ap-northeast-2a` |
| **IPv4 CIDR** | `10.0.1.0/24` |

#### Subnet 2:
| 설정 | 값 |
|------|-----|
| **VPC** | `fairstay-mvp-vpc` |
| **서브넷 이름** | `fairstay-public-subnet-2` |
| **가용 영역** | `ap-northeast-2c` |
| **IPv4 CIDR** | `10.0.2.0/24` |

**[서브넷 생성]**

### 5-3. Internet Gateway 생성 및 연결

**VPC → 인터넷 게이트웨이 → 인터넷 게이트웨이 생성**

| 설정 | 값 |
|------|-----|
| **이름** | `fairstay-igw` |

**[인터넷 게이트웨이 생성]** 후:
1. 생성된 IGW 선택
2. **작업 → VPC에 연결**
3. VPC: `fairstay-mvp-vpc` 선택
4. **[연결]**

### 5-4. 라우팅 테이블 설정

**VPC → 라우팅 테이블**

1. `fairstay-mvp-vpc`의 메인 라우팅 테이블 선택
2. **라우팅 탭 → 라우팅 편집**
3. **라우팅 추가**:
   - **대상**: `0.0.0.0/0`
   - **타겟**: `fairstay-igw`
4. **[변경 사항 저장]**

5. **서브넷 연결 탭 → 서브넷 연결 편집**
6. 두 Subnet 체크:
   - `fairstay-public-subnet-1`
   - `fairstay-public-subnet-2`
7. **[연결 저장]**

### 5-5. Security Group 생성 (ALB용)

**VPC → 보안 그룹 → 보안 그룹 생성**

| 설정 | 값 |
|------|-----|
| **보안 그룹 이름** | `fairstay-alb-sg` |
| **설명** | `Security group for Application Load Balancer` |
| **VPC** | `fairstay-mvp-vpc` |

**인바운드 규칙**:
| 유형 | 포트 | 소스 |
|------|------|------|
| HTTP | 80 | `0.0.0.0/0` |

**[보안 그룹 생성]**

### 5-6. Security Group 생성 (ECS Task용)

**VPC → 보안 그룹 → 보안 그룹 생성**

| 설정 | 값 |
|------|-----|
| **보안 그룹 이름** | `fairstay-ecs-sg` |
| **설명** | `Security group for ECS tasks` |
| **VPC** | `fairstay-mvp-vpc` |

**인바운드 규칙**:
| 유형 | 포트 | 소스 |
|------|------|------|
| 사용자 지정 TCP | 8000 | `fairstay-alb-sg` (ALB 보안 그룹 선택) |

**[보안 그룹 생성]**

---

## 🐳 Step 6: ECS Cluster 생성 (Console)

**AWS Console → ECS → 클러스터 → 클러스터 생성**

| 설정 | 값 |
|------|-----|
| **클러스터 이름** | `fairstay-mvp-cluster` |
| **네트워킹** | VPC: `fairstay-mvp-vpc` |
| **서브넷** | `fairstay-public-subnet-1`, `fairstay-public-subnet-2` |
| **인프라** | AWS Fargate (서버리스) ✅ |

**[생성]**

---

## 📝 Step 7: Task Definition 생성 (Console)

**ECS → 태스크 정의 → 새 태스크 정의 생성**

### 7-1. 태스크 정의 구성

| 설정 | 값 |
|------|-----|
| **태스크 정의 패밀리 이름** | `fairstay-ai-task` |
| **시작 유형** | AWS Fargate |
| **운영 체제/아키텍처** | Linux/X86_64 |
| **네트워크 모드** | awsvpc |
| **태스크 실행 역할** | ecsTaskExecutionRole (자동 생성) |
| **CPU** | `2 vCPU` (2048) |
| **메모리** | `8 GB` (8192 MB) |

### 7-2. 컨테이너 정의

**컨테이너 추가** 버튼 클릭

| 설정 | 값 |
|------|-----|
| **컨테이너 이름** | `fairstay-ai-container` |
| **이미지 URI** | `897722707561.dkr.ecr.ap-northeast-2.amazonaws.com/fairstay-mvp-ai:latest` |
| **포트 매핑** | 컨테이너 포트: `8000` / 프로토콜: TCP |

**로그 구성**:
- **로그 드라이버**: awslogs
- **로그 그룹**: `/ecs/fairstay-ai-task` (자동 생성)

**[추가]** → **[생성]**

---

## ⚖️ Step 8: Application Load Balancer 생성 (Console)

**EC2 → 로드 밸런서 → Load Balancer 생성 → Application Load Balancer**

### 8-1. 기본 구성

| 설정 | 값 |
|------|-----|
| **Load Balancer 이름** | `fairstay-ai-alb` |
| **체계** | 인터넷 경계 (Internet-facing) |
| **IP 주소 유형** | IPv4 |

### 8-2. 네트워크 매핑

| 설정 | 값 |
|------|-----|
| **VPC** | `fairstay-mvp-vpc` |
| **가용 영역** | ✅ `ap-northeast-2a` → `fairstay-public-subnet-1` |
|  | ✅ `ap-northeast-2c` → `fairstay-public-subnet-2` |

### 8-3. 보안 그룹

**기존 보안 그룹 선택**: `fairstay-alb-sg`

### 8-4. 대상 그룹 생성

**대상 그룹 생성** 클릭 (새 창):

| 설정 | 값 |
|------|-----|
| **대상 유형** | IP 주소 (Fargate는 IP 모드) |
| **대상 그룹 이름** | `fairstay-ai-tg` |
| **프로토콜** | HTTP |
| **포트** | `8000` |
| **VPC** | `fairstay-mvp-vpc` |
| **프로토콜 버전** | HTTP1 |

**Health Check 설정**:
| 설정 | 값 |
|------|-----|
| **Health Check 경로** | `/health` |
| **간격** | 30초 |
| **제한 시간** | 5초 |
| **정상 임계값** | 2 |
| **비정상 임계값** | 2 |

**[대상 그룹 생성]** 후 ALB 화면으로 돌아가서 선택

### 8-5. 리스너 설정

**리스너**:
| 프로토콜 | 포트 | 기본 작업 |
|---------|------|----------|
| HTTP | 80 | `fairstay-ai-tg`로 전달 |

**[Load Balancer 생성]**

**대기**: ALB 상태가 `active`가 될 때까지 2-3분 대기

---

## 🚢 Step 9: ECS Service 생성 (Console)

**ECS → 클러스터 → `fairstay-mvp-cluster` → 서비스 탭 → 생성**

### 9-1. 환경

| 설정 | 값 |
|------|-----|
| **컴퓨팅 옵션** | 시작 유형 |
| **시작 유형** | FARGATE |

### 9-2. 배포 구성

| 설정 | 값 |
|------|-----|
| **패밀리** | `fairstay-ai-task` |
| **서비스 이름** | `fairstay-ai-service` |
| **서비스 유형** | 복제본 |
| **원하는 작업 수** | `1` |

### 9-3. 네트워킹

| 설정 | 값 |
|------|-----|
| **VPC** | `fairstay-mvp-vpc` |
| **서브넷** | `fairstay-public-subnet-1`, `fairstay-public-subnet-2` |
| **보안 그룹** | `fairstay-ecs-sg` |
| **퍼블릭 IP** | ✅ 활성화 (TURNED ON) |

### 9-4. 로드 밸런싱

| 설정 | 값 |
|------|-----|
| **로드 밸런서 유형** | Application Load Balancer |
| **로드 밸런서** | `fairstay-ai-alb` |
| **리스너** | 80:HTTP |
| **대상 그룹** | `fairstay-ai-tg` |
| **상태 확인 유예 기간** | 60초 |

**[생성]**

### 9-5. 배포 확인

1. **ECS → 클러스터 → 서비스 → `fairstay-ai-service`**
2. **작업 탭**: Task가 `RUNNING` 상태 확인 (2-3분 소요)
3. **이벤트 탭**: 배포 로그 확인

---

## 🌐 Step 10: ALB DNS 확인 및 테스트

### 10-1. ALB DNS 이름 확인

**EC2 → 로드 밸런서 → `fairstay-ai-alb`**

**DNS 이름** 복사:
```
fairstay-ai-alb-1234567890.ap-northeast-2.elb.amazonaws.com
```

### 10-2. Health Check 테스트

터미널에서:
```bash
curl http://fairstay-ai-alb-1234567890.ap-northeast-2.elb.amazonaws.com/health
```

**예상 응답**:
```json
{
  "status": "healthy",
  "model_loaded": true,
  "model_path": "best.pt",
  "save_dir": "/tmp/result"
}
```

### 10-3. 이미지 분석 테스트

```bash
curl -X POST \
  http://fairstay-ai-alb-1234567890.ap-northeast-2.elb.amazonaws.com/detect-crack \
  -F "image=@test.jpg"
```

**예상 응답**:
```json
{
  "image_url": "/result/uuid-here"
}
```

---

## 🔗 Step 11: Backend Lambda 환경 변수 설정

### 11-1. Backend Lambda 환경 변수 추가

**Lambda Console → Backend Lambda 함수 → 구성 → 환경 변수 → 편집**

**새 환경 변수 추가**:
| 키 | 값 |
|-----|-----|
| `AI_SERVER_URL` | `http://fairstay-ai-alb-1234567890.ap-northeast-2.elb.amazonaws.com` |

**[저장]**

### 11-2. Backend 통합 테스트

**Lambda Console → Backend Lambda → 테스트**

테스트 이벤트로 실행 → AI 서버 호출 성공 확인!

---

## 🔄 코드 업데이트 시 재배포

### 수정 후 재배포:

```bash
# 코드 수정 후
git add .
git commit -m "Update AI model"
git push

# GitHub Actions가 자동으로:
# 1. Docker 이미지 빌드
# 2. ECR에 푸시
# 3. 완료!
```

### ECS Service 업데이트:

**ECS Console → 클러스터 → 서비스 → `fairstay-ai-service`**

**[업데이트]** → **[새 배포 강제 적용]** 체크 → **[업데이트]**

---

## 💰 예상 비용

### ECS Fargate (24시간 실행)
- CPU: 2 vCPU × $0.04048/시간 = $0.08096/시간
- 메모리: 8GB × $0.004445/GB/시간 = $0.03556/시간
- **합계**: ~$0.12/시간 = **$86/월**

### Application Load Balancer
- ALB 시간: $0.0225/시간 = **$16/월**
- LCU: **~$5-10/월** (트래픽에 따라)

### ECR (이미지 저장)
- 스토리지: 3GB × $0.10/GB/월 = **$0.3/월**

### **총 예상 비용: 약 $107-112/월**

### 비용 절감:
- Fargate Spot 사용: 70% 할인
- Auto Scaling: 사용량 적으면 Task 0으로 축소

---

## 🐛 트러블슈팅

### GitHub Actions 빌드 실패
- **Actions 탭에서 로그 확인**
- AWS Secrets 올바르게 설정되었는지 확인
- ECR 리포지토리 존재 확인

### ECS Task가 시작되지 않음
- **CloudWatch Logs 확인**: `/ecs/fairstay-ai-task`
- ECR 이미지 URI가 올바른지 확인
- Task Definition 메모리/CPU 충분한지 확인

### Health Check 실패
- Security Group 포트 8000 열렸는지 확인
- `/health` 엔드포인트 정상 응답 확인
- Task 로그에서 모델 로딩 실패 여부 확인

### ALB에서 502/503 에러
- Target Group Health Check 상태 확인
- ECS Task가 `RUNNING` 상태인지 확인
- Security Group 규칙 확인 (ALB → ECS)

---

## ✅ 배포 완료!

**AI 서버 엔드포인트**: `http://fairstay-ai-alb-xxxxx.elb.amazonaws.com`

**Backend Lambda 환경 변수**: `AI_SERVER_URL` 설정 완료 ✅

**자동 배포**: Git push만 하면 GitHub Actions가 자동 배포! 🚀

---

## 📚 다음 단계

1. **HTTPS 설정** (선택사항)
   - AWS Certificate Manager에서 SSL 인증서 생성
   - ALB에 HTTPS 리스너 추가

2. **Auto Scaling 설정** (선택사항)
   - ECS Service Auto Scaling 활성화
   - CPU/메모리 기반 자동 확장

3. **모니터링**
   - CloudWatch Container Insights 활성화
   - 알람 설정 (CPU, 메모리, 에러율)

4. **프로덕션 최적화**
   - CORS `allow_origins`를 특정 도메인으로 제한
   - CloudFront CDN 추가 (결과 이미지 캐싱)
