from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime,
    ForeignKey, Text, UniqueConstraint
)
from sqlalchemy.orm import relationship
from database import Base


class Playlist(Base):
    __tablename__ = "playlists"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    source_type = Column(String(50))  # m3u or xtream
    source_url = Column(Text)
    xtream_host = Column(String(255))
    xtream_user = Column(String(255))
    xtream_pass = Column(String(255))
    content_hash = Column(String(64))
    version = Column(Integer, default=1)
    status = Column(String(50), default="active")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    channels = relationship("Channel", back_populates="playlist", cascade="all, delete-orphan")


class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True)
    raw_name = Column(String(255))
    normalized_name = Column(String(255))
    category_type = Column(String(50))  # live, movie, series, sports, news, kids, adult
    created_at = Column(DateTime, default=datetime.utcnow)

    channels = relationship("Channel", back_populates="category")


class Channel(Base):
    __tablename__ = "channels"

    id = Column(Integer, primary_key=True, index=True)
    playlist_id = Column(Integer, ForeignKey("playlists.id"))
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=True)
    name = Column(String(500))
    url = Column(Text)
    logo = Column(Text)
    tvg_id = Column(String(255))
    language = Column(String(100))
    country = Column(String(100))
    group_title = Column(String(255))
    dedup_key = Column(String(64), index=True)
    is_blacklisted = Column(Boolean, default=False)
    is_whitelisted = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (UniqueConstraint("playlist_id", "dedup_key", name="uq_channel_playlist"),)

    playlist = relationship("Playlist", back_populates="channels")
    category = relationship("Category", back_populates="channels")


class Blacklist(Base):
    __tablename__ = "blacklist"

    id = Column(Integer, primary_key=True, index=True)
    channel_name_pattern = Column(String(500))
    url_pattern = Column(String(500))
    category = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow)


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    action = Column(String(100))
    entity_type = Column(String(100))
    entity_id = Column(Integer)
    detail = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
