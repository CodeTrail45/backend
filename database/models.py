from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, func, Boolean, Table
from sqlalchemy.orm import relationship
from .config import Base
from datetime import datetime


# We're removing this association table since we have a proper CommentUpvote class
# comment_upvotes = Table(
#     'comment_upvotes',
#     Base.metadata,
#     Column('comment_id', Integer, ForeignKey('comments.id'), primary_key=True),
#     Column('ip_address', String, primary_key=True),
#     Column('created_at', DateTime, default=datetime.utcnow)
# )

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class Song(Base):
    __tablename__ = "songs"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    artist = Column(String, index=True)
    lyrics = Column(Text)
    view_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    analyses = relationship("Analysis", back_populates="song")
    comments = relationship("Comment", back_populates="song")


class Analysis(Base):
    __tablename__ = "analyses"

    id = Column(Integer, primary_key=True, index=True)
    song_id = Column(Integer, ForeignKey("songs.id"))
    analysis_data = Column(Text)  # JSON string of the analysis
    version = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    song = relationship("Song", back_populates="analyses")


class Comment(Base):
    __tablename__ = "comments"

    id = Column(Integer, primary_key=True, index=True)
    song_id = Column(Integer, ForeignKey("songs.id"))
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    content = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    song = relationship("Song", back_populates="comments")
    user = relationship("User", back_populates="comments")

# Add relationship to Song model
Song.comments = relationship("Comment", back_populates="song")
# Add relationship to User model
User.comments = relationship("Comment", back_populates="user")