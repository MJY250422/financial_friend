# enums.py - Pydantic 스키마용 Enum 정의

from enum import Enum

class UserTypeEnum(str, Enum):
    """사용자 유형
    
    - GUEST: 임시 사용자 (UUID만 존재)
    - REGISTERED: 등록 사용자 (이메일/비밀번호 있음)
    """
    GUEST = "guest"
    REGISTERED = "registered"


class InteractionTypeEnum(str, Enum):
    """뉴스 상호작용 유형
    
    - VIEW: 뉴스 조회 (자동 기록)
    - LIKE: 좋아요
    - BOOKMARK: 북마크 저장
    - SHARE: 공유
    - COMMENT: 댓글 (향후 확장)
    """
    VIEW = "view"
    LIKE = "like"
    BOOKMARK = "bookmark"
    SHARE = "share"
    COMMENT = "comment"


class SenderTypeEnum(str, Enum):
    """대화 발신자 유형
    
    - USER: 사용자 메시지
    - AGENT: 에이전트 응답
    - SYSTEM: 시스템 메시지 (알림, 오류 등)
    """
    USER = "user"
    AGENT = "agent"
    SYSTEM = "system"


class TaskStatusEnum(str, Enum):
    """에이전트 태스크 상태
    
    - PENDING: 대기 중
    - RUNNING: 실행 중
    - COMPLETED: 완료
    - FAILED: 실패 (error_reason 필드에 상세 기록)
    - CANCELLED: 취소됨
    """
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class AgentTypeEnum(str, Enum):
    """에이전트 유형
    
    - RAG_QUERY: RAG 기반 질의응답
    - TERM_EXPLAINER: 금융 용어 설명
    - NEWS_ANALYZER: 뉴스 분석 및 요약
    - ORCHESTRATOR: 멀티 에이전트 오케스트레이션
    """
    RAG_QUERY = "rag_query"
    TERM_EXPLAINER = "term_explainer"
    NEWS_ANALYZER = "news_analyzer"
    ORCHESTRATOR = "orchestrator"


class IntentTypeEnum(str, Enum):
    """대화 의도 분류 (NLU용)
    
    - TERM_QUERY: 용어 설명 요청
    - NEWS_SEARCH: 뉴스 검색
    - NEWS_SUMMARY: 뉴스 요약 요청
    - MARKET_ANALYSIS: 시장 분석 요청
    - GENERAL_CHAT: 일반 대화
    - UNKNOWN: 의도 불명
    """
    TERM_QUERY = "term_query"
    NEWS_SEARCH = "news_search"
    NEWS_SUMMARY = "news_summary"
    MARKET_ANALYSIS = "market_analysis"
    GENERAL_CHAT = "general_chat"
    UNKNOWN = "unknown"