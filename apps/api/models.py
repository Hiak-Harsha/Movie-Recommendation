"""
SQLAlchemy ORM models for CineMatch persistence.
Defect D7: Persistent user sessions, ratings, watchlists, feedback, and media caching.
"""
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    DateTime,
    ForeignKey,
    Text,
    UniqueConstraint,
    Index
)
from sqlalchemy.orm import relationship
from apps.api.database import Base


def utc_now():
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id = Column(String(64), primary_key=True, index=True)
    username = Column(String(128), nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    ratings = relationship("Rating", back_populates="user", cascade="all, delete-orphan")
    watchlist_items = relationship("Watchlist", back_populates="user", cascade="all, delete-orphan")
    feedback_items = relationship("Feedback", back_populates="user", cascade="all, delete-orphan")


class Rating(Base):
    __tablename__ = "ratings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(64), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    movie_id = Column(Integer, nullable=False, index=True)
    rating = Column(Float, nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    user = relationship("User", back_populates="ratings")

    __table_args__ = (
        UniqueConstraint("user_id", "movie_id", name="uq_user_movie_rating"),
        Index("idx_rating_user_movie", "user_id", "movie_id"),
    )


class Watchlist(Base):
    __tablename__ = "watchlist"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(64), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    movie_id = Column(Integer, nullable=False, index=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utc_now, nullable=False)

    user = relationship("User", back_populates="watchlist_items")

    __table_args__ = (
        UniqueConstraint("user_id", "movie_id", name="uq_user_movie_watchlist"),
        Index("idx_watchlist_user_movie", "user_id", "movie_id"),
    )


class Feedback(Base):
    __tablename__ = "feedback"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(64), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    movie_id = Column(Integer, nullable=False, index=True)
    interaction_type = Column(String(32), nullable=False)  # 'click', 'like', 'dislike', 'dismiss'
    created_at = Column(DateTime, default=utc_now, nullable=False)

    user = relationship("User", back_populates="feedback_items")


class MediaCache(Base):
    __tablename__ = "media_cache"

    tmdb_id = Column(Integer, primary_key=True, index=True)
    poster_url = Column(String(512), nullable=True)
    backdrop_url = Column(String(512), nullable=True)
    overview = Column(Text, nullable=True)
    cast_json = Column(Text, nullable=True)
    director = Column(String(256), nullable=True)
    trailer_key = Column(String(128), nullable=True)
    streaming_providers_json = Column(Text, nullable=True)
    runtime = Column(Integer, nullable=True)
    vote_average = Column(Float, nullable=True)
    fetched_at = Column(DateTime, default=utc_now, nullable=False)
