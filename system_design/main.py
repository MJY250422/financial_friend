"""
FastAPI 메인 애플리케이션
"""
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import uvicorn

from database import get_db, init_db
from routers import users, sessions, news, agent_tasks, dialogues
from schemas import HealthCheck

# -----------------------------
# 환경 변수 로드
# -----------------------------
load_dotenv()

API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", 8000))
API_RELOAD = os.getenv("API_RELOAD", "True").lower() == "true"
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "").split(",")

# -----------------------------
# FastAPI 앱 생성
# -----------------------------
app = FastAPI(
    title="News Agent API",
    description="뉴스 추천 및 AI 에이전트 API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# -----------------------------
# CORS 설정
# -----------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,  # .env에서 가져옴
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -----------------------------
# 라우터 등록
# -----------------------------
app.include_router(users.router, prefix="/api/v1/users", tags=["Users"])
app.include_router(sessions.router, prefix="/api/v1/sessions", tags=["Sessions"])
app.include_router(news.router, prefix="/api/v1/news", tags=["News"])
app.include_router(agent_tasks.router, prefix="/api/v1/agent-tasks", tags=["Agent Tasks"])
app.include_router(dialogues.router, prefix="/api/v1/dialogues", tags=["Dialogues"])

# -----------------------------
# 앱 이벤트
# -----------------------------
@app.on_event("startup")
async def startup_event():
    """애플리케이션 시작 시 실행"""
    print("🚀 Starting News Agent API...")
    try:
        init_db()
        print("✅ Database initialized")
    except Exception as e:
        print(f"⚠️ Database initialization failed: {e}")

@app.on_event("shutdown")
async def shutdown_event():
    """애플리케이션 종료 시 실행"""
    print("👋 Shutting down News Agent API...")

# -----------------------------
# 헬스 체크 엔드포인트
# -----------------------------
@app.get("/", response_model=HealthCheck)
async def root():
    """루트 엔드포인트 - 헬스 체크"""
    return {
        "status": "healthy",
        "message": "News Agent API is running",
        "version": "1.0.0"
    }

@app.get("/health", response_model=HealthCheck)
async def health_check():
    """헬스 체크 엔드포인트"""
    return {
        "status": "healthy",
        "message": "All systems operational",
        "version": "1.0.0"
    }

# -----------------------------
# 개발 서버 실행
# -----------------------------
if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=API_HOST,
        port=API_PORT,
        reload=API_RELOAD,
        log_level="info"
    )
