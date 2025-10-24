"""
Agent Tasks API 라우터
에이전트 작업 관련 엔드포인트
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from typing import List, Optional
from datetime import datetime

from database import get_db
from db_schema_design import AgentTask, AgentInfo, Session as DBSession
from schemas import AgentTaskCreate, AgentTaskUpdate, AgentTaskResponse
from enums import TaskStatus

router = APIRouter()


@router.post("/", response_model=AgentTaskResponse, status_code=status.HTTP_201_CREATED)
async def create_agent_task(
    task: AgentTaskCreate,
    db: Session = Depends(get_db)
):
    """
    새 에이전트 작업 생성
    
    - **agent_id**: 에이전트 ID (필수)
    - **session_id**: 세션 ID (필수)
    - **dialogue_id**: 대화 ID (선택)
    - **input_data**: 입력 데이터 (선택, JSON)
    """
    # 에이전트 존재 확인
    agent = db.query(AgentInfo).filter(AgentInfo.agent_id == task.agent_id).first()
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent not found"
        )
    
    # 세션 존재 확인
    session = db.query(DBSession).filter(DBSession.session_id == task.session_id).first()
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    
    db_task = AgentTask(
        agent_id=task.agent_id,
        session_id=task.session_id,
        dialogue_id=task.dialogue_id,
        input_data=task.input_data,
        status=TaskStatus.PENDING,
        created_at=datetime.utcnow()
    )
    
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    
    return db_task


@router.get("/", response_model=List[AgentTaskResponse])
async def get_agent_tasks(
    session_id: Optional[int] = None,
    agent_id: Optional[int] = None,
    status_filter: Optional[TaskStatus] = None,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """
    에이전트 작업 목록 조회
    
    - **session_id**: 세션 ID 필터 (선택)
    - **agent_id**: 에이전트 ID 필터 (선택)
    - **status_filter**: 상태 필터 (선택)
    - **skip**: 건너뛸 레코드 수
    - **limit**: 최대 반환 레코드 수
    """
    query = db.query(AgentTask)
    
    if session_id:
        query = query.filter(AgentTask.session_id == session_id)
    
    if agent_id:
        query = query.filter(AgentTask.agent_id == agent_id)
    
    if status_filter:
        query = query.filter(AgentTask.status == status_filter)
    
    tasks = query.order_by(desc(AgentTask.created_at)).offset(skip).limit(limit).all()
    return tasks


@router.get("/{task_id}", response_model=AgentTaskResponse)
async def get_agent_task(task_id: int, db: Session = Depends(get_db)):
    """
    특정 에이전트 작업 조회
    
    - **task_id**: 작업 ID
    """
    task = db.query(AgentTask).filter(AgentTask.task_id == task_id).first()
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    return task


@router.put("/{task_id}", response_model=AgentTaskResponse)
async def update_agent_task(
    task_id: int,
    task_update: AgentTaskUpdate,
    db: Session = Depends(get_db)
):
    """
    에이전트 작업 업데이트
    
    - **task_id**: 작업 ID
    - **status**: 작업 상태 (선택)
    - **output_data**: 출력 데이터 (선택, JSON)
    - **error_reason**: 에러 사유 (선택)
    - **duration_ms**: 실행 시간 (밀리초) (선택)
    """
    task = db.query(AgentTask).filter(AgentTask.task_id == task_id).first()
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    update_data = task_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(task, field, value)
    
    db.commit()
    db.refresh(task)
    
    return task


@router.post("/{task_id}/start", response_model=AgentTaskResponse)
async def start_agent_task(task_id: int, db: Session = Depends(get_db)):
    """
    에이전트 작업 시작
    
    - **task_id**: 작업 ID
    """
    task = db.query(AgentTask).filter(AgentTask.task_id == task_id).first()
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    if task.status != TaskStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Task is already {task.status.value}"
        )
    
    task.status = TaskStatus.IN_PROGRESS
    db.commit()
    db.refresh(task)
    
    return task


@router.post("/{task_id}/complete", response_model=AgentTaskResponse)
async def complete_agent_task(
    task_id: int,
    output_data: dict,
    duration_ms: int,
    db: Session = Depends(get_db)
):
    """
    에이전트 작업 완료
    
    - **task_id**: 작업 ID
    - **output_data**: 작업 결과 데이터 (JSON)
    - **duration_ms**: 실행 시간 (밀리초)
    """
    task = db.query(AgentTask).filter(AgentTask.task_id == task_id).first()
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    task.status = TaskStatus.COMPLETED
    task.output_data = output_data
    task.duration_ms = duration_ms
    
    db.commit()
    db.refresh(task)
    
    return task


@router.post("/{task_id}/fail", response_model=AgentTaskResponse)
async def fail_agent_task(
    task_id: int,
    error_reason: str,
    duration_ms: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """
    에이전트 작업 실패 처리
    
    - **task_id**: 작업 ID
    - **error_reason**: 실패 사유
    - **duration_ms**: 실행 시간 (밀리초) (선택)
    """
    task = db.query(AgentTask).filter(AgentTask.task_id == task_id).first()
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    task.status = TaskStatus.FAILED
    task.error_reason = error_reason
    if duration_ms:
        task.duration_ms = duration_ms
    
    db.commit()
    db.refresh(task)
    
    return task


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_agent_task(task_id: int, db: Session = Depends(get_db)):
    """
    에이전트 작업 삭제
    
    - **task_id**: 작업 ID
    """
    task = db.query(AgentTask).filter(AgentTask.task_id == task_id).first()
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    db.delete(task)
    db.commit()
    
    return None


@router.get("/statistics/session/{session_id}")
async def get_session_task_statistics(
    session_id: int,
    db: Session = Depends(get_db)
):
    """
    세션의 작업 통계 조회
    
    - **session_id**: 세션 ID
    """
    # 상태별 작업 수
    status_counts = db.query(
        AgentTask.status,
        func.count(AgentTask.task_id).label('count')
    ).filter(
        AgentTask.session_id == session_id
    ).group_by(AgentTask.status).all()
    
    # 평균 실행 시간
    avg_duration = db.query(
        func.avg(AgentTask.duration_ms)
    ).filter(
        AgentTask.session_id == session_id,
        AgentTask.duration_ms.isnot(None)
    ).scalar()
    
    return {
        "session_id": session_id,
        "status_counts": {status.value: count for status, count in status_counts},
        "average_duration_ms": avg_duration or 0
    }