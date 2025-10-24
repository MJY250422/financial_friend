"""
Sessions API 라우터
세션 관련 엔드포인트
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session as DBSession
from typing import List
from datetime import datetime, timedelta
import secrets

from database import get_db
from db_schema_design import Session, User
from schemas import SessionCreate, SessionResponse

router = APIRouter()


def generate_session_token() -> str:
    """세션 토큰 생성"""
    return secrets.token_urlsafe(32)


@router.post("/", response_model=SessionResponse, status_code=status.HTTP_201_CREATED)
async def create_session(
    session_data: SessionCreate,
    db: DBSession = Depends(get_db)
):
    """
    새 세션 생성
    
    - **user_id**: 사용자 ID (필수)
    - **context**: 세션 컨텍스트 (선택, JSON 형태)
    """
    # 사용자 존재 확인
    user = db.query(User).filter(User.user_id == session_data.user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # 세션 토큰 생성
    session_token = generate_session_token()
    
    # 만료 시간 설정 (24시간 후)
    expires_at = datetime.utcnow() + timedelta(hours=24)
    
    db_session = Session(
        user_id=session_data.user_id,
        session_token=session_token,
        context=session_data.context,
        created_at=datetime.utcnow(),
        expires_at=expires_at
    )
    
    db.add(db_session)
    db.commit()
    db.refresh(db_session)
    
    return db_session


@router.get("/", response_model=List[SessionResponse])
async def get_sessions(
    user_id: str,
    skip: int = 0,
    limit: int = 50,
    db: DBSession = Depends(get_db)
):
    """
    사용자의 세션 목록 조회
    
    - **user_id**: 사용자 ID
    - **skip**: 건너뛸 레코드 수
    - **limit**: 최대 반환 레코드 수
    """
    sessions = db.query(Session).filter(
        Session.user_id == user_id
    ).order_by(Session.created_at.desc()).offset(skip).limit(limit).all()
    
    return sessions


@router.get("/{session_id}", response_model=SessionResponse)
async def get_session(session_id: int, db: DBSession = Depends(get_db)):
    """
    특정 세션 조회
    
    - **session_id**: 세션 ID
    """
    session = db.query(Session).filter(Session.session_id == session_id).first()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    
    return session


@router.get("/token/{session_token}", response_model=SessionResponse)
async def get_session_by_token(
    session_token: str,
    db: DBSession = Depends(get_db)
):
    """
    토큰으로 세션 조회
    
    - **session_token**: 세션 토큰
    """
    session = db.query(Session).filter(
        Session.session_token == session_token
    ).first()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    
    # 세션 만료 확인
    if session.expires_at < datetime.utcnow():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session expired"
        )
    
    return session


@router.put("/{session_id}/context", response_model=SessionResponse)
async def update_session_context(
    session_id: int,
    context: dict,
    db: DBSession = Depends(get_db)
):
    """
    세션 컨텍스트 업데이트
    
    - **session_id**: 세션 ID
    - **context**: 새 컨텍스트 데이터 (JSON)
    """
    session = db.query(Session).filter(Session.session_id == session_id).first()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    
    session.context = context
    db.commit()
    db.refresh(session)
    
    return session


@router.post("/{session_id}/refresh", response_model=SessionResponse)
async def refresh_session(session_id: int, db: DBSession = Depends(get_db)):
    """
    세션 만료 시간 연장
    
    - **session_id**: 세션 ID
    """
    session = db.query(Session).filter(Session.session_id == session_id).first()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    
    # 만료 시간 24시간 연장
    session.expires_at = datetime.utcnow() + timedelta(hours=24)
    db.commit()
    db.refresh(session)
    
    return session


@router.delete("/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_session(session_id: int, db: DBSession = Depends(get_db)):
    """
    세션 삭제
    
    - **session_id**: 세션 ID
    """
    session = db.query(Session).filter(Session.session_id == session_id).first()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    
    db.delete(session)
    db.commit()
    
    return None


@router.delete("/user/{user_id}/sessions", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user_sessions(user_id: str, db: DBSession = Depends(get_db)):
    """
    사용자의 모든 세션 삭제
    
    - **user_id**: 사용자 ID
    """
    db.query(Session).filter(Session.user_id == user_id).delete()
    db.commit()
    
    return None