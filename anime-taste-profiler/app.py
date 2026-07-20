from __future__ import annotations

import pandas as pd
import streamlit as st

from analyzer import (
    bangumi_entries_to_dataframe,
    compute_preference_profile,
    compute_rating_stats,
    entries_to_dataframe,
    score_distribution,
)
from anilist_api import AniListError, fetch_completed_anime as fetch_anilist_completed, fetch_trending_anime
from bangumi_api import BangumiError, fetch_completed_anime as fetch_bangumi_completed, fetch_ranked_anime
from comparison import compare_profiles, compare_text, comparison_summary
from i18n import t
from profile_card import CARD_CSS, build_profile_card_html, build_profile_card_markdown, card_text
from profile_generator import classify_rating_style, classify_taste_archetype, generate_profile_report
from recommender import score_recommendations


st.set_page_config(page_title="Anime Taste Profiler", layout="wide")


@st.cache_data(ttl=3600, show_spinner=False)
def load_anilist_completed(username: str):
    return fetch_anilist_completed(username)


@st.cache_data(ttl=3600, show_spinner=False)
def load_bangumi_completed(username: str):
    return fetch_bangumi_completed(username)


@st.cache_data(ttl=1800, show_spinner=False)
def load_anilist_candidates():
    return fetch_trending_anime(per_page=50)


@st.cache_data(ttl=1800, show_spinner=False)
def load_bangumi_candidates():
    return fetch_ranked_anime(per_page=50)


def copy(lang: str, tone: str, key: str, **kwargs) -> str:
    return t(lang, key, tone=tone, **kwargs)


def format_percent(value: float) -> str:
    return f"{value:.1f}%"


def preference_table(table: pd.DataFrame, lang: str, tone: str) -> pd.DataFrame:
    if table.empty:
        return pd.DataFrame(
            {
                copy(lang, tone, "signal"): [copy(lang, tone, "no_signal")],
                copy(lang, tone, "score"): [""],
                copy(lang, tone, "mentions"): [""],
            }
        )
    return table.rename(
        columns={
            "name": copy(lang, tone, "signal"),
            "preference_score": copy(lang, tone, "score"),
            "mentions": copy(lang, tone, "mentions"),
            "average_delta": copy(lang, tone, "avg_delta"),
        }
    )[
        [
            copy(lang, tone, "signal"),
            copy(lang, tone, "score"),
            copy(lang, tone, "mentions"),
            copy(lang, tone, "avg_delta"),
        ]
    ]


def load_profile_data(source: str, username: str):
    if source == "Bangumi":
        user, entries = load_bangumi_completed(username)
        return user, bangumi_entries_to_dataframe(entries)

    user, entries = load_anilist_completed(username)
    return user, entries_to_dataframe(entries, user["score_format"])


def show_recommendations(
    source: str,
    df: pd.DataFrame,
    preferences: dict[str, pd.DataFrame],
    lang: str,
    tone: str,
) -> None:
    st.subheader(copy(lang, tone, "recommendations"))
    try:
        candidates = load_bangumi_candidates() if source == "Bangumi" else load_anilist_candidates()
        completed_ids = set(df["media_id"].dropna().astype(int).tolist())
        recommendations = score_recommendations(candidates, completed_ids, preferences)
    except (AniListError, BangumiError) as exc:
        st.warning(copy(lang, tone, "recommendation_error", error=str(exc)))
        return

    if not recommendations:
        st.info(copy(lang, tone, "no_recommendations"))
        return

    fit_labels = {
        "strong": {"en": "strong match", "zh": "强匹配"},
        "good": {"en": "good match", "zh": "稳匹配"},
        "niche": {"en": "niche match", "zh": "偏门匹配"},
    }

    for item in recommendations:
        details = []
        fit_label = fit_labels.get(item.get("fit_level"), fit_labels["niche"]).get(lang, fit_labels["niche"]["en"])
        match_text = f"Match {item['match_score']}/100 · {fit_label}" if lang == "en" else f"匹配度 {item['match_score']}/100 · {fit_label}"
        details.append(match_text)
        if item.get("year"):
            details.append(str(item["year"]))
        if item.get("format"):
            details.append(str(item["format"]).replace("_", " ").title())
        if item.get("average_score"):
            details.append(copy(lang, tone, "average_label", source=source, score=item["average_score"] / 10))

        reason_text = ", ".join(item["reasons"])
        caution = ""
        if item["cautions"]:
            caution = copy(lang, tone, "caution", cautions=", ".join(item["cautions"]))

        title = item["title"]
        if item.get("site_url"):
            title = f"[{title}]({item['site_url']})"

        st.markdown(
            f"**{title}**  \n"
            f"{' - '.join(details)}  \n"
            f"{copy(lang, tone, 'matches', reasons=reason_text, caution=caution)}"
        )


def show_share_card(
    user_name: str,
    source: str,
    stats: dict,
    preferences: dict[str, pd.DataFrame],
    rating_style: dict[str, str],
    archetype: dict[str, str],
    lang: str,
    tone: str,
) -> None:
    st.subheader(card_text(lang, tone, "share_card"))
    st.markdown(
        CARD_CSS
        + build_profile_card_html(
            user_name,
            source,
            stats,
            preferences,
            rating_style,
            archetype,
            lang,
            tone,
        ),
        unsafe_allow_html=True,
    )
    st.download_button(
        card_text(lang, tone, "download_card"),
        data=build_profile_card_markdown(
            user_name,
            source,
            stats,
            preferences,
            rating_style,
            archetype,
            lang,
            tone,
        ),
        file_name=f"{user_name}-{source}-anime-taste-card.md",
        mime="text/markdown",
    )


def profile_parts(df: pd.DataFrame, lang: str, tone: str) -> tuple[dict, dict[str, pd.DataFrame], dict[str, str], dict[str, str]]:
    stats = compute_rating_stats(df)
    preferences = compute_preference_profile(df)
    rating_style = classify_rating_style(stats, lang=lang, tone=tone)
    archetype = classify_taste_archetype(
        preferences["top_positive_genres"],
        preferences["top_positive_tags"],
        rating_style,
        lang=lang,
        tone=tone,
    )
    return stats, preferences, rating_style, archetype


def render_profile(source: str, username: str, lang: str, tone: str) -> None:
    try:
        with st.spinner(copy(lang, tone, "fetching", source=source)):
            user, df = load_profile_data(source, username)
    except (AniListError, BangumiError) as exc:
        st.error(str(exc))
        return

    if df.empty:
        st.error(copy(lang, tone, "no_data"))
        return

    stats, preferences, rating_style, archetype = profile_parts(df, lang, tone)
    report = generate_profile_report(
        stats,
        preferences,
        rating_style,
        archetype,
        lang=lang,
        source_label=source,
        tone=tone,
    )

    st.caption(copy(lang, tone, "caption", name=user["name"], source=source))

    if stats["total_completed"] < 10:
        st.warning(copy(lang, tone, "low_count"))

    st.subheader(copy(lang, tone, "basic_stats"))
    metric_cols = st.columns(6)
    metric_cols[0].metric(copy(lang, tone, "completed"), stats["total_completed"])
    metric_cols[1].metric(copy(lang, tone, "average"), f"{stats['average_score']:.2f}")
    metric_cols[2].metric(copy(lang, tone, "median"), f"{stats['median_score']:.2f}")
    metric_cols[3].metric(copy(lang, tone, "std_dev"), f"{stats['std_score']:.2f}")
    metric_cols[4].metric(copy(lang, tone, "tens"), stats["ten_count"])
    metric_cols[5].metric(copy(lang, tone, "high_scores"), format_percent(stats["pct_scores_gte_8"]))

    comparison_cols = st.columns(2)
    comparison_cols[0].metric(copy(lang, tone, "low_scores"), format_percent(stats["pct_scores_lte_5"]))
    if stats["avg_user_minus_site"] is not None:
        comparison_cols[1].metric(
            copy(lang, tone, "vs_site", source=source),
            f"{stats['avg_user_minus_site']:+.2f}",
            help=copy(lang, tone, "vs_help"),
        )
    else:
        comparison_cols[1].metric(copy(lang, tone, "vs_site", source=source), copy(lang, tone, "unavailable"))

    st.subheader(copy(lang, tone, "rating_habits"))
    habit_cols = st.columns([1, 2])
    habit_cols[0].markdown(f"### {rating_style['name']}")
    habit_cols[0].write(rating_style["explanation"])
    habit_cols[1].bar_chart(score_distribution(df), x="score_bucket", y="count", width="stretch")

    st.subheader(copy(lang, tone, "taste_signals"))
    signal_tabs = st.tabs(
        [
            copy(lang, tone, "liked_genres"),
            copy(lang, tone, "disliked_genres"),
            copy(lang, tone, "liked_tags"),
            copy(lang, tone, "disliked_tags"),
        ]
    )
    signal_tabs[0].dataframe(preference_table(preferences["top_positive_genres"], lang, tone), hide_index=True, width="stretch")
    signal_tabs[1].dataframe(preference_table(preferences["top_negative_genres"], lang, tone), hide_index=True, width="stretch")
    signal_tabs[2].dataframe(preference_table(preferences["top_positive_tags"], lang, tone), hide_index=True, width="stretch")
    signal_tabs[3].dataframe(preference_table(preferences["top_negative_tags"], lang, tone), hide_index=True, width="stretch")

    st.subheader(copy(lang, tone, "archetype"))
    st.markdown(f"### {archetype['name']}")
    st.write(archetype["explanation"])

    st.subheader(copy(lang, tone, "report"))
    st.write(report)

    show_share_card(user["name"], source, stats, preferences, rating_style, archetype, lang, tone)

    with st.expander(copy(lang, tone, "top_bottom")):
        display_cols = ["title", "score", "average_score_10", "format", "episodes", "season_year"]
        renamed = df[display_cols].rename(
            columns={
                "title": copy(lang, tone, "title"),
                "score": copy(lang, tone, "user_score"),
                "average_score_10": copy(lang, tone, "site_avg", source=source),
                "format": copy(lang, tone, "format"),
                "episodes": copy(lang, tone, "episodes"),
                "season_year": copy(lang, tone, "year"),
            }
        )
        user_score_col = copy(lang, tone, "user_score")
        top_bottom = pd.concat(
            [
                renamed.sort_values(user_score_col, ascending=False).head(10),
                renamed.sort_values(user_score_col, ascending=True).head(10),
            ]
        ).drop_duplicates()
        st.dataframe(top_bottom, hide_index=True, width="stretch")

    show_recommendations(source, df, preferences, lang, tone)


def _joined(items: list[str], lang: str) -> str:
    if not items:
        return compare_text(lang, "no_overlap")
    return ", ".join(items)


def render_comparison(source: str, username_a: str, username_b: str, lang: str, tone: str) -> None:
    try:
        with st.spinner(compare_text(lang, "fetching_pair", source=source)):
            user_a, df_a = load_profile_data(source, username_a)
            user_b, df_b = load_profile_data(source, username_b)
    except (AniListError, BangumiError) as exc:
        st.error(str(exc))
        return

    if df_a.empty or df_b.empty:
        st.error(copy(lang, tone, "no_data"))
        return

    stats_a, preferences_a, rating_style_a, archetype_a = profile_parts(df_a, lang, tone)
    stats_b, preferences_b, rating_style_b, archetype_b = profile_parts(df_b, lang, tone)
    comparison = compare_profiles(
        user_a["name"],
        user_b["name"],
        df_a,
        df_b,
        stats_a,
        stats_b,
        preferences_a,
        preferences_b,
    )

    st.subheader(compare_text(lang, "comparison_title"))
    metric_cols = st.columns(4)
    metric_cols[0].metric(compare_text(lang, "similarity"), f"{comparison['similarity']}%")
    metric_cols[1].metric(compare_text(lang, "shared_completed"), comparison["common_count"])
    if comparison["score_correlation"] is None:
        metric_cols[2].metric(compare_text(lang, "score_sync"), copy(lang, tone, "unavailable"))
    else:
        metric_cols[2].metric(compare_text(lang, "score_sync"), f"{comparison['score_correlation']:.2f}")
    metric_cols[3].metric(
        compare_text(lang, "stricter"),
        comparison["stricter_user"] or compare_text(lang, "similar_strictness"),
    )
    st.write(comparison_summary(comparison, lang))

    profile_cols = st.columns(2)
    for col, user, stats, rating_style, archetype in [
        (profile_cols[0], user_a, stats_a, rating_style_a, archetype_a),
        (profile_cols[1], user_b, stats_b, rating_style_b, archetype_b),
    ]:
        col.markdown(f"### {user['name']}")
        col.metric(copy(lang, tone, "completed"), stats["total_completed"])
        col.metric(copy(lang, tone, "average"), f"{stats['average_score']:.2f}")
        col.write(f"**{archetype['name']}**")
        col.caption(rating_style["name"])

    st.subheader(compare_text(lang, "common_favorites"))
    if comparison["common_favorites"]:
        favorites = pd.DataFrame(comparison["common_favorites"]).rename(
            columns={
                "title_a": copy(lang, tone, "title"),
                "score_a": user_a["name"],
                "score_b": user_b["name"],
            }
        )
        st.dataframe(favorites, hide_index=True, width="stretch")
    else:
        st.info(compare_text(lang, "no_overlap"))

    signal_cols = st.columns(3)
    signal_cols[0].markdown(f"**{compare_text(lang, 'shared_likes')}**")
    signal_cols[0].write(_joined(comparison["shared_likes"], lang))
    signal_cols[1].markdown(f"**{compare_text(lang, 'shared_weak_spots')}**")
    signal_cols[1].write(_joined(comparison["shared_weak_spots"], lang))
    signal_cols[2].markdown(f"**{compare_text(lang, 'taste_clashes')}**")
    clashes = []
    if comparison["a_likes_b_avoids"]:
        clashes.append(
            f"{compare_text(lang, 'user_a_likes_b_avoids', a=user_a['name'], b=user_b['name'])}: "
            f"{', '.join(comparison['a_likes_b_avoids'])}"
        )
    if comparison["b_likes_a_avoids"]:
        clashes.append(
            f"{compare_text(lang, 'user_b_likes_a_avoids', a=user_a['name'], b=user_b['name'])}: "
            f"{', '.join(comparison['b_likes_a_avoids'])}"
        )
    signal_cols[2].write("\n\n".join(clashes) if clashes else compare_text(lang, "no_overlap"))


use_chinese = st.sidebar.toggle(
    "中文 / English",
    value=st.session_state.get("language_mode", "en") == "zh",
    help=t("zh", "language_help"),
)
lang = "zh" if use_chinese else "en"
st.session_state.language_mode = lang

use_anime_tone = st.sidebar.toggle(
    copy(lang, "standard", "tone"),
    value=st.session_state.get("tone_mode", "standard") == "anime",
    help=copy(lang, "standard", "tone_help"),
)
tone = "anime" if use_anime_tone else "standard"
st.session_state.tone_mode = tone

source = st.sidebar.radio(copy(lang, tone, "source"), ["AniList", "Bangumi"], horizontal=True)
mode = st.sidebar.radio(
    compare_text(lang, "mode"),
    ["profile", "compare"],
    format_func=lambda value: compare_text(lang, "profile_mode" if value == "profile" else "compare_mode"),
    horizontal=True,
)

st.title(copy(lang, tone, "page_title"))

if mode == "profile":
    with st.form("taste-form"):
        username = st.text_input(
            copy(lang, tone, "username", source=source),
            placeholder=copy(lang, tone, "username_placeholder", source=source),
            key=f"username_{source}",
        )
        analyze = st.form_submit_button(copy(lang, tone, "analyze"), type="primary")

    if analyze:
        clean_username = username.strip()
        if not clean_username:
            st.warning(copy(lang, tone, "empty_username", source=source))
            st.stop()

        st.session_state.profile_request = {
            "mode": "profile",
            "source": source,
            "username": clean_username,
        }
else:
    with st.form("compare-form"):
        user_cols = st.columns(2)
        username_a = user_cols[0].text_input(
            compare_text(lang, "first_username", source=source),
            key=f"compare_username_a_{source}",
        )
        username_b = user_cols[1].text_input(
            compare_text(lang, "second_username", source=source),
            key=f"compare_username_b_{source}",
        )
        compare_submit = st.form_submit_button(compare_text(lang, "compare_button"), type="primary")

    if compare_submit:
        clean_a = username_a.strip()
        clean_b = username_b.strip()
        if not clean_a or not clean_b or clean_a == clean_b:
            st.warning(compare_text(lang, "empty_compare", source=source))
            st.stop()

        st.session_state.profile_request = {
            "mode": "compare",
            "source": source,
            "username_a": clean_a,
            "username_b": clean_b,
        }

request = st.session_state.get("profile_request")
if request:
    if request.get("mode") == "compare":
        render_comparison(request["source"], request["username_a"], request["username_b"], lang, tone)
    else:
        render_profile(request["source"], request["username"], lang, tone)
