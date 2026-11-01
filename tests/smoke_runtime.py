"""Teste de operacao real isolada: FastAPI, PostgreSQL, Redis e Celery.

NUNCA executar contra o painel M81: requer ambiente de teste e API local.
"""
from __future__ import annotations

import os
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

import requests

API = "http://127.0.0.1:18765"
FIRST_PLAYLIST = (
    '#EXTM3U\n'
    '#EXTINF:-1 group-title="Esportes" tvg-language="pt",Canal Teste A\n'
    'https://example.com/test-a.m3u8\n'
    '#EXTINF:-1 group-title="Filmes",Canal Teste B\n'
    'https://example.com/test-b.m3u8\n'
)
ADDED_ENTRY = (
    '#EXTINF:-1 group-title="Noticias",Canal Teste C\n'
    'https://example.com/test-c.m3u8\n'
)


class TestPlaylistHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if urlparse(self.path).path != "/fixture.m3u":
            self.send_error(404)
            return
        payload = self.server.current_m3u.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "audio/x-mpegurl")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def log_message(self, _fmt, *_args):
        return


def checked(response, label):
    response.raise_for_status()
    assert response.ok, f"{label}: HTTP {response.status_code}"
    return response


def wait_for_api():
    deadline = time.monotonic() + 35
    while time.monotonic() < deadline:
        try:
            result = requests.get(f"{API}/openapi.json", timeout=2)
            if result.status_code == 200:
                return
        except requests.RequestException:
            pass
        time.sleep(0.5)
    raise AssertionError("API nao iniciou no ambiente isolado")


def main():
    if os.getenv("APP_ENV") != "test" or os.getenv("ALLOW_ISOLATED_SMOKE") != "1":
        raise SystemExit("Smoke bloqueado: use APP_ENV=test e ALLOW_ISOLATED_SMOKE=1")

    db_url = os.getenv("DATABASE_URL", "")
    redis_url = os.getenv("REDIS_URL", "")
    if not (
        db_url.startswith("postgresql://iptv:iptv@localhost:5432/iptvbot")
        and redis_url == "redis://localhost:6379/0"
    ):
        raise SystemExit("Smoke bloqueado: PostgreSQL/Redis devem ser locais e descartaveis")

    source = ThreadingHTTPServer(("127.0.0.1", 0), TestPlaylistHandler)
    source.current_m3u = FIRST_PLAYLIST
    thread = threading.Thread(target=source.serve_forever, daemon=True)
    thread.start()
    try:
        wait_for_api()
        fixture_url = f"http://127.0.0.1:{source.server_port}/fixture.m3u"

        ingest = checked(
            requests.post(
                f"{API}/ingest/m3u",
                params={"name": "CI - Teste isolado", "url": fixture_url},
                timeout=15,
            ),
            "ingestao",
        ).json()
        assert ingest["inserted"] == 2, ingest
        playlist_id = ingest["playlist_id"]

        listing = checked(requests.get(f"{API}/channels", timeout=5), "canais").json()
        assert len(listing) == 2, listing
        assert {item["name"] for item in listing} == {"Canal Teste A", "Canal Teste B"}

        stats = checked(requests.get(f"{API}/stats", timeout=5), "estatisticas").json()
        assert stats["total_channels"] == 2, stats

        exported = checked(requests.get(f"{API}/export/m3u", timeout=5), "exportacao").text
        assert exported.startswith("#EXTM3U") and "Canal Teste A" in exported

        source.current_m3u += ADDED_ENTRY
        task = checked(
            requests.post(f"{API}/playlists/{playlist_id}/refresh", timeout=5),
            "fila de atualizacao",
        ).json()
        assert task["task_id"], task

        deadline = time.monotonic() + 45
        while time.monotonic() < deadline:
            channels = checked(requests.get(f"{API}/channels", timeout=5), "refresh").json()
            playlists = checked(requests.get(f"{API}/playlists", timeout=5), "versao").json()
            version = next(p["version"] for p in playlists if p["id"] == playlist_id)
            if len(channels) == 3 and version >= 2:
                print("OK: API HTTP, PostgreSQL, ingestao M3U, exportacao, Redis/Celery e refresh")
                return
            time.sleep(1)
        raise AssertionError("Celery nao atualizou a playlist em tempo habil")
    finally:
        source.shutdown()
        source.server_close()


if __name__ == "__main__":
    main()
