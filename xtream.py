import requests
from typing import List, Dict, Any
from normalizer import normalize_category, normalize_language, make_dedup_key, normalize_name


def fetch_xtream_categories(host: str, username: str, password: str) -> Dict:
    """
    Busca categorias Live, VOD e Series via API Xtream Codes.
    """
    base = host.rstrip("/")
    categories = {"live": [], "vod": [], "series": []}

    try:
        for cat_type in ["live", "vod", "series"]:
            url = f"{base}/player_api.php?username={username}&password={password}&action=get_{cat_type}_categories"
            r = requests.get(url, timeout=15)
            r.raise_for_status()
            categories[cat_type] = r.json()
    except Exception as e:
        raise RuntimeError(f"Erro ao buscar categorias Xtream: {e}")

    return categories


def fetch_xtream_streams(
    host: str, username: str, password: str, stream_type: str = "live"
) -> List[Dict[str, Any]]:
    """
    Busca canais/streams de um tipo (live, vod, series).
    """
    base = host.rstrip("/")
    action_map = {
        "live": "get_live_streams",
        "vod": "get_vod_streams",
        "series": "get_series",
    }
    action = action_map.get(stream_type, "get_live_streams")
    url = f"{base}/player_api.php?username={username}&password={password}&action={action}"

    try:
        r = requests.get(url, timeout=30)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        raise RuntimeError(f"Erro ao buscar streams Xtream: {e}")


def xtream_to_channels(
    streams: List[Dict],
    host: str,
    username: str,
    password: str,
    stream_type: str = "live"
) -> List[Dict[str, Any]]:
    """
    Converte streams Xtream para formato padrao de canal.
    """
    channels = []
    ext_map = {"live": "", "vod": ".mp4", "series": ""}
    ext = ext_map.get(stream_type, "")

    for s in streams:
        stream_id = s.get("stream_id") or s.get("series_id", "")
        name = normalize_name(s.get("name", ""))
        group_title = s.get("category_name", "") or s.get("category_id", "")
        logo = s.get("stream_icon", "") or s.get("cover", "")
        language = s.get("stream_language", "") or ""
        country = ""

        url = f"{host.rstrip('/')}/{stream_type}/{username}/{password}/{stream_id}{ext}"

        channel = {
            "name": name,
            "url": url,
            "logo": logo,
            "tvg_id": str(stream_id),
            "language": normalize_language(language, str(group_title), name),
            "country": country,
            "group_title": str(group_title),
            "category": normalize_category(str(group_title), name),
            "dedup_key": make_dedup_key(url, name),
        }
        channels.append(channel)

    return channels


def fetch_all_xtream_channels(
    host: str, username: str, password: str
) -> List[Dict[str, Any]]:
    """
    Busca todos os canais (live + vod + series) de um servidor Xtream.
    """
    all_channels = []
    for stream_type in ["live", "vod", "series"]:
        try:
            streams = fetch_xtream_streams(host, username, password, stream_type)
            channels = xtream_to_channels(streams, host, username, password, stream_type)
            all_channels.extend(channels)
        except Exception:
            continue
    return all_channels
