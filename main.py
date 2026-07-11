import logging
from typing import Optional, List
from fastapi import FastAPI, UploadFile, File, Depends, HTTPException, Response
from fastapi.responses import PlainTextResponse
from sqlalchemy.orm import Session
from sqlalchemy import func

from database import get_db, init_db
from models import Playlist, Channel, Category, Blacklist, AuditLog
from schemas import (
    ChannelOut, PlaylistOut, PlaylistCreate,
    XtreamIngest, BlacklistCreate, BlacklistOut, StatsOut
)
from parser import parse_m3u, compute_content_hash
from xtream import fetch_all_xtream_channels
from exporter import export_m3u, export_json
from normalizer import normalize_category, normalize_language, make_dedup_key

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="IPTV Bot",
    description="Bot de ingestao, parsing e normalizacao de playlists M3U/Xtream",
    version="10.0.0",
)


@app.on_event("startup")
def startup():
    init_db()
    logger.info("IPTV Bot iniciado - banco criado/verificado")


# ─── INGEST M3U ───────────────────────────────────────────────────────────────

@app.post("/ingest/m3u", summary="Ingere playlist M3U por upload ou URL")
def ingest_m3u(
    name: str,
    file: Optional[UploadFile] = File(None),
    url: Optional[str] = None,
    db: Session = Depends(get_db)
):
    import requests

    if file:
        content = file.file.read().decode("utf-8", errors="ignore")
    elif url:
        r = requests.get(url, timeout=60)
        r.raise_for_status()
        content = r.text
    else:
        raise HTTPException(400, "Envie um arquivo ou uma URL")

    content_hash = compute_content_hash(content)
    playlist = Playlist(
        name=name,
        source_type="m3u",
        source_url=url,
        content_hash=content_hash,
        status="processing",
    )
    db.add(playlist)
    db.flush()

    channels_data = parse_m3u(content)
    inserted, skipped = _save_channels(db, playlist.id, channels_data)

    playlist.status = "active"
    db.commit()

    log_audit(db, "ingest_m3u", "playlist", playlist.id, f"{inserted} inseridos, {skipped} duplicados")

    return {
        "playlist_id": playlist.id,
        "total_parsed": len(channels_data),
        "inserted": inserted,
        "skipped": skipped,
    }


# ─── INGEST XTREAM ────────────────────────────────────────────────────────────

@app.post("/ingest/xtream", summary="Ingere via credenciais Xtream Codes")
def ingest_xtream(data: XtreamIngest, db: Session = Depends(get_db)):
    channels_data = fetch_all_xtream_channels(data.host, data.username, data.password)

    playlist = Playlist(
        name=data.name,
        source_type="xtream",
        xtream_host=data.host,
        xtream_user=data.username,
        xtream_pass=data.password,
        status="processing",
    )
    db.add(playlist)
    db.flush()

    inserted, skipped = _save_channels(db, playlist.id, channels_data)
    playlist.status = "active"
    db.commit()

    log_audit(db, "ingest_xtream", "playlist", playlist.id, f"{inserted} inseridos")

    return {
        "playlist_id": playlist.id,
        "total_parsed": len(channels_data),
        "inserted": inserted,
        "skipped": skipped,
    }


# ─── CHANNELS ─────────────────────────────────────────────────────────────────

@app.get("/channels", response_model=List[ChannelOut], summary="Lista canais")
def list_channels(
    category: Optional[str] = None,
    language: Optional[str] = None,
    playlist_id: Optional[int] = None,
    blacklisted: bool = False,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    query = db.query(Channel)
    if category:
        cat = db.query(Category).filter(Category.normalized_name == category).first()
        if cat:
            query = query.filter(Channel.category_id == cat.id)
    if language:
        query = query.filter(Channel.language == language)
    if playlist_id:
        query = query.filter(Channel.playlist_id == playlist_id)
    if not blacklisted:
        query = query.filter(Channel.is_blacklisted == False)
    return query.offset(skip).limit(limit).all()


# ─── EXPORT M3U ───────────────────────────────────────────────────────────────

@app.get("/export/m3u", response_class=PlainTextResponse, summary="Exporta M3U")
def get_export_m3u(
    playlist_id: Optional[int] = None,
    category: Optional[str] = None,
    language: Optional[str] = None,
    db: Session = Depends(get_db)
):
    content = export_m3u(db, playlist_id=playlist_id, category=category, language=language)
    return Response(content=content, media_type="audio/x-mpegurl")


# ─── STATS ────────────────────────────────────────────────────────────────────

@app.get("/stats", response_model=StatsOut, summary="Estatisticas gerais")
def get_stats(db: Session = Depends(get_db)):
    total_channels = db.query(Channel).count()
    total_playlists = db.query(Playlist).count()

    by_category_raw = (
        db.query(Category.normalized_name, func.count(Channel.id))
        .join(Channel, Channel.category_id == Category.id)
        .group_by(Category.normalized_name)
        .all()
    )
    by_language_raw = (
        db.query(Channel.language, func.count(Channel.id))
        .group_by(Channel.language)
        .all()
    )

    return StatsOut(
        total_channels=total_channels,
        total_playlists=total_playlists,
        by_category={k: v for k, v in by_category_raw},
        by_language={k or "other": v for k, v in by_language_raw},
    )


# ─── PLAYLISTS ────────────────────────────────────────────────────────────────

@app.get("/playlists", response_model=List[PlaylistOut], summary="Lista playlists")
def list_playlists(db: Session = Depends(get_db)):
    return db.query(Playlist).all()


@app.delete("/playlists/{playlist_id}", summary="Remove playlist e seus canais")
def delete_playlist(playlist_id: int, db: Session = Depends(get_db)):
    pl = db.query(Playlist).filter(Playlist.id == playlist_id).first()
    if not pl:
        raise HTTPException(404, "Playlist nao encontrada")
    db.delete(pl)
    db.commit()
    return {"deleted": playlist_id}


# ─── BLACKLIST ────────────────────────────────────────────────────────────────

@app.post("/blacklist", response_model=BlacklistOut, summary="Adiciona regra a blacklist")
def add_blacklist(data: BlacklistCreate, db: Session = Depends(get_db)):
    bl = Blacklist(**data.dict())
    db.add(bl)
    db.commit()
    db.refresh(bl)
    _apply_blacklist(db, bl)
    return bl


@app.delete("/blacklist/{blacklist_id}", summary="Remove regra da blacklist")
def remove_blacklist(blacklist_id: int, db: Session = Depends(get_db)):
    bl = db.query(Blacklist).filter(Blacklist.id == blacklist_id).first()
    if not bl:
        raise HTTPException(404, "Regra nao encontrada")
    db.delete(bl)
    db.commit()
    return {"deleted": blacklist_id}


@app.get("/blacklist", response_model=List[BlacklistOut], summary="Lista regras de blacklist")
def list_blacklist(db: Session = Depends(get_db)):
    return db.query(Blacklist).all()


# ─── REFRESH ──────────────────────────────────────────────────────────────────

@app.post("/playlists/{playlist_id}/refresh", summary="Recarrega playlist M3U da origem")
def refresh_playlist(playlist_id: int, db: Session = Depends(get_db)):
    from worker import refresh_m3u_task
    result = refresh_m3u_task.delay(playlist_id)
    return {"task_id": result.id, "status": "enqueued"}


# ─── HELPERS ──────────────────────────────────────────────────────────────────

def _save_channels(db: Session, playlist_id: int, channels_data: list):
    inserted = 0
    skipped = 0
    for ch in channels_data:
        existing = db.query(Channel).filter(
            Channel.playlist_id == playlist_id,
            Channel.dedup_key == ch["dedup_key"]
        ).first()
        if existing:
            skipped += 1
            continue
        cat = _get_or_create_category(db, ch["category"])
        channel = Channel(
            playlist_id=playlist_id,
            category_id=cat.id if cat else None,
            name=ch["name"],
            url=ch["url"],
            logo=ch.get("logo", ""),
            tvg_id=ch.get("tvg_id", ""),
            language=ch.get("language", ""),
            country=ch.get("country", ""),
            group_title=ch.get("group_title", ""),
            dedup_key=ch["dedup_key"],
        )
        db.add(channel)
        inserted += 1
    db.flush()
    return inserted, skipped


def _get_or_create_category(db: Session, normalized_name: str):
    cat = db.query(Category).filter(Category.normalized_name == normalized_name).first()
    if not cat:
        cat = Category(
            raw_name=normalized_name,
            normalized_name=normalized_name,
            category_type=normalized_name.lower(),
        )
        db.add(cat)
        db.flush()
    return cat


def _apply_blacklist(db: Session, bl: Blacklist):
    query = db.query(Channel)
    if bl.channel_name_pattern:
        query = query.filter(Channel.name.ilike(f"%{bl.channel_name_pattern}%"))
    if bl.url_pattern:
        query = query.filter(Channel.url.ilike(f"%{bl.url_pattern}%"))
    query.update({"is_blacklisted": True}, synchronize_session=False)
    db.commit()


def log_audit(db: Session, action: str, entity_type: str, entity_id: int, detail: str):
    log = AuditLog(action=action, entity_type=entity_type, entity_id=entity_id, detail=detail)
    db.add(log)
    db.commit()
