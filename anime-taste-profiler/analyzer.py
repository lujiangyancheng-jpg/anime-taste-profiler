"""Data cleaning and rule-based analysis helpers."""

from __future__ import annotations

from collections import defaultdict
from typing import Any

import pandas as pd


SCORE_FORMAT_MULTIPLIERS = {
    "POINT_100": 0.1,
    "POINT_10_DECIMAL": 1.0,
    "POINT_10": 1.0,
    "POINT_5": 2.0,
    "POINT_3": 10.0 / 3.0,
}

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


def normalize_score(score: float | int | None, score_format: str) -> float | None:
    if score is None or score <= 0:
        return None

    multiplier = SCORE_FORMAT_MULTIPLIERS.get(score_format)
    if multiplier is None:
        multiplier = 0.1 if score > 10 else 1.0

    return round(min(float(score) * multiplier, 10.0), 2)


def _display_title(media: dict[str, Any]) -> str:
    title = media.get("title") or {}
    return title.get("english") or title.get("romaji") or "Untitled"


def entries_to_dataframe(entries: list[dict[str, Any]], score_format: str) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []

    for entry in entries:
        media = entry.get("media") or {}
        normalized_score = normalize_score(entry.get("score"), score_format)
        if normalized_score is None:
            continue

        rows.append(
            {
                "media_id": media.get("id"),
                "title": _display_title(media),
                "title_romaji": (media.get("title") or {}).get("romaji"),
                "title_english": (media.get("title") or {}).get("english"),
                "raw_score": entry.get("score"),
                "score": normalized_score,
                "format": media.get("format"),
                "episodes": media.get("episodes"),
                "genres": media.get("genres") or [],
                "tags": media.get("tags") or [],
                "average_score": media.get("averageScore"),
                "average_score_10": (media.get("averageScore") / 10) if media.get("averageScore") else None,
                "popularity": media.get("popularity"),
                "season_year": media.get("seasonYear"),
                "site_url": media.get("siteUrl"),
            }
        )

    return pd.DataFrame(rows)


def bangumi_entries_to_dataframe(entries: list[dict[str, Any]]) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []

    for entry in entries:
        subject = entry.get("subject") or {}
        score = normalize_score(entry.get("rate"), "POINT_10")
        if score is None:
            continue

        community_score = subject.get("score")
        date_text = subject.get("date") or ""
        season_year = None
        if len(date_text) >= 4 and date_text[:4].isdigit():
            season_year = int(date_text[:4])

        subject_tags = subject.get("tags") or []
        max_tag_count = max((tag.get("count") or 0 for tag in subject_tags), default=0)
        tags = []
        for tag in subject_tags[:20]:
            name = tag.get("name")
            if not name:
                continue
            if max_tag_count:
                rank = max(20, min(100, int((tag.get("count", 0) / max_tag_count) * 100)))
            else:
                rank = 50
            tags.append({"name": name, "rank": rank})
        genres = [tag["name"] for tag in tags if tag["name"] in BANGUMI_GENRE_TAGS]

        rows.append(
            {
                "media_id": subject.get("id") or entry.get("subject_id"),
                "title": subject.get("name_cn") or subject.get("name") or "Untitled",
                "title_romaji": subject.get("name"),
                "title_english": subject.get("name_cn"),
                "raw_score": entry.get("rate"),
                "score": score,
                "format": subject.get("platform"),
                "episodes": subject.get("eps"),
                "genres": genres,
                "tags": tags,
                "average_score": (community_score * 10) if community_score is not None else None,
                "average_score_10": community_score,
                "popularity": subject.get("collection_total"),
                "season_year": season_year,
                "site_url": f"https://bgm.tv/subject/{subject.get('id')}" if subject.get("id") else None,
            }
        )

    return pd.DataFrame(rows)


def compute_rating_stats(df: pd.DataFrame) -> dict[str, Any]:
    if df.empty:
        return {
            "total_completed": 0,
            "average_score": 0.0,
            "median_score": 0.0,
            "std_score": 0.0,
            "ten_count": 0,
            "pct_scores_gte_8": 0.0,
            "pct_scores_lte_5": 0.0,
            "avg_user_minus_anilist": None,
            "avg_anilist_score": None,
            "avg_user_minus_site": None,
            "avg_site_score": None,
        }

    scores = df["score"].astype(float)
    with_averages = df.dropna(subset=["average_score_10"])
    avg_delta = None
    avg_anilist = None
    if not with_averages.empty:
        avg_delta = float((with_averages["score"] - with_averages["average_score_10"]).mean())
        avg_anilist = float(with_averages["average_score_10"].mean())

    return {
        "total_completed": int(len(df)),
        "average_score": float(scores.mean()),
        "median_score": float(scores.median()),
        "std_score": float(scores.std(ddof=0)),
        "ten_count": int((scores >= 9.75).sum()),
        "pct_scores_gte_8": float((scores >= 8).mean() * 100),
        "pct_scores_lte_5": float((scores <= 5).mean() * 100),
        "avg_user_minus_anilist": avg_delta,
        "avg_anilist_score": avg_anilist,
        "avg_user_minus_site": avg_delta,
        "avg_site_score": avg_anilist,
    }


def _preference_table(scores: dict[str, float], counts: dict[str, int]) -> pd.DataFrame:
    rows = [
        {
            "name": name,
            "preference_score": round(total, 2),
            "mentions": counts[name],
            "average_delta": round(total / counts[name], 2) if counts[name] else 0.0,
        }
        for name, total in scores.items()
        if counts[name] > 0
    ]
    if not rows:
        return pd.DataFrame(columns=["name", "preference_score", "mentions", "average_delta"])

    return pd.DataFrame(rows)


def compute_preference_profile(df: pd.DataFrame, top_n: int = 8) -> dict[str, pd.DataFrame]:
    """Calculate weighted genre and tag preferences from score deltas."""

    if df.empty:
        empty = pd.DataFrame(columns=["name", "preference_score", "mentions", "average_delta"])
        return {
            "genres": empty,
            "tags": empty,
            "top_positive_genres": empty,
            "top_negative_genres": empty,
            "top_positive_tags": empty,
            "top_negative_tags": empty,
        }

    user_average = float(df["score"].mean())
    genre_scores: dict[str, float] = defaultdict(float)
    genre_counts: dict[str, int] = defaultdict(int)
    tag_scores: dict[str, float] = defaultdict(float)
    tag_counts: dict[str, int] = defaultdict(int)

    for _, row in df.iterrows():
        rating_delta = float(row["score"]) - user_average

        for genre in row.get("genres") or []:
            genre_scores[genre] += rating_delta
            genre_counts[genre] += 1

        for tag in row.get("tags") or []:
            name = tag.get("name")
            if not name:
                continue
            rank = tag.get("rank")
            tag_rank_weight = float(rank) / 100 if rank else 0.5
            tag_scores[name] += rating_delta * tag_rank_weight
            tag_counts[name] += 1

    min_mentions = 2 if len(df) >= 15 else 1
    genres = _preference_table(genre_scores, genre_counts)
    tags = _preference_table(tag_scores, tag_counts)

    filtered_genres = genres[genres["mentions"] >= min_mentions] if not genres.empty else genres
    filtered_tags = tags[tags["mentions"] >= min_mentions] if not tags.empty else tags

    positive_genres = filtered_genres[filtered_genres["preference_score"] > 0] if not filtered_genres.empty else filtered_genres
    negative_genres = filtered_genres[filtered_genres["preference_score"] < 0] if not filtered_genres.empty else filtered_genres
    positive_tags = filtered_tags[filtered_tags["preference_score"] > 0] if not filtered_tags.empty else filtered_tags
    negative_tags = filtered_tags[filtered_tags["preference_score"] < 0] if not filtered_tags.empty else filtered_tags

    top_positive_genres = positive_genres.sort_values(
        ["preference_score", "average_delta"], ascending=[False, False]
    ).head(top_n)
    top_negative_genres = negative_genres.sort_values(
        ["preference_score", "average_delta"], ascending=[True, True]
    ).head(top_n)
    top_positive_tags = positive_tags.sort_values(
        ["preference_score", "average_delta"], ascending=[False, False]
    ).head(top_n)
    top_negative_tags = negative_tags.sort_values(
        ["preference_score", "average_delta"], ascending=[True, True]
    ).head(top_n)

    return {
        "genres": genres.sort_values("preference_score", ascending=False),
        "tags": tags.sort_values("preference_score", ascending=False),
        "top_positive_genres": top_positive_genres,
        "top_negative_genres": top_negative_genres,
        "top_positive_tags": top_positive_tags,
        "top_negative_tags": top_negative_tags,
    }


def score_distribution(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(columns=["score_bucket", "count"])

    buckets = pd.cut(
        df["score"],
        bins=[0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
        labels=["1", "2", "3", "4", "5", "6", "7", "8", "9", "10"],
        include_lowest=True,
    )
    return buckets.value_counts(sort=False).rename_axis("score_bucket").reset_index(name="count")
