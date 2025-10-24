"""
Users API 라우터
사용자 관련 엔드포인트
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
import uuid
from datetime import datetime

from database import get_db
from db_schema_design import User
from schemas import UserCreate, UserUpdate, UserResponse
from utils import hash_password

router = APIRouter()


@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(user: UserCreate, db: Session = Depends(get_db)):
    """
    새 사용자 생성
    
    - **email**: 사용자 이메일 (필수, 중복 불가)
    - **password**: 비밀번호 (필수, 최소 8자)
    - **username**: 사용자명 (선택)
    - **user_type**: 사용자 타입 (기본값: USER)
    """
    # 이메일 중복 체크
    existing_user = db.query(User).filter(User.email == user.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # 비밀번호 해싱
    hashed_password = hash_password(user.password)
    
    # 새 사용자 생성
    db_user = User(
        user_id=str(uuid.uuid4()),
        email=user.email,
        username=user.username,
        user_type=user.user_type,
        password_hash=hashed_password,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    return db_user


@router.get("/", response_model=List[UserResponse])
async def get_users(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    사용자 목록 조회
    
    - **skip**: 건너뛸 레코드 수 (기본값: 0)
    - **limit**: 최대 반환 레코드 수 (기본값: 100)
    """
    users = db.query(User).filter(User.deleted_at.is_(None)).offset(skip).limit(limit).all()
    return users


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(user_id: str, db: Session = Depends(get_db)):
    """
    특정 사용자 조회
    
    - **user_id**: 사용자 ID
    """
    user = db.query(User).filter(
        User.user_id == user_id,
        User.deleted_at.is_(None)
    ).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return user


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: str,
    user_update: UserUpdate,
    db: Session = Depends(get_db)
):
    """
    사용자 정보 수정
    
    - **user_id**: 사용자 ID
    - **email**: 새 이메일 (선택)
    - **username**: 새 사용자명 (선택)
    - **user_type**: 새 사용자 타입 (선택)
    """
    user = db.query(User).filter(
        User.user_id == user_id,
        User.deleted_at.is_(None)
    ).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # 업데이트할 필드만 적용
    update_data = user_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(user, field, value)
    
    user.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(user)
    
    return user


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(user_id: str, db: Session = Depends(get_db)):
    """
    사용자 삭제 (Soft Delete)
    
    - **user_id**: 사용자 ID
    """
    user = db.query(User).filter(
        User.user_id == user_id,
        User.deleted_at.is_(None)
    ).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Soft delete
    user.deleted_at = datetime.utcnow()
    db.commit()
    
    return None


@router.post("/{user_id}/activate", response_model=UserResponse)
async def activate_user(user_id: str, db: Session = Depends(get_db)):
    """
    사용자 활성화 (마지막 활동 시간 업데이트)
    
    - **user_id**: 사용자 ID
    """
    user = db.query(User).filter(User.user_id == user_id).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    user.last_active_at = datetime.utcnow()
    db.commit()
    db.refresh(user)
    
    return user