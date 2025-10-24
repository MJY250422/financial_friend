"""
Pydantic 스키마 정의
요청/응답 데이터 검증 및 직렬화
"""
from pydantic import BaseModel, EmailStr, Field, ConfigDict
from datetime import datetime
from typing import Optional, List, Any
from enums import UserType, InteractionType, SenderType, TaskStatus


# ============ 공통 스키마 ============
class HealthCheck(BaseModel):
    """헬스 체크 응답"""
    status: str
    message: str
    version: str


# ============ User 스키마 ============
class UserBase(BaseModel):
    """사용자 기본 스키마"""
    email: EmailStr
    username: Optional[str] = None
    user_type: UserType = UserType.USER


class UserCreate(UserBase):
    """사용자 생성 요청"""
    password: str = Field(..., min_length=8, description="최소 8자 이상")


class UserUpdate(BaseModel):
    """사용자 수정 요청"""
    email: Optional[EmailStr] = None
    username: Optional[str] = None
    user_type: Optional[UserType] = None


class UserResponse(UserBase):
    """사용자 응답"""
    user_id: str
    created_at: datetime
    updated_at: datetime
    last_active_at: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)


# ============ Session 스키마 ============
class SessionCreate(BaseModel):
    """세션 생성 요청"""
    user_id: str
    context: Optional[dict] = None


class SessionResponse(BaseModel):
    """세션 응답"""
    session_id: int
    user_id: str
    session_token: str
    created_at: datetime
    expires_at: datetime
    context: Optional[dict] = None
    
    model_config = ConfigDict(from_attributes=True)


# ============ News 스키마 ============
class NewsBase(BaseModel):
    """뉴스 기본 스키마"""
    title: str = Field(..., max_length=500)
    url: str = Field(..., max_length=1000)
    content: Optional[str] = None
    source: Optional[str] = Field(None, max_length=100)
    published_at: Optional[datetime] = None


class NewsCreate(NewsBase):
    """뉴스 생성 요청"""
    pass


class NewsUpdate(BaseModel):
    """뉴스 수정 요청"""
    title: Optional[str] = Field(None, max_length=500)
    content: Optional[str] = None
    source: Optional[str] = Field(None, max_length=100)
    published_at: Optional[datetime] = None


class NewsResponse(NewsBase):
    """뉴스 응답"""
    news_id: int
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class NewsWithInteractions(NewsResponse):
    """상호작용 정보를 포함한 뉴스 응답"""
    interaction_count: int = 0
    user_interacted: bool = False


# ============ News Embedding 스키마 ============
class NewsEmbeddingCreate(BaseModel):
    """뉴스 임베딩 생성 요청"""
    news_id: int
    embedding_vector: bytes
    model_version: str


class NewsEmbeddingResponse(BaseModel):
    """뉴스 임베딩 응답"""
    embedding_id: int
    news_id: int
    model_version: str
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


# ============ User News Interaction 스키마 ============
class InteractionCreate(BaseModel):
    """상호작용 생성 요청"""
    news_id: int
    interaction_type: InteractionType


class InteractionResponse(BaseModel):
    """상호작용 응답"""
    interaction_id: int
    user_id: str
    news_id: int
    interaction_type: InteractionType
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


# ============ Agent Info 스키마 ============
class AgentInfoBase(BaseModel):
    """에이전트 기본 스키마"""
    agent_type: str = Field(..., max_length=50)
    description: Optional[str] = None
    version: Optional[str] = Field(None, max_length=20)
    model_version: Optional[str] = Field(None, max_length=50)
    is_active: bool = True


class AgentInfoCreate(AgentInfoBase):
    """에이전트 생성 요청"""
    pass


class AgentInfoResponse(AgentInfoBase):
    """에이전트 응답"""
    agent_id: int
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


# ============ Agent Task 스키마 ============
class AgentTaskCreate(BaseModel):
    """에이전트 작업 생성 요청"""
    agent_id: int
    session_id: int
    dialogue_id: Optional[int] = None
    input_data: Optional[dict] = None


class AgentTaskUpdate(BaseModel):
    """에이전트 작업 수정 요청"""
    status: Optional[TaskStatus] = None
    output_data: Optional[dict] = None
    error_reason: Optional[str] = None
    duration_ms: Optional[int] = None


class AgentTaskResponse(BaseModel):
    """에이전트 작업 응답"""
    task_id: int
    agent_id: int
    session_id: int
    dialogue_id: Optional[int] = None
    input_data: Optional[dict] = None
    output_data: Optional[dict] = None
    status: TaskStatus
    error_reason: Optional[str] = None
    duration_ms: Optional[int] = None
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


# ============ Dialogue 스키마 ============
class DialogueCreate(BaseModel):
    """대화 생성 요청"""
    session_id: int
    sender_type: SenderType
    content: str
    intent: Optional[str] = Field(None, max_length=50)


class DialogueResponse(BaseModel):
    """대화 응답"""
    dialogue_id: int
    session_id: int
    sender_type: SenderType
    content: str
    intent: Optional[str] = None
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


# ============ 페이지네이션 스키마 ============
class PaginatedResponse(BaseModel):
    """페이지네이션 응답"""
    total: int
    page: int
    page_size: int
    items: List[Any]


# ============ 에러 응답 스키마 ============
class ErrorResponse(BaseModel):
    """에러 응답"""
    error: str
    detail: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)