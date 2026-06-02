/**
 * Lunchloop シードスクリプト
 * 開発用テストデータを自動生成
 * 実行: yarn db:seed
 */

import { PrismaClient, UserType, GenderPref, LunchMode, PartySize, DocType, VerificationStatus } from "@prisma/client";

const prisma = new PrismaClient();

async function main() {
  console.log("🌱 Seeding database...");

  // ─── ユーザー作成（3属性×各3人）────────────────
  const users = await Promise.all([
    // 大学生
    createUser("田中 葵", "student", "早稲田大学", "経済学部", "female"),
    createUser("佐藤 蓮", "student", "慶應義塾大学", "理工学部", "male"),
    createUser("鈴木 莉子", "student", "東京大学", "文学部", "female"),
    // 社会人
    createUser("山田 健太", "worker", "DeNA", "エンジニア", "male"),
    createUser("小林 あかり", "worker", "メルカリ", "デザイナー", "female"),
    createUser("中村 翔", "worker", "SmartHR", "営業", "male"),
    // 専門学生
    createUser("伊藤 ゆい", "vocational", "東京デザイン専門学校", "グラフィックデザイン", "female"),
    createUser("渡辺 大輝", "vocational", "HAL東京", "ゲームプログラミング", "male"),
  ]);

  // ─── プロフィール作成 ────────────────────────────
  await prisma.userProfile.createMany({
    data: [
      {
        user_id: users[0].id,
        hobbies: ["カフェ巡り", "読書"],
        interests: ["起業", "マーケティング"],
        talk_themes: ["キャリア", "留学"],
        target_industries: ["IT", "コンサル"],
        favorite_foods: ["カフェ", "イタリアン"],
        bio: "新しい出会いを楽しみにしています！",
        gender_pref: GenderPref.same_gender_only,
      },
      {
        user_id: users[1].id,
        hobbies: ["プログラミング", "筋トレ"],
        interests: ["AI", "スタートアップ"],
        talk_themes: ["エンジニア転職", "副業"],
        target_industries: ["IT", "FinTech"],
        favorite_foods: ["ラーメン", "定食"],
        bio: "エンジニア志望。技術の話大好きです",
        gender_pref: GenderPref.opposite_gender_ok,
      },
      {
        user_id: users[3].id,
        hobbies: ["登山", "料理"],
        interests: ["AI", "Web3"],
        talk_themes: ["副業", "フリーランス"],
        target_industries: ["IT", "スタートアップ"],
        favorite_foods: ["ラーメン", "焼肉"],
        bio: "DeNAでサーバーサイド書いてます",
        gender_pref: GenderPref.opposite_gender_ok,
      },
      {
        user_id: users[4].id,
        hobbies: ["映画鑑賞", "ヨガ"],
        interests: ["UX", "プロダクト"],
        talk_themes: ["デザイン思考", "女性のキャリア"],
        target_industries: ["IT", "ブランディング"],
        favorite_foods: ["カフェ", "和食"],
        bio: "メルカリでプロダクトデザイン担当",
        gender_pref: GenderPref.same_gender_only,
      },
    ],
  });

  // ─── 本人確認（全員 approved）───────────────────
  await prisma.userVerification.createMany({
    data: users.map((u) => ({
      user_id: u.id,
      doc_type: DocType.student_id,
      doc_image_url: `https://s3.ap-northeast-1.amazonaws.com/lunchloop-dev/verifications/${u.id}/doc.jpg`,
      status: VerificationStatus.approved,
      reviewed_at: new Date(),
    })),
  });

  // is_verified を true に更新
  await prisma.user.updateMany({
    data: { is_verified: true },
  });

  // ─── ランチリクエスト（今日のマッチングアワー）──
  const today = new Date();
  today.setHours(0, 0, 0, 0);

  await prisma.lunchRequest.createMany({
    data: [
      {
        user_id: users[0].id,
        mode: LunchMode.scheduled,
        date: today,
        time_start: new Date("1970-01-01T12:00:00"),
        time_end: new Date("1970-01-01T13:00:00"),
        budget_min: 500,
        budget_max: 1000,
        food_genre: ["カフェ", "イタリアン"],
        party_size: PartySize.one_on_one,
        gender_pref: GenderPref.same_gender_only,
        latitude: 35.6762,    // 上野エリア
        longitude: 139.6503,
        radius_m: 1000,
        status: "waiting",
      },
      {
        user_id: users[3].id,
        mode: LunchMode.now,
        date: today,
        time_start: new Date("1970-01-01T12:00:00"),
        time_end: new Date("1970-01-01T13:30:00"),
        budget_min: 800,
        budget_max: 1500,
        food_genre: ["ラーメン", "定食"],
        party_size: PartySize.one_on_one,
        gender_pref: GenderPref.opposite_gender_ok,
        latitude: 35.6764,    // ほぼ同地点（即時マッチ対象）
        longitude: 139.6505,
        radius_m: 400,
        status: "waiting",
      },
    ],
  });

  // ─── テスト用レストラン ──────────────────────────
  await prisma.restaurant.createMany({
    data: [
      {
        name: "上野 焼肉 大将",
        genre: ["焼肉"],
        budget_avg: 2000,
        latitude: 35.6761,
        longitude: 139.6502,
        address: "東京都台東区上野3-1-1",
        open_hours: { mon: "11:00-23:00", tue: "11:00-23:00", wed: "11:00-23:00", thu: "11:00-23:00", fri: "11:00-23:00", sat: "11:00-23:00", sun: "11:00-23:00" },
        google_place_id: "ChIJtest001",
      },
      {
        name: "カフェ・ド・クレール",
        genre: ["カフェ", "イタリアン"],
        budget_avg: 900,
        latitude: 35.6760,
        longitude: 139.6504,
        address: "東京都台東区上野2-5-3",
        open_hours: { mon: "08:00-20:00", tue: "08:00-20:00", wed: "08:00-20:00", thu: "08:00-20:00", fri: "08:00-20:00", sat: "10:00-18:00", sun: "休" },
        google_place_id: "ChIJtest002",
      },
      {
        name: "麺屋 一心",
        genre: ["ラーメン"],
        budget_avg: 1000,
        latitude: 35.6763,
        longitude: 139.6501,
        address: "東京都台東区上野4-2-7",
        open_hours: { mon: "11:00-15:00", tue: "11:00-15:00", wed: "11:00-15:00", thu: "11:00-15:00", fri: "11:00-15:00", sat: "11:00-15:00", sun: "休" },
        google_place_id: "ChIJtest003",
      },
    ],
  });

  console.log("✅ Seed complete!");
  console.log(`   👤 Users: ${users.length}`);
  console.log("   🍱 LunchRequests: 2");
  console.log("   🏪 Restaurants: 3");
}

async function createUser(
  name: string,
  type: string,
  org: string,
  dept: string,
  gender: string,
) {
  return prisma.user.create({
    data: {
      display_name: name,
      email: `${name.replace(/\s/g, "").toLowerCase()}@lunchloop.dev`,
      age: type === "student" ? 21 : type === "vocational" ? 20 : 28,
      gender,
      user_type: type as UserType,
      school_or_company: org,
      major_or_industry: dept,
      avatar_url: null,
      trust_score: 3.0,
    },
  });
}

main()
  .catch((e) => {
    console.error("❌ Seed failed:", e);
    process.exit(1);
  })
  .finally(() => prisma.$disconnect());
