from pydantic import BaseModel, ConfigDict, EmailStr
from typing import List, Optional
from datetime import datetime

class CommentBase(BaseModel):
    content: str

class CommentCreate(CommentBase):
    song_id: int
    user_id: Optional[int] = None
    ip_address: Optional[str] = None

class Comment(CommentBase):
    id: int
    song_id: int
    user_id: Optional[int]
    ip_address: Optional[str]
    upvote_count: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class CommentUpvote(BaseModel):
    comment_id: int
    ip_address: str

class SongBase(BaseModel):
    title: str
    artist: str
    lyrics: str

class SongCreate(SongBase):
    pass

class Song(SongBase):
    id: int
    view_count: int
    created_at: datetime
    updated_at: datetime
    comments: List[Comment] = []

    model_config = ConfigDict(from_attributes=True)

class AnalysisBase(BaseModel):
    analysis_data: str

class AnalysisCreate(AnalysisBase):
    song_id: int

class Analysis(AnalysisBase):
    id: int
    song_id: int
    version: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class PaginatedResponse(BaseModel):
    items: List[Song]
    total: int
    page: int
    size: int
    pages: int

class UserBase(BaseModel):
    username: str
    email: Optional[EmailStr] = None

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: int
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True) 