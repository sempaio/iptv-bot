from typing import List, Optional
from sqlalchemy.orm import Session
from models import Channel, Category


def build_m3u_line(channel: Channel, category_name: str = "") -> str:
    """
    Monta uma entrada M3U para um canal.
    """
    logo = channel.logo or ""
    tvg_id = channel.tvg_id or ""
    language = channel.language or ""
    country = channel.country or ""
    group = category_name or channel.group_title or ""

    extinf = (
        f'#EXTINF:-1 tvg-id="{tvg_id}" tvg-name="{channel.name}" '
        f'tvg-logo="{logo}" tvg-language="{language}" '
        f'tvg-country="{country}" group-title="{group}",{channel.name}'
    )
    return f"{extinf}\n{channel.url}"


def export_m3u(
    db: Session,
    playlist_id: Optional[int] = None,
    category: Optional[str] = None,
    language: Optional[str] = None,
    include_blacklisted: bool = False,
) -> str:
    """
    Exporta uma M3U organizada por categoria.
    Suporta filtros por playlist, categoria e idioma.
    """
    query = db.query(Channel)

    if playlist_id:
        query = query.filter(Channel.playlist_id == playlist_id)

    if category:
        cat = db.query(Category).filter(
            Category.normalized_name == category
        ).first()
        if cat:
            query = query.filter(Channel.category_id == cat.id)

    if language:
        query = query.filter(Channel.language == language)

    if not include_blacklisted:
        query = query.filter(Channel.is_blacklisted == False)

    channels = query.order_by(Channel.group_title, Channel.name).all()

    lines = ["#EXTM3U"]
    for ch in channels:
        cat_name = ch.category.normalized_name if ch.category else ch.group_title
        lines.append(build_m3u_line(ch, cat_name))

    return "\n".join(lines)


def export_json(db: Session, playlist_id: Optional[int] = None) -> List[dict]:
    """
    Exporta canais como lista de dicionarios (para painel).
    """
    query = db.query(Channel).filter(Channel.is_blacklisted == False)

    if playlist_id:
        query = query.filter(Channel.playlist_id == playlist_id)

    channels = query.order_by(Channel.group_title, Channel.name).all()

    result = []
    for ch in channels:
        cat_name = ch.category.normalized_name if ch.category else ch.group_title
        result.append({
            "id": ch.id,
            "name": ch.name,
            "url": ch.url,
            "logo": ch.logo,
            "tvg_id": ch.tvg_id,
            "language": ch.language,
            "country": ch.country,
            "category": cat_name,
            "group_title": ch.group_title,
        })

    return result
