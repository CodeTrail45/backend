from datetime import datetime, timedelta
from typing import Optional, Callable
from fastapi import HTTPException, Depends, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials, OAuth2PasswordBearer
from sqlalchemy.orm import Session
from .config import get_db
from . import models
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
import os
import hashlib
import hmac
import json
import base64
import time
from collections import defaultdict
import threading

# Rate limiting
ENV = os.getenv("ENV", "development")
if ENV == "test":
    RATE_LIMIT_WINDOW = 1  # 1 second for tests
    RATE_LIMIT_MAX_REQUESTS = 1000  # 1000 requests per second for tests
else:
    RATE_LIMIT_WINDOW = 60  # 1 minute for production
    RATE_LIMIT_MAX_REQUESTS = 100  # 100 requests per minute for production

# In-memory rate limiting storage
request_counts = defaultdict(list)
rate_limit_lock = threading.Lock()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return hmac.compare_digest(
        hashed_password.encode(),
        hashlib.sha256(plain_password.encode()).hexdigest().encode()
    )

def get_password_hash(password: str) -> str:
    """Generate a password hash."""
    return hashlib.sha256(password.encode()).hexdigest()

def check_rate_limit(request: Request) -> bool:
    """Check if the request is within rate limits"""
    if ENV == "test":
        return True  # Skip rate limiting in test environment
    
    client_ip = request.client.host
    current_time = time.time()
    
    with rate_limit_lock:
        # Clean old requests
        request_counts[client_ip] = [
            req_time for req_time in request_counts[client_ip]
            if current_time - req_time < RATE_LIMIT_WINDOW
        ]
        
        # Check if limit is exceeded
        if len(request_counts[client_ip]) >= RATE_LIMIT_MAX_REQUESTS:
            return False
        
        # Add new request
        request_counts[client_ip].append(current_time)
        return True

class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp):
        super().__init__(app)

    async def dispatch(self, request: Request, call_next: Callable):
        if not check_rate_limit(request):
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many requests"
            )
        return await call_next(request)

# Database-based authentication
class DBAuth:
    def create_user(self, username: str, password: str, db: Session, email: Optional[str] = None) -> models.User:
        """Create a new user."""
        # Check if username already exists
        if db.query(models.User).filter(models.User.username == username).first():
            raise HTTPException(status_code=400, detail="Username already registered")
        
        # Check if email already exists
        if email and db.query(models.User).filter(models.User.email == email).first():
            raise HTTPException(status_code=400, detail="Email already registered")
        
        # Create new user
        hashed_password = get_password_hash(password)
        db_user = models.User(
            username=username,
            hashed_password=hashed_password,
            email=email
        )
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return db_user

    def authenticate_user(self, username: str, password: str, db: Session) -> Optional[models.User]:
        """Authenticate a user."""
        user = db.query(models.User).filter(models.User.username == username).first()
        if not user or not verify_password(password, user.hashed_password):
            return None
        return user

# Create a global auth instance
auth = DBAuth()

# Dependency for getting current user
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer()),
    db: Session = Depends(get_db)
) -> models.User:
    """Get the current user from the token."""
    user = verify_token(credentials.credentials, db)
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user

def generate_token(user: models.User) -> str:
    """Generate a JWT-like token without a secret key."""
    # Create header
    header = {
        "alg": "HS256",
        "typ": "JWT"
    }
    
    # Create payload
    payload = {
        "sub": str(user.id),
        "username": user.username,
        "exp": (datetime.utcnow() + timedelta(days=1)).timestamp(),
        "iat": datetime.utcnow().timestamp()
    }
    
    # Encode header and payload
    encoded_header = base64.urlsafe_b64encode(json.dumps(header).encode()).decode().rstrip('=')
    encoded_payload = base64.urlsafe_b64encode(json.dumps(payload).encode()).decode().rstrip('=')
    
    # Create signature using user's password hash
    signature_input = f"{encoded_header}.{encoded_payload}"
    signature = hmac.new(
        user.hashed_password.encode(),
        signature_input.encode(),
        hashlib.sha256
    ).hexdigest()
    
    # Combine all parts
    return f"{encoded_header}.{encoded_payload}.{signature}"

def verify_token(token: str, db: Session) -> Optional[models.User]:
    """Verify a JWT-like token."""
    try:
        # Split token
        header_b64, payload_b64, signature = token.split('.')
        
        # Add padding back
        header_b64 += '=' * (4 - len(header_b64) % 4)
        payload_b64 += '=' * (4 - len(payload_b64) % 4)
        
        # Decode header and payload
        header = json.loads(base64.urlsafe_b64decode(header_b64))
        payload = json.loads(base64.urlsafe_b64decode(payload_b64))
        
        # Check expiration
        if datetime.utcnow().timestamp() > payload['exp']:
            return None
        
        # Get user
        user = db.query(models.User).filter(models.User.id == int(payload['sub'])).first()
        if not user:
            return None
        
        # Verify signature
        signature_input = f"{header_b64.rstrip('=')}.{payload_b64.rstrip('=')}"
        expected_signature = hmac.new(
            user.hashed_password.encode(),
            signature_input.encode(),
            hashlib.sha256
        ).hexdigest()
        
        if not hmac.compare_digest(signature, expected_signature):
            return None
        
        return user
    except:
        return None 