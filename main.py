from fastapi import FastAPI, UploadFile, File
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from ultralytics import YOLO
import uvicorn
import numpy as np
import cv2
import os
import uuid

app = FastAPI()

# CORS 설정 (백엔드에서 호출 가능하도록)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 프로덕션에서는 특정 도메인으로 제한
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Lambda 환경과 로컬 환경 모두 지원
MODEL_PATH = os.environ.get("MODEL_PATH", "best.pt")
SAVE_DIR = os.environ.get("SAVE_DIR", "/tmp/result")

# 모델 로딩 (Lambda는 /tmp 사용)
if not os.path.exists(MODEL_PATH):
    MODEL_PATH = "best.pt"  # 현재 디렉토리에서 찾기

model = YOLO(MODEL_PATH)
os.makedirs(SAVE_DIR, exist_ok=True)

def resize_mask(mask, W, H):
    mask_uint8 = (mask * 255).astype(np.uint8)
    return cv2.resize(mask_uint8, (W, H), interpolation=cv2.INTER_NEAREST)

@app.get("/")
async def root():
    """루트 엔드포인트 - 기본 health check"""
    return {"message": "Welcome to FairStay AI", "status": "ok"}

@app.get("/health")
async def health():
    """백엔드에서 호출하는 health check 엔드포인트"""
    try:
        # 모델이 로드되어 있는지 확인
        if model is None:
            return JSONResponse(
                status_code=503,
                content={"status": "unhealthy", "message": "Model not loaded"}
            )
        
        return {
            "status": "healthy",
            "model_loaded": True,
            "model_path": MODEL_PATH,
            "save_dir": SAVE_DIR
        }
    except Exception as e:
        return JSONResponse(
            status_code=503,
            content={"status": "unhealthy", "message": str(e)}
        )

@app.post("/detect-crack")
async def detect_crack(file: UploadFile = File(...), image: UploadFile = File(None)):
    """
    백엔드 호환성: 'file' 또는 'image' 필드명 모두 지원
    """
    upload_file = file if file else image
    if not upload_file:
        return JSONResponse(
            status_code=400,
            content={"error": "No image file provided"}
        )
    
    contents = await upload_file.read()
    nparr = np.frombuffer(contents, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    if img is None:
        return JSONResponse(
            status_code=400,
            content={"error": "Invalid image file"}
        )

    H, W = img.shape[:2]
    results = model(img)

    has_crack = False
    max_confidence = 0.0
    bounding_boxes = []

    for r in results:
        if r.masks is None:
            continue

        masks = r.masks.data.cpu().numpy()
        boxes = r.boxes
        
        if boxes is not None:
            confidences = boxes.conf.cpu().numpy()
        else:
            confidences = [0.0] * len(masks)

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

            bounding_boxes.append({
                "x": x_min,
                "y": y_min,
                "width": x_max - x_min,
                "height": y_max - y_min
            })

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
    cv2.imwrite(out_path, img)

    # 백엔드 호환 응답 형식
    return {
        "file_id": file_id,
        "image_url": f"/result/{file_id}",
        "has_crack": has_crack,
        "confidence": max_confidence,
        "crack_count": len(bounding_boxes),
        "bounding_boxes": bounding_boxes
    }

@app.get("/result/{file_id}")
async def get_result(file_id: str):
    path = f"{SAVE_DIR}/{file_id}.jpg"
    return FileResponse(path)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)