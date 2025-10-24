from datetime import datetime
from sqlalchemy import (
    Column, String, Integer, BigInteger, Boolean, DateTime, 
    Text, Enum, JSON, LargeBinary, ForeignKey
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
import enum

Base = declarative_base()


class UserType(enum.Enum):
    """사용자 유형 Enum"""
    ADMIN = "admin"
    USER = "user"
    GUEST = "guest"


class InteractionType(enum.Enum):
    """사용자 상호작용 유형 Enum"""
    CLICK = "click"
    VIEW = "view"
    SHARE = "share"
    LIKE = "like"


class SenderType(enum.Enum):
    """대화 발신자 유형 Enum"""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class TaskStatus(enum.Enum):
    """작업 상태 Enum"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class User(Base):
    """사용자 테이블"""
    __tablename__ = 'users'
    
    user_id = Column(String(36), primary_key=True)
    user_type = Column(Enum(UserType), nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    username = Column(String(50), unique=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_active_at = Column(DateTime)
    deleted_at = Column(DateTime)
    
    # Relationships
    sessions = relationship("Session", back_populates="user", cascade="all, delete-orphan")
    interactions = relationship("UserNewsInteraction", back_populates="user", cascade="all, delete-orphan")


class Session(Base):
    """세션 테이블"""
    __tablename__ = 'sessions'
    
    session_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(36), ForeignKey('users.user_id'), nullable=False)
    session_token = Column(String(255), unique=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)
    context = Column(JSON)
    
    # Relationships
    user = relationship("User", back_populates="sessions")
    agent_tasks = relationship("AgentTask", back_populates="session", cascade="all, delete-orphan")
    dialogues = relationship("Dialogue", back_populates="session", cascade="all, delete-orphan")


class News(Base):
    """뉴스 테이블"""
    __tablename__ = 'news'
    
    news_id = Column(BigInteger, primary_key=True, autoincrement=True)
    title = Column(String(500), nullable=False)
    url = Column(String(1000), unique=True, nullable=False)
    content = Column(Text)
    source = Column(String(100))
    published_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime)
    
    # Relationships
    embeddings = relationship("NewsEmbedding", back_populates="news", cascade="all, delete-orphan")
    interactions = relationship("UserNewsInteraction", back_populates="news", cascade="all, delete-orphan")


class NewsEmbedding(Base):
    """뉴스 임베딩 테이블"""
    __tablename__ = 'news_embeddings'
    
    embedding_id = Column(BigInteger, primary_key=True, autoincrement=True)
    news_id = Column(BigInteger, ForeignKey('news.news_id'), nullable=False)
    embedding_vector = Column(LargeBinary, nullable=False)
    model_version = Column(String(50), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    news = relationship("News", back_populates="embeddings")


class UserNewsInteraction(Base):
    """사용자-뉴스 상호작용 테이블"""
    __tablename__ = 'user_news_interactions'
    
    interaction_id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(String(36), ForeignKey('users.user_id'), nullable=False)
    news_id = Column(BigInteger, ForeignKey('news.news_id'), nullable=False)
    interaction_type = Column(Enum(InteractionType), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="interactions")
    news = relationship("News", back_populates="interactions")


class AgentInfo(Base):
    """에이전트 정보 테이블"""
    __tablename__ = 'agent_info'
    
    agent_id = Column(Integer, primary_key=True, autoincrement=True)
    agent_type = Column(String(50), nullable=False)
    description = Column(Text)
    version = Column(String(20))
    model_version = Column(String(50))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    tasks = relationship("AgentTask", back_populates="agent", cascade="all, delete-orphan")


class AgentTask(Base):
    """에이전트 작업 테이블"""
    __tablename__ = 'agent_tasks'
    
    task_id = Column(BigInteger, primary_key=True, autoincrement=True)
    agent_id = Column(Integer, ForeignKey('agent_info.agent_id'), nullable=False)
    session_id = Column(Integer, ForeignKey('sessions.session_id'), nullable=False)
    dialogue_id = Column(BigInteger, ForeignKey('dialogues.dialogue_id'))
    input_data = Column(JSON)
    output_data = Column(JSON)
    status = Column(Enum(TaskStatus), default=TaskStatus.PENDING)
    error_reason = Column(Text)
    duration_ms = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    agent = relationship("AgentInfo", back_populates="tasks")
    session = relationship("Session", back_populates="agent_tasks")
    dialogue = relationship("Dialogue", back_populates="agent_tasks")


class Dialogue(Base):
    """대화 테이블"""
    __tablename__ = 'dialogues'
    
    dialogue_id = Column(BigInteger, primary_key=True, autoincrement=True)
    session_id = Column(Integer, ForeignKey('sessions.session_id'), nullable=False)
    sender_type = Column(Enum(SenderType), nullable=False)
    content = Column(Text, nullable=False)
    intent = Column(String(50))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    session = relationship("Session", back_populates="dialogues")
    agent_tasks = relationship("AgentTask", back_populates="dialogue", cascade="all, delete-orphan")