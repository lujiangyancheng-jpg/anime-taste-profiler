"""Shareable taste profile card helpers."""

from __future__ import annotations

from html import escape
from typing import Any

import pandas as pd

from i18n import t


CARD_CSS = """
<style>
.atp-card {
  border: 1px solid rgba(255, 255, 255, 0.16);
  border-left: 6px solid #ff5c8a;
  border-radius: 8px;
  background: #171923;
  color: #f6f7fb;
  padding: 18px 20px;
  margin: 0.25rem 0 1rem;
  box-shadow: 0 18px 45px rgba(0, 0, 0, 0.22);
}
.atp-card-kicker {
  color: #84d2ff;
  font-size: 0.78rem;
  font-weight: 700;
  letter-spacing: 0;
  text-transform: uppercase;
}
.atp-card-title {
  font-size: 1.55rem;
  line-height: 1.2;
  font-weight: 800;
  margin-top: 0.2rem;
}
.atp-card-subtitle {
  color: #c9cedd;
  margin-top: 0.35rem;
}
.atp-card-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 10px;
  margin: 1rem 0;
}
.atp-card-stat {
  border: 1px solid rgba(255, 255, 255, 0.12);
  border-radius: 8px;
  padding: 10px;
  background: #202433;
}
.atp-card-stat-label {
  color: #aeb6c9;
  font-size: 0.72rem;
}
.atp-card-stat-value {
  font-weight: 800;
  font-size: 1.1rem;
  margin-top: 0.2rem;
}
.atp-card-section {
  margin-top: 0.8rem;
}
.atp-card-section-title {
  color: #ffd166;
  font-size: 0.82rem;
  font-weight: 800;
  margin-bottom: 0.35rem;
}
.atp-card-pills {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}
.atp-card-pill {
  border-radius: 999px;
  background: rgba(132, 210, 255, 0.14);
  border: 1px solid rgba(132, 210, 255, 0.28);
  color: #eef8ff;
  padding: 5px 10px;
  font-size: 0.82rem;
}
.atp-card-pill.weak {
  background: rgba(255, 209, 102, 0.12);
  border-color: rgba(255, 209, 102, 0.30);
}
@media (max-width: 720px) {
  .atp-card-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}
</style>
"""


CARD_TEXT = {
    "en": {
        "share_card": "Shareable Profile Card",
        "download_card": "Download Card",
        "card_kicker": "{source} taste profile",
        "card_liked": "Favorite signals",
        "card_weaker": "Watch-out signals",
    },
    "zh": {
        "share_card": "可分享口味卡",
        "download_card": "下载卡片",
        "card_kicker": "{source} 口味画像",
        "card_liked": "本命信号",
        "card_weaker": "雷达预警",
    },
}


CARD_ANIME_TEXT = {
    "en": {
        "share_card": "Screenshot-Ready Profile Card",
        "download_card": "Download Character Card",
        "card_kicker": "{source} anime aura scan",
        "card_liked": "Buff flags",
        "card_weaker": "Debuff flags",
    },
    "zh": {
        "share_card": "可截图人设卡",
        "download_card": "下载人设卡",
        "card_kicker": "{source} 动画气场扫描",
        "card_liked": "加成旗帜",
        "card_weaker": "减益旗帜",
    },
}


def card_text(lang: str, tone: str, key: str, **kwargs) -> str:
    source = CARD_ANIME_TEXT if tone == "anime" else CARD_TEXT
    text = source.get(lang, source["en"]).get(key, CARD_TEXT["en"][key])
    return text.format(**kwargs)


def _names(table: pd.DataFrame, limit: int = 4) -> list[str]:
    if table is None or table.empty:
        return []
    return [str(value) for value in table["name"].head(limit).tolist() if str(value).strip()]


def _format_percent(value: float) -> str:
    return f"{value:.0f}%"


def _profile_lists(preferences: dict[str, pd.DataFrame]) -> tuple[list[str], list[str]]:
    liked = _names(preferences["top_positive_genres"], 3) + _names(preferences["top_positive_tags"], 3)
    weaker = _names(preferences["top_negative_genres"], 3) + _names(preferences["top_negative_tags"], 3)
    return liked[:5], weaker[:5]


def _pill_html(items: list[str], fallback: str, weak: bool = False) -> str:
    if not items:
        items = [fallback]
    class_name = "atp-card-pill weak" if weak else "atp-card-pill"
    return "".join(f'<span class="{class_name}">{escape(item)}</span>' for item in items)


def build_profile_card_html(
    user_name: str,
    source: str,
    stats: dict[str, Any],
    preferences: dict[str, pd.DataFrame],
    rating_style: dict[str, str],
    archetype: dict[str, str],
    lang: str,
    tone: str,
) -> str:
    liked, weaker = _profile_lists(preferences)
    no_signal = t(lang, "no_signal", tone=tone)
    delta = stats.get("avg_user_minus_site")
    delta_text = t(lang, "unavailable", tone=tone) if delta is None else f"{delta:+.2f}"

    stats_html = "".join(
        f"""
        <div class="atp-card-stat">
          <div class="atp-card-stat-label">{escape(label)}</div>
          <div class="atp-card-stat-value">{escape(value)}</div>
        </div>
        """
        for label, value in [
            (t(lang, "completed", tone=tone), str(stats["total_completed"])),
            (t(lang, "average", tone=tone), f"{stats['average_score']:.2f}"),
            (t(lang, "high_scores", tone=tone), _format_percent(stats["pct_scores_gte_8"])),
            (t(lang, "vs_site", tone=tone, source=source), delta_text),
        ]
    )

    return f"""
<div class="atp-card">
  <div class="atp-card-kicker">{escape(card_text(lang, tone, "card_kicker", source=source))}</div>
  <div class="atp-card-title">{escape(user_name)} · {escape(archetype["name"])}</div>
  <div class="atp-card-subtitle">{escape(rating_style["name"])} · {escape(rating_style["explanation"])}</div>
  <div class="atp-card-grid">{stats_html}</div>
  <div class="atp-card-section">
    <div class="atp-card-section-title">{escape(card_text(lang, tone, "card_liked"))}</div>
    <div class="atp-card-pills">{_pill_html(liked, no_signal)}</div>
  </div>
  <div class="atp-card-section">
    <div class="atp-card-section-title">{escape(card_text(lang, tone, "card_weaker"))}</div>
    <div class="atp-card-pills">{_pill_html(weaker, no_signal, weak=True)}</div>
  </div>
</div>
"""


def build_profile_card_markdown(
    user_name: str,
    source: str,
    stats: dict[str, Any],
    preferences: dict[str, pd.DataFrame],
    rating_style: dict[str, str],
    archetype: dict[str, str],
    lang: str,
    tone: str,
) -> str:
    liked, weaker = _profile_lists(preferences)
    no_signal = t(lang, "no_signal", tone=tone)
    liked_text = ", ".join(liked) if liked else no_signal
    weaker_text = ", ".join(weaker) if weaker else no_signal
    delta = stats.get("avg_user_minus_site")
    delta_text = t(lang, "unavailable", tone=tone) if delta is None else f"{delta:+.2f}"

    return "\n".join(
        [
            f"# {user_name} - {archetype['name']}",
            "",
            f"- {t(lang, 'source', tone=tone)}: {source}",
            f"- {t(lang, 'completed', tone=tone)}: {stats['total_completed']}",
            f"- {t(lang, 'average', tone=tone)}: {stats['average_score']:.2f}",
            f"- {t(lang, 'high_scores', tone=tone)}: {_format_percent(stats['pct_scores_gte_8'])}",
            f"- {t(lang, 'vs_site', tone=tone, source=source)}: {delta_text}",
            f"- {t(lang, 'rating_habits', tone=tone)}: {rating_style['name']}",
            f"- {card_text(lang, tone, 'card_liked')}: {liked_text}",
            f"- {card_text(lang, tone, 'card_weaker')}: {weaker_text}",
            "",
            rating_style["explanation"],
            "",
            archetype["explanation"],
            "",
        ]
    )
