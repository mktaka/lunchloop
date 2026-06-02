"""
Lunchloop Matching Service — FastAPI
設計書 AL-001〜AL-003 を実装

エンドポイント:
  POST /matching/run        → 通常マッチング（AL-001 + AL-002）
  POST /matching/run/now    → 今すぐモード（GPS即時マッチ、AL-001 + AL-002）
  POST /matching/fallback   → 不成立時3候補返却
  POST /matching/restaurants → 店舗スコアリング（AL-003）
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import math
from typing import Optional
from pydantic import BaseModel

app = FastAPI(
    title="Lunchloop Matching Service",
    version="0.1.0",
    description="AIスコアリング・GPS即時マッチング・店舗提案",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─────────────────────────────────────────────
# スキーマ定義
# ─────────────────────────────────────────────

class LunchRequest(BaseModel):
    id: str
    user_id: str
    mode: str                    # "scheduled" | "now"
    user_type: str               # "student" | "vocational" | "worker"
    gender: str
    gender_pref: str
    time_start: str              # "HH:MM"
    time_end: str
    budget_min: int
    budget_max: int
    food_genre: list[str]
    party_size: str
    latitude: float
    longitude: float
    radius_m: int
    interests: list[str]
    hobbies: list[str]
    talk_themes: list[str]
    target_industries: list[str]
    trust_score: float           # 0.0〜5.0
    no_show_recent: bool         # 直近3回以内にno_showあり

class MatchRequest(BaseModel):
    target: LunchRequest
    candidates: list[LunchRequest]

class FallbackRequest(BaseModel):
    target: LunchRequest
    rejected: list[LunchRequest]  # ハードフィルター不通過のリクエスト

class GpsCoord(BaseModel):
    user_id: str
    latitude: float
    longitude: float

class Restaurant(BaseModel):
    id: str
    name: str
    genre: list[str]
    budget_avg: int
    latitude: float
    longitude: float
    google_place_id: str

class RestaurantSuggestRequest(BaseModel):
    users: list[GpsCoord]
    budget_min: int
    budget_max: int
    food_genre: list[str]
    candidates: list[Restaurant]
    walk_times: dict[str, dict[str, int]]  # {user_id: {restaurant_id: seconds}}


# ─────────────────────────────────────────────
# ヘルスチェック
# ─────────────────────────────────────────────

@app.get("/health")
def health():
    return {"status": "ok", "service": "matching"}


# ─────────────────────────────────────────────
# AL-001: ハードフィルター
# ─────────────────────────────────────────────

def hard_filter(target: LunchRequest, candidate: LunchRequest) -> tuple[bool, str]:
    """
    条件不一致を完全除外。
    Returns: (通過したか, 除外理由)
    """
    # 1. 属性一致（大学生↔大学生など）
    if target.user_type != candidate.user_type:
        return False, "user_type_mismatch"

    # 2. 本人確認（is_verified は呼び出し元で確認済み想定）

    # 3. 時間帯重複チェック
    if not time_overlap(target.time_start, target.time_end,
                        candidate.time_start, candidate.time_end):
        return False, "no_time_overlap"

    # 4. GPS距離チェック
    dist_m = haversine_m(target.latitude, target.longitude,
                         candidate.latitude, candidate.longitude)
    max_radius = max(target.radius_m, candidate.radius_m)
    if dist_m > max_radius:
        return False, "too_far"

    # 5. 性別条件の矛盾チェック
    if not gender_compat(target.gender, target.gender_pref,
                         candidate.gender, candidate.gender_pref):
        return False, "gender_pref_conflict"

    # 6. ノーショーフラグ
    if candidate.no_show_recent:
        return False, "no_show_flag"

    return True, "ok"


def gender_compat(g_a: str, pref_a: str, g_b: str, pref_b: str) -> bool:
    """性別条件の矛盾チェック（設計書 3-3 参照）"""
    same_gender = g_a == g_b

    def allows(pref: str, same: bool) -> bool:
        if pref == "same_gender_only":
            return same
        if pref == "opposite_gender_ok":
            return True
        if pref == "mixed_ok":
            return True
        if pref == "group_only_mixed":
            return True  # 人数チェックは上位で行う
        return False

    return allows(pref_a, same_gender) and allows(pref_b, same_gender)


def time_overlap(s1: str, e1: str, s2: str, e2: str) -> bool:
    """時間帯重複チェック"""
    def to_min(t: str) -> int:
        h, m = map(int, t.split(":"))
        return h * 60 + m

    return to_min(s1) < to_min(e2) and to_min(s2) < to_min(e1)


# ─────────────────────────────────────────────
# AL-002: スコアリング
# ─────────────────────────────────────────────

def score(target: LunchRequest, candidate: LunchRequest) -> dict:
    """
    重み付きスコアリング（設計書 AL-002 準拠）
    """
    # interest_score: Jaccard係数（興味・趣味・テーマ・業界タグの合算）
    tags_a = set(target.interests + target.hobbies + target.talk_themes + target.target_industries)
    tags_b = set(candidate.interests + candidate.hobbies + candidate.talk_themes + candidate.target_industries)
    if tags_a or tags_b:
        jaccard = len(tags_a & tags_b) / len(tags_a | tags_b)
    else:
        jaccard = 0.0

    # budget_score: 予算帯の重複割合
    overlap_min = max(target.budget_min, candidate.budget_min)
    overlap_max = min(target.budget_max, candidate.budget_max)
    if overlap_max > overlap_min:
        denom = max(target.budget_max, candidate.budget_max)
        budget_sc = (overlap_max - overlap_min) / denom if denom > 0 else 0
    else:
        budget_sc = 0.0

    # time_score: 重複時間 / 短い方の時間
    def to_min(t: str) -> int:
        h, m = map(int, t.split(":"))
        return h * 60 + m

    overlap_start = max(to_min(target.time_start), to_min(candidate.time_start))
    overlap_end = min(to_min(target.time_end), to_min(candidate.time_end))
    overlap_min_t = max(0, overlap_end - overlap_start)
    dur_a = to_min(target.time_end) - to_min(target.time_start)
    dur_b = to_min(candidate.time_end) - to_min(candidate.time_start)
    short_dur = min(dur_a, dur_b)
    time_sc = overlap_min_t / short_dur if short_dur > 0 else 0.0

    # distance_score: Haversine距離
    dist_km = haversine_m(target.latitude, target.longitude,
                          candidate.latitude, candidate.longitude) / 1000
    max_r_km = max(target.radius_m, candidate.radius_m) / 1000
    dist_sc = max(0.0, 1 - dist_km / max_r_km) if max_r_km > 0 else 0.0

    # trust_score: 0〜5 を 0〜1 に正規化
    trust_sc = candidate.trust_score / 5.0

    # 重み付き合計（設計書 AL-002）
    total = (
        jaccard  * 0.35 +
        budget_sc * 0.20 +
        time_sc   * 0.15 +
        dist_sc   * 0.15 +
        trust_sc  * 0.15
    )

    return {
        "interest_score":  round(jaccard, 3),
        "budget_score":    round(budget_sc, 3),
        "time_score":      round(time_sc, 3),
        "distance_score":  round(dist_sc, 3),
        "trust_score":     round(trust_sc, 3),
        "total":           round(total, 3),
    }


# ─────────────────────────────────────────────
# AL-005: マッチ理由自動生成
# ─────────────────────────────────────────────

def match_reasons(target: LunchRequest, candidate: LunchRequest, sc: dict) -> list[str]:
    """設計書 AL-005 準拠。最大4件返す"""
    reasons = []

    # 共通タグ（最大2件）
    tags_a = set(target.interests + target.hobbies + target.talk_themes)
    tags_b = set(candidate.interests + candidate.hobbies + candidate.talk_themes)
    common = list(tags_a & tags_b)[:2]
    for tag in common:
        reasons.append(f"「{tag}」に興味がある")

    # 予算帯が近い
    if sc["budget_score"] > 0.8:
        reasons.append("予算帯が近い")

    # 距離 < 300m
    dist_m = haversine_m(target.latitude, target.longitude,
                         candidate.latitude, candidate.longitude)
    if dist_m < 300:
        reasons.append("すぐ近くにいる")

    # 信頼スコア高い（フェーズ2以降実績値）
    if candidate.trust_score >= 4.0:
        reasons.append("信頼スコアが高い")

    return reasons[:4]


# ─────────────────────────────────────────────
# エンドポイント: POST /matching/run
# ─────────────────────────────────────────────

@app.post("/matching/run")
def run_matching(req: MatchRequest):
    """
    通常マッチング（事前予約モード）
    AL-001 → AL-002 → 上位1名選出
    """
    results = []

    for candidate in req.candidates:
        if candidate.user_id == req.target.user_id:
            continue

        passed, reason = hard_filter(req.target, candidate)
        if not passed:
            continue

        sc = score(req.target, candidate)
        reasons = match_reasons(req.target, candidate, sc)

        results.append({
            "user_id": candidate.user_id,
            "request_id": candidate.id,
            "score": sc,
            "match_reasons": reasons,
        })

    # スコア降順でソート
    results.sort(key=lambda x: x["score"]["total"], reverse=True)

    if not results:
        return {"matched": False, "candidates": []}

    # 上位1名をマッチング成立
    best = results[0]
    return {
        "matched": True,
        "match": best,
        "fallback_candidates": results[1:3],  # 不成立時の予備
    }


# ─────────────────────────────────────────────
# エンドポイント: POST /matching/run/now
# 今すぐモード: GPS 400m固定
# ─────────────────────────────────────────────

@app.post("/matching/run/now")
def run_now_matching(req: MatchRequest):
    """
    今すぐモード（GPS即時マッチ）
    radius_m は 400m 固定で再チェック
    """
    GPS_LIMIT_M = 400

    results = []
    for candidate in req.candidates:
        if candidate.user_id == req.target.user_id:
            continue

        dist_m = haversine_m(req.target.latitude, req.target.longitude,
                             candidate.latitude, candidate.longitude)
        if dist_m > GPS_LIMIT_M:
            continue

        passed, reason = hard_filter(req.target, candidate)
        if not passed:
            continue

        sc = score(req.target, candidate)
        reasons = match_reasons(req.target, candidate, sc)

        results.append({
            "user_id": candidate.user_id,
            "request_id": candidate.id,
            "distance_m": round(dist_m),
            "score": sc,
            "match_reasons": reasons,
        })

    results.sort(key=lambda x: x["score"]["total"], reverse=True)

    if not results:
        return {"matched": False, "candidates": []}

    return {
        "matched": True,
        "match": results[0],
        "fallback_candidates": results[1:3],
    }


# ─────────────────────────────────────────────
# エンドポイント: POST /matching/restaurants
# AL-003: 店舗スコアリング
# ─────────────────────────────────────────────

@app.post("/matching/restaurants")
def suggest_restaurants(req: RestaurantSuggestRequest):
    """
    双方の徒歩時間合計が最小の店舗 TOP3 を返す
    AL-003 準拠
    """
    # 1. 重心算出（全ユーザーの座標の算術平均）
    centroid_lat = sum(u.latitude for u in req.users) / len(req.users)
    centroid_lng = sum(u.longitude for u in req.users) / len(req.users)

    scored = []
    for r in req.candidates:
        # 3. 全ユーザーの徒歩時間合計
        total_walk = sum(
            req.walk_times.get(u.user_id, {}).get(r.id, 9999)
            for u in req.users
        )

        # 4. 予算一致ボーナス
        budget_bonus = 0
        if req.budget_min <= r.budget_avg <= req.budget_max:
            budget_bonus = 300  # 秒換算ボーナス

        # ジャンル一致ボーナス
        genre_bonus = 0
        if any(g in r.genre for g in req.food_genre):
            genre_bonus = 200

        # score = -(徒歩時間合計) + ボーナス（高いほど良い）
        sc = -total_walk + budget_bonus + genre_bonus

        # 重心からの距離（参考値）
        dist_from_center = haversine_m(centroid_lat, centroid_lng,
                                       r.latitude, r.longitude)

        scored.append({
            "restaurant": r.model_dump(),
            "score": sc,
            "total_walk_seconds": total_walk,
            "distance_from_center_m": round(dist_from_center),
        })

    scored.sort(key=lambda x: x["score"], reverse=True)

    return {
        "centroid": {"lat": centroid_lat, "lng": centroid_lng},
        "top3": scored[:3],
    }


# ─────────────────────────────────────────────
# ユーティリティ: Haversine 公式
# ─────────────────────────────────────────────

def haversine_m(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """2点間の距離（メートル）を Haversine 公式で計算"""
    R = 6_371_000  # 地球半径（m）
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lng2 - lng1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
