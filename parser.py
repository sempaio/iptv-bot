import re
import hashlib
from typing import List, Dict, Any
from normalizer import normalize_category, normalize_language, make_dedup_key, normalize_name


def parse_m3u(content: str) -> List[Dict[str, Any]]:
    """
    Parser proprio para playlists M3U/M3U8.
    Extrai todos os atributos de cada canal.
    """
    channels = []
    lines = content.splitlines()

    if not lines or not lines[0].startswith("#EXTM3U"):
        raise ValueError("Arquivo invalido: nao e um M3U valido")

    i = 1
    while i < len(lines):
        line = lines[i].strip()

        if line.startswith("#EXTINF:"):
            attrs = parse_extinf(line)
            url = ""
            j = i + 1
            while j < len(lines):
                next_line = lines[j].strip()
                if next_line and not next_line.startswith("#"):
                    url = next_line
                    i = j
                    break
                j += 1

            if url:
                name = normalize_name(attrs.get("name", ""))
                group_title = attrs.get("group-title", "")
                language = attrs.get("tvg-language", "")

                channel = {
                    "name": name,
                    "url": url,
                    "logo": attrs.get("tvg-logo", ""),
                    "tvg_id": attrs.get("tvg-id", ""),
                    "language": normalize_language(language, group_title, name),
                    "country": attrs.get("tvg-country", ""),
                    "group_title": group_title,
                    "category": normalize_category(group_title, name),
                    "dedup_key": make_dedup_key(url, name),
                }
                channels.append(channel)

        i += 1

    return channels


def parse_extinf(line: str) -> Dict[str, str]:
    """
    Extrai atributos da linha #EXTINF.
    Exemplo: #EXTINF:-1 tvg-id="" tvg-name="" group-title="",Canal Name
    """
    attrs = {}

    # Extrai o nome do canal (depois da ultima virgula)
    comma_idx = line.rfind(",")
    if comma_idx != -1:
        attrs["name"] = line[comma_idx + 1:].strip()

    # Extrai atributos chave="valor"
    attr_pattern = re.compile(r'([\w-]+)="([^"]*)"')
    for match in attr_pattern.finditer(line):
        key = match.group(1).lower()
        value = match.group(2).strip()
        attrs[key] = value

    return attrs


def compute_content_hash(content: str) -> str:
    return hashlib.sha256(content.encode()).hexdigest()
