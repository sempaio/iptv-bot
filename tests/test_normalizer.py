"""Regressoes alinhadas ao contrato do normalizador atual."""
import pytest

from normalizer import (
    make_dedup_key,
    normalize_category,
    normalize_language,
    normalize_name,
)


@pytest.mark.parametrize(
    ("group", "name", "expected"),
    [
        ("Esporte", "", "Esportes"),
        ("SPORT", "", "Esportes"),
        ("FUTEBOL", "", "Esportes"),
        ("Filme", "", "Filmes"),
        ("MOVIES", "", "Filmes"),
        ("SERIES", "", "Series"),
        ("NEWS", "", "Noticias"),
        ("INFANTIL", "", "Kids"),
        ("ADULTO", "", "Adulto"),
        ("Desconhecida", "", "Live"),
    ],
)
def test_normalize_category(group, name, expected):
    assert normalize_category(group, name) == expected


@pytest.mark.parametrize(
    ("language", "group", "name", "expected"),
    [
        ("pt", "", "", "pt"),
        ("PT", "", "", "pt"),
        ("portugues", "", "", "pt"),
        ("en", "", "", "en"),
        ("English", "", "", "en"),
        ("es", "", "", "es"),
        ("", "Sem grupo", "", "other"),
        (None, "Sem grupo", "", "other"),
    ],
)
def test_normalize_language(language, group, name, expected):
    assert normalize_language(language, group, name) == expected


def test_normalize_name_preserves_resolution_and_trims_spaces():
    assert normalize_name("  ESPN   HD  ") == "ESPN HD"


def test_dedup_key_normalizes_name_case():
    assert make_dedup_key("https://example.com/live", "Canal A") == make_dedup_key(
        "https://example.com/live", "canal a"
    )
    assert make_dedup_key("https://example.com/live", "Canal A") != make_dedup_key(
        "https://example.com/other", "Canal A"
    )
