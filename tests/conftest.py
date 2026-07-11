import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database import Base, get_db
from main import app
from config import settings


# ---- Test Database Setup ----

TEST_DATABASE_URL = settings.DATABASE_URL.replace(
    "/iptvbot", "/iptvbot_test"
)

engine = create_engine(TEST_DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    """Create test database tables before tests, drop after."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def db_session():
    """Provide a transactional database session for each test."""
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    yield session
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture()
def client(db_session):
    """FastAPI test client with DB dependency override."""
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


# ---- M3U Sample Data ----

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


@pytest.fixture()
def sample_channel_data():
    return [
        {
            "name": "ESPN HD",
            "url": "http://example.com/stream/espn",
            "group": "Esportes",
            "language": "Portugues",
            "country": "BR",
            "tvg_id": "ESPN",
            "tvg_logo": "",
        },
        {
            "name": "CNN Internacional",
            "url": "http://example.com/stream/cnn",
            "group": "Noticias",
            "language": "English",
            "country": "US",
            "tvg_id": "CNN",
            "tvg_logo": "",
        },
    ]
