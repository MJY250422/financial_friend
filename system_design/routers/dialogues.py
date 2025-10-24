"""
Dialogues API 라우터
대화 관련 엔드포인트
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from typing import List, Optional
from datetime import datetime

from database import get_db
from db_schema_design import Dialogue, Session as DBSession
from schemas import DialogueCreate, DialogueResponse
from enums import SenderType

router = APIRouter()


@router.post("/", response_model=DialogueResponse, status_code=status.HTTP_201_CREATED)
async def create_dialogue(
    dialogue: DialogueCreate,
    db: Session = Depends(get_db)
):
    """
    새 대화 메시지 생성
    
    - **session_id**: 세션 ID (필수)
    - **sender_type**: 발신자 타입 (user/assistant/system) (필수)
    - **content**: 메시지 내용 (필수)
    - **intent**: 의도 분류 (선택)
    """
    # 세션 존재 확인
    session = db.query(DBSession).filter(
        DBSession.session_id == dialogue.session_id
    ).first()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    
    db_dialogue = Dialogue(
        session_id=dialogue.session_id,
        sender_type=dialogue.sender_type,
        content=dialogue.content,
        intent=dialogue.intent,
        created_at=datetime.utcnow()
    )
    
    db.add(db_dialogue)
    db.commit()
    db.refresh(db_dialogue)
    
    return db_dialogue


@router.get("/", response_model=List[DialogueResponse])
async def get_dialogues(
    session_id: int,
    sender_type: Optional[SenderType] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    대화 목록 조회
    
    - **session_id**: 세션 ID (필수)
    - **sender_type**: 발신자 타입 필터 (선택)
    - **skip**: 건너뛸 레코드 수
    - **limit**: 최대 반환 레코드 수
    """
    query = db.query(Dialogue).filter(Dialogue.session_id == session_id)
    
    if sender_type:
        query = query.filter(Dialogue.sender_type == sender_type)
    
    dialogues = query.order_by(Dialogue.created_at.asc()).offset(skip).limit(limit).all()
    return dialogues


@router.get("/{dialogue_id}", response_model=DialogueResponse)
async def get_dialogue(dialogue_id: int, db: Session = Depends(get_db)):
    """
    특정 대화 메시지 조회
    
    - **dialogue_id**: 대화 ID
    """
    dialogue = db.query(Dialogue).filter(
        Dialogue.dialogue_id == dialogue_id
    ).first()
    
    if not dialogue:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dialogue not found"
        )
    
    return dialogue


@router.get("/session/{session_id}/history", response_model=List[DialogueResponse])
async def get_session_history(
    session_id: int,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """
    세션의 대화 이력 조회 (최근 순)
    
    - **session_id**: 세션 ID
    - **limit**: 최대 반환 레코드 수 (기본값: 50)
    """
    dialogues = db.query(Dialogue).filter(
        Dialogue.session_id == session_id
    ).order_by(desc(Dialogue.created_at)).limit(limit).all()
    
    # 시간 순으로 정렬하여 반환
    return list(reversed(dialogues))


@router.get("/session/{session_id}/context")
async def get_conversation_context(
    session_id: int,
    message_count: int = 10,
    db: Session = Depends(get_db)
):
    """
    대화 컨텍스트 조회 (최근 N개 메시지)
    AI 에이전트가 이전 대화를 참고할 때 사용
    
    - **session_id**: 세션 ID
    - **message_count**: 가져올 메시지 수 (기본값: 10)
    """
    dialogues = db.query(Dialogue).filter(
        Dialogue.session_id == session_id
    ).order_by(desc(Dialogue.created_at)).limit(message_count).all()
    
    # 시간 순으로 정렬
    dialogues = list(reversed(dialogues))
    
    # 대화 컨텍스트 구성
    context = {
        "session_id": session_id,
        "message_count": len(dialogues),
        "messages": [
            {
                "role": d.sender_type.value,
                "content": d.content,
                "timestamp": d.created_at.isoformat()
            }
            for d in dialogues
        ]
    }
    
    return context


@router.delete("/{dialogue_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_dialogue(dialogue_id: int, db: Session = Depends(get_db)):
    """
    대화 메시지 삭제
    
    - **dialogue_id**: 대화 ID
    """
    dialogue = db.query(Dialogue).filter(
        Dialogue.dialogue_id == dialogue_id
    ).first()
    
    if not dialogue:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dialogue not found"
        )
    
    db.delete(dialogue)
    db.commit()
    
    return None


@router.delete("/session/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_session_dialogues(
    session_id: int,
    db: Session = Depends(get_db)
):
    """
    세션의 모든 대화 삭제
    
    - **session_id**: 세션 ID
    """
    db.query(Dialogue).filter(Dialogue.session_id == session_id).delete()
    db.commit()
    
    return None


@router.get("/session/{session_id}/statistics")
async def get_session_dialogue_statistics(
    session_id: int,
    db: Session = Depends(get_db)
):
    """
    세션의 대화 통계 조회
    
    - **session_id**: 세션 ID
    """
    # 전체 메시지 수
    total_messages = db.query(func.count(Dialogue.dialogue_id)).filter(
        Dialogue.session_id == session_id
    ).scalar()
    
    # 발신자별 메시지 수
    sender_counts = db.query(
        Dialogue.sender_type,
        func.count(Dialogue.dialogue_id).label('count')
    ).filter(
        Dialogue.session_id == session_id
    ).group_by(Dialogue.sender_type).all()
    
    # 의도별 메시지 수
    intent_counts = db.query(
        Dialogue.intent,
        func.count(Dialogue.dialogue_id).label('count')
    ).filter(
        Dialogue.session_id == session_id,
        Dialogue.intent.isnot(None)
    ).group_by(Dialogue.intent).all()
    
    return {
        "session_id": session_id,
        "total_messages": total_messages,
        "sender_counts": {sender.value: count for sender, count in sender_counts},
        "intent_counts": {intent: count for intent, count in intent_counts}
    }