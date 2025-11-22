"""
AWS Lambda Handler for AI Crack Detection
FastAPI 애플리케이션을 Lambda에서 실행하기 위한 어댑터
"""

from mangum import Mangum
from main import app

# Mangum을 사용하여 FastAPI를 Lambda에서 실행
handler = Mangum(app, lifespan="off")
