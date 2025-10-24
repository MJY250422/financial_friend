"""
데이터베이스 Enum 타입 정의
각 Enum은 특정 필드에서 사용 가능한 값들을 제한합니다.
"""
import enum


class UserType(enum.Enum):
    """
    사용자 유형
    users 테이블의 user_type 필드에 사용
    """
    ADMIN = "admin"      # 관리자
    USER = "user"        # 일반 사용자
    GUEST = "guest"      # 게스트
    PREMIUM = "premium"  # 프리미엄 사용자
    
    def __str__(self):
        return self.value
    
    @classmethod
    def get_choices(cls):
        """사용 가능한 모든 선택지 반환"""
        return [member.value for member in cls]


class InteractionType(enum.Enum):
    """
    사용자-뉴스 상호작용 유형
    user_news_interactions 테이블의 interaction_type 필드에 사용
    """
    CLICK = "click"      # 클릭
    VIEW = "view"        # 조회
    SHARE = "share"      # 공유
    LIKE = "like"        # 좋아요
    BOOKMARK = "bookmark"  # 북마크
    COMMENT = "comment"  # 댓글
    
    def __str__(self):
        return self.value
    
    @classmethod
    def get_choices(cls):
        return [member.value for member in cls]


class SenderType(enum.Enum):
    """
    대화 발신자 유형
    dialogues 테이블의 sender_type 필드에 사용
    """
    USER = "user"            # 사용자 메시지
    ASSISTANT = "assistant"  # AI 어시스턴트 응답
    SYSTEM = "system"        # 시스템 메시지
    
    def __str__(self):
        return self.value
    
    @classmethod
    def get_choices(cls):
        return [member.value for member in cls]


class TaskStatus(enum.Enum):
    """
    에이전트 작업 상태
    agent_tasks 테이블의 status 필드에 사용
    """
    PENDING = "pending"          # 대기 중
    IN_PROGRESS = "in_progress"  # 진행 중
    COMPLETED = "completed"      # 완료
    FAILED = "failed"            # 실패
    CANCELLED = "cancelled"      # 취소됨
    
    def __str__(self):
        return self.value
    
    @classmethod
    def get_choices(cls):
        return [member.value for member in cls]
    
    def is_terminal(self):
        """작업이 종료 상태인지 확인"""
        return self in (TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED)