import re
import hashlib

CATEGORY_RULES = [
    ("Esportes", [
        "sport", "esport", "futebol", "football", "soccer", "basquete", "basketball",
        "tenis", "volei", "f1", "formula", "nba", "nfl", "ufc", "mma", "luta",
        "olimpiadas", "olympic", "atletismo", "natacao", "ciclismo",
    ]),
    ("Noticias", [
        "noticia", "news", "jornal", "jornalismo", "informativo",
        "cnn", "bbc", "globonews", "band news", "record news",
    ]),
    ("Filmes", [
        "filme", "movie", "cinema", "vod", "film",
    ]),
    ("Series", [
        "serie", "series", "show", "tv show", "temporada", "season",
    ]),
    ("Kids", [
        "kids", "infantil", "crianca", "cartoon", "animacao", "disney",
        "nickelodeon", "discovery kids",
    ]),
    ("Adulto", [
        "adult", "adulto", "xxx", "erotic", "18+",
    ]),
    ("Musica", [
        "musica", "music", "mtv", "radio", "fm",
    ]),
    ("Religioso", [
        "religioso", "religious", "gospel", "evangelico", "catolico", "church",
    ]),
]

LANGUAGE_RULES = [
    ("pt", ["brasil", "brazil", "portugues", "portuguese", "br", "pt-br"]),
    ("en", ["english", "united states", "usa", "uk", "us", "en"]),
    ("es", ["espanol", "spanish", "spain", "mexico", "colombia", "argentina", "es"]),
    ("fr", ["french", "france", "francais", "fr"]),
    ("de", ["german", "deutsch", "germany", "de"]),
    ("it", ["italian", "italiano", "italy", "it"]),
    ("ar", ["arabic", "arabe", "arab", "ar"]),
    ("tr", ["turkish", "turco", "turkey", "tr"]),
]


def normalize_category(group_title: str, name: str) -> str:
    text = (group_title + " " + name).lower()
    for category, keywords in CATEGORY_RULES:
        for kw in keywords:
            if kw in text:
                return category
    return "Live"


def normalize_language(language: str, group_title: str, name: str) -> str:
    if language and len(language.strip()) > 0:
        lang_lower = language.lower().strip()
        for lang_code, aliases in LANGUAGE_RULES:
            if lang_lower in aliases or lang_lower == lang_code:
                return lang_code
    text = (group_title + " " + name).lower()
    for lang_code, aliases in LANGUAGE_RULES:
        for alias in aliases:
            if alias in text:
                return lang_code
    return "other"


def make_dedup_key(url: str, name: str) -> str:
    raw = f"{url.strip()}|{name.strip().lower()}"
    return hashlib.md5(raw.encode()).hexdigest()


def normalize_name(name: str) -> str:
    name = re.sub(r"\s+", " ", name).strip()
    return name
