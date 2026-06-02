-- CreateEnum
CREATE TYPE "UserType" AS ENUM ('student', 'vocational', 'worker');

-- CreateEnum
CREATE TYPE "GenderPref" AS ENUM ('same_gender_only', 'opposite_gender_ok', 'mixed_ok', 'group_only_mixed');

-- CreateEnum
CREATE TYPE "LunchMode" AS ENUM ('scheduled', 'now');

-- CreateEnum
CREATE TYPE "RequestStatus" AS ENUM ('waiting', 'matched', 'cancelled', 'expired');

-- CreateEnum
CREATE TYPE "MatchStatus" AS ENUM ('pending', 'confirmed', 'ongoing', 'completed', 'cancelled');

-- CreateEnum
CREATE TYPE "PartySize" AS ENUM ('one_on_one', 'two_to_three', 'three_to_four', 'any');

-- CreateEnum
CREATE TYPE "DocType" AS ENUM ('student_id', 'license', 'mynumber', 'passport', 'residence');

-- CreateEnum
CREATE TYPE "VerificationStatus" AS ENUM ('pending', 'approved', 'rejected');

-- CreateTable
CREATE TABLE "users" (
    "id" UUID NOT NULL,
    "email" TEXT NOT NULL,
    "phone" TEXT,
    "display_name" TEXT NOT NULL,
    "age" INTEGER NOT NULL,
    "gender" TEXT NOT NULL,
    "user_type" "UserType" NOT NULL,
    "school_or_company" TEXT NOT NULL,
    "major_or_industry" TEXT NOT NULL,
    "avatar_url" TEXT,
    "trust_score" DECIMAL(3,1) NOT NULL DEFAULT 3.0,
    "is_verified" BOOLEAN NOT NULL DEFAULT false,
    "is_premium" BOOLEAN NOT NULL DEFAULT false,
    "is_active" BOOLEAN NOT NULL DEFAULT true,
    "created_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "users_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "user_profiles" (
    "id" UUID NOT NULL,
    "user_id" UUID NOT NULL,
    "hobbies" TEXT[],
    "interests" TEXT[],
    "talk_themes" TEXT[],
    "target_industries" TEXT[],
    "favorite_foods" TEXT[],
    "mbti" TEXT,
    "bio" TEXT,
    "gender_pref" "GenderPref" NOT NULL DEFAULT 'same_gender_only',
    "updated_at" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "user_profiles_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "user_verifications" (
    "id" UUID NOT NULL,
    "user_id" UUID NOT NULL,
    "doc_type" "DocType" NOT NULL,
    "doc_image_url" TEXT NOT NULL,
    "status" "VerificationStatus" NOT NULL DEFAULT 'pending',
    "reviewed_at" TIMESTAMP(3),
    "created_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "user_verifications_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "lunch_requests" (
    "id" UUID NOT NULL,
    "user_id" UUID NOT NULL,
    "mode" "LunchMode" NOT NULL,
    "date" DATE NOT NULL,
    "time_start" TIME NOT NULL,
    "time_end" TIME NOT NULL,
    "budget_min" INTEGER NOT NULL DEFAULT 500,
    "budget_max" INTEGER NOT NULL DEFAULT 1500,
    "food_genre" TEXT[],
    "party_size" "PartySize" NOT NULL DEFAULT 'one_on_one',
    "gender_pref" "GenderPref" NOT NULL,
    "latitude" DECIMAL(10,7) NOT NULL,
    "longitude" DECIMAL(10,7) NOT NULL,
    "radius_m" INTEGER NOT NULL DEFAULT 1000,
    "status" "RequestStatus" NOT NULL DEFAULT 'waiting',
    "created_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "lunch_requests_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "matches" (
    "id" UUID NOT NULL,
    "lunch_request_ids" UUID[],
    "matched_user_ids" UUID[],
    "restaurant_id" UUID,
    "meetup_time" TIMESTAMP(3),
    "meetup_location" TEXT,
    "status" "MatchStatus" NOT NULL DEFAULT 'pending',
    "chat_room_id" UUID,
    "merged_at" TIMESTAMP(3),
    "created_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "matches_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "match_attendance" (
    "id" UUID NOT NULL,
    "match_id" UUID NOT NULL,
    "user_id" UUID NOT NULL,
    "checked_in" BOOLEAN NOT NULL DEFAULT false,
    "checked_in_at" TIMESTAMP(3),
    "gps_verified" BOOLEAN NOT NULL DEFAULT false,
    "gps_lat" DECIMAL(10,7),
    "gps_lng" DECIMAL(10,7),
    "no_show" BOOLEAN NOT NULL DEFAULT false,
    "no_show_penalty_applied" BOOLEAN NOT NULL DEFAULT false,

    CONSTRAINT "match_attendance_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "restaurants" (
    "id" UUID NOT NULL,
    "name" TEXT NOT NULL,
    "genre" TEXT[],
    "budget_avg" INTEGER NOT NULL,
    "latitude" DECIMAL(10,7) NOT NULL,
    "longitude" DECIMAL(10,7) NOT NULL,
    "address" TEXT NOT NULL,
    "open_hours" JSONB NOT NULL,
    "google_place_id" TEXT NOT NULL,
    "created_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "restaurants_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "chat_rooms" (
    "id" UUID NOT NULL,
    "is_closed" BOOLEAN NOT NULL DEFAULT false,
    "created_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "chat_rooms_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "messages" (
    "id" UUID NOT NULL,
    "room_id" UUID NOT NULL,
    "sender_id" UUID NOT NULL,
    "body" TEXT NOT NULL,
    "is_deleted" BOOLEAN NOT NULL DEFAULT false,
    "created_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "messages_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "reviews" (
    "id" UUID NOT NULL,
    "match_id" UUID NOT NULL,
    "reviewer_id" UUID NOT NULL,
    "reviewee_id" UUID NOT NULL,
    "was_punctual" BOOLEAN NOT NULL,
    "joined_convo" BOOLEAN NOT NULL,
    "no_bad_behavior" BOOLEAN NOT NULL,
    "want_rematch" BOOLEAN NOT NULL,
    "score" DECIMAL(3,1) NOT NULL,
    "created_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "reviews_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "thank_messages" (
    "id" UUID NOT NULL,
    "match_id" UUID NOT NULL,
    "sender_id" UUID NOT NULL,
    "receiver_id" UUID NOT NULL,
    "body" TEXT NOT NULL,
    "created_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "thank_messages_pkey" PRIMARY KEY ("id")
);

-- CreateIndex
CREATE UNIQUE INDEX "users_email_key" ON "users"("email");

-- CreateIndex
CREATE UNIQUE INDEX "user_profiles_user_id_key" ON "user_profiles"("user_id");

-- CreateIndex
CREATE INDEX "lunch_requests_status_date_idx" ON "lunch_requests"("status", "date");

-- CreateIndex
CREATE INDEX "lunch_requests_latitude_longitude_idx" ON "lunch_requests"("latitude", "longitude");

-- CreateIndex
CREATE UNIQUE INDEX "matches_chat_room_id_key" ON "matches"("chat_room_id");

-- CreateIndex
CREATE UNIQUE INDEX "match_attendance_match_id_user_id_key" ON "match_attendance"("match_id", "user_id");

-- CreateIndex
CREATE UNIQUE INDEX "restaurants_google_place_id_key" ON "restaurants"("google_place_id");

-- CreateIndex
CREATE INDEX "messages_room_id_created_at_idx" ON "messages"("room_id", "created_at");

-- CreateIndex
CREATE UNIQUE INDEX "reviews_match_id_reviewer_id_reviewee_id_key" ON "reviews"("match_id", "reviewer_id", "reviewee_id");

-- AddForeignKey
ALTER TABLE "user_profiles" ADD CONSTRAINT "user_profiles_user_id_fkey" FOREIGN KEY ("user_id") REFERENCES "users"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "user_verifications" ADD CONSTRAINT "user_verifications_user_id_fkey" FOREIGN KEY ("user_id") REFERENCES "users"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "lunch_requests" ADD CONSTRAINT "lunch_requests_user_id_fkey" FOREIGN KEY ("user_id") REFERENCES "users"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "matches" ADD CONSTRAINT "matches_restaurant_id_fkey" FOREIGN KEY ("restaurant_id") REFERENCES "restaurants"("id") ON DELETE SET NULL ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "matches" ADD CONSTRAINT "matches_chat_room_id_fkey" FOREIGN KEY ("chat_room_id") REFERENCES "chat_rooms"("id") ON DELETE SET NULL ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "match_attendance" ADD CONSTRAINT "match_attendance_match_id_fkey" FOREIGN KEY ("match_id") REFERENCES "matches"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "match_attendance" ADD CONSTRAINT "match_attendance_user_id_fkey" FOREIGN KEY ("user_id") REFERENCES "users"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "messages" ADD CONSTRAINT "messages_room_id_fkey" FOREIGN KEY ("room_id") REFERENCES "chat_rooms"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "messages" ADD CONSTRAINT "messages_sender_id_fkey" FOREIGN KEY ("sender_id") REFERENCES "users"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "reviews" ADD CONSTRAINT "reviews_match_id_fkey" FOREIGN KEY ("match_id") REFERENCES "matches"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "reviews" ADD CONSTRAINT "reviews_reviewer_id_fkey" FOREIGN KEY ("reviewer_id") REFERENCES "users"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "reviews" ADD CONSTRAINT "reviews_reviewee_id_fkey" FOREIGN KEY ("reviewee_id") REFERENCES "users"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "thank_messages" ADD CONSTRAINT "thank_messages_match_id_fkey" FOREIGN KEY ("match_id") REFERENCES "matches"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "thank_messages" ADD CONSTRAINT "thank_messages_sender_id_fkey" FOREIGN KEY ("sender_id") REFERENCES "users"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "thank_messages" ADD CONSTRAINT "thank_messages_receiver_id_fkey" FOREIGN KEY ("receiver_id") REFERENCES "users"("id") ON DELETE RESTRICT ON UPDATE CASCADE;
