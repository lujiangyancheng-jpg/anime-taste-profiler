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


def _average_score_10(media: dict[str, Any]) -> float | None:
    average_score = media.get("averageScore")
    if average_score is None:
        return None
    return float(average_score) / 10


def _community_bonus(media: dict[str, Any]) -> float:
    average_score = _average_score_10(media)
    if average_score is None:
        return 0.0
    return max(-1.0, min(1.2, (average_score - 7.0) * 0.35))


def _fit_level(match_score: int) -> str:
    if match_score >= 85:
        return "strong"
    if match_score >= 70:
        return "good"
    return "niche"


def _append_unique(items: list[str], value: str) -> None:
    if value not in items:
        items.append(value)


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
        reason_details: list[dict[str, Any]] = []
        caution_details: list[dict[str, Any]] = []

        for genre in media.get("genres") or []:
            key = genre.lower()
            if key in positive_genres:
                points = max(positive_genres[key], 0.2)
                score += points
                _append_unique(reasons, genre)
                reason_details.append({"signal": genre, "type": "genre", "points": round(points, 2)})
            if key in negative_genres:
                points = min(negative_genres[key], -0.2)
                score += points
                _append_unique(caution_reasons, genre)
                caution_details.append({"signal": genre, "type": "genre", "points": round(points, 2)})

        for tag in media.get("tags") or []:
            name = tag.get("name")
            if not name:
                continue
            key = name.lower()
            weight = (tag.get("rank") or 50) / 100
            if key in positive_tags:
                points = max(positive_tags[key], 0.2) * weight
                score += points
                _append_unique(reasons, name)
                reason_details.append({"signal": name, "type": "tag", "points": round(points, 2)})
            if key in negative_tags:
                points = min(negative_tags[key], -0.2) * weight
                score += points
                _append_unique(caution_reasons, name)
                caution_details.append({"signal": name, "type": "tag", "points": round(points, 2)})

        if score <= 0 or not reasons:
            continue

        bonus = _community_bonus(media)
        match_score = int(max(0, min(100, round(55 + (score * 7) + (bonus * 8)))))

        scored.append(
            {
                "title": _title(media),
                "score": round(score, 2),
                "match_score": match_score,
                "fit_level": _fit_level(match_score),
                "year": media.get("seasonYear"),
                "format": media.get("format"),
                "average_score": media.get("averageScore"),
                "site_url": media.get("siteUrl"),
                "reasons": reasons[:5],
                "cautions": caution_reasons[:3],
                "reason_details": sorted(reason_details, key=lambda item: item["points"], reverse=True)[:5],
                "caution_details": sorted(caution_details, key=lambda item: item["points"])[:3],
            }
        )

    return sorted(scored, key=lambda item: (item["match_score"], item["score"]), reverse=True)[:limit]
