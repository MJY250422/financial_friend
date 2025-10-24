from datetime import datetime, timezone
from typing import Optional, List
from enum import Enum as PyEnum
from sqlalchemy import (
    Column, Integer, String, Text, DateTime, Boolean, 
    ForeignKey, Enum, BigInteger, JSON, Index
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB
from pgvector.sqlalchemy import Vector
import uuid

# ===== Base =====
class Base(DeclarativeBase):
    """모든 모델의 기본 클래스"""
    pass

# ===== Enums =====
class UserType(str, PyEnum):
    """사용자 유형"""
    GUEST = "guest"
    REGISTERED = "registered"

class InteractionType(str, PyEnum):
    """뉴스 상호작용 유형"""
    VIEW = "view"           # 조회
    LIKE = "like"           # 좋아요
    BOOKMARK = "bookmark"   # 북마크
    SHARE = "share"         # 공유
    COMMENT = "comment"     # 댓글 (향후 확장)

class SenderType(str, PyEnum):
    """대화 발신자 유형"""
    USER = "user"
    AGENT = "agent"
    SYSTEM = "system"

class TaskStatus(str, PyEnum):
    """에이전트 태스크 상태"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class AgentType(str, PyEnum):
    """에이전트 유형"""
    RAG_QUERY = "rag_query"           # RAG 검색 에이전트
    TERM_EXPLAINER = "term_explainer" # 용어 설명 에이전트
    NEWS_ANALYZER = "news_analyzer"   # 뉴스 분석 에이전트
    ORCHESTRATOR = "orchestrator"     # 오케스트레이터

# ===== Mixins =====
class TimestampMixin:
    """타임스탬프 필드 믹스인 (UTC 기준)"""
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False
    )

class SoftDeleteMixin:
    """소프트 삭제 믹스인"""
    deleted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=None
    )
    
    @property
    def is_deleted(self) -> bool:
        return self.deleted_at is not None
    
    def soft_delete(self):
        """소프트 삭제 수행"""
        self.deleted_at = datetime.now(timezone.utc)

# ===== Models =====

class User(Base, TimestampMixin, SoftDeleteMixin):
    """사용자 테이블
    
    역할:
    - 게스트 및 등록 사용자 관리
    - UUID 기반 식별로 프라이버시 강화
    - Soft delete로 사용자 데이터 복구 가능
    """
    __tablename__ = "users"
    
    user_id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )
    user_type: Mapped[UserType] = mapped_column(
        Enum(UserType),
        nullable=False,
        default=UserType.GUEST
    )
    email: Mapped[Optional[str]] = mapped_column(String(100), unique=True, nullable=True)
    password_hash: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    username: Mapped[Optional[str]] = mapped_column(String(50), unique=True, nullable=True)
    last_active_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    
    # Relationships
    sessions: Mapped[List["Session"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan"
    )
    interactions: Mapped[List["UserNewsInteraction"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan"
    )
    
    __table_args__ = (
        Index('idx_users_email_not_deleted', 'email', postgresql_where=Column('deleted_at').is_(None)),
        Index('idx_users_type_not_deleted', 'user_type', postgresql_where=Column('deleted_at').is_(None)),
    )


class FinancialTerm(Base, TimestampMixin, SoftDeleteMixin):
    """금융 용어 테이블
    
    역할:
    - 금융 용어 사전 관리
    - 한영 용어 매핑
    - 관련 법규 및 카테고리 분류
    """
    __tablename__ = "financial_terms"
    
    term_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    term: Mapped[str] = mapped_column(String(200), nullable=False, unique=True)
    definition: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    related_law: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    english_term: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    examples: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Relationships (1:1)
    embedding: Mapped[Optional["TermEmbedding"]] = relationship(
        back_populates="term",
        uselist=False,
        cascade="all, delete-orphan"
    )
    
    __table_args__ = (
        Index('idx_terms_category', 'category', postgresql_where=Column('deleted_at').is_(None)),
        Index('idx_terms_term_search', 'term', postgresql_where=Column('deleted_at').is_(None)),
    )


class TermEmbedding(Base, TimestampMixin):
    """용어 임베딩 테이블
    
    역할:
    - 금융 용어의 벡터 임베딩 저장
    - pgvector를 활용한 시맨틱 검색
    - 모델 버전별 임베딩 관리
    """
    __tablename__ = "term_embeddings"
    
    embedding_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    term_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("financial_terms.term_id", ondelete="CASCADE"),
        nullable=False,
        unique=True  # 1:1 관계 보장
    )
    # pgvector 타입 (1536은 OpenAI text-embedding-ada-002 기준)
    embedding_vector: Mapped[List[float]] = mapped_column(
        Vector(1536),
        nullable=False
    )
    model_version: Mapped[str] = mapped_column(String(50), nullable=False)
    
    # Relationships
    term: Mapped["FinancialTerm"] = relationship(back_populates="embedding")
    
    __table_args__ = (
        # HNSW 인덱스로 벡터 검색 최적화 (코사인 유사도)
        Index(
            'idx_term_embeddings_vector',
            'embedding_vector',
            postgresql_using='hnsw',
            postgresql_with={'m': 16, 'ef_construction': 64},
            postgresql_ops={'embedding_vector': 'vector_cosine_ops'}
        ),
    )


class News(Base, TimestampMixin, SoftDeleteMixin):
    """뉴스 테이블
    
    역할:
    - 금융 뉴스 원문 저장
    - 출처 및 발행일 관리
    - URL 중복 방지
    """
    __tablename__ = "news"
    
    news_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    url: Mapped[str] = mapped_column(String(1000), nullable=False, unique=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    source: Mapped[str] = mapped_column(String(100), nullable=False)
    published_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    
    # Relationships
    embedding: Mapped[Optional["NewsEmbedding"]] = relationship(
        back_populates="news",
        uselist=False,
        cascade="all, delete-orphan"
    )
    interactions: Mapped[List["UserNewsInteraction"]] = relationship(
        back_populates="news",
        cascade="all, delete-orphan"
    )
    
    __table_args__ = (
        Index('idx_news_published_at', 'published_at', postgresql_where=Column('deleted_at').is_(None)),
        Index('idx_news_source', 'source', postgresql_where=Column('deleted_at').is_(None)),
    )


class NewsEmbedding(Base, TimestampMixin):
    """뉴스 임베딩 테이블
    
    역할:
    - 뉴스 본문의 벡터 임베딩 저장
    - RAG 검색 시 사용
    - 버전별 임베딩 업데이트 추적
    """
    __tablename__ = "news_embeddings"
    
    embedding_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    news_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("news.news_id", ondelete="CASCADE"),
        nullable=False,
        unique=True
    )
    embedding_vector: Mapped[List[float]] = mapped_column(Vector(1536), nullable=False)
    model_version: Mapped[str] = mapped_column(String(50), nullable=False)
    
    # Relationships
    news: Mapped["News"] = relationship(back_populates="embedding")
    
    __table_args__ = (
        Index(
            'idx_news_embeddings_vector',
            'embedding_vector',
            postgresql_using='hnsw',
            postgresql_with={'m': 16, 'ef_construction': 64},
            postgresql_ops={'embedding_vector': 'vector_cosine_ops'}
        ),
    )


class UserNewsInteraction(Base, TimestampMixin):
    """사용자-뉴스 상호작용 테이블 (N:N)
    
    역할:
    - 사용자의 뉴스 조회/좋아요/북마크 추적
    - 추천 시스템 데이터 수집
    - 컨텍스트 정보 JSON 저장
    """
    __tablename__ = "user_news_interactions"
    
    interaction_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.user_id", ondelete="CASCADE"),
        nullable=False
    )
    news_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("news.news_id", ondelete="CASCADE"),
        nullable=False
    )
    interaction_type: Mapped[InteractionType] = mapped_column(
        Enum(InteractionType),
        nullable=False
    )
    context: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)  # 추가 메타데이터
    
    # Relationships
    user: Mapped["User"] = relationship(back_populates="interactions")
    news: Mapped["News"] = relationship(back_populates="interactions")
    
    __table_args__ = (
        # 동일 사용자가 동일 뉴스에 동일 타입 중복 방지
        Index('idx_unique_interaction', 'user_id', 'news_id', 'interaction_type', unique=True),
        Index('idx_interactions_user', 'user_id'),
        Index('idx_interactions_news', 'news_id'),
        Index('idx_interactions_type', 'interaction_type'),
    )


class Session(Base, TimestampMixin):
    """세션 테이블
    
    역할:
    - 사용자 세션 관리
    - JWT 토큰 발급 및 검증
    - 만료 시간 추적
    """
    __tablename__ = "sessions"
    
    session_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.user_id", ondelete="CASCADE"),
        nullable=False
    )
    session_token: Mapped[str] = mapped_column(String(36), nullable=False, unique=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    context: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)  # 세션 컨텍스트
    
    # Relationships
    user: Mapped["User"] = relationship(back_populates="sessions")
    dialogues: Mapped[List["Dialogue"]] = relationship(
        back_populates="session",
        cascade="all, delete-orphan"
    )
    agent_tasks: Mapped[List["AgentTask"]] = relationship(
        back_populates="session",
        cascade="all, delete-orphan"
    )
    
    __table_args__ = (
        Index('idx_sessions_token', 'session_token'),
        Index('idx_sessions_expires_at', 'expires_at'),
        Index('idx_sessions_user', 'user_id'),
    )


class Dialogue(Base, TimestampMixin):
    """대화 테이블
    
    역할:
    - 사용자-에이전트 대화 히스토리 저장
    - 세션별 대화 추적
    - 멀티턴 대화 컨텍스트 관리
    """
    __tablename__ = "dialogues"
    
    dialogue_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    session_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("sessions.session_id", ondelete="CASCADE"),
        nullable=False
    )
    sender_type: Mapped[SenderType] = mapped_column(Enum(SenderType), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    intent: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # 의도 분류
    
    # Relationships
    session: Mapped["Session"] = relationship(back_populates="dialogues")
    agent_tasks: Mapped[List["AgentTask"]] = relationship(
        back_populates="dialogue",
        cascade="all, delete-orphan"
    )
    
    __table_args__ = (
        Index('idx_dialogues_session', 'session_id'),
        Index('idx_dialogues_created_at', 'created_at'),
    )


class AgentInfo(Base, TimestampMixin):
    """에이전트 정보 테이블
    
    역할:
    - 다양한 에이전트 유형 관리
    - 버전별 에이전트 배포
    - 활성화 상태 제어
    """
    __tablename__ = "agent_info"
    
    agent_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    agent_type: Mapped[AgentType] = mapped_column(Enum(AgentType), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    version: Mapped[str] = mapped_column(String(20), nullable=False)
    model_version: Mapped[str] = mapped_column(String(50), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    # Relationships
    agent_tasks: Mapped[List["AgentTask"]] = relationship(
        back_populates="agent",
        cascade="all, delete-orphan"
    )
    
    __table_args__ = (
        Index('idx_agents_type_active', 'agent_type', 'is_active'),
        Index('idx_agents_version', 'version'),
    )


class AgentTask(Base, TimestampMixin):
    """에이전트 태스크 테이블
    
    역할:
    - 에이전트 작업 실행 추적
    - 입출력 데이터 로깅
    - 오류 및 성능 모니터링
    """
    __tablename__ = "agent_tasks"
    
    task_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    agent_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("agent_info.agent_id", ondelete="CASCADE"),
        nullable=False
    )
    session_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("sessions.session_id", ondelete="CASCADE"),
        nullable=False
    )
    dialogue_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("dialogues.dialogue_id", ondelete="CASCADE"),
        nullable=False
    )
    input_data: Mapped[dict] = mapped_column(JSONB, nullable=False)
    output_data: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    status: Mapped[TaskStatus] = mapped_column(
        Enum(TaskStatus),
        nullable=False,
        default=TaskStatus.PENDING
    )
    error_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    duration_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # 실행 시간
    
    # Relationships
    agent: Mapped["AgentInfo"] = relationship(back_populates="agent_tasks")
    session: Mapped["Session"] = relationship(back_populates="agent_tasks")
    dialogue: Mapped["Dialogue"] = relationship(back_populates="agent_tasks")
    
    __table_args__ = (
        Index('idx_tasks_status', 'status'),
        Index('idx_tasks_session', 'session_id'),
        Index('idx_tasks_agent', 'agent_id'),
        Index('idx_tasks_created_at', 'created_at'),
    )