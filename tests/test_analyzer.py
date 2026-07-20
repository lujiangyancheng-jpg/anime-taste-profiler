from __future__ import annotations

import sys
import unittest
from pathlib import Path

import pandas as pd

APP_DIR = Path(__file__).resolve().parents[1] / "anime-taste-profiler"
sys.path.insert(0, str(APP_DIR))

from analyzer import compute_preference_profile, compute_rating_stats, normalize_score, score_distribution
from recommender import score_recommendations


class AnalyzerTests(unittest.TestCase):
    def test_normalize_score_handles_common_formats(self) -> None:
        self.assertEqual(normalize_score(80, "POINT_100"), 8.0)
        self.assertEqual(normalize_score(4, "POINT_5"), 8.0)
        self.assertEqual(normalize_score(3, "POINT_3"), 10.0)
        self.assertIsNone(normalize_score(0, "POINT_10"))

    def test_rating_stats_include_site_average_delta(self) -> None:
        df = pd.DataFrame(
            [
                {"score": 10.0, "average_score_10": 8.0},
                {"score": 8.0, "average_score_10": 7.0},
                {"score": 4.0, "average_score_10": 6.0},
            ]
        )

        stats = compute_rating_stats(df)

        self.assertEqual(stats["total_completed"], 3)
        self.assertAlmostEqual(stats["average_score"], 7.3333333333)
        self.assertAlmostEqual(stats["avg_user_minus_site"], 0.3333333333)
        self.assertEqual(stats["ten_count"], 1)

    def test_preference_profile_splits_positive_and_negative_signals(self) -> None:
        df = pd.DataFrame(
            [
                {"score": 10.0, "genres": ["Action"], "tags": [{"name": "Robots", "rank": 100}]},
                {"score": 8.0, "genres": ["Action"], "tags": [{"name": "Robots", "rank": 80}]},
                {"score": 4.0, "genres": ["Drama"], "tags": [{"name": "Sad", "rank": 100}]},
            ]
        )

        profile = compute_preference_profile(df)

        self.assertEqual(profile["top_positive_genres"].iloc[0]["name"], "Action")
        self.assertEqual(profile["top_negative_genres"].iloc[0]["name"], "Drama")
        self.assertEqual(profile["top_positive_tags"].iloc[0]["name"], "Robots")

    def test_score_distribution_always_uses_ten_buckets(self) -> None:
        df = pd.DataFrame([{"score": 1.0}, {"score": 8.1}, {"score": 10.0}])

        distribution = score_distribution(df)

        self.assertEqual(len(distribution), 10)
        self.assertEqual(int(distribution["count"].sum()), 3)

    def test_recommendations_explain_positive_matches(self) -> None:
        preferences = {
            "top_positive_genres": pd.DataFrame([{"name": "Action", "preference_score": 3.0}]),
            "top_negative_genres": pd.DataFrame([{"name": "Drama", "preference_score": -2.0}]),
            "top_positive_tags": pd.DataFrame([{"name": "Robots", "preference_score": 2.0}]),
            "top_negative_tags": pd.DataFrame([{"name": "Sad", "preference_score": -1.0}]),
        }
        candidates = [
            {
                "id": 1,
                "title": {"english": "Mecha Star"},
                "genres": ["Action"],
                "tags": [{"name": "Robots", "rank": 80}],
                "averageScore": 82,
                "siteUrl": "https://example.test/anime/1",
            },
            {
                "id": 2,
                "title": {"english": "Quiet Drama"},
                "genres": ["Drama"],
                "tags": [{"name": "Sad", "rank": 80}],
            },
        ]

        recommendations = score_recommendations(candidates, completed_ids=set(), preferences=preferences)

        self.assertEqual(len(recommendations), 1)
        self.assertEqual(recommendations[0]["title"], "Mecha Star")
        self.assertIn("Action", recommendations[0]["reasons"])


if __name__ == "__main__":
    unittest.main()
