# AGENTS.md - AIアシスタント向けガイド

## 目的
このドキュメントは、GitHub CopilotやClaudeなどのAIアシスタントがこのレポジトリ（techblog_cms）を理解し、効果的に支援するためのガイドラインを提供します。レポジトリの構造、技術スタック、開発プロセスを明確にし、AIが適切なコード生成やアドバイスを行えるようにします。

## レポジトリ概要
techblog_cmsは、Djangoベースの技術ブログコンテンツ管理システムです。Docker Composeを使用したコンテナ化環境で、Nginxによるリバースプロキシ、PostgreSQLデータベース、Redisキャッシュ、Let's EncryptによるSSL証明書の自動管理を統合しています。プロダクションレディな構成を目指し、セキュリティとスケーラビリティを重視しています。

## 技術スタック
- **バックエンド**: Django 4.2, Python 3.11
- **データベース**: PostgreSQL
- **キャッシュ**: Redis
- **Webサーバー**: Nginx (リバースプロキシ + 静的ファイル配信)
- **コンテナ化**: Docker, Docker Compose
- **SSL証明書**: Let's Encrypt (Certbot)
- **テスト**: pytest, Django Test Framework
- **CI/CD**: GitHub Actions
- **セキュリティ**: HTTPS強制, セキュリティヘッダー, 環境変数管理
- **フロントエンド**: HTML/CSS (Tailwind CSS), JavaScript (最小限)

## プロジェクト構造
```
techblog_cms/
├── app/                          # Djangoアプリケーション
│   ├── techblog_cms/            # メインDjangoアプリ
│   │   ├── __init__.py
│   │   ├── settings.py          # Django設定（環境変数使用）
│   │   ├── urls.py              # URLマッピング
│   │   ├── views.py             # ビュー関数
│   │   ├── wsgi.py              # WSGIエントリーポイント
│   │   └── templates/           # HTMLテンプレート
│   └── requirements.txt         # Python依存関係
├── nginx/                        # Nginx設定
│   ├── conf.d/
│   │   └── default.conf         # Nginx設定ファイル
│   └── Dockerfile               # Nginxコンテナ定義
├── scripts/                      # ユーティリティスクリプト
│   ├── init-letsencrypt.sh      # SSL証明書初期化
│   └── renew-cert.sh            # SSL証明書更新
├── static/                       # 静的ファイル
├── tests/                        # テストファイル
├── docker-compose.yml            # コンテナオーケストレーション
├── Dockerfile.*                  # 各種Dockerfile
├── requirements.txt              # プロジェクト全体の依存関係
└── pytest.ini                    # pytest設定
```

## 開発ガイドライン

### コーディング標準
- **Python**: PEP 8準拠、Blackフォーマッター使用
- **Django**: Djangoベストプラクティスに従う
- **Docker**: マルチステージビルド、セキュリティスキャン（Trivy）
- **セキュリティ**: 環境変数で機密情報を管理、HTTPS強制

### 環境変数
重要な設定は環境変数で管理：
- `DEBUG`: デバッグモード（本番ではFalse）
- `SECRET_KEY`: Djangoシークレットキー
- `DATABASE_URL`: PostgreSQL接続文字列
- `REDIS_URL`: Redis接続文字列
- `ALLOWED_HOSTS`: 許可ホストリスト

### テスト
- pytestを使用したユニットテストと統合テスト
- CI/CDで自動テスト実行
- カバレッジレポート生成

## AIアシスタントへの指示

### コード生成時の考慮事項
1. **セキュリティ優先**: 機密情報は環境変数を使用。ハードコーディング禁止。
2. **コンテナ化対応**: Dockerベストプラクティスに従い、軽量イメージを作成。
3. **Djangoベストプラクティス**: ビュー関数、モデル、テンプレートの適切な分離。
4. **エラーハンドリング**: 適切な例外処理とログ出力。
5. **パフォーマンス**: データベースクエリの最適化、キャッシュの活用。

### 支援時のガイドライン
1. **新規機能追加**: 既存の構造に準拠。必要に応じてマイグレーション作成。
2. **バグ修正**: テストケースを追加し、リグレッションを防ぐ。
3. **ドキュメント更新**: コード変更時はREADME.mdやこのAGENTS.mdを更新。
4. **依存関係**: 新しいパッケージ追加時はrequirements.txtを更新。
5. **Docker設定**: 変更時はdocker-compose.ymlと関連Dockerfileを確認。

### 禁止事項
- ハードコーディングされたパスワードやAPIキー
- 非効率なデータベースクエリ
- セキュリティホール（SQLインジェクション、XSSなど）
- 不要な依存関係の追加

### 推奨ツール使用
- **コード編集**: replace_string_in_file または insert_edit_into_file
- **ファイル作成**: create_file
- **ターミナル実行**: run_in_terminal（Dockerコマンドなど）
- **テスト実行**: runTests
- **ファイル検索**: grep_search または semantic_search

## 貢献ガイド
1. developブランチからフィーチャーブランチを作成
2. 変更を実装し、テストを追加
3. プルリクエストを作成し、レビューを依頼
4. マージ後、必要に応じてドキュメント更新

## 連絡先
質問や改善提案は、GitHub IssuesまたはPull Requestsをご利用ください。

---
最終更新: 2025年8月31日
