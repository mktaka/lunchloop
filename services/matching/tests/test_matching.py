"""
マッチングアルゴリズムのユニットテスト
AL-001 ハードフィルター / AL-002 スコアリング / AL-003 店舗提案
"""

import pytest
from app.main import hard_filter, score, match_reasons, haversine_m, LunchRequest

# ─────────────────────────────────────────────
# テスト用フィクスチャ
# ─────────────────────────────────────────────

def make_request(**overrides) -> LunchRequest:
    defaults = dict(
        id="req-001",
        user_id="user-001",
        mode="scheduled",
        user_type="student",
        gender="female",
        gender_pref="same_gender_only",
        time_start="12:00",
        time_end="13:00",
        budget_min=500,
        budget_max=1000,
        food_genre=["カフェ"],
        party_size="one_on_one",
        latitude=35.6762,
        longitude=139.6503,
        radius_m=1000,
        interests=["起業", "AI"],
        hobbies=["カフェ巡り"],
        talk_themes=["キャリア"],
        target_industries=["IT"],
        trust_score=3.0,
        no_show_recent=False,
    )
    defaults.update(overrides)
    return LunchRequest(**defaults)


# ─────────────────────────────────────────────
# AL-001: ハードフィルター
# ─────────────────────────────────────────────

class TestHardFilter:
    def test_pass_same_type_same_gender(self):
        a = make_request(user_id="u1", gender="female", gender_pref="same_gender_only")
        b = make_request(user_id="u2", gender="female", gender_pref="same_gender_only")
        passed, reason = hard_filter(a, b)
        assert passed is True

    def test_fail_different_user_type(self):
        a = make_request(user_id="u1", user_type="student")
        b = make_request(user_id="u2", user_type="worker")
        passed, reason = hard_filter(a, b)
        assert passed is False
        assert reason == "user_type_mismatch"

    def test_fail_no_time_overlap(self):
        a = make_request(user_id="u1", time_start="11:00", time_end="12:00")
        b = make_request(user_id="u2", time_start="13:00", time_end="14:00")
        passed, reason = hard_filter(a, b)
        assert passed is False
        assert reason == "no_time_overlap"

    def test_fail_too_far(self):
        a = make_request(user_id="u1", latitude=35.6762, longitude=139.6503, radius_m=400)
        b = make_request(user_id="u2", latitude=35.7000, longitude=139.7000, radius_m=400)
        passed, reason = hard_filter(a, b)
        assert passed is False
        assert reason == "too_far"

    def test_fail_gender_conflict(self):
        a = make_request(user_id="u1", gender="female", gender_pref="same_gender_only")
        b = make_request(user_id="u2", gender="male", gender_pref="opposite_gender_ok")
        passed, reason = hard_filter(a, b)
        assert passed is False
        assert reason == "gender_pref_conflict"

    def test_fail_no_show_flag(self):
        a = make_request(user_id="u1")
        b = make_request(user_id="u2", no_show_recent=True)
        passed, reason = hard_filter(a, b)
        assert passed is False
        assert reason == "no_show_flag"


# ─────────────────────────────────────────────
# AL-002: スコアリング
# ─────────────────────────────────────────────

class TestScoring:
    def test_perfect_match_high_score(self):
        a = make_request(user_id="u1", interests=["AI", "起業"], hobbies=["カフェ巡り"],
                         budget_min=800, budget_max=1200, trust_score=5.0)
        b = make_request(user_id="u2", interests=["AI", "起業"], hobbies=["カフェ巡り"],
                         budget_min=800, budget_max=1200, trust_score=5.0)
        sc = score(a, b)
        assert sc["total"] > 0.8
        assert sc["interest_score"] == 1.0  # 完全一致

    def test_no_common_interests_low_score(self):
        a = make_request(user_id="u1", interests=["AI"], hobbies=[], talk_themes=[], target_industries=[])
        b = make_request(user_id="u2", interests=["料理"], hobbies=[], talk_themes=[], target_industries=[])
        sc = score(a, b)
        assert sc["interest_score"] == 0.0

    def test_budget_no_overlap(self):
        a = make_request(user_id="u1", budget_min=2000, budget_max=3000)
        b = make_request(user_id="u2", budget_min=500, budget_max=1000)
        sc = score(a, b)
        assert sc["budget_score"] == 0.0

    def test_score_keys_present(self):
        a = make_request(user_id="u1")
        b = make_request(user_id="u2", gender="female")
        sc = score(a, b)
        assert all(k in sc for k in ["interest_score", "budget_score", "time_score",
                                      "distance_score", "trust_score", "total"])


# ─────────────────────────────────────────────
# Haversine 距離計算
# ─────────────────────────────────────────────

class TestHaversine:
    def test_same_point_zero(self):
        d = haversine_m(35.6762, 139.6503, 35.6762, 139.6503)
        assert d == pytest.approx(0.0, abs=0.1)

    def test_known_distance(self):
        # 上野〜秋葉原 約1.5km
        d = haversine_m(35.7136, 139.7775, 35.6984, 139.7731)
        assert 1400 < d < 1700

    def test_400m_threshold(self):
        # 約400m離れた2点
        d = haversine_m(35.6762, 139.6503, 35.6762, 139.6548)
        assert d == pytest.approx(380, abs=50)
