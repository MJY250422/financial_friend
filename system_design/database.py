"""
데이터베이스 설정 및 세션 관리
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from db_schema_design import Base
import os

# 데이터베이스 URL 설정
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:1234@localhost:5432/newsagent_db"
)

# 엔진 생성 - client_encoding 추가
engine = create_engine(
    DATABASE_URL,
    echo=True,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
    connect_args={
        "client_encoding": "utf8"  # ✅ 추가
    }
)

# 세션 팩토리 생성
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)


def init_db():
    """데이터베이스 테이블 생성"""
    try:
        Base.metadata.create_all(bind=engine)
        print("✅ Database tables created successfully")
    except Exception as e:
        print(f"❌ Database initialization error: {e}")
        raise  # ✅ 상세한 에러 메시지 확인을 위해 추가


def get_db() -> Session:
    """
    데이터베이스 세션 의존성
    FastAPI 엔드포인트에서 사용
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()