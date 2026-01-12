# FairStay AI 배포 가이드 (GitHub Actions + ECR + ECS EC2)

## 🎯 배포 개요

**로컬 컴퓨터 RAM 부족 문제 해결 + 비용 절감!**
- GitHub Actions에서 자동 빌드 (무료, RAM 16GB)
- ECR에 Docker 이미지 푸시
- **ECS EC2**에서 컨테이너 실행 (Fargate보다 50% 저렴!)
- ALB로 HTTP 엔드포인트 제공

**총 소요 시간: 약 40-50분 (자동 빌드 5-7분 포함)**

**예상 비용: $56-81/월** (Fargate $107/월 대비 25-47% 절감!)

---

## 📋 전체 단계

1. **AWS Access Key 생성** (5분)
2. **GitHub Secrets 설정** (2분)
3. **Git Push (자동 빌드 시작)** (1분)
4. **GitHub Actions 빌드 확인** (5-7분 대기)
5. **AWS VPC 및 네트워크 설정** (Console, 10분)
6. **IAM Role 생성 (ECS EC2용)** (Console, 5분)
7. **EC2 인스턴스 생성** (Console, 5분)
8. **ECS Cluster 생성** (Console, 5분)
9. **Task Definition 생성** (Console, 10분)
10. **Application Load Balancer 생성** (Console, 15분)
11. **ECS Service 생성** (Console, 10분)
12. **Backend Lambda 환경 변수 설정** (Console, 2분)
13. **테스트 및 검증** (5분)

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
git commit -m "Add GitHub Actions deployment with best.pt model (EC2)"

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

### 5-6. Security Group 생성 (ECS EC2용)

**VPC → 보안 그룹 → 보안 그룹 생성**

| 설정 | 값 |
|------|-----|
| **보안 그룹 이름** | `fairstay-ecs-sg` |
| **설명** | `Security group for ECS EC2 instances` |
| **VPC** | `fairstay-mvp-vpc` |

**인바운드 규칙**:
| 유형 | 포트 | 소스 | 설명 |
|------|------|------|------|
| 사용자 지정 TCP | 8000 | `fairstay-alb-sg` | ALB에서 컨테이너 접근 |
| SSH | 22 | `내 IP` | EC2 SSH 접속 (선택사항) |
| 모든 트래픽 | 모두 | `fairstay-ecs-sg` | ECS 인스턴스 간 통신 |

**[보안 그룹 생성]**

---

## 🔐 Step 6: IAM Role 생성 (ECS EC2용)

### 6-1. IAM Role 생성

**IAM Console → 역할 → 역할 만들기**

#### 6-1-1. 신뢰할 수 있는 엔터티 선택:
- **신뢰할 수 있는 엔터티 유형**: AWS 서비스
- **사용 사례**: EC2
- **[다음]**

#### 6-1-2. 권한 정책 추가:
검색해서 다음 정책 선택:
- ✅ `AmazonEC2ContainerServiceforEC2Role`
- ✅ `AmazonSSMManagedInstanceCore` (선택사항, Session Manager 사용 시)

**[다음]**

#### 6-1-3. 역할 이름:
- **역할 이름**: `ecsInstanceRole`
- **설명**: `Role for ECS EC2 instances`

**[역할 생성]**

---

## 💻 Step 7: EC2 인스턴스 생성

### 7-1. EC2 인스턴스 시작

**EC2 Console → 인스턴스 → 인스턴스 시작**

### 7-2. AMI 선택

**중요**: ECS-Optimized AMI 선택!

1. **Application and OS Images (Amazon Machine Image)**
2. **AWS Marketplace AMI** 탭 클릭
3. 검색: `ECS Optimized`
4. 선택: **Amazon ECS-Optimized Amazon Linux 2023 AMI**
5. **[선택]**

### 7-3. 인스턴스 구성

| 설정 | 값 |
|------|-----|
| **이름** | `fairstay-ecs-instance` |
| **인스턴스 유형** | `t3.large` (2 vCPU, 8GB RAM) |
| **키 페어** | 새로 생성 또는 기존 키 선택 |

**키 페어 (없으면 생성)**:
- **키 페어 이름**: `fairstay-keypair`
- **키 페어 유형**: RSA
- **프라이빗 키 파일 형식**: `.pem`
- **키 페어 생성** → `.pem` 파일 다운로드 및 안전하게 보관

### 7-4. 네트워크 설정

| 설정 | 값 |
|------|-----|
| **VPC** | `fairstay-mvp-vpc` |
| **서브넷** | `fairstay-public-subnet-1` |
| **퍼블릭 IP 자동 할당** | 활성화 |
| **방화벽(보안 그룹)** | 기존 보안 그룹 선택 |
| **보안 그룹 선택** | `fairstay-ecs-sg` |

### 7-5. 스토리지 구성

| 설정 | 값 |
|------|-----|
| **크기** | `30 GiB` |
| **볼륨 유형** | gp3 |

### 7-6. 고급 세부 정보

**IAM 인스턴스 프로파일**: `ecsInstanceRole` 선택

**사용자 데이터** (텍스트 입력):
```bash
#!/bin/bash
echo ECS_CLUSTER=fairstay-mvp-cluster >> /etc/ecs/ecs.config
```

**[인스턴스 시작]**

### 7-7. 인스턴스 시작 확인

**EC2 Console → 인스턴스**

상태가 `running`이 될 때까지 2-3분 대기

---

## 🐳 Step 8: ECS Cluster 생성 (Console)

**AWS Console → ECS → 클러스터 → 클러스터 생성**

| 설정 | 값 |
|------|-----|
| **클러스터 이름** | `fairstay-mvp-cluster` |
| **네트워킹** | VPC: `fairstay-mvp-vpc` |
| **서브넷** | `fairstay-public-subnet-1`, `fairstay-public-subnet-2` |
| **인프라** | Amazon EC2 인스턴스 ✅ |

**인프라 세부 정보**:
- **자동 크기 조정 그룹** 생성 안 함 (수동으로 EC2 생성했으므로)
- **용량 공급자**: 기본값

**모니터링 (선택사항)**:
- Container Insights 활성화 (권장)

**[생성]**

### 8-1. EC2 인스턴스 등록 확인

**ECS Console → 클러스터 → `fairstay-mvp-cluster` → 인프라 탭**

**컨테이너 인스턴스**: `1개 등록됨` 확인 (2-5분 소요)

**만약 등록 안 되면**:
1. EC2 인스턴스 상태 확인 (running?)
2. IAM Role 확인 (ecsInstanceRole?)
3. 사용자 데이터 확인 (ECS_CLUSTER 설정?)
4. EC2 재부팅

---

## 📝 Step 9: Task Definition 생성 (Console)

**ECS → 태스크 정의 → 새 태스크 정의 생성**

### 9-1. 태스크 정의 구성

| 설정 | 값 |
|------|-----|
| **태스크 정의 패밀리 이름** | `fairstay-ai-task` |
| **시작 유형** | EC2 |
| **네트워크 모드** | bridge |
| **태스크 실행 역할** | ecsTaskExecutionRole (자동 생성) |
| **태스크 역할** | 없음 |

### 9-2. 태스크 크기

| 설정 | 값 |
|------|-----|
| **태스크 메모리** | `6144 MB` (EC2 8GB의 75%) |
| **태스크 CPU** | `1024` (1 vCPU) |

### 9-3. 컨테이너 정의

**컨테이너 추가** 버튼 클릭

| 설정 | 값 |
|------|-----|
| **컨테이너 이름** | `fairstay-ai-container` |
| **이미지 URI** | `897722707561.dkr.ecr.ap-northeast-2.amazonaws.com/fairstay-mvp-ai:latest` |
| **메모리 제한** | 하드 제한: `6144 MB` |
| **포트 매핑** | |
| - 호스트 포트 | `0` (동적 포트 할당) |
| - 컨테이너 포트 | `8000` |
| - 프로토콜 | TCP |

**환경 변수** (선택사항):
| 키 | 값 |
|-----|-----|
| `MODEL_PATH` | `best.pt` |
| `SAVE_DIR` | `/tmp/result` |

**로그 구성**:
- **로그 드라이버**: awslogs
- **로그 그룹**: `/ecs/fairstay-ai-task` (자동 생성)
- **리전**: `ap-northeast-2`
- **로그 스트림 접두사**: `ecs`

**[추가]** → **[생성]**

---

## ⚖️ Step 10: Application Load Balancer 생성 (Console)

**EC2 → 로드 밸런서 → Load Balancer 생성 → Application Load Balancer**

### 10-1. 기본 구성

| 설정 | 값 |
|------|-----|
| **Load Balancer 이름** | `fairstay-ai-alb` |
| **체계** | 인터넷 경계 (Internet-facing) |
| **IP 주소 유형** | IPv4 |

### 10-2. 네트워크 매핑

| 설정 | 값 |
|------|-----|
| **VPC** | `fairstay-mvp-vpc` |
| **가용 영역** | ✅ `ap-northeast-2a` → `fairstay-public-subnet-1` |
|  | ✅ `ap-northeast-2c` → `fairstay-public-subnet-2` |

### 10-3. 보안 그룹

**기존 보안 그룹 선택**: `fairstay-alb-sg`

### 10-4. 대상 그룹 생성

**대상 그룹 생성** 클릭 (새 창):

| 설정 | 값 |
|------|-----|
| **대상 유형** | 인스턴스 (EC2 모드) |
| **대상 그룹 이름** | `fairstay-ai-tg` |
| **프로토콜** | HTTP |
| **포트** | `80` (동적 포트 사용하므로 의미 없음) |
| **VPC** | `fairstay-mvp-vpc` |
| **프로토콜 버전** | HTTP1 |

**Health Check 설정**:
| 설정 | 값 |
|------|-----|
| **Health Check 프로토콜** | HTTP |
| **Health Check 경로** | `/health` |
| **간격** | 30초 |
| **제한 시간** | 5초 |
| **정상 임계값** | 2 |
| **비정상 임계값** | 2 |

**고급 health check 설정**:
| 설정 | 값 |
|------|-----|
| **포트** | 트래픽 포트 (동적 포트 자동 감지) |
| **정상 상태 코드** | 200 |

**대상 등록 (지금은 건너뛰기)**:
- ECS Service가 자동으로 등록함
- **[대상 그룹 생성]**

ALB 화면으로 돌아가서 생성한 대상 그룹 선택

### 10-5. 리스너 설정

**리스너**:
| 프로토콜 | 포트 | 기본 작업 |
|---------|------|----------|
| HTTP | 80 | `fairstay-ai-tg`로 전달 |

**[Load Balancer 생성]**

**대기**: ALB 상태가 `active`가 될 때까지 2-3분 대기

---

## 🚢 Step 11: ECS Service 생성 (Console)

**ECS → 클러스터 → `fairstay-mvp-cluster` → 서비스 탭 → 생성**

### 11-1. 환경

| 설정 | 값 |
|------|-----|
| **컴퓨팅 옵션** | 시작 유형 |
| **시작 유형** | EC2 |

### 11-2. 배포 구성

| 설정 | 값 |
|------|-----|
| **패밀리** | `fairstay-ai-task` |
| **서비스 이름** | `fairstay-ai-service` |
| **서비스 유형** | 복제본 |
| **원하는 작업 수** | `1` |

### 11-3. 배치

| 설정 | 값 |
|------|-----|
| **배치 전략** | AZ Balanced Spread (기본값) |
| **작업 배치 제약 조건** | 없음 |

### 11-4. 로드 밸런싱

| 설정 | 값 |
|------|-----|
| **로드 밸런서 유형** | Application Load Balancer |
| **로드 밸런서** | `fairstay-ai-alb` |
| **리스너** | 80:HTTP |
| **대상 그룹** | `fairstay-ai-tg` |
| **컨테이너** | `fairstay-ai-container:8000` |
| **상태 확인 유예 기간** | 60초 |

**[생성]**

### 11-5. 배포 확인

1. **ECS → 클러스터 → 서비스 → `fairstay-ai-service`**
2. **작업 탭**: Task가 `RUNNING` 상태 확인 (2-3분 소요)
3. **이벤트 탭**: 배포 로그 확인

**만약 Task가 시작 안 되면**:
- CloudWatch Logs 확인: `/ecs/fairstay-ai-task`
- EC2 인스턴스 메모리/CPU 확인
- Security Group 확인

---

## 🌐 Step 12: ALB DNS 확인 및 테스트

### 12-1. ALB DNS 이름 확인

**EC2 → 로드 밸런서 → `fairstay-ai-alb`**

**DNS 이름** 복사:
```
fairstay-ai-alb-1234567890.ap-northeast-2.elb.amazonaws.com
```

### 12-2. Target Group Health Check 확인

**EC2 → 대상 그룹 → `fairstay-ai-tg` → 대상 탭**

**상태**: `healthy` 확인 (1-2분 소요)

**만약 unhealthy**:
- Health check 경로 확인 (`/health`)
- Security Group 확인 (ALB → EC2:8000 허용?)
- 컨테이너 로그 확인

### 12-3. Health Check 테스트

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

### 12-4. 이미지 분석 테스트

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

## 🔗 Step 13: Backend Lambda 환경 변수 설정

### 13-1. Backend Lambda 환경 변수 추가

**Lambda Console → Backend Lambda 함수 → 구성 → 환경 변수 → 편집**

**새 환경 변수 추가**:
| 키 | 값 |
|-----|-----|
| `AI_SERVER_URL` | `http://fairstay-ai-alb-1234567890.ap-northeast-2.elb.amazonaws.com` |

**[저장]**

### 13-2. Backend 통합 테스트

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

## 💰 예상 비용 (EC2)

### 온디맨드 인스턴스
- **EC2 t3.large**: 2 vCPU, 8GB RAM
  - 시간당: $0.0832
  - **월 비용 (24시간)**: ~$60/월

### Application Load Balancer
- ALB 시간: $0.0225/시간 = **$16/월**
- LCU: **~$5-10/월** (트래픽에 따라)

### ECR (이미지 저장)
- 스토리지: 3GB × $0.10/GB/월 = **$0.3/월**

### EBS 볼륨
- gp3 30GB: $0.08/GB/월 = **$2.4/월**

### **총 예상 비용 (온디맨드): $83-88/월**

---

## 💰 비용 절감 옵션

### 1. Reserved Instance (1년 약정)
- **EC2 t3.large 예약**: ~$35/월 (42% 할인)
- **총 비용**: **$58-63/월** (35% 절감!)

### 2. Spot Instance (중단 가능)
- **EC2 t3.large Spot**: ~$18-25/월 (70% 할인)
- **총 비용**: **$41-48/월** (55% 절감!)
- **주의**: 가격 변동 시 중단 가능 (프로덕션 비추천)

### 3. Savings Plans (유연한 약정)
- 1년/3년 약정 시 20-40% 할인
- EC2 타입 변경 가능

---

## 📊 Fargate vs EC2 비용 비교

| 항목 | Fargate | EC2 (온디맨드) | EC2 (예약) |
|------|---------|---------------|-----------|
| **컴퓨팅** | $86/월 | $60/월 | $35/월 |
| **ALB** | $21/월 | $21/월 | $21/월 |
| **ECR** | $0.3/월 | $0.3/월 | $0.3/월 |
| **EBS** | - | $2.4/월 | $2.4/월 |
| **총합** | **$107/월** | **$83/월** | **$58/월** |
| **절감** | - | 22% | 46% |

**결론**: EC2 예약 인스턴스 사용 시 **월 $49 절감!**

---

## 🔧 EC2 관리 팁

### Auto Scaling (선택사항)
트래픽 증가 시 EC2 인스턴스 자동 추가:

**ECS → 클러스터 → 용량 공급자 → Auto Scaling 그룹 생성**

### 모니터링
- **CloudWatch**: CPU, 메모리 사용률 모니터링
- **Container Insights**: 컨테이너별 상세 메트릭
- **알람 설정**: CPU 80% 초과 시 알림

### 백업
- **AMI 스냅샷**: EC2 인스턴스 정기 백업
- **EBS 스냅샷**: 데이터 백업

### SSH 접속 (필요 시)
```bash
chmod 400 fairstay-keypair.pem
ssh -i fairstay-keypair.pem ec2-user@<EC2-Public-IP>
```

---

## 🐛 트러블슈팅

### GitHub Actions 빌드 실패
- **Actions 탭에서 로그 확인**
- AWS Secrets 올바르게 설정되었는지 확인
- ECR 리포지토리 존재 확인

### EC2 인스턴스가 ECS Cluster에 등록 안 됨
1. **IAM Role 확인**: `ecsInstanceRole` 연결 확인
2. **사용자 데이터 확인**: ECS_CLUSTER 설정 확인
3. **EC2 인스턴스 로그**:
   ```bash
   ssh -i key.pem ec2-user@<EC2-IP>
   cat /var/log/ecs/ecs-agent.log
   ```
4. **ECS Agent 재시작**:
   ```bash
   sudo systemctl restart ecs
   ```

### ECS Task가 시작되지 않음
- **CloudWatch Logs 확인**: `/ecs/fairstay-ai-task`
- **EC2 메모리 부족**: Task 메모리를 4096MB로 줄여보기
- **ECR 이미지 URI** 확인
- **EC2 인스턴스 용량** 확인 (메모리, CPU 충분?)

### Health Check 실패
- **Security Group 확인**: ALB → EC2:8000 허용?
- **컨테이너 로그 확인**: `/health` 엔드포인트 정상 응답?
- **동적 포트 확인**: Task 실행 시 할당된 호스트 포트 확인

### ALB에서 502/503 에러
- **Target Group Health** 확인: Healthy?
- **ECS Task 상태**: RUNNING?
- **Security Group 규칙**: ALB SG → ECS SG 허용?
- **컨테이너 포트**: 8000 정상 리스닝?

### EC2 인스턴스 SSH 접속 안 됨
- **보안 그룹**: SSH 포트 22 허용?
- **키 페어 권한**: `chmod 400 key.pem`
- **Public IP**: 할당되어 있나?
- **Session Manager 사용**: SSH 대신 AWS Console에서 접속

---

## ✅ 배포 완료!

**AI 서버 엔드포인트**: `http://fairstay-ai-alb-xxxxx.elb.amazonaws.com`

**Backend Lambda 환경 변수**: `AI_SERVER_URL` 설정 완료 ✅

**자동 배포**: Git push만 하면 GitHub Actions가 자동 배포! 🚀

**비용**: $58-88/월 (Fargate 대비 22-46% 절감!)

---

## 📚 다음 단계

### 1. HTTPS 설정 (추천!)
- AWS Certificate Manager에서 SSL 인증서 생성
- ALB에 HTTPS 리스너 추가 (443 포트)
- HTTP → HTTPS 리디렉션 설정

### 2. Auto Scaling 설정
- EC2 Auto Scaling 그룹 생성
- CPU/메모리 기반 자동 확장
- 트래픽 증가 시 인스턴스 자동 추가

### 3. Reserved Instance 구매 (비용 절감!)
- 1년 약정으로 42% 할인
- 월 $49 절감 → 연간 $588 절감!

### 4. 모니터링 강화
- CloudWatch 알람 설정
- Container Insights 활성화
- 로그 보존 기간 설정

### 5. 프로덕션 최적화
- CORS `allow_origins`를 특정 도메인으로 제한
- CloudFront CDN 추가 (결과 이미지 캐싱)
- WAF (Web Application Firewall) 추가

### 6. 백업 및 재해 복구
- AMI 정기 스냅샷
- Multi-AZ 배포 (고가용성)
- 재해 복구 계획 수립
