# iptv-bot

Bot de ingestao, parsing e normalizacao de playlists M3U/Xtream com FastAPI + PostgreSQL.

## Funcionalidades (v10)

- Upload e ingestao de playlists M3U/M3U8
- Import via credenciais Xtream Codes
- Parser proprio com extracao de: title, url, group-title, tvg-language, tvg-country, tvg-id, tvg-logo
- Normalizacao automatica de categorias (Esportes, Filmes, Series, Noticias, Kids, Adulto, Live)
- Normalizacao de idiomas por alias (SPORT, ESPORTE, FUTEBOL -> Esportes)
- Deduplicacao por URL + nome
- Blacklist/whitelist por canal ou categoria
- Versionamento de playlist
- Export M3U organizado por categoria
- Export filtrado por idioma, categoria ou perfil de cliente
- Estatisticas de canais por categoria e idioma
- Jobs assincronos para playlists grandes (Celery + Redis)
- API RESTful com FastAPI
- Banco de dados PostgreSQL com SQLAlchemy
- Docker e docker-compose prontos para producao

## Stack

- Python 3.11+
- FastAPI
- PostgreSQL + SQLAlchemy + Alembic
- Celery + Redis
- Docker / docker-compose

## Estrutura do projeto

```
iptv-bot/
  main.py          # FastAPI app e endpoints
  parser.py        # Parser M3U proprio
  xtream.py        # Import Xtream Codes
  normalizer.py    # Regras de categoria e idioma
  exporter.py      # Export M3U/JSON
  models.py        # Modelos SQLAlchemy
  schemas.py       # Schemas Pydantic
  database.py      # Conexao PostgreSQL
  worker.py        # Worker Celery
  requirements.txt
  Dockerfile
  docker-compose.yml
```

## Como usar

```bash
docker-compose up --build
```

Acesse: http://localhost:8000/docs

## Endpoints principais

| Metodo | Rota | Descricao |
|--------|------|-----------|
| POST | /ingest/m3u | Upload e ingestao de M3U |
| POST | /ingest/xtream | Import via Xtream Codes |
| GET | /channels | Lista canais normalizados |
| GET | /channels?category=Esportes | Filtra por categoria |
| GET | /channels?language=pt | Filtra por idioma |
| GET | /export/m3u | Exporta M3U organizado |
| GET | /export/m3u?category=Filmes | Exporta M3U filtrado |
| GET | /stats | Estatisticas gerais |
| GET | /playlists | Lista playlists ingeridas |
| POST | /blacklist | Adiciona canal a blacklist |
| DELETE | /blacklist/{id} | Remove da blacklist |

## Versoes

- v1: Parser M3U basico + FastAPI
- v2: Persistencia PostgreSQL + deduplicacao
- v3: Normalizacao de categorias
- v4: Normalizacao de idiomas + aliases
- v5: Import Xtream Codes
- v6: Export M3U organizado
- v7: Filtros por categoria/idioma/perfil
- v8: Blacklist/whitelist + versionamento
- v9: Jobs assincronos Celery + Redis
- v10: Docker producao + logs + auditoria
