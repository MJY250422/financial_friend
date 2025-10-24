"""
유틸리티 함수
"""
import hashlib
import secrets
from typing import Optional


def hash_password(password: str) -> str:
    """
    비밀번호 해싱
    
    Args:
        password: 평문 비밀번호
    
    Returns:
        해싱된 비밀번호
    """
    # 실제 프로덕션에서는 bcrypt나 argon2 사용 권장
    # 예: from passlib.hash import bcrypt
    # return bcrypt.hash(password)
    
    # 간단한 예제 (실제로는 사용하지 마세요!)
    salt = secrets.token_hex(16)
    hashed = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode('utf-8'),
        salt.encode('utf-8'),
        100000
    )
    return f"{salt}${hashed.hex()}"


def verify_password(password: str, hashed_password: str) -> bool:
    """
    비밀번호 검증
    
    Args:
        password: 평문 비밀번호
        hashed_password: 해싱된 비밀번호
    
    Returns:
        비밀번호 일치 여부
    """
    try:
        salt, stored_hash = hashed_password.split('$')
        hashed = hashlib.pbkdf2_hmac(
            'sha256',
            password.encode('utf-8'),
            salt.encode('utf-8'),
            100000
        )
        return hashed.hex() == stored_hash
    except Exception:
        return False