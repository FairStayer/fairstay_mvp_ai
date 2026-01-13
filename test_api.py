"""
FairStay AI API 테스트 스크립트
모든 엔드포인트를 테스트하고 응답 구조를 검증합니다.
"""

import requests
import json
import os
import sys
from io import BytesIO
from PIL import Image
import numpy as np

# 테스트할 서버 URL (로컬 또는 Lambda Function URL)
# 환경변수로 설정하거나 직접 입력
BASE_URL = os.environ.get("AI_SERVER_URL", "http://localhost:8000")

# 색상 코드 (터미널 출력용)
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
RESET = "\033[0m"
BOLD = "\033[1m"


def print_header(text: str):
    """테스트 섹션 헤더 출력"""
    print(f"\n{BOLD}{BLUE}{'=' * 60}{RESET}")
    print(f"{BOLD}{BLUE}{text}{RESET}")
    print(f"{BOLD}{BLUE}{'=' * 60}{RESET}\n")


def print_success(text: str):
    """성공 메시지 출력"""
    print(f"{GREEN}✅ {text}{RESET}")


def print_error(text: str):
    """에러 메시지 출력"""
    print(f"{RED}❌ {text}{RESET}")


def print_info(text: str):
    """정보 메시지 출력"""
    print(f"{YELLOW}ℹ️  {text}{RESET}")


def create_test_image(with_pattern: bool = False) -> BytesIO:
    """
    테스트용 이미지 생성
    
    Args:
        with_pattern: True면 crack 패턴 유사 이미지, False면 단순 이미지
    
    Returns:
        BytesIO: 이미지 바이트 스트림
    """
    if with_pattern:
        # Crack 패턴 유사 이미지 생성 (검은 배경에 흰 선)
        img_array = np.zeros((512, 512, 3), dtype=np.uint8)
        # 대각선 crack 패턴
        for i in range(0, 512, 2):
            img_array[i:i+5, i:i+5] = [255, 255, 255]
        img = Image.fromarray(img_array)
    else:
        # 단순 회색 이미지
        img = Image.new('RGB', (512, 512), color=(128, 128, 128))
    
    img_bytes = BytesIO()
    img.save(img_bytes, format='JPEG')
    img_bytes.seek(0)
    return img_bytes


def test_root_endpoint():
    """루트 엔드포인트 테스트 (/)"""
    print_header("Test 1: Root Endpoint (GET /)")
    
    try:
        response = requests.get(f"{BASE_URL}/", timeout=10)
        
        print_info(f"Status Code: {response.status_code}")
        print_info(f"Response: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code == 200:
            data = response.json()
            if "message" in data and data["message"] == "Welcome to FairStay AI":
                print_success("Root endpoint working correctly")
                return True
            else:
                print_error("Unexpected response format")
                return False
        else:
            print_error(f"Expected status 200, got {response.status_code}")
            return False
    
    except Exception as e:
        print_error(f"Request failed: {str(e)}")
        return False


def test_health_endpoint():
    """Health check 엔드포인트 테스트 (/health)"""
    print_header("Test 2: Health Check (GET /health)")
    
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=10)
        
        print_info(f"Status Code: {response.status_code}")
        print_info(f"Response: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code == 200:
            data = response.json()
            required_fields = ["status", "model_loaded"]
            
            missing_fields = [field for field in required_fields if field not in data]
            
            if not missing_fields:
                if data["status"] == "healthy" and data["model_loaded"]:
                    print_success("Health check passed - Model loaded successfully")
                    return True
                else:
                    print_error(f"Health check failed - Status: {data.get('status')}, Model loaded: {data.get('model_loaded')}")
                    return False
            else:
                print_error(f"Missing fields in response: {missing_fields}")
                return False
        else:
            print_error(f"Expected status 200, got {response.status_code}")
            return False
    
    except Exception as e:
        print_error(f"Request failed: {str(e)}")
        return False


def test_detect_crack_with_file_field():
    """Crack detection 테스트 - 'file' 필드명 사용 (백엔드 호환)"""
    print_header("Test 3: Detect Crack (POST /detect-crack) - 'file' field")
    
    try:
        test_image = create_test_image(with_pattern=True)
        
        files = {'file': ('test_crack.jpg', test_image, 'image/jpeg')}
        
        print_info("Sending POST request with test image...")
        response = requests.post(
            f"{BASE_URL}/detect-crack",
            files=files,
            timeout=60
        )
        
        print_info(f"Status Code: {response.status_code}")
        print_info(f"Response: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code == 200:
            data = response.json()
            
            # 백엔드가 기대하는 필드 검증
            required_fields = ["file_id", "image_url", "has_crack", "confidence"]
            missing_fields = [field for field in required_fields if field not in data]
            
            if not missing_fields:
                print_success(f"Crack detection successful")
                print_info(f"  - File ID: {data['file_id']}")
                print_info(f"  - Image URL: {data['image_url']}")
                print_info(f"  - Has Crack: {data['has_crack']}")
                print_info(f"  - Confidence: {data['confidence']:.4f}")
                print_info(f"  - Crack Count: {data.get('crack_count', 0)}")
                
                if 'bounding_boxes' in data and len(data['bounding_boxes']) > 0:
                    print_info(f"  - Bounding Boxes: {len(data['bounding_boxes'])} detected")
                    for i, bbox in enumerate(data['bounding_boxes'][:3]):  # 최대 3개만 출력
                        print_info(f"    [{i+1}] x={bbox['x']}, y={bbox['y']}, w={bbox['width']}, h={bbox['height']}")
                
                return True, data
            else:
                print_error(f"Missing required fields: {missing_fields}")
                return False, None
        else:
            print_error(f"Expected status 200, got {response.status_code}")
            return False, None
    
    except Exception as e:
        print_error(f"Request failed: {str(e)}")
        return False, None


def test_detect_crack_with_image_field():
    """Crack detection 테스트 - 'image' 필드명 사용"""
    print_header("Test 4: Detect Crack (POST /detect-crack) - 'image' field")
    
    try:
        test_image = create_test_image(with_pattern=False)
        
        files = {'image': ('test_no_crack.jpg', test_image, 'image/jpeg')}
        
        print_info("Sending POST request with test image (no crack pattern)...")
        response = requests.post(
            f"{BASE_URL}/detect-crack",
            files=files,
            timeout=60
        )
        
        print_info(f"Status Code: {response.status_code}")
        print_info(f"Response: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code == 200:
            data = response.json()
            print_success(f"Image processed successfully")
            print_info(f"  - Has Crack: {data.get('has_crack', False)}")
            print_info(f"  - Confidence: {data.get('confidence', 0):.4f}")
            return True, data
        else:
            print_error(f"Expected status 200, got {response.status_code}")
            return False, None
    
    except Exception as e:
        print_error(f"Request failed: {str(e)}")
        return False, None


def test_get_result_image(file_id: str):
    """처리된 이미지 조회 테스트 (GET /result/{file_id})"""
    print_header(f"Test 5: Get Result Image (GET /result/{file_id})")
    
    try:
        response = requests.get(f"{BASE_URL}/result/{file_id}", timeout=30)
        
        print_info(f"Status Code: {response.status_code}")
        print_info(f"Content-Type: {response.headers.get('Content-Type')}")
        print_info(f"Content-Length: {len(response.content)} bytes")
        
        if response.status_code == 200:
            if 'image' in response.headers.get('Content-Type', ''):
                print_success(f"Result image retrieved successfully ({len(response.content)} bytes)")
                
                # 이미지 저장 (선택사항)
                output_path = f"test_result_{file_id}.jpg"
                with open(output_path, 'wb') as f:
                    f.write(response.content)
                print_info(f"Saved result image to: {output_path}")
                
                return True
            else:
                print_error(f"Expected image content type, got {response.headers.get('Content-Type')}")
                return False
        else:
            print_error(f"Expected status 200, got {response.status_code}")
            return False
    
    except Exception as e:
        print_error(f"Request failed: {str(e)}")
        return False


def test_invalid_image():
    """잘못된 이미지 업로드 테스트"""
    print_header("Test 6: Invalid Image Upload")
    
    try:
        # 텍스트 파일을 이미지로 위장
        invalid_file = BytesIO(b"This is not an image file")
        
        files = {'file': ('fake.jpg', invalid_file, 'image/jpeg')}
        
        print_info("Sending POST request with invalid image...")
        response = requests.post(
            f"{BASE_URL}/detect-crack",
            files=files,
            timeout=30
        )
        
        print_info(f"Status Code: {response.status_code}")
        print_info(f"Response: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code == 400:
            print_success("Invalid image rejected correctly (400 Bad Request)")
            return True
        else:
            print_error(f"Expected status 400, got {response.status_code}")
            return False
    
    except Exception as e:
        print_error(f"Request failed: {str(e)}")
        return False


def test_missing_file():
    """파일 누락 테스트"""
    print_header("Test 7: Missing File Upload")
    
    try:
        print_info("Sending POST request without file...")
        response = requests.post(
            f"{BASE_URL}/detect-crack",
            timeout=30
        )
        
        print_info(f"Status Code: {response.status_code}")
        
        if response.status_code in [400, 422]:  # 400 Bad Request or 422 Unprocessable Entity
            print_success(f"Missing file handled correctly ({response.status_code})")
            return True
        else:
            print_error(f"Expected status 400 or 422, got {response.status_code}")
            return False
    
    except Exception as e:
        print_error(f"Request failed: {str(e)}")
        return False


def run_all_tests():
    """모든 테스트 실행"""
    print(f"\n{BOLD}🚀 FairStay AI API Testing Suite{RESET}")
    print(f"{BOLD}Testing server: {BASE_URL}{RESET}\n")
    
    results = []
    file_id_for_result_test = None
    
    # Test 1: Root endpoint
    results.append(("Root Endpoint", test_root_endpoint()))
    
    # Test 2: Health check
    results.append(("Health Check", test_health_endpoint()))
    
    # Test 3: Detect crack (file field)
    success, data = test_detect_crack_with_file_field()
    results.append(("Detect Crack (file field)", success))
    if success and data:
        file_id_for_result_test = data.get("file_id")
    
    # Test 4: Detect crack (image field)
    success, _ = test_detect_crack_with_image_field()
    results.append(("Detect Crack (image field)", success))
    
    # Test 5: Get result image (if file_id available)
    if file_id_for_result_test:
        results.append(("Get Result Image", test_get_result_image(file_id_for_result_test)))
    else:
        print_info("Skipping result image test (no file_id available)")
        results.append(("Get Result Image", False))
    
    # Test 6: Invalid image
    results.append(("Invalid Image", test_invalid_image()))
    
    # Test 7: Missing file
    results.append(("Missing File", test_missing_file()))
    
    # 결과 요약
    print_header("Test Results Summary")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = f"{GREEN}PASS{RESET}" if result else f"{RED}FAIL{RESET}"
        print(f"{status} - {test_name}")
    
    print(f"\n{BOLD}Total: {passed}/{total} tests passed{RESET}")
    
    if passed == total:
        print(f"{GREEN}{BOLD}🎉 All tests passed!{RESET}\n")
        return 0
    else:
        print(f"{RED}{BOLD}⚠️  Some tests failed{RESET}\n")
        return 1


if __name__ == "__main__":
    # 사용법 출력
    if len(sys.argv) > 1:
        if sys.argv[1] in ["-h", "--help"]:
            print(f"""
Usage: python test_api.py [SERVER_URL]

Examples:
  # Test local server
  python test_api.py
  python test_api.py http://localhost:8000
  
  # Test Lambda Function URL
  python test_api.py https://abc123.lambda-url.ap-northeast-2.on.aws
  
  # Or use environment variable
  export AI_SERVER_URL=https://abc123.lambda-url.ap-northeast-2.on.aws
  python test_api.py
""")
            sys.exit(0)
        else:
            BASE_URL = sys.argv[1].rstrip('/')
    
    exit_code = run_all_tests()
    sys.exit(exit_code)
