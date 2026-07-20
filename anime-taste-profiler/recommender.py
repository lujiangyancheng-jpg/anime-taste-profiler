"""Simple rule-based recommendation scoring for AniList candidates."""

from __future__ import annotations

from typing import Any

import pandas as pd


def _preference_lookup(table: pd.DataFrame) -> dict[str, float]:
    if table is None or table.empty:
        return {}
    return {
        str(row["name"]).lower(): float(row["preference_score"])
        for _, row in table.iterrows()
    }


def _title(media: dict[str, Any]) -> str:
    title = media.get("title") or {}
    return title.get("english") or title.get("romaji") or "Untitled"


def score_recommendations(
    candidates: list[dict[str, Any]],
    completed_ids: set[int],
    preferences: dict[str, pd.DataFrame],
    limit: int = 5,
) -> list[dict[str, Any]]:
    positive_genres = _preference_lookup(preferences["top_positive_genres"])
    negative_genres = _preference_lookup(preferences["top_negative_genres"])
    positive_tags = _preference_lookup(preferences["top_positive_tags"])
    negative_tags = _preference_lookup(preferences["top_negative_tags"])

    scored: list[dict[str, Any]] = []
    for media in candidates:
        media_id = media.get("id")
        if media_id in completed_ids:
            continue

        score = 0.0
        reasons: list[str] = []
        caution_reasons: list[str] = []

        for genre in media.get("genres") or []:
            key = genre.lower()
            if key in positive_genres:
                score += max(positive_genres[key], 0.2)
                reasons.append(genre)
            if key in negative_genres:
                score += min(negative_genres[key], -0.2)
                caution_reasons.append(genre)

        for tag in media.get("tags") or []:
            name = tag.get("name")
            if not name:
                continue
            key = name.lower()
            weight = (tag.get("rank") or 50) / 100
            if key in positive_tags:
                score += max(positive_tags[key], 0.2) * weight
                reasons.append(name)
            if key in negative_tags:
                score += min(negative_tags[key], -0.2) * weight
                caution_reasons.append(name)

        if score <= 0 or not reasons:
            continue

        scored.append(
            {
                "title": _title(media),
                "score": round(score, 2),
                "year": media.get("seasonYear"),
                "format": media.get("format"),
                "average_score": media.get("averageScore"),
                "site_url": media.get("siteUrl"),
                "reasons": sorted(set(reasons))[:5],
                "cautions": sorted(set(caution_reasons))[:3],
            }
        )

    return sorted(scored, key=lambda item: item["score"], reverse=True)[:limit]
