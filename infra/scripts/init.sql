-- Lunchloop DB 初期化スクリプト
-- Docker Compose 起動時に自動実行される

-- UUID 拡張を有効化（Prisma の @default(uuid()) に必要）
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 時刻比較を日本時間に統一（本番は RDS パラメータグループで設定）
SET timezone = 'Asia/Tokyo';
