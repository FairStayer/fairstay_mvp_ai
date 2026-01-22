import os

# 🔥 반드시 YOLO import 전에 설정 (Lambda read-only FS 대응)
os.environ["YOLO_VERBOSE"] = "False"
os.environ["YOLO_CONFIG_DIR"] = "/tmp/Ultralytics"
os.environ["ULTRALYTICS_RUNS_DIR"] = "/tmp/runs"
os.environ["ULTRALYTICS_CACHE_DIR"] = "/tmp/Ultralytics"

from fastapi import FastAPI, UploadFile, File
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import numpy as np
import cv2
import uuid
import logging
import time
from datetime import datetime

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI()

# CORS 설정 (백엔드에서 호출 가능하도록)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 프로덕션에서는 특정 도메인으로 제한
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

logger.info("FastAPI application starting...")

# Lambda 환경과 로컬 환경 모두 지원
MODEL_PATH = os.environ.get("MODEL_PATH", "best.pt")
SAVE_DIR = os.environ.get("SAVE_DIR", "/tmp/result")

logger.info(f"MODEL_PATH: {MODEL_PATH}")
logger.info(f"SAVE_DIR: {SAVE_DIR}")

# 모델 로딩 (Lambda는 /tmp 사용)
if not os.path.exists(MODEL_PATH):
    logger.warning(f"Model not found at {MODEL_PATH}, trying current directory")
    MODEL_PATH = "best.pt"  # 현재 디렉토리에서 찾기

from ultralytics import YOLO

# 🔥 YOLO가 사용할 디렉토리 명시적으로 생성
os.makedirs("/tmp/runs", exist_ok=True)
os.makedirs("/tmp/Ultralytics", exist_ok=True)
os.makedirs(SAVE_DIR, exist_ok=True)

# 🔥 Lazy Loading: 모델을 전역 변수로 선언만 하고, 첫 요청 시 로딩
model = None

def load_model():
    """모델을 지연 로딩하는 함수 (첫 요청 시에만 실행)"""
    global model
    if model is None:
        logger.info("Loading YOLO model (lazy loading)...")
        model_load_start = time.time()
        model = YOLO(MODEL_PATH)
        model_load_time = time.time() - model_load_start
        logger.info(f"YOLO model loaded successfully in {model_load_time:.2f} seconds")
    return model

logger.info(f"FastAPI initialized - Model will be loaded on first request")
logger.info(f"Save directory created/verified: {SAVE_DIR}")

def resize_mask(mask, W, H):
    mask_uint8 = (mask * 255).astype(np.uint8)
    return cv2.resize(mask_uint8, (W, H), interpolation=cv2.INTER_NEAREST)

@app.get("/")
async def root():
    """루트 엔드포인트 - 기본 health check"""
    logger.info("[GET /] Root endpoint accessed")
    response = {"message": "Welcome to FairStay AI", "status": "ok"}
    logger.info(f"[GET /] Response: {response}")
    return response

@app.get("/health")
async def health():
    """백엔드에서 호출하는 health check 엔드포인트"""
    logger.info("[GET /health] Health check requested")
    try:
        # 모델 로딩 상태 확인 (lazy loading이므로 None일 수 있음)
        model_loaded = model is not None
        
        response = {
            "status": "healthy",
            "model_loaded": model_loaded,
            "model_path": MODEL_PATH,
            "save_dir": SAVE_DIR,
            "note": "Model will be loaded on first inference request" if not model_loaded else None
        }
        logger.info(f"[GET /health] Status: healthy, model_loaded={model_loaded}")
        return response
    except Exception as e:
        logger.error(f"[GET /health] Exception: {str(e)}", exc_info=True)
        return JSONResponse(
            status_code=503,
            content={"status": "unhealthy", "message": str(e)}
        )

@app.post("/detect-crack")
async def detect_crack(file: UploadFile = File(None), image: UploadFile = File(None)):
    """
    백엔드 호환성: 'file' 또는 'image' 필드명 모두 지원
    """
    request_start = time.time()
    request_id = str(uuid.uuid4())[:8]
    logger.info(f"[POST /detect-crack] Request {request_id} started at {datetime.now().isoformat()}")
    
    # 🔥 첫 요청 시 모델 로딩 (Lazy Loading)
    current_model = load_model()
    
    upload_file = file or image
    if not upload_file:
        logger.error(f"[POST /detect-crack] Request {request_id} - No image file provided")
        return JSONResponse(
            status_code=400,
            content={"error": "No image file provided"}
        )
    
    logger.info(f"[POST /detect-crack] Request {request_id} - File received: {upload_file.filename}, Content-Type: {upload_file.content_type}")
    
    contents = await upload_file.read()
    file_size = len(contents)
    logger.info(f"[POST /detect-crack] Request {request_id} - File size: {file_size} bytes ({file_size/1024:.2f} KB)")
    
    nparr = np.frombuffer(contents, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    if img is None:
        logger.error(f"[POST /detect-crack] Request {request_id} - Invalid image file (cv2.imdecode failed)")
        return JSONResponse(
            status_code=400,
            content={"error": "Invalid image file"}
        )

    H, W = img.shape[:2]
    logger.info(f"[POST /detect-crack] Request {request_id} - Image dimensions: {W}x{H}")
    
    # YOLO 모델 실행
    inference_start = time.time()
    logger.info(f"[POST /detect-crack] Request {request_id} - Starting YOLO inference...")
    
    # Lambda read-only FS 대응: project와 name을 /tmp로 명시적 지정
    results = current_model(
        img, 
        save=False, 
        verbose=False,
        project="/tmp/runs",
        name="predict",
        exist_ok=True
    )
    
    inference_time = time.time() - inference_start
    logger.info(f"[POST /detect-crack] Request {request_id} - YOLO inference completed in {inference_time:.3f}s")

    has_crack = False
    max_confidence = 0.0
    bounding_boxes = []

    for r in results:
        if r.masks is None:
            logger.info(f"[POST /detect-crack] Request {request_id} - No masks detected in this result")
            continue

        masks = r.masks.data.cpu().numpy()
        boxes = r.boxes
        
        logger.info(f"[POST /detect-crack] Request {request_id} - Found {len(masks)} mask(s)")
        
        if boxes is not None:
            confidences = boxes.conf.cpu().numpy()
            logger.info(f"[POST /detect-crack] Request {request_id} - Confidence scores: {[f'{c:.3f}' for c in confidences]}")
        else:
            confidences = [0.0] * len(masks)
            logger.warning(f"[POST /detect-crack] Request {request_id} - No confidence scores available")

        for i, (mask, conf) in enumerate(zip(masks, confidences)):
            has_crack = True
            max_confidence = max(max_confidence, float(conf))
            
            mask_resized = resize_mask(mask, W, H)
            mask_bool = mask_resized > 127

            ys, xs = np.where(mask_bool)
            if len(xs) == 0:
                continue

            x_min, x_max = int(xs.min()), int(xs.max())
            y_min, y_max = int(ys.min()), int(ys.max())

            bbox = {
                "x": x_min,
                "y": y_min,
                "width": x_max - x_min,
                "height": y_max - y_min
            }
            bounding_boxes.append(bbox)
            logger.info(f"[POST /detect-crack] Request {request_id} - Crack {i+1}: bbox={bbox}, confidence={conf:.3f}")

            cv2.rectangle(img, (x_min, y_min), (x_max, y_max), (0, 0, 255), 3)
            cv2.putText(
                img,
                f"crack {i+1} ({conf:.2f})",
                (x_min, y_min - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 0, 255),
                2,
            )

    file_id = str(uuid.uuid4())
    out_path = f"{SAVE_DIR}/{file_id}.jpg"
    
    # 이미지 저장
    save_start = time.time()
    cv2.imwrite(out_path, img)
    save_time = time.time() - save_start
    logger.info(f"[POST /detect-crack] Request {request_id} - Result image saved: {out_path} (took {save_time:.3f}s)")
    
    total_time = time.time() - request_start

    # 백엔드 호환 응답 형식
    response = {
        "file_id": file_id,
        "image_url": f"/result/{file_id}",
        "has_crack": has_crack,
        "confidence": max_confidence,
        "crack_count": len(bounding_boxes),
        "bounding_boxes": bounding_boxes
    }
    
    logger.info(f"[POST /detect-crack] Request {request_id} - Processing completed in {total_time:.3f}s")
    logger.info(f"[POST /detect-crack] Request {request_id} - Result: has_crack={has_crack}, crack_count={len(bounding_boxes)}, confidence={max_confidence:.3f}")
    logger.info(f"[POST /detect-crack] Request {request_id} - Response: file_id={file_id}")
    
    return response

@app.get("/result/{file_id}")
async def get_result(file_id: str):
    logger.info(f"[GET /result/{file_id}] Result image requested")
    path = f"{SAVE_DIR}/{file_id}.jpg"
    
    if not os.path.exists(path):
        logger.error(f"[GET /result/{file_id}] File not found: {path}")
        return JSONResponse(
            status_code=404,
            content={"error": "Result image not found"}
        )
    
    file_size = os.path.getsize(path)
    logger.info(f"[GET /result/{file_id}] Returning image: {path} ({file_size} bytes, {file_size/1024:.2f} KB)")
    return FileResponse(path)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)