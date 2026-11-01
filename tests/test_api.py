"""Testes de API em banco descartavel; nao acessam o M81 nem streams reais."""


def test_m3u_ingest_export_and_stats(client, sample_m3u_content):
    response = client.post(
        "/ingest/m3u",
        params={"name": "Lista de teste"},
        files={"file": ("fixture.m3u", sample_m3u_content, "audio/x-mpegurl")},
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["inserted"] == 3
    assert body["total_parsed"] == 3

    playlists = client.get("/playlists")
    assert playlists.status_code == 200, playlists.text
    assert len(playlists.json()) == 1

    channels = client.get("/channels")
    assert channels.status_code == 200, channels.text
    assert len(channels.json()) == 3
    assert channels.json()[0]["category"] in {"Esportes", "Noticias", "Filmes"}

    exported = client.get("/export/m3u")
    assert exported.status_code == 200
    assert exported.text.startswith("#EXTM3U")
    assert "ESPN HD" in exported.text

    stats = client.get("/stats")
    assert stats.status_code == 200, stats.text
    assert stats.json()["total_channels"] == 3
    assert stats.json()["total_playlists"] == 1


def test_m3u_ingest_rejects_absent_source(client):
    result = client.post("/ingest/m3u", params={"name": "Sem arquivo"})
    assert result.status_code == 400


def test_empty_db(client):
    response = client.get("/playlists")
    assert response.status_code == 200
    assert response.json() == []
