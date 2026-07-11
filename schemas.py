from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, HttpUrl


class ChannelOut(BaseModel):
    id: int
    name: str
    url: str
    logo: Optional[str] = None
    tvg_id: Optional[str] = None
    language: Optional[str] = None
    country: Optional[str] = None
    group_title: Optional[str] = None
    category: Optional[str] = None
    is_blacklisted: bool = False
    is_whitelisted: bool = False
    created_at: datetime

    class Config:
        from_attributes = True


class PlaylistOut(BaseModel):
    id: int
    name: str
    source_type: str
    source_url: Optional[str] = None
    version: int
    status: str
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class PlaylistCreate(BaseModel):
    name: str
    source_url: Optional[str] = None


class XtreamIngest(BaseModel):
    name: str
    host: str
    username: str
    password: str


class BlacklistCreate(BaseModel):
    channel_name_pattern: Optional[str] = None
    url_pattern: Optional[str] = None
    category: Optional[str] = None


class BlacklistOut(BaseModel):
    id: int
    channel_name_pattern: Optional[str] = None
    url_pattern: Optional[str] = None
    category: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class StatsOut(BaseModel):
    total_channels: int
    total_playlists: int
    by_category: dict
    by_language: dict
