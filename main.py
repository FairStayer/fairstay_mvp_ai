from fastapi import FastAPI, UploadFile, File
from fastapi.responses import FileResponse
from ultralytics import YOLO
import uvicorn
import numpy as np
import cv2
import os
import uuid

app = FastAPI()

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

@app.post("/detect-crack")
async def detect_crack(image: UploadFile = File(...)):
    contents = await image.read()
    nparr = np.frombuffer(contents, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    H, W = img.shape[:2]
    results = model(img)

    for r in results:
        if r.masks is None:
            continue

        masks = r.masks.data.cpu().numpy()
        N, h, w = masks.shape

        for i, mask in enumerate(masks):
            mask_resized = resize_mask(mask, W, H)
            mask_bool = mask_resized > 127

            ys, xs = np.where(mask_bool)
            if len(xs) == 0:
                continue

            x_min, x_max = xs.min(), xs.max()
            y_min, y_max = ys.min(), ys.max()

            cv2.rectangle(img, (x_min, y_min), (x_max, y_max), (0, 0, 255), 3)
            cv2.putText(
                img,
                f"crack {i+1}",
                (x_min, y_min - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 0, 255),
                2,
            )

    file_id = str(uuid.uuid4())
    out_path = f"{SAVE_DIR}/{file_id}.jpg"
    cv2.imwrite(out_path, img)

    return {"image_url": f"/result/{file_id}"}

@app.get("/result/{file_id}")
async def get_result(file_id: str):
    path = f"{SAVE_DIR}/{file_id}.jpg"
    return FileResponse(path)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)