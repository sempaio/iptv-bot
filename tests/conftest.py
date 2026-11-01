"""Fixtures isoladas: os testes nao alteram o PostgreSQL do painel M81."""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from database import Base, get_db
from main import app


@pytest.fixture()
def db_session():
    """Banco SQLite descartavel apenas para cada teste de API."""
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    session_factory = sessionmaker(bind=engine, expire_on_commit=False)
    with session_factory() as session:
        yield session
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture()
def client(db_session):
    """Evita o startup de producao e substitui a dependencia do banco."""
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    test_client = TestClient(app)
    try:
        yield test_client
    finally:
        test_client.close()
        app.dependency_overrides.clear()


@pytest.fixture()
def sample_m3u_content():
    return """#EXTM3U
#EXTINF:-1 tvg-id="ESPN" tvg-name="ESPN HD" tvg-language="Portugues" tvg-country="BR" group-title="Esportes",ESPN HD
http://example.com/stream/espn
#EXTINF:-1 tvg-id="CNN" tvg-name="CNN Internacional" tvg-language="English" tvg-country="US" group-title="Noticias",CNN Internacional
http://example.com/stream/cnn
#EXTINF:-1 tvg-id="FILM1" tvg-name="FilmBox" tvg-language="" tvg-country="" group-title="Filmes",FilmBox
http://example.com/stream/filmbox
"""
