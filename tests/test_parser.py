"""Contratos reais do parser M3U (sem URLs de streaming reais)."""
import pytest
from parser import parse_m3u


M3U_SAMPLE = """#EXTM3U
#EXTINF:-1 tvg-id="ESPN" tvg-name="ESPN HD" tvg-language="Portugues" \
tvg-country="BR" group-title="Esportes",ESPN HD
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
    espn = parse_m3u(M3U_SAMPLE)[0]
    assert espn["name"] == "ESPN HD"
    assert espn["url"] == "http://example.com/stream/espn"
    assert espn["group_title"] == "Esportes"
    assert espn["category"] == "Esportes"
    assert espn["language"] == "pt"
    assert espn["country"] == "BR"


def test_parse_m3u_missing_language():
    filmbox = parse_m3u(M3U_SAMPLE)[2]
    assert filmbox["language"] == "other"
    assert filmbox["country"] == ""


def test_parse_m3u_urls_are_retained():
    for channel in parse_m3u(M3U_SAMPLE):
        assert channel["url"].startswith("http")


def test_parse_m3u_empty_content():
    assert parse_m3u("#EXTM3U") == []


def test_parse_m3u_invalid_content():
    with pytest.raises(ValueError, match="M3U"):
        parse_m3u("not a valid m3u")


def test_parse_m3u_group_title_extraction():
    groups = {channel["group_title"] for channel in parse_m3u(M3U_SAMPLE)}
    assert {"Esportes", "Noticias", "Filmes"} == groups


def test_parse_m3u_deduplicates_keys_not_rows():
    repeated = M3U_SAMPLE + M3U_SAMPLE.splitlines()[1] + "\n" + M3U_SAMPLE.splitlines()[2] + "\n"
    channels = parse_m3u(repeated)
    assert len(channels) == 4
    assert channels[0]["dedup_key"] == channels[-1]["dedup_key"]
