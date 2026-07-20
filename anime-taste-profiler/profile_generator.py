"""Transparent taste classification and natural language report generation."""

from __future__ import annotations

from typing import Any

import pandas as pd


ARCHETYPE_LABELS = {
    "emotional": {"en": "Emotional Character-Driven Viewer", "zh": "情感与角色驱动型观众"},
    "romance": {"en": "Romance and Relationship Dynamics Enjoyer", "zh": "恋爱与关系动态爱好者"},
    "slice_of_life": {"en": "Atmosphere and Slice-of-Life Viewer", "zh": "氛围与日常系观众"},
    "mystery": {"en": "Plot Twist and Mystery Seeker", "zh": "悬疑反转探索者"},
    "fantasy": {"en": "Worldbuilding and Fantasy Explorer", "zh": "世界观与幻想探索者"},
    "action": {"en": "Action and Hype-Driven Viewer", "zh": "动作与燃点驱动型观众"},
    "comedy": {"en": "Comedy Comfort Viewer", "zh": "喜剧舒适区观众"},
    "critical": {"en": "Critical Selective Viewer", "zh": "挑剔选择型观众"},
}


ARCHETYPE_ANIME_LABELS = {
    "emotional": {"en": "Character-Drama Main Route Enjoyer", "zh": "角色厨与情绪回收型主角"},
    "romance": {"en": "Relationship-Flag Hunter", "zh": "恋爱旗帜捕获者"},
    "slice_of_life": {"en": "Slice-of-Life Healing Camp Resident", "zh": "日常治愈营地常驻民"},
    "mystery": {"en": "Plot-Twist Investigation Club Member", "zh": "悬疑反转考据社成员"},
    "fantasy": {"en": "Worldbuilding Lore Explorer", "zh": "世界观设定考据党"},
    "action": {"en": "Hype Scene and Battle Aura Chaser", "zh": "燃点与战斗气场追番人"},
    "comedy": {"en": "Comfort Comedy Recharge Viewer", "zh": "搞笑充电型观众"},
    "critical": {"en": "Selective Anime Critic Senpai", "zh": "挑剔审番前辈"},
}


ARCHETYPE_KEYWORDS = {
    "emotional": {
        "drama",
        "coming of age",
        "family life",
        "tragedy",
        "ensemble cast",
        "character development",
        "female protagonist",
        "male protagonist",
        "剧情",
        "催泪",
        "成长",
        "青春",
        "家庭",
        "群像",
        "治愈",
        "虐心",
    },
    "romance": {
        "romance",
        "school",
        "love triangle",
        "relationships",
        "shoujo",
        "josei",
        "unrequited love",
        "couple life",
        "female protagonist",
        "恋爱",
        "爱情",
        "校园",
        "少女",
        "女性向",
        "青春",
        "恋爱喜剧",
        "后宫",
    },
    "slice_of_life": {
        "slice of life",
        "iyashikei",
        "rural",
        "family life",
        "cute girls doing cute things",
        "healing",
        "everyday life",
        "slow life",
        "日常",
        "治愈",
        "空气系",
        "芳文社",
        "萌",
        "生活",
        "慢节奏",
    },
    "mystery": {
        "psychological",
        "mystery",
        "thriller",
        "crime",
        "detective",
        "time manipulation",
        "conspiracy",
        "survival",
        "suspense",
        "悬疑",
        "推理",
        "心理",
        "惊悚",
        "犯罪",
        "侦探",
        "时间",
        "轮回",
        "智斗",
        "黑暗",
    },
    "fantasy": {
        "fantasy",
        "adventure",
        "supernatural",
        "magic",
        "mythology",
        "isekai",
        "worldbuilding",
        "historical",
        "demons",
        "奇幻",
        "冒险",
        "魔法",
        "异世界",
        "架空",
        "世界观",
        "神话",
        "历史",
        "妖怪",
    },
    "action": {
        "action",
        "sports",
        "martial arts",
        "super power",
        "battle royale",
        "shounen",
        "mecha",
        "military",
        "swordplay",
        "动作",
        "战斗",
        "热血",
        "少年",
        "机战",
        "机甲",
        "运动",
        "军事",
        "格斗",
        "科幻",
    },
    "comedy": {
        "comedy",
        "parody",
        "slapstick",
        "gag humor",
        "absurdist humor",
        "cute girls doing cute things",
        "surreal comedy",
        "喜剧",
        "搞笑",
        "吐槽",
        "恶搞",
        "欢乐",
        "泡面番",
    },
}


STYLE_LABELS = {
    "strict": {"en": "Strict Rater", "zh": "严格评分者"},
    "balanced": {"en": "Balanced Rater", "zh": "均衡评分者"},
    "generous": {"en": "Generous Rater", "zh": "宽松评分者"},
    "polarized": {"en": "Polarized Rater", "zh": "两极化评分者"},
    "completion_biased": {"en": "Completion-biased Rater", "zh": "完成偏向型评分者"},
}


STYLE_ANIME_LABELS = {
    "strict": {"en": "S-Tier Gatekeeper", "zh": "高分守门员"},
    "balanced": {"en": "Balanced Route Selector", "zh": "均衡路线选择者"},
    "generous": {"en": "Good-Vibes Watcher", "zh": "好感度加成型观众"},
    "polarized": {"en": "Love-or-Drop Reactor", "zh": "爱憎分明型观众"},
    "completion_biased": {"en": "Drop-Radar Specialist", "zh": "弃番雷达型观众"},
}


STYLE_EXPLANATIONS = {
    "strict": {
        "en": "Your average score is relatively low and top scores are rare, so a high rating from you carries extra weight.",
        "zh": "你的平均分相对偏低，高分也不常见，所以你给出的高分含金量更高。",
    },
    "balanced": {
        "en": "Your average sits near the middle-high range and you use enough of the scale to show meaningful preference.",
        "zh": "你的平均分处在中高区间，也会使用足够多的分数段来表达真实偏好。",
    },
    "generous": {
        "en": "You often finish and rate shows positively, especially around the 8+ range.",
        "zh": "你完成并给出正面评价的作品不少，8 分以上的比例也比较高。",
    },
    "polarized": {
        "en": "Your completed list has both clear favorites and clear misses, so your scores separate hits from disappointments sharply.",
        "zh": "你的已完成列表里既有明确心头好，也有明显不合拍的作品，评分区分度很强。",
    },
    "completion_biased": {
        "en": "Very few completed anime land in your low-score range, which suggests you may drop weak matches before they reach your completed list.",
        "zh": "低分完结作品很少，说明你可能会在不合口味的作品进入“已完成”之前就放弃它们。",
    },
}


STYLE_ANIME_EXPLANATIONS = {
    "strict": {
        "en": "Your 9s and 10s are rare loot drops. When a show clears your bar, it really earned the badge.",
        "zh": "你的 9 分和 10 分像稀有掉落，不是谁都能进神作殿堂。能过你这关的作品，基本都是真打中了。",
    },
    "balanced": {
        "en": "You use the score scale like a route map: enough praise, enough pushback, and clear taste flags.",
        "zh": "你的评分像路线选择图：该夸会夸，该扣会扣，口味旗帜插得比较清楚。",
    },
    "generous": {
        "en": "Your watchlist has strong good-vibes energy. If a show gives you enough charm, you are willing to hand it a warm score.",
        "zh": "你的追番记录自带好感滤镜。只要作品给到足够魅力，你很愿意给它发一张高分通行证。",
    },
    "polarized": {
        "en": "Your reactions have high episode-drama energy: favorites shine hard, weak matches fall fast.",
        "zh": "你的评分反应很有弹幕起伏：本命会被高高举起，不合拍的作品也会被迅速打入冷宫。",
    },
    "completion_biased": {
        "en": "Your low-score shelf is small, which makes the drop radar look active before bad matches reach the ending.",
        "zh": "你的低分完结区很小，像是弃番雷达提前工作，把不少不合拍作品挡在终点线外。",
    },
}


def _label(key: str, lang: str, tone: str, standard: dict[str, dict[str, str]], anime: dict[str, dict[str, str]]) -> str:
    labels = anime if tone == "anime" else standard
    return labels[key].get(lang, labels[key]["en"])


def _names(table: pd.DataFrame, limit: int = 5) -> list[str]:
    if table is None or table.empty:
        return []
    return [str(value) for value in table["name"].head(limit).tolist()]


def _unique(items: list[str]) -> list[str]:
    seen = set()
    result = []
    for item in items:
        if item and item not in seen:
            seen.add(item)
            result.append(item)
    return result


def _sentence_list(items: list[str], fallback: str, lang: str) -> str:
    items = _unique([item for item in items if item])
    if not items:
        return fallback
    if lang == "zh":
        return "、".join(items)
    if len(items) == 1:
        return items[0]
    if len(items) == 2:
        return f"{items[0]} and {items[1]}"
    return f"{', '.join(items[:-1])}, and {items[-1]}"


def classify_rating_style(stats: dict[str, Any], lang: str = "en", tone: str = "standard") -> dict[str, str]:
    average = stats["average_score"]
    std = stats["std_score"]
    high_pct = stats["pct_scores_gte_8"]
    low_pct = stats["pct_scores_lte_5"]
    ten_count = stats["ten_count"]
    total = max(stats["total_completed"], 1)

    if std >= 2.0 and high_pct >= 25 and low_pct >= 10:
        key = "polarized"
    elif average <= 6.4 and high_pct <= 25 and ten_count <= max(1, total * 0.05):
        key = "strict"
    elif average >= 7.8 and high_pct >= 45:
        key = "generous"
    elif low_pct <= 5 and average >= 7.0:
        key = "completion_biased"
    else:
        key = "balanced"

    explanations = STYLE_ANIME_EXPLANATIONS if tone == "anime" else STYLE_EXPLANATIONS
    return {
        "key": key,
        "name": _label(key, lang, tone, STYLE_LABELS, STYLE_ANIME_LABELS),
        "explanation": explanations[key].get(lang, explanations[key]["en"]),
    }


def classify_taste_archetype(
    positive_genres: pd.DataFrame,
    positive_tags: pd.DataFrame,
    rating_style: dict[str, str],
    lang: str = "en",
    tone: str = "standard",
) -> dict[str, Any]:
    signals = pd.concat([positive_genres, positive_tags], ignore_index=True)
    if signals.empty:
        explanation = {
            "en": "There are not enough strong genre or tag signals yet, so your clearest trait is selectiveness.",
            "zh": "目前还没有足够强的类型或标签信号，所以最清楚的特征是选择性较强。",
        }
        if tone == "anime":
            explanation = {
                "en": "The taste aura is still charging, so the clearest current trait is selectiveness.",
                "zh": "口味气场还在蓄力，目前最明显的人设是：选择性很强，不轻易入坑。",
            }
        return {
            "key": "critical",
            "name": _label("critical", lang, tone, ARCHETYPE_LABELS, ARCHETYPE_ANIME_LABELS),
            "matched_terms": [],
            "explanation": explanation[lang],
        }

    archetype_scores: dict[str, float] = {}
    matched_terms: dict[str, list[str]] = {}
    for archetype_key, keywords in ARCHETYPE_KEYWORDS.items():
        score = 0.0
        matches: list[str] = []
        for _, row in signals.iterrows():
            name = str(row["name"])
            normalized = name.lower()
            if normalized in keywords or name in keywords:
                score += max(float(row.get("preference_score", 0)), 0.25)
                matches.append(name)
        archetype_scores[archetype_key] = score
        matched_terms[archetype_key] = matches

    best_key = max(archetype_scores, key=archetype_scores.get)
    if archetype_scores[best_key] <= 0:
        if rating_style.get("key") == "strict":
            matches = _names(signals, 3)
            explanation = {
                "en": "Your positive signals are specific rather than broad, and your ratings suggest you are choosy about what truly lands.",
                "zh": "你的正向信号更偏具体而非宽泛，同时评分也显示你对真正打动自己的作品比较挑剔。",
            }
            if tone == "anime":
                explanation = {
                    "en": "Your favorite flags are niche and precise. This is less generic fan energy, more selective senpai energy.",
                    "zh": "你的本命信号比较精准，不是大众向无脑入坑，更像会认真筛番的审番前辈。",
                }
            return {
                "key": "critical",
                "name": _label("critical", lang, tone, ARCHETYPE_LABELS, ARCHETYPE_ANIME_LABELS),
                "matched_terms": matches,
                "explanation": explanation[lang],
            }
        best_key = "emotional"

    matches = matched_terms.get(best_key, []) or _names(signals, 3)
    if lang == "zh":
        if tone == "anime":
            explanation = f"这个人设被这些本命信号点亮：{_sentence_list(matches[:5], '你高分区的高光属性', lang)}。"
        else:
            explanation = f"这个原型最贴近你的强正向信号：{_sentence_list(matches[:5], '你评分明显偏高的模式', lang)}。"
    else:
        if tone == "anime":
            explanation = f"This archetype lights up from these favorite flags: {_sentence_list(matches[:5], 'your high-score aura', lang)}."
        else:
            explanation = f"This best matches your strongest positive signals: {_sentence_list(matches[:5], 'your highest-rated patterns', lang)}."

    return {
        "key": best_key,
        "name": _label(best_key, lang, tone, ARCHETYPE_LABELS, ARCHETYPE_ANIME_LABELS),
        "matched_terms": matches[:5],
        "explanation": explanation,
    }


def _comparison_text(stats: dict[str, Any], source_label: str, lang: str, tone: str) -> str:
    delta = stats.get("avg_user_minus_site")
    if delta is None:
        return ""

    if lang == "zh":
        direction = "高出" if delta >= 0 else "低"
        if tone == "anime":
            return f" 你的评分平均比同作品的 {source_label} 站内均分{direction} {abs(delta):.2f} 分，说明你的个人雷达和大众弹幕并不是完全同步。"
        return f" 你的评分平均比同作品的 {source_label} 站内均分{direction} {abs(delta):.2f} 分，这能帮助区分你的个人口味和大众评价。"

    direction = "above" if delta >= 0 else "below"
    if tone == "anime":
        return f" Your scores sit {abs(delta):.2f} points {direction} the {source_label} average, so your personal radar is not just echoing the crowd."
    return (
        f" On average, your scores sit {abs(delta):.2f} points {direction} the {source_label} average for the same shows,"
        " which helps separate your personal taste from general popularity."
    )


def generate_profile_report(
    stats: dict[str, Any],
    preferences: dict[str, pd.DataFrame],
    rating_style: dict[str, str],
    archetype: dict[str, Any],
    lang: str = "en",
    source_label: str = "AniList",
    tone: str = "standard",
) -> str:
    positive_genres = _names(preferences["top_positive_genres"], 4)
    positive_tags = _names(preferences["top_positive_tags"], 5)
    negative_genres = _names(preferences["top_negative_genres"], 3)
    negative_tags = _names(preferences["top_negative_tags"], 4)

    comparison = _comparison_text(stats, source_label, lang, tone)

    if lang == "zh":
        liked = _sentence_list(positive_genres + positive_tags[:2], "少数非常具体的作品特征", lang)
        disliked = _sentence_list(negative_genres + negative_tags[:2], "不够稳定的类型或标签模式", lang)
        favorites = _sentence_list(positive_tags or positive_genres, "执行到位、情绪契合的作品元素", lang)
        blind_spots = _sentence_list(negative_genres + negative_tags, "你平时不太容易主动进入的作品区域", lang)
        next_try = _sentence_list(positive_genres[:2] + positive_tags[:2], "和你的强正向信号相邻的作品", lang)

        if tone == "anime":
            return (
                f"你的口味设定档显示，本命人设大概率是「{archetype['name']}」。"
                f"高分区最容易被 {liked} 点亮；换句话说，{favorites} 是你的属性加成。"
                f"评分人设则是「{rating_style['name']}」：{rating_style['explanation']}{comparison}\n\n"
                f"雷达另一侧，{disliked} 比较容易触发“相性微妙”。"
                "这不代表这些属性一定踩雷，只是它们需要更强的演出、更稳的角色关系，或者更漂亮的情绪回收，才有机会从路人番升格成本命番。"
                f"你的潜在盲区是 {blind_spots}；如果哪部作品能把这些元素和你的本命属性缝到一起，它就有机会打出隐藏路线。\n\n"
                f"下一部安利方向：优先找同时带有 {next_try} 的动画。"
                "别只看热度榜，重点看它有没有命中你的高分旗帜。命中了，就是可以开追的信号。"
            )

        return (
            f"你的动画口味画像更接近“{archetype['name']}”。"
            f"你更容易奖励带有 {liked} 的作品，这说明你对 {favorites} 比较敏感。"
            f"你的评分习惯属于“{rating_style['name']}”：{rating_style['explanation']}{comparison}\n\n"
            f"相对来说，你可能没那么吃 {disliked} 这一类信号。"
            "这并不代表这些元素一定不适合你，而是它们通常需要更强的执行、更好的角色关系，或者更贴近你偏好的叙事方式，才更容易打动你。"
            f"一个可能的盲区是 {blind_spots}；如果这些作品同时拥有你喜欢的核心元素，仍然可能给你惊喜。\n\n"
            f"下一步可以优先尝试同时包含 {next_try} 的动画。"
            "比起单纯追热门，你更适合找那些和自己高分模式明确重叠、并且在你重视的元素上口碑扎实的作品。"
        )

    liked = _sentence_list(positive_genres + positive_tags[:2], "a few very specific favorites", lang)
    disliked = _sentence_list(negative_genres + negative_tags[:2], "less consistent genre or tag patterns", lang)
    favorites = _sentence_list(positive_tags or positive_genres, "well-executed ideas that match your mood", lang)
    blind_spots = _sentence_list(negative_genres + negative_tags, "formats outside your usual comfort zone", lang)
    next_try = _sentence_list(positive_genres[:2] + positive_tags[:2], "anime adjacent to your strongest positive signals", lang)

    if tone == "anime":
        return (
            f"Your taste character sheet points to {archetype['name']}. "
            f"Your high-score aura lights up around {liked}; in fan-speak, {favorites} are your strongest buffs. "
            f"Your scoring role is {rating_style['name']}: {rating_style['explanation']}{comparison}\n\n"
            f"On the debuff side, {disliked} look more likely to create weak compatibility. "
            "That does not make those flags automatic skips, but they need sharper execution, stronger cast chemistry, or a cleaner emotional payoff to become a favorite route. "
            f"Your possible blind spot is {blind_spots}; a standout show there could still unlock a hidden route if it overlaps with your favorite flags.\n\n"
            f"For the next watch, look for anime carrying {next_try}. "
            "Do not just chase the hype chart; chase the shows that ping your actual high-score flags."
        )

    return (
        f"Your anime taste profile suggests that you are closest to a {archetype['name']}. "
        f"You tend to reward anime connected to {liked}, which points toward a taste for {favorites}. "
        f"Your scoring pattern reads as {rating_style['name'].lower()}: {rating_style['explanation']}{comparison}\n\n"
        f"You may be less interested in anime where the strongest signals are {disliked}. "
        f"That does not mean those elements never work for you, but they appear to need stronger execution or a better supporting cast to overcome your usual hesitation. "
        f"A possible blind spot is {blind_spots}; a standout title in one of those areas might still surprise you if it overlaps with your favorite elements.\n\n"
        f"For what to try next, look for anime that combine {next_try} with strong word-of-mouth from viewers who care about the same elements you do. "
        "Your best matches are likely shows whose appeal is not just popularity, but a clear alignment with the patterns you consistently score above your own average."
    )
