---
description: TechBlog CMS repository-wide Copilot instructions
mode: agent
tools: ['extensions', 'codebase', 'usages', 'vscodeAPI', 'problems', 'changes', 'testFailure', 'terminalSelection', 'terminalLastCommand', 'openSimpleBrowser', 'fetch', 'findTestFiles', 'searchResults', 'githubRepo', 'getPythonEnvironmentInfo', 'getPythonExecutableCommand', 'installPythonPackage', 'configurePythonEnvironment', 'runTests', 'runCommands', 'runTasks', 'editFiles', 'runNotebooks', 'search']
model: Grok Code Fast 1 (Preview)
---
# .github/copilot-instructions.md

> Copilot Chat / Code Review / Coding Agent が参照する共通ルール。断定形・簡潔。
> このリポジトリは Django 4.2 + Python 3.11 の技術ブログ CMS。Docker Compose で Nginx/PG/Redis を統合。

## Project facts
- ランタイム: Python 3.11 / Django 4.2
- Web/WSGI: Gunicorn / WSGI (`techblog_cms.wsgi`)
- Webサーバ: Nginx（HTTPS, セキュリティヘッダー）
- DB/キャッシュ: PostgreSQL 16 / Redis 7
- テスト: pytest, pytest-django, Playwright（E2E）
- コンテナ: Docker, Docker Compose
- 静的/メディア: Nginx 配信（Django は DEBUG 時のみ）

## How to build, test, run
- 推奨: Docker Compose
  - 起動: `docker compose up -d`
  - 初期化は `docker/entrypoint.sh` が担当（migrate, collectstatic）
  - Djangoコマンド: `docker compose exec django python manage.py <command>`
- ローカル（必要時）
  - 依存: `pip install -r requirements.txt`
  - DB設定: `.env.example` を `.env` にコピーし値を設定
  - マイグレーション: `python manage.py migrate`
  - 起動: `gunicorn --config gunicorn.conf.py techblog_cms.wsgi:application`
- テスト
  - ユニット: `pytest -v`
  - E2E: Playwright 依存をインストール後、サーバ起動状態で実行

## Repository structure（前提）
- `techblog_cms/`: 主要 Django アプリ（正系統）
- `app/techblog_cms/`: 重複ツリー。新規コードは作らない。段階的に統合・撤去。
- `nginx/`, `docker/`, `scripts/`: インフラ/運用
- `_note/`: レビュー/要件/ToDo ドキュメント
- 静的資産は `techblog_cms/static/` のみを使用。`templates/static/` は使用しない。

## Coding conventions
- Python: PEP 8。Black を想定。型ヒントを優先。
- Django: CSRF を無効化しない。`@csrf_exempt` は避け、AJAX はトークン送付。
- モデル: `get_absolute_url` は `urls.py` の name と一致させる。
- スラグ生成はモデルで一元化。ビューの重複ロジックは追加しない。
- ログ: 資格情報や秘密は出力しない。`print` ではなくロギングを使用。
- 静的配信: 本番は Nginx に委譲。Django の `static()` 追加は DEBUG 条件下のみ。

## Security & secrets
- 秘密情報は環境変数で管理。ソースに直書きしない。
- `.env` はコミットしない。共有は `.env.example` にキーのみ追加。
- `SECRET_KEY` 未設定で本番起動させない設計を前提。
- Markdown 生成はサニタイズ必須（許可タグ/属性限定）。

## Expectations in CI / PR
- CI で pytest が通ること。必要に応じて `collectstatic` も検証。
- 1 PR = 1 目的。機能追加と大規模リファクタを混在させない。
- 依存追加時は `requirements.txt` を更新し、採用理由と影響範囲を記載。
- 仕様/セキュリティに関わる変更は `_note/requirements.md` / `_note/todo.md` を更新。

## Preferences for Copilot
- 既存スタイル/構成に沿い、小さく安全に提案・変更する。
- 変更はテスト追加/更新を伴う提案とする（pytest/Playwright）。
- インフラ変更は Docker Compose/Nginx の現行設計に合わせる。
- 既知の重複ツリー（`app/techblog_cms`）には新規ファイルを作らない。
- ファイル参照はパスと行番号を明示する。

---

### よくある作業例（補助）
- 「API/ビュー追加」: URL name 設計 → ビュー実装 → テンプレ/Serializer → 単体テスト → E2E 影響確認。
- 「Markdown処理強化」: サニタイズ導入 → 危険タグ除去テスト → 本番/プレビューの同一パイプライン化。
- 「CSRF関連不具合」: フロントのトークン付与 → ミドルウェア順番確認 → 403 ハンドリング → テスト整備。

参照: `AGENTS.md`（AIアシスタント向けガイド）

