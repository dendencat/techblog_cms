# Tech Blog CMS 🚀

技術ブログのコンテンツ管理システム（CMS）です。Docker、Django、Nginx を使用した最新のウェブアプリケーションプラットフォームです。

## 🌟 特徴

- 🔒 SSL/TLS による HTTPS 対応（Let's Encrypt）
- 🐳 Docker による完全コンテナ化
- 🎯 CI/CD パイプライン（GitHub Actions）
- 🔄 自動証明書更新
- 📊 テスト自動化と品質管理

## 🛠 技術スタック

- **Web フレームワーク**: Django 4.x
- **Web サーバー**: Nginx
- **アプリケーションサーバー**: Gunicorn
- **データベース**: PostgreSQL 16
- **キャッシュ**: Redis
- **コンテナ化**: Docker & Docker Compose
- **CI/CD**: GitHub Actions


## 📁 リポジトリ構成

```text
techblog_cms/                 # 正系統の Django アプリケーション
├── templates/                # Django テンプレート
├── static/                   # CSS / JavaScript / 画像などの静的資産
├── tests/                    # pytest ベースのテスト
├── settings.py               # 環境変数を使う基本設定
└── urls.py / views.py        # URL ルーティングとビュー
docker/                       # Django コンテナのエントリポイントなど
nginx/                        # Nginx 設定
scripts/                      # 証明書更新や運用補助スクリプト
.github/workflows/            # CI/CD ワークフロー
```

静的資産は `techblog_cms/static/` に集約しています。テンプレート配下には CSS/JavaScript を配置しない方針です。

## 🚀 クイックスタート

### 前提条件

- Docker および Docker Compose がインストールされていること
- Git がインストールされていること

### インストール

```bash
# リポジトリのクローン
git clone https://github.com/dendencat/techblog_cms.git
cd techblog_cms

# 環境変数の設定
cp .env.example .env
# .env ファイルを編集して適切な値を設定

# アプリケーションの起動
docker compose up -d
```

### SSL 証明書のセットアップ

```bash
# 証明書の初期化と取得
chmod +x scripts/init-letsencrypt.sh
sudo ./scripts/init-letsencrypt.sh
```

## 🧪 テスト

```bash
# テストの実行
python -m pytest -v
```

## 🔧 開発環境

開発環境では以下の機能が利用可能です：

- ホットリロード
- デバッグモード
- 開発用サーバー（localhost:8000）

## 📦 デプロイ

GitHub Actions による自動デプロイが設定されています：

- `main` ブランチへのプッシュで自動的にテストが実行
- テスト成功後、Docker イメージを GitHub Container Registry にプッシュ
- セキュリティスキャン（Trivy）の実行

## 🔒 セキュリティ

- HTTPS 強制リダイレクト
- 最新の TLS 設定
- セキュリティヘッダーの適切な設定
- 定期的な依存関係の更新

## 📝 ライセンス

このプロジェクトは MIT ライセンスの下で公開されています。

## 🤝 コントリビューション

1. このリポジトリをフォーク
2. 新しいブランチを作成 (`git checkout -b feature/amazing-feature`)
3. 変更をコミット (`git commit -m 'Add amazing feature'`)
4. ブランチをプッシュ (`git push origin feature/amazing-feature`)
5. プルリクエストを作成

## ✨ メンテナ

- [@dendencat](https://github.com/dendencat)
