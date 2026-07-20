"""Small AniList GraphQL client used by the Streamlit app."""

from __future__ import annotations

from typing import Any

import requests


API_URL = "https://graphql.anilist.co"
TIMEOUT_SECONDS = 20


class AniListError(Exception):
    """Raised when AniList cannot return usable data for the request."""


USER_LIST_QUERY = """
query ($username: String) {
  User(name: $username) {
    id
    name
    mediaListOptions {
      scoreFormat
    }
  }
  MediaListCollection(userName: $username, type: ANIME, status: COMPLETED) {
    lists {
      entries {
        id
        status
        score
        media {
          id
          type
          title {
            romaji
            english
          }
          format
          episodes
          genres
          tags {
            name
            rank
          }
          averageScore
          popularity
          seasonYear
          siteUrl
        }
      }
    }
  }
}
"""


TRENDING_QUERY = """
query ($page: Int, $perPage: Int) {
  Page(page: $page, perPage: $perPage) {
    media(
      type: ANIME,
      sort: TRENDING_DESC,
      status_not: NOT_YET_RELEASED,
      isAdult: false
    ) {
      id
      title {
        romaji
        english
      }
      format
      episodes
      genres
      tags {
        name
        rank
      }
      averageScore
      popularity
      seasonYear
      siteUrl
    }
  }
}
"""


def _post_graphql(query: str, variables: dict[str, Any]) -> dict[str, Any]:
    try:
        response = requests.post(
            API_URL,
            json={"query": query, "variables": variables},
            timeout=TIMEOUT_SECONDS,
        )
    except requests.RequestException as exc:
        raise AniListError("Could not reach AniList. Check your connection and try again.") from exc

    try:
        payload = response.json()
    except ValueError as exc:
        raise AniListError("AniList returned an unreadable response.") from exc

    if response.status_code >= 400 or payload.get("errors"):
        message = "AniList could not return data for that request."
        errors = payload.get("errors") or []
        if errors and isinstance(errors[0], dict):
            message = errors[0].get("message", message)
        raise AniListError(message)

    return payload.get("data") or {}


def fetch_completed_anime(username: str) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Fetch a user's completed, scored anime entries from AniList."""

    username = username.strip()
    if not username:
        raise AniListError("Enter an AniList username.")

    data = _post_graphql(USER_LIST_QUERY, {"username": username})
    user = data.get("User")
    if not user:
        raise AniListError("AniList username not found.")

    collection = data.get("MediaListCollection")
    if not collection:
        raise AniListError("This anime list is private, empty, or unavailable.")

    entries: list[dict[str, Any]] = []
    for media_list in collection.get("lists") or []:
        for entry in media_list.get("entries") or []:
            media = entry.get("media") or {}
            if (
                entry.get("status") == "COMPLETED"
                and (entry.get("score") or 0) > 0
                and media.get("type") == "ANIME"
            ):
                entries.append(entry)

    score_format = (user.get("mediaListOptions") or {}).get("scoreFormat") or "POINT_10"
    return {"id": user.get("id"), "name": user.get("name"), "score_format": score_format}, entries


def fetch_trending_anime(page: int = 1, per_page: int = 50) -> list[dict[str, Any]]:
    """Fetch currently trending anime candidates for simple recommendations."""

    data = _post_graphql(TRENDING_QUERY, {"page": page, "perPage": per_page})
    page_data = data.get("Page") or {}
    return page_data.get("media") or []
