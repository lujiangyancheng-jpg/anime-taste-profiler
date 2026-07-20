"""Small Bangumi v0 API client used by the Streamlit app."""

from __future__ import annotations

from datetime import datetime
from typing import Any

import requests


API_URL = "https://api.bgm.tv"
TIMEOUT_SECONDS = 20
USER_AGENT = "AnimeTasteProfiler/0.2 (local Streamlit app)"
BANGUMI_GENRE_TAGS = {
    "动作",
    "冒险",
    "搞笑",
    "喜剧",
    "日常",
    "治愈",
    "恋爱",
    "爱情",
    "少女",
    "校园",
    "青春",
    "剧情",
    "科幻",
    "奇幻",
    "魔法",
    "异世界",
    "悬疑",
    "推理",
    "心理",
    "惊悚",
    "恐怖",
    "运动",
    "音乐",
    "机战",
    "机甲",
    "军事",
    "历史",
    "百合",
    "耽美",
    "后宫",
    "热血",
    "战斗",
    "原创",
}


class BangumiError(Exception):
    """Raised when Bangumi cannot return usable data for the request."""


def _headers() -> dict[str, str]:
    return {"User-Agent": USER_AGENT, "Accept": "application/json"}


def _get_json(path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    try:
        response = requests.get(
            f"{API_URL}{path}",
            params=params,
            headers=_headers(),
            timeout=TIMEOUT_SECONDS,
        )
    except requests.RequestException as exc:
        raise BangumiError("Could not reach Bangumi. Check your connection and try again.") from exc

    try:
        payload = response.json()
    except ValueError as exc:
        raise BangumiError("Bangumi returned an unreadable response.") from exc

    if response.status_code == 404:
        raise BangumiError("Bangumi username not found, or this collection is private.")
    if response.status_code >= 400:
        message = payload.get("description") or payload.get("message") or "Bangumi could not return data."
        raise BangumiError(message)

    return payload


def fetch_completed_anime(username: str, page_size: int = 50, max_items: int = 1000) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Fetch a user's watched, scored anime collections from Bangumi."""

    username = username.strip()
    if not username:
        raise BangumiError("Enter a Bangumi username or numeric user ID.")

    entries: list[dict[str, Any]] = []
    offset = 0
    total = None

    while True:
        payload = _get_json(
            f"/v0/users/{username}/collections",
            {
                "subject_type": 2,
                "type": 2,
                "limit": page_size,
                "offset": offset,
            },
        )
        total = payload.get("total", total)
        batch = payload.get("data") or []
        entries.extend(
            entry
            for entry in batch
            if entry.get("type") == 2
            and entry.get("subject_type") == 2
            and (entry.get("rate") or 0) > 0
            and not entry.get("private")
        )

        offset += len(batch)
        if not batch or (total is not None and offset >= total) or len(entries) >= max_items:
            break

    return {
        "id": username,
        "name": username,
        "score_format": "POINT_10",
        "source": "Bangumi",
    }, entries[:max_items]


def _season_year(date_text: str | None) -> int | None:
    if not date_text:
        return None
    try:
        return datetime.strptime(date_text[:10], "%Y-%m-%d").year
    except ValueError:
        return None


def _weighted_tags(subject: dict[str, Any]) -> list[dict[str, Any]]:
    raw_tags = subject.get("tags") or []
    max_count = max((tag.get("count") or 0 for tag in raw_tags), default=0)
    tags: list[dict[str, Any]] = []
    for tag in raw_tags[:20]:
        name = tag.get("name")
        if not name:
            continue
        if max_count:
            rank = max(20, min(100, int((tag.get("count", 0) / max_count) * 100)))
        else:
            rank = 50
        tags.append({"name": name, "rank": rank})
    return tags


def _normalise_subject(subject: dict[str, Any]) -> dict[str, Any]:
    title = subject.get("name_cn") or subject.get("name") or "Untitled"
    date_text = subject.get("date")
    score = subject.get("score")
    site_url = f"https://bgm.tv/subject/{subject.get('id')}" if subject.get("id") else None

    tags = _weighted_tags(subject)
    genres = [tag["name"] for tag in tags if tag["name"] in BANGUMI_GENRE_TAGS]

    return {
        "id": subject.get("id"),
        "type": "ANIME",
        "title": {"romaji": subject.get("name"), "english": title},
        "format": subject.get("platform"),
        "episodes": subject.get("eps"),
        "genres": genres,
        "tags": tags,
        "averageScore": (score * 10) if score is not None else None,
        "popularity": subject.get("collection_total"),
        "seasonYear": _season_year(date_text),
        "siteUrl": site_url,
    }


def fetch_ranked_anime(page: int = 1, per_page: int = 50) -> list[dict[str, Any]]:
    """Fetch ranked Bangumi anime candidates for simple recommendations."""

    offset = max(page - 1, 0) * per_page
    payload = _get_json(
        "/v0/subjects",
        {"type": 2, "sort": "rank", "limit": per_page, "offset": offset},
    )
    return [_normalise_subject(subject) for subject in payload.get("data") or []]
