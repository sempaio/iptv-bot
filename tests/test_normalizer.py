import pytest
from normalizer import (
    normalize_category,
    normalize_language,
    normalize_channel_name,
    is_duplicate,
)


# ---- normalize_category ----

def test_normalize_category_esportes():
    assert normalize_category("Esporte") == "Esportes"
    assert normalize_category("SPORT") == "Esportes"
    assert normalize_category("ESPORTE") == "Esportes"
    assert normalize_category("FUTEBOL") == "Esportes"


def test_normalize_category_filmes():
    assert normalize_category("Filme") == "Filmes"
    assert normalize_category("MOVIES") == "Filmes"
    assert normalize_category("CINEMA") == "Filmes"


def test_normalize_category_series():
    assert normalize_category("Serie") == "Series"
    assert normalize_category("SERIES") == "Series"
    assert normalize_category("TV SHOW") == "Series"


def test_normalize_category_noticias():
    assert normalize_category("NEWS") == "Noticias"
    assert normalize_category("Noticia") == "Noticias"


def test_normalize_category_kids():
    assert normalize_category("INFANTIL") == "Kids"
    assert normalize_category("KIDS") == "Kids"
    assert normalize_category("CRIANCA") == "Kids"


def test_normalize_category_adulto():
    assert normalize_category("ADULTO") == "Adulto"
    assert normalize_category("ADULT") == "Adulto"
    assert normalize_category("XXX") == "Adulto"


def test_normalize_category_unknown():
    # Categorias não mapeadas retornam o valor original com título
    result = normalize_category("Some Unknown Category")
    assert result == "Some Unknown Category"


# ---- normalize_language ----

def test_normalize_language_portugues():
    assert normalize_language("pt") == "Portugues"
    assert normalize_language("PT") == "Portugues"
    assert normalize_language("Português") == "Portugues"
    assert normalize_language("portugues") == "Portugues"


def test_normalize_language_english():
    assert normalize_language("en") == "English"
    assert normalize_language("EN") == "English"
    assert normalize_language("English") == "English"


def test_normalize_language_espanhol():
    assert normalize_language("es") == "Espanhol"
    assert normalize_language("Spanish") == "Espanhol"


def test_normalize_language_empty():
    assert normalize_language("") == "Desconhecido"
    assert normalize_language(None) == "Desconhecido"


# ---- normalize_channel_name ----

def test_normalize_channel_name_strips_hd():
    assert "HD" not in normalize_channel_name("ESPN HD")


def test_normalize_channel_name_strips_fhd():
    assert "FHD" not in normalize_channel_name("CNN FHD")


def test_normalize_channel_name_strips_4k():
    assert "4K" not in normalize_channel_name("Canal+ 4K")


def test_normalize_channel_name_strips_sd():
    assert "SD" not in normalize_channel_name("Record SD")


def test_normalize_channel_name_preserves_content():
    name = normalize_channel_name("ESPN HD")
    assert "ESPN" in name


# ---- is_duplicate ----

def test_is_duplicate_same_url():
    seen = {"http://example.com/stream"}
    assert is_duplicate("http://example.com/stream", "Canal A", seen) is True


def test_is_duplicate_same_name():
    seen_names = {"Canal A"}
    assert is_duplicate("http://other.com/stream", "Canal A", set(), seen_names) is True


def test_is_not_duplicate():
    seen_urls = {"http://example.com/stream1"}
    seen_names = {"Canal B"}
    assert is_duplicate("http://example.com/stream2", "Canal A", seen_urls, seen_names) is False
