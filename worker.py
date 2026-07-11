import os
from celery import Celery
from database import SessionLocal
from models import Playlist, Channel, Category
from parser import parse_m3u, compute_content_hash
from normalizer import normalize_category, normalize_language, make_dedup_key
import requests

REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")

celery_app = Celery(
    "iptv_worker",
    broker=REDIS_URL,
    backend=REDIS_URL,
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="America/Sao_Paulo",
    enable_utc=True,
)


@celery_app.task(bind=True, max_retries=3)
def ingest_m3u_task(self, playlist_id: int, content: str):
    """
    Task assincrona para ingerir uma playlist M3U.
    Usada para playlists grandes sem bloquear a API.
    """
    db = SessionLocal()
    try:
        playlist = db.query(Playlist).filter(Playlist.id == playlist_id).first()
        if not playlist:
            return {"error": "Playlist nao encontrada"}

        channels_data = parse_m3u(content)
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

            cat = get_or_create_category(db, ch["category"])

            channel = Channel(
                playlist_id=playlist_id,
                category_id=cat.id if cat else None,
                name=ch["name"],
                url=ch["url"],
                logo=ch["logo"],
                tvg_id=ch["tvg_id"],
                language=ch["language"],
                country=ch["country"],
                group_title=ch["group_title"],
                dedup_key=ch["dedup_key"],
            )
            db.add(channel)
            inserted += 1

        playlist.status = "active"
        db.commit()

        return {"inserted": inserted, "skipped": skipped}

    except Exception as exc:
        db.rollback()
        raise self.retry(exc=exc, countdown=10)
    finally:
        db.close()


@celery_app.task()
def refresh_m3u_task(playlist_id: int):
    """
    Re-baixa e reingere uma playlist M3U a partir da URL de origem.
    """
    db = SessionLocal()
    try:
        playlist = db.query(Playlist).filter(Playlist.id == playlist_id).first()
        if not playlist or not playlist.source_url:
            return {"error": "Playlist sem URL de origem"}

        r = requests.get(playlist.source_url, timeout=60)
        r.raise_for_status()
        content = r.text

        new_hash = compute_content_hash(content)
        if new_hash == playlist.content_hash:
            return {"status": "sem_alteracoes"}

        playlist.content_hash = new_hash
        playlist.version += 1
        db.commit()

        ingest_m3u_task.delay(playlist_id, content)
        return {"status": "refresh_iniciado", "version": playlist.version}

    finally:
        db.close()


def get_or_create_category(db, normalized_name: str):
    cat = db.query(Category).filter(
        Category.normalized_name == normalized_name
    ).first()
    if not cat:
        cat = Category(
            raw_name=normalized_name,
            normalized_name=normalized_name,
            category_type=normalized_name.lower(),
        )
        db.add(cat)
        db.flush()
    return cat
