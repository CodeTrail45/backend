from pydantic import BaseModel, ConfigDict, EmailStr
from typing import List, Optional
from datetime import datetime

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

class CommentBase(BaseModel):
    content: str
    song_id: int  # This is the external song ID from Genius API

class CommentCreate(CommentBase):
    pass

class CommentResponse(CommentBase):
    id: int
    created_at: datetime
    updated_at: datetime
    username: Optional[str] = None  # Add username field for display
    upvote_count: int = 0  # Add upvote count field

    model_config = ConfigDict(from_attributes=True)
