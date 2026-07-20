"""Two-user taste comparison helpers."""

from __future__ import annotations

from typing import Any

import pandas as pd


COMPARE_TEXT = {
    "en": {
        "mode": "Mode",
        "profile_mode": "Single profile",
        "compare_mode": "Compare users",
        "first_username": "First {source} username",
        "second_username": "Second {source} username",
        "compare_button": "Compare Taste",
        "empty_compare": "Enter two different {source} usernames.",
        "fetching_pair": "Fetching both {source} lists...",
        "comparison_title": "Taste Compatibility",
        "similarity": "Similarity",
        "shared_completed": "Shared completed",
        "score_sync": "Score sync",
        "stricter": "Stricter rater",
        "similar_strictness": "Similar",
        "common_favorites": "Common favorites",
        "shared_likes": "Shared likes",
        "shared_weak_spots": "Shared weak spots",
        "taste_clashes": "Taste clashes",
        "no_overlap": "No clear overlap yet",
        "user_a_likes_b_avoids": "{a} likes, {b} avoids",
        "user_b_likes_a_avoids": "{b} likes, {a} avoids",
    },
    "zh": {
        "mode": "模式",
        "profile_mode": "单人画像",
        "compare_mode": "双人对比",
        "first_username": "第一个 {source} 用户名",
        "second_username": "第二个 {source} 用户名",
        "compare_button": "对比口味",
        "empty_compare": "请输入两个不同的 {source} 用户名。",
        "fetching_pair": "正在读取两份 {source} 片单...",
        "comparison_title": "口味相性",
        "similarity": "相似度",
        "shared_completed": "共同看过",
        "score_sync": "评分同步",
        "stricter": "更严格",
        "similar_strictness": "差不多",
        "common_favorites": "共同高分",
        "shared_likes": "共同喜好",
        "shared_weak_spots": "共同雷区",
        "taste_clashes": "口味冲突",
        "no_overlap": "暂时没有明显重合",
        "user_a_likes_b_avoids": "{a} 喜欢，{b} 避雷",
        "user_b_likes_a_avoids": "{b} 喜欢，{a} 避雷",
    },
}


def compare_text(lang: str, key: str, **kwargs) -> str:
    text = COMPARE_TEXT.get(lang, COMPARE_TEXT["en"]).get(key, COMPARE_TEXT["en"][key])
    return text.format(**kwargs)


def _signals(preferences: dict[str, pd.DataFrame], positive: bool) -> set[str]:
    genre_key = "top_positive_genres" if positive else "top_negative_genres"
    tag_key = "top_positive_tags" if positive else "top_negative_tags"
    values: set[str] = set()
    for table in [preferences.get(genre_key), preferences.get(tag_key)]:
        if table is not None and not table.empty:
            values.update(str(value) for value in table["name"].head(8).tolist() if str(value).strip())
    return values


def _common_entries(df_a: pd.DataFrame, df_b: pd.DataFrame) -> pd.DataFrame:
    left = df_a.dropna(subset=["media_id"])[["media_id", "title", "score"]].copy()
    right = df_b.dropna(subset=["media_id"])[["media_id", "title", "score"]].copy()
    left["media_id"] = left["media_id"].astype(str)
    right["media_id"] = right["media_id"].astype(str)
    return left.merge(right, on="media_id", suffixes=("_a", "_b"))


def _score_correlation(common: pd.DataFrame) -> float | None:
    if len(common) < 2:
        return None
    if common["score_a"].nunique() < 2 or common["score_b"].nunique() < 2:
        return None
    value = common["score_a"].corr(common["score_b"])
    if pd.isna(value):
        return None
    return float(value)


def compare_profiles(
    user_a: str,
    user_b: str,
    df_a: pd.DataFrame,
    df_b: pd.DataFrame,
    stats_a: dict[str, Any],
    stats_b: dict[str, Any],
    preferences_a: dict[str, pd.DataFrame],
    preferences_b: dict[str, pd.DataFrame],
) -> dict[str, Any]:
    common = _common_entries(df_a, df_b)
    common_favorites = common[(common["score_a"] >= 8) & (common["score_b"] >= 8)].copy()
    if not common_favorites.empty:
        common_favorites["combined_score"] = common_favorites["score_a"] + common_favorites["score_b"]
        common_favorites = common_favorites.sort_values("combined_score", ascending=False).head(8)

    liked_a = _signals(preferences_a, positive=True)
    liked_b = _signals(preferences_b, positive=True)
    weak_a = _signals(preferences_a, positive=False)
    weak_b = _signals(preferences_b, positive=False)

    shared_likes = sorted(liked_a & liked_b)
    shared_weak_spots = sorted(weak_a & weak_b)
    a_likes_b_avoids = sorted(liked_a & weak_b)
    b_likes_a_avoids = sorted(liked_b & weak_a)

    signal_union = liked_a | liked_b | weak_a | weak_b
    signal_similarity = 0.0
    if signal_union:
        signal_similarity = (len(shared_likes) + len(shared_weak_spots)) / len(signal_union)

    correlation = _score_correlation(common)
    correlation_score = 0.5 if correlation is None else (correlation + 1) / 2
    common_score = min(len(common) / 10, 1.0)
    similarity = int(round((signal_similarity * 0.55 + correlation_score * 0.30 + common_score * 0.15) * 100))

    average_gap = float(stats_a["average_score"] - stats_b["average_score"])
    stricter_user = None
    if abs(average_gap) >= 0.25:
        stricter_user = user_a if average_gap < 0 else user_b

    return {
        "user_a": user_a,
        "user_b": user_b,
        "similarity": max(0, min(100, similarity)),
        "common_count": int(len(common)),
        "score_correlation": correlation,
        "stricter_user": stricter_user,
        "shared_likes": shared_likes[:8],
        "shared_weak_spots": shared_weak_spots[:8],
        "a_likes_b_avoids": a_likes_b_avoids[:8],
        "b_likes_a_avoids": b_likes_a_avoids[:8],
        "common_favorites": common_favorites[["title_a", "score_a", "score_b"]].to_dict("records"),
    }


def comparison_summary(result: dict[str, Any], lang: str) -> str:
    if lang == "zh":
        if result["similarity"] >= 70:
            lead = "这两份片单的电波很接近。"
        elif result["similarity"] >= 45:
            lead = "这两份片单有一些共同频道，但也保留了各自的偏好。"
        else:
            lead = "这两份片单的口味距离比较明显。"

        common = f"共同看过并评分的作品有 {result['common_count']} 部。"
        if result["stricter_user"]:
            strict = f"{result['stricter_user']} 的打分整体更严格。"
        else:
            strict = "两个人的打分宽严程度比较接近。"
        return f"{lead} {common} {strict}"

    if result["similarity"] >= 70:
        lead = "These two lists are tuned to a similar wavelength."
    elif result["similarity"] >= 45:
        lead = "These two lists share some taste channels while keeping distinct preferences."
    else:
        lead = "These two lists have a clear taste distance."

    common = f"They share {result['common_count']} completed scored anime."
    if result["stricter_user"]:
        strict = f"{result['stricter_user']} is the stricter rater overall."
    else:
        strict = "Their rating strictness is fairly similar."
    return f"{lead} {common} {strict}"
