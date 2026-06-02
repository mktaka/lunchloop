# 🍱 Lunchloop — 開発環境セットアップガイド

ランチの時間をきっかけに、普段関わらない人と広く浅くつながるマッチングサービス。

## モノレポ構成

```
lunchloop/
├── apps/
│   ├── api/          # Next.js API Server (CO002)
│   └── mobile/       # Expo React Native (CO001)
├── services/
│   └── matching/     # FastAPI マッチングサービス (CO003)
├── packages/
│   ├── types/        # 共有型定義
│   └── utils/        # 共有ユーティリティ
├── prisma/
│   ├── schema.prisma # DB定義（全テーブル）
│   └── seed.ts       # 開発用シードデータ
├── infra/
│   ├── nginx/        # Nginx設定
│   └── scripts/      # DB初期化SQL
├── .github/
│   └── workflows/
│       └── ci.yml    # GitHub Actions CI/CD
└── docker-compose.yml
```

## 🚀 開始手順（5分でローカル環境が立ち上がる）

### 1. 前提条件

- Node.js 20+
- Docker Desktop
- Python 3.12+（マッチングサービスをローカルで動かす場合）

### 2. セットアップ

```bash
# リポジトリをクローン
git clone https://github.com/your-org/lunchloop.git
cd lunchloop

# 環境変数をコピー
cp .env.example .env
# .env を編集（Supabase / Google Maps キーを設定）

# 依存関係インストール
yarn install

# Docker でDBとマッチングサービスを起動
docker compose up -d

# DBマイグレーション
yarn db:migrate

# シードデータ投入（テスト用ユーザー・店舗）
yarn db:seed

# Next.js 開発サーバー起動
yarn dev:api
```

### 3. 動作確認

| サービス | URL |
|---|---|
| Next.js API | http://localhost:3000 |
| FastAPI Matching | http://localhost:8000 |
| FastAPI Docs | http://localhost:8000/docs |
| DB管理 (Adminer) | `docker compose --profile tools up -d` → http://localhost:8080 |

## 🛠️ よく使うコマンド

```bash
# 全サービス起動（Docker）
yarn docker:up

# ログ確認
yarn docker:logs

# DBリセット＋シード再投入
yarn db:reset

# Prisma Studio（DB GUI）
yarn db:studio

# マッチングサービスのテスト
cd services/matching && pytest tests/ -v

# 全サービスのテスト（CI相当）
yarn test
```

## 📊 技術スタック

| レイヤー | 技術 | 理由 |
|---|---|---|
| モバイル | Expo (React Native) | iOS/Android同時開発 |
| APIサーバー | Next.js API Routes | フロントとサーバーを一体化 |
| マッチングエンジン | FastAPI (Python) | Haversine/Jaccard計算に最適 |
| DB | PostgreSQL (RDS) | JSONBサポート・地理計算 |
| 認証 | Supabase Auth | JWT管理・メール認証を即時利用 |
| リアルタイム | Supabase Realtime | チャットのPub/Sub |
| ストレージ | AWS S3 + CloudFront | 本人確認書類・画像配信 |
| 通知 | Expo Push + AWS SNS | クロスプラットフォーム通知 |

## 🗓️ スプリント進捗

- [x] **Sprint 0**: モノレポ構成 / Docker / CI/CD
- [ ] **Sprint 1**: Supabase Auth / DBマイグレーション / 本人確認
- [ ] **Sprint 2**: マッチングコア (FN005/FN006) / チャット (FN009)
- [ ] **Sprint 3**: MVP6画面 / プッシュ通知 / 本番デプロイ

## 🏗️ 本番環境

```
EC2 (t3.small)
  └─ Nginx
      ├─ Next.js (PM2)
      └─ FastAPI (systemd)

RDS PostgreSQL (t3.micro Single-AZ)
S3 + CloudFront (本人確認書類・画像)
Supabase (Auth + Realtime)
```

月額コスト概算: **$41〜58/月**（設計書 8-3 参照）
