import pytest
from parser import parse_m3u


M3U_SAMPLE = """#EXTM3U
#EXTINF:-1 tvg-id="ESPN" tvg-name="ESPN HD" tvg-language="Portugues" tvg-country="BR" group-title="Esportes",ESPN HD
http://example.com/stream/espn
#EXTINF:-1 tvg-id="CNN" tvg-name="CNN Internacional" tvg-language="English" tvg-country="US" group-title="Noticias",CNN Internacional
http://example.com/stream/cnn
#EXTINF:-1 tvg-id="FILM1" tvg-name="FilmBox" tvg-language="" tvg-country="" group-title="Filmes",FilmBox
http://example.com/stream/filmbox
"""


def test_parse_m3u_returns_list():
    channels = parse_m3u(M3U_SAMPLE)
    assert isinstance(channels, list)
    assert len(channels) == 3


def test_parse_m3u_channel_fields():
    channels = parse_m3u(M3U_SAMPLE)
    espn = channels[0]
    assert espn["name"] == "ESPN HD"
    assert espn["url"] == "http://example.com/stream/espn"
    assert espn["group"] == "Esportes"
    assert espn["language"] == "Portugues"
    assert espn["country"] == "BR"


def test_parse_m3u_missing_language():
    channels = parse_m3u(M3U_SAMPLE)
    filmbox = channels[2]
    assert filmbox["language"] == ""
    assert filmbox["country"] == ""


def test_parse_m3u_url_correct():
    channels = parse_m3u(M3U_SAMPLE)
    for ch in channels:
        assert ch["url"].startswith("http")


def test_parse_m3u_empty_content():
    channels = parse_m3u("#EXTM3U")
    assert channels == []


def test_parse_m3u_invalid_content():
    channels = parse_m3u("not a valid m3u")
    assert channels == []


def test_parse_m3u_group_title_extraction():
    channels = parse_m3u(M3U_SAMPLE)
    groups = {ch["group"] for ch in channels}
    assert "Esportes" in groups
    assert "Noticias" in groups
    assert "Filmes" in groups
