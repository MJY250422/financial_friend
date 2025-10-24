"""
News API 라우터
뉴스 관련 엔드포인트
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from typing import List, Optional
from datetime import datetime

from database import get_db
from db_schema_design import News, UserNewsInteraction, NewsEmbedding
from schemas import (
    NewsCreate, NewsUpdate, NewsResponse, NewsWithInteractions,
    InteractionCreate, InteractionResponse
)
from enums import InteractionType

router = APIRouter()


@router.post("/", response_model=NewsResponse, status_code=status.HTTP_201_CREATED)
async def create_news(news: NewsCreate, db: Session = Depends(get_db)):
    """
    새 뉴스 기사 생성
    
    - **title**: 뉴스 제목 (필수)
    - **url**: 뉴스 URL (필수, 중복 불가)
    - **content**: 뉴스 본문 (선택)
    - **source**: 뉴스 출처 (선택)
    - **published_at**: 발행 시간 (선택)
    """
    # URL 중복 체크
    existing_news = db.query(News).filter(News.url == news.url).first()
    if existing_news:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="News with this URL already exists"
        )
    
    db_news = News(
        title=news.title,
        url=news.url,
        content=news.content,
        source=news.source,
        published_at=news.published_at,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    
    db.add(db_news)
    db.commit()
    db.refresh(db_news)
    
    return db_news


@router.get("/", response_model=List[NewsResponse])
async def get_news_list(
    skip: int = 0,
    limit: int = 20,
    source: Optional[str] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    뉴스 목록 조회
    
    - **skip**: 건너뛸 레코드 수 (기본값: 0)
    - **limit**: 최대 반환 레코드 수 (기본값: 20)
    - **source**: 출처 필터 (선택)
    - **search**: 제목 검색 (선택)
    """
    query = db.query(News).filter(News.deleted_at.is_(None))
    
    if source:
        query = query.filter(News.source == source)
    
    if search:
        query = query.filter(News.title.contains(search))
    
    news_list = query.order_by(desc(News.published_at)).offset(skip).limit(limit).all()
    return news_list


@router.get("/{news_id}", response_model=NewsResponse)
async def get_news(news_id: int, db: Session = Depends(get_db)):
    """
    특정 뉴스 조회
    
    - **news_id**: 뉴스 ID
    """
    news = db.query(News).filter(
        News.news_id == news_id,
        News.deleted_at.is_(None)
    ).first()
    
    if not news:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="News not found"
        )
    
    return news


@router.get("/{news_id}/with-interactions", response_model=NewsWithInteractions)
async def get_news_with_interactions(
    news_id: int,
    user_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    상호작용 정보를 포함한 뉴스 조회
    
    - **news_id**: 뉴스 ID
    - **user_id**: 사용자 ID (선택, 해당 사용자의 상호작용 여부 확인)
    """
    news = db.query(News).filter(
        News.news_id == news_id,
        News.deleted_at.is_(None)
    ).first()
    
    if not news:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="News not found"
        )
    
    # 전체 상호작용 수 계산
    interaction_count = db.query(func.count(UserNewsInteraction.interaction_id)).filter(
        UserNewsInteraction.news_id == news_id
    ).scalar()
    
    # 사용자가 상호작용했는지 확인
    user_interacted = False
    if user_id:
        user_interaction = db.query(UserNewsInteraction).filter(
            UserNewsInteraction.news_id == news_id,
            UserNewsInteraction.user_id == user_id
        ).first()
        user_interacted = user_interaction is not None
    
    return {
        **news.__dict__,
        "interaction_count": interaction_count,
        "user_interacted": user_interacted
    }


@router.put("/{news_id}", response_model=NewsResponse)
async def update_news(
    news_id: int,
    news_update: NewsUpdate,
    db: Session = Depends(get_db)
):
    """
    뉴스 정보 수정
    
    - **news_id**: 뉴스 ID
    """
    news = db.query(News).filter(
        News.news_id == news_id,
        News.deleted_at.is_(None)
    ).first()
    
    if not news:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="News not found"
        )
    
    update_data = news_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(news, field, value)
    
    news.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(news)
    
    return news


@router.delete("/{news_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_news(news_id: int, db: Session = Depends(get_db)):
    """
    뉴스 삭제 (Soft Delete)
    
    - **news_id**: 뉴스 ID
    """
    news = db.query(News).filter(
        News.news_id == news_id,
        News.deleted_at.is_(None)
    ).first()
    
    if not news:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="News not found"
        )
    
    news.deleted_at = datetime.utcnow()
    db.commit()
    
    return None


@router.post("/{news_id}/interactions", response_model=InteractionResponse, status_code=status.HTTP_201_CREATED)
async def create_interaction(
    news_id: int,
    interaction: InteractionCreate,
    user_id: str = Query(..., description="사용자 ID"),
    db: Session = Depends(get_db)
):
    """
    뉴스 상호작용 생성 (클릭, 조회, 좋아요 등)
    
    - **news_id**: 뉴스 ID
    - **user_id**: 사용자 ID (쿼리 파라미터)
    - **interaction_type**: 상호작용 타입 (click, view, like, share 등)
    """
    # 뉴스 존재 확인
    news = db.query(News).filter(News.news_id == news_id).first()
    if not news:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="News not found"
        )
    
    db_interaction = UserNewsInteraction(
        user_id=user_id,
        news_id=news_id,
        interaction_type=interaction.interaction_type,
        created_at=datetime.utcnow()
    )
    
    db.add(db_interaction)
    db.commit()
    db.refresh(db_interaction)
    
    return db_interaction


@router.get("/user/{user_id}/interactions", response_model=List[InteractionResponse])
async def get_user_interactions(
    user_id: str,
    interaction_type: Optional[InteractionType] = None,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """
    사용자의 뉴스 상호작용 이력 조회
    
    - **user_id**: 사용자 ID
    - **interaction_type**: 상호작용 타입 필터 (선택)
    - **skip**: 건너뛸 레코드 수
    - **limit**: 최대 반환 레코드 수
    """
    query = db.query(UserNewsInteraction).filter(
        UserNewsInteraction.user_id == user_id
    )
    
    if interaction_type:
        query = query.filter(UserNewsInteraction.interaction_type == interaction_type)
    
    interactions = query.order_by(desc(UserNewsInteraction.created_at)).offset(skip).limit(limit).all()
    return interactions


@router.get("/trending/", response_model=List[NewsWithInteractions])
async def get_trending_news(
    limit: int = 10,
    hours: int = 24,
    db: Session = Depends(get_db)
):
    """
    인기 뉴스 조회 (최근 N시간 내 상호작용 많은 순)
    
    - **limit**: 최대 반환 레코드 수 (기본값: 10)
    - **hours**: 시간 범위 (기본값: 24시간)
    """
    from datetime import timedelta
    
    time_threshold = datetime.utcnow() - timedelta(hours=hours)
    
    # 상호작용 수 기준으로 정렬
    trending = db.query(
        News,
        func.count(UserNewsInteraction.interaction_id).label('interaction_count')
    ).join(
        UserNewsInteraction,
        News.news_id == UserNewsInteraction.news_id
    ).filter(
        News.deleted_at.is_(None),
        UserNewsInteraction.created_at >= time_threshold
    ).group