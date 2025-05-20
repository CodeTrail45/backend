from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from .config import Base
from datetime import datetime

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    comments = relationship("Comment", back_populates="user")

class ExternalSongReference(Base):
    """Keeps track of external songs that have been accessed in our system"""
    __tablename__ = "external_song_references"

    id = Column(Integer, primary_key=True, index=True)
    external_id = Column(Integer, unique=True, index=True)  # The Genius API song ID
    title = Column(String)
    artist = Column(String)
    view_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    comments = relationship("Comment", back_populates="song_reference")
    analyses = relationship("Analysis", back_populates="song_reference")

class Analysis(Base):
    __tablename__ = "analyses"

    id = Column(Integer, primary_key=True, index=True)
    external_song_id = Column(Integer, ForeignKey("external_song_references.external_id"))
    analysis_data = Column(Text)  # JSON string of the analysis
    version = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    song_reference = relationship("ExternalSongReference", back_populates="analyses")

class Comment(Base):
    __tablename__ = "comments"

    id = Column(Integer, primary_key=True, index=True)
    external_song_id = Column(Integer, ForeignKey("external_song_references.external_id"))
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    content = Column(Text)
    upvote_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="comments")
    song_reference = relationship("ExternalSongReference", back_populates="comments")