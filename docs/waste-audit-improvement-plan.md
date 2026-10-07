# 無駄と思える箇所の洗い出しと改善計画

作成日: 2026-07-08  
対象: `techblog_cms` リポジトリ全体

## 1. エグゼクティブサマリー

現状のリポジトリは Django アプリケーションとして動作する主要コードを持つ一方で、過去の試行錯誤やデバッグ作業の痕跡が同居しており、運用・保守・CI の観点で「無駄」または「混乱の原因」になり得る箇所が複数あります。特に影響が大きいのは以下です。

- Django プロジェクトが `techblog_cms/` と `app/techblog_cms/` に二重化しており、どちらを正とするかが曖昧。
- Nginx/Docker 関連ファイルが複数系統あり、実際に使う設定と古い設定が混在。
- テスト・デバッグ生成物と思われる HTML、Cookie、Playwright スクリプトがルート直下に残存。
- 本番起動時に `makemigrations` を実行するなど、コンテナ起動のたびに不要・危険な作業が走る。
- 依存関係に未使用または用途が曖昧なパッケージが含まれ、ビルド時間・脆弱性表面・レビュー負荷を増やしている。

このレポートでは、削減対象を「即時削除候補」「統合・整理候補」「設計見直し候補」に分類し、段階的な改善計画を提示します。

## 2. 調査観点と判定基準

以下の観点で「無駄」を判定しました。

1. **重複**: 同じ責務のファイル・設定・アプリケーションが複数存在する。
2. **未使用・孤立**: 実行経路、README、Compose、CI から参照されていない可能性が高い。
3. **運用コスト増**: 起動時間、ビルド時間、セキュリティスキャン対象、レビュー対象を不必要に増やす。
4. **安全性低下**: 本番環境で不要な処理やデバッグ設定が残り、障害・情報漏えい・設定ミスにつながる。
5. **認知負荷**: 新規参加者が「どれが正か」を判断しづらい。

## 3. 詳細な洗い出し

### 3.1 Django アプリケーションの二重構造

#### 対象

- `techblog_cms/`
- `app/techblog_cms/`
- `app/Dockerfile`
- `app/requirements.txt`

#### 問題

ルート直下の `techblog_cms/` が現在の主要アプリとして使われている一方、`app/techblog_cms/` にも別の Django 設定・URL・モデル・ビューが残っています。`docker-compose.yml` の Django サービスはルートをビルドコンテキストにし、`Dockerfile.django` を使い、`DJANGO_SETTINGS_MODULE=techblog_cms.settings` を指定しています。したがって、`app/` 配下は旧構成または別案の残骸である可能性が高いです。

#### 無駄・リスク

- 修正対象を間違えるリスクが高い。
- 同名モジュールが存在するため、`PYTHONPATH` や作業ディレクトリ次第で別実装を読んでしまう可能性がある。
- `app/requirements.txt` はバージョン固定がなく、利用されると再現性が低い。
- ドキュメント上の構成説明とも現在の実態がずれている。

#### 改善方針

1. 正式なアプリ配置を `techblog_cms/` に一本化する。
2. `app/` 配下が不要であれば削除する。
3. もし移行履歴として残す必要がある場合は、`archive/` ではなく Git 履歴に任せる。
4. README と AGENTS.md の構成図を実態に合わせて更新する。

#### 優先度

高。最も認知負荷が高く、今後の変更ミスにつながりやすいです。

---

### 3.2 Dockerfile と Nginx 設定の重複

#### 対象

- `Dockerfile`
- `Dockerfile.django`
- `Dockerfile.nginx`
- `Dockerfile.nginx.static`
- `nginx/Dockerfile`
- `nginx.conf`
- `nginx/nginx.conf`
- `nginx/conf.d/default.conf`

#### 問題

Dockerfile と Nginx 設定が複数あります。`docker-compose.yml` では Django に `Dockerfile.django`、Nginx に `Dockerfile.nginx` が指定されています。一方、ルートの `Dockerfile` は `FROM` がなく単体 Dockerfile としては成立しない断片に見えます。また、ルートの `nginx.conf` は `yourdomain.com` や自己署名証明書パスを含む汎用サンプルで、現在の `nginx/conf.d/default.conf` と役割が重複しています。

#### 無駄・リスク

- 実際に使うファイルが判別しづらい。
- 古い Nginx 設定を誤ってデプロイすると証明書パス・ドメイン・セキュリティヘッダーがずれる。
- 複数の Dockerfile があることで CI/CD とローカル起動の差異が生まれやすい。
- 使われない Dockerfile も脆弱性レビューや保守判断の対象になり、レビュー工数が増える。

#### 改善方針

1. Compose と CI で使う Dockerfile を明示的に棚卸しする。
2. 使用中: `Dockerfile.django`, `Dockerfile.nginx` のみに絞る。
3. 不要な `Dockerfile`, `Dockerfile.nginx.static`, `nginx/Dockerfile`, `nginx.conf`, `nginx/nginx.conf` は削除候補にする。
4. 代替用途がある場合は `docs/deployment.md` に用途を明記し、ファイル名も `Dockerfile.<purpose>` に統一する。

#### 優先度

高。デプロイ設定の混乱は本番障害に直結します。

---

### 3.3 ルート直下のデバッグ・一時生成物

#### 対象

- `cookies.txt`
- `login_response.html`
- `login_response2.html`
- `csrf_debug_playwright.py`
- `test_rest_api.py`
- `SimpleWebServer.ps1`
- `static/index.html`

#### 問題

ログインレスポンス HTML、Cookie ファイル、CSRF デバッグ用 Playwright スクリプトなど、調査時の一時成果物と思われるファイルがルート直下に残っています。テストとして継続利用するなら `techblog_cms/tests/` に整理すべきですが、現状は命名・配置から一時ファイルに見えます。

#### 無駄・リスク

- Cookie やログインレスポンスに機密・セッション情報が混入するリスクがある。
- ルート直下のファイル数が増え、主要な設定ファイルを探しづらくする。
- `test_rest_api.py` のように pytest が拾う可能性のある名前のファイルがルートにあり、意図しないテスト実行や失敗要因になり得る。
- `static/index.html` は Django のテンプレートや Nginx の静的配信設計と責務が曖昧。

#### 改善方針

1. 一時生成物は即時削除する。
2. 必要な検証スクリプトは `scripts/` または `techblog_cms/tests/` に移動し、README に実行手順を書く。
3. Cookie・レスポンス HTML は Git 管理から外し、`.gitignore` にパターンを追加する。

#### 優先度

高。削除の効果が大きく、実装への影響が小さいため早期に対応できます。

---

### 3.4 本番起動時の `makemigrations`

#### 対象

- `docker/entrypoint.sh`

#### 問題

コンテナ起動時に `python manage.py makemigrations` が実行されています。マイグレーションファイルの生成は開発時に行い、レビュー・コミットされたものを本番で `migrate` するのが一般的です。

#### 無駄・リスク

- 起動時間が増える。
- 本番コンテナ内で意図しないマイグレーションファイルが生成される可能性がある。
- ボリュームマウントや権限設定によって起動失敗の原因になる。
- スキーマ変更のレビュー可能性が下がる。

#### 改善方針

1. 本番起動フローから `makemigrations` を削除する。
2. CI に `python manage.py makemigrations --check --dry-run` を追加し、マイグレーション漏れを検知する。
3. 開発用に必要なら `scripts/makemigrations.sh` など明示的な手動コマンドに分離する。

#### 優先度

高。運用の安定性に関わります。

---

### 3.5 不要または用途不明な依存関係

#### 対象

- `requirements.txt`

#### 問題

`requirements.txt` には `whitenoise`, `django-compressor`, `django-cors-headers`, `django-csp`, `sentry-sdk`, `django-extensions`, `playwright`, `flake8`, `black`, `isort` などが含まれています。一方、設定ファイル上でミドルウェアや `INSTALLED_APPS` に組み込まれていないもの、実行環境と開発環境で分けるべきものが混在しています。

#### 無駄・リスク

- 本番イメージに開発・テスト用依存が入り、イメージサイズと脆弱性表面が増える。
- Playwright 依存のために Dockerfile にブラウザ系 OS パッケージが追加され、ビルド時間とサイズが増える。
- 未使用のセキュリティ系ライブラリは「導入済み」と誤解されやすい。

#### 改善方針

1. `requirements/base.txt`, `requirements/prod.txt`, `requirements/dev.txt`, `requirements/test.txt` に分割する。
2. 本番イメージは `prod.txt` のみをインストールする。
3. Playwright は E2E テスト専用イメージまたは CI ステップに分離する。
4. 未使用ライブラリは「使うなら設定に組み込む」「使わないなら削除」の二択にする。

#### 優先度

中〜高。ビルドとセキュリティに効きますが、分割には CI 調整が必要です。

---

### 3.6 CSRF 無効化とテスト向け分岐の混在

#### 対象

- `techblog_cms/settings.py`
- `techblog_cms/views.py`

#### 問題

設定ファイルでは pytest 検知時に CSRF ミドルウェアを削除しています。また、ログインビューと Markdown プレビュー API に `csrf_exempt` が付いています。テスト容易性のための無効化と、本番コード上の例外設定が混在しています。

#### 無駄・リスク

- テスト時と本番時でセキュリティ挙動が大きく変わり、テストが本番挙動を保証しにくい。
- ログインフォームの CSRF 免除は攻撃面を広げる。
- CSRF デバッグ用ファイルが残っていることから、過去の問題回避のために一時対応が積み重なった可能性がある。

#### 改善方針

1. ログインビューの `csrf_exempt` を削除し、テンプレート側の CSRF トークンを標準化する。
2. Markdown プレビュー API は CSRF トークン付き AJAX に修正する。
3. テストでは `Client(enforce_csrf_checks=True)` を使うケースを追加し、本番挙動を検証する。
4. pytest 検知によるミドルウェア削除は原則撤廃し、必要なテストだけ明示的に調整する。

#### 優先度

中〜高。セキュリティ改善として早めに対応すべきです。

---

### 3.7 設定値の重複・上書き

#### 対象

- `techblog_cms/settings.py`
- `techblog_cms/settings_production.py`

#### 問題

`CSRF_TRUSTED_ORIGINS` が静的リストで定義された後、環境変数由来の値で再代入されています。また、`settings_production.py` は `from .settings import *` の後に `MIDDLEWARE.insert(0, 'django.middleware.security.SecurityMiddleware')` を実行するため、既に含まれる SecurityMiddleware を重複挿入する可能性があります。

#### 無駄・リスク

- 設定の最終値が読み取りづらい。
- 重複ミドルウェアは不要な処理を増やし、予期せぬ副作用の調査コストを上げる。
- 静的に書いた trusted origins が環境変数未設定時に空になるなど、コメントと実挙動がずれる。

#### 改善方針

1. 設定値は一箇所で定義し、環境変数デフォルトに既定値を入れる。
2. `settings_production.py` の重複挿入は削除するか、存在チェック付きにする。
3. `print()` による設定デバッグ出力は logging に置き換えるか削除する。

#### 優先度

中。小さな修正で混乱を減らせます。

---

### 3.8 テンプレート・静的ファイルの重複と異常なファイル名

#### 対象

- `techblog_cms/templates/static/js/articles.js`
- `techblog_cms/templates/static/js/main.js`
- `techblog_cms/templates/static/css/style.css`
- `techblog_cms/static/js/articles.js`
- `techblog_cms/static/js/main.js`
- `techblog_cms/static/css/style.css`
- `techblog_cms/templates/index.html.template`
- `techblog_cms/templates/components/{% url 'categories' %}`

#### 問題

静的ファイルが `techblog_cms/static/` と `techblog_cms/templates/static/` に重複しています。さらに、テンプレートディレクトリ内に `{% url 'categories' %}` というテンプレートタグのような文字列を含むファイル名が存在します。これは誤操作や生成ミスの可能性が高いです。

#### 無駄・リスク

- どちらの CSS/JS を編集すべきか分からない。
- テンプレート配下に静的ファイルがあると、Django の責務分離が崩れる。
- 異常なファイル名はシェル操作・エディタ・CI で扱いづらく、事故の元になる。

#### 改善方針

1. 静的ファイルは `techblog_cms/static/` に統一する。
2. `templates/static/` 配下を削除する。
3. 異常なファイル名を削除し、必要な内容がある場合は適切なテンプレート名へ移す。
4. `index.html.template` が不要なら削除し、必要なら用途を README に明記する。

#### 優先度

中。表示崩れの回帰確認をしながら進めます。

---

### 3.9 使われていない可能性のあるビュー・テンプレート

#### 対象

- `techblog_cms/views.py` の `index()`
- `techblog_cms/templates/index.html`
- `techblog_cms/templates/index.html.template`

#### 問題

URL ルートは `home_view` に紐づいており、`index()` は現行 URL から参照されていないように見えます。`index.html` 系テンプレートも役割が曖昧です。

#### 無駄・リスク

- 不要な画面が残ることで修正漏れが起きる。
- テンプレートの重複がデザイン変更時のコストになる。

#### 改善方針

1. URL 参照、テンプレート参照、テスト参照を確認する。
2. 未使用であれば `index()` と関連テンプレートを削除する。
3. 必要なら `home.html` と統合する。

#### 優先度

低〜中。影響範囲確認後に対応します。

---

### 3.10 DB クエリ最適化余地

#### 対象

- `techblog_cms/views.py`
- `techblog_cms/models.py`

#### 問題

記事一覧・詳細・カテゴリ・タグ画面でカテゴリとタグを毎回取得しています。また、記事一覧では `select_related('category')` や `prefetch_related('tags')` が使われていません。テンプレート内でカテゴリやタグを参照している場合、N+1 クエリにつながる可能性があります。

#### 無駄・リスク

- 記事数・タグ数が増えるほど DB クエリが増える。
- 全ページで同じサイドバー用データを取得する処理が重複する。

#### 改善方針

1. 共通サイドバー用のカテゴリ・タグ取得を context processor または専用ヘルパーに集約する。
2. 記事 QuerySet に `select_related('category')` と `prefetch_related('tags')` を追加する。
3. `Category.article_count()` は必要に応じて annotate へ置き換える。
4. Django Debug Toolbar ではなくテストで `assertNumQueries` を追加し、回帰を検知する。

#### 優先度

中。データ量増加前に対応すると効果的です。

## 4. 改善ロードマップ

### Phase 0: 削除前の安全確認

- 現在の CI テストを実行する。
- `docker compose config` で Compose 設定の構文を確認する。
- `rg` で削除候補ファイルの参照有無を確認する。
- 削除対象を Pull Request 上で明示し、必要ならバックアップではなく Git 履歴から復元する方針を合意する。

### Phase 1: 低リスクな掃除

- `cookies.txt`, `login_response*.html` を削除。
- 明らかな一時スクリプトを `scripts/` に移すか削除。
- `.gitignore` にレスポンス HTML、Cookie、ローカルデバッグ成果物を追加。
- `templates/static/` と異常なファイル名の中身を確認し、重複なら削除。

### Phase 2: 構成の一本化

- Django アプリを `techblog_cms/` に一本化し、`app/` を削除。
- Dockerfile と Nginx 設定を実運用ファイルに統一。
- README、AGENTS.md、docs を現在の構成へ更新。

### Phase 3: 起動・依存関係の最適化

- `docker/entrypoint.sh` から本番 `makemigrations` を削除。
- CI に `makemigrations --check --dry-run` を追加。
- requirements を用途別に分割。
- Playwright とブラウザ依存を E2E 専用へ分離。

### Phase 4: セキュリティと性能改善

- `csrf_exempt` を撤廃または最小化。
- CSRF の本番同等テストを追加。
- QuerySet に `select_related` / `prefetch_related` を追加。
- 共通サイドバー取得を集約し、クエリ数テストを追加。

## 5. 推奨タスク一覧

| 優先度 | タスク | 期待効果 | 主な確認コマンド |
| --- | --- | --- | --- |
| 高 | 一時生成物の削除 | 情報漏えい・認知負荷低減 | `python -m pytest -v` |
| 高 | `app/` 旧 Django 構成の削除 | 修正対象の一本化 | `python manage.py check` |
| 高 | Docker/Nginx 設定の棚卸し | デプロイミス防止 | `docker compose config` |
| 高 | 本番 `makemigrations` の削除 | 起動安定化 | `python manage.py makemigrations --check --dry-run` |
| 中 | requirements 分割 | イメージ軽量化・脆弱性表面削減 | `docker build -f Dockerfile.django .` |
| 中 | CSRF 例外の削減 | セキュリティ強化 | `python -m pytest techblog_cms/tests/test_login_security.py -v` |
| 中 | QuerySet 最適化 | DB 負荷削減 | `python -m pytest techblog_cms/tests/test_views.py -v` |
| 低 | 未使用ビュー・テンプレート削除 | 保守対象削減 | `rg "index\(" techblog_cms tests` |

## 6. 成功指標

- ルート直下の一時ファイルが 0 件になる。
- Django 実装ディレクトリが 1 系統に統一される。
- Compose/CI/README が同じ Dockerfile と設定ファイルを指す。
- 本番イメージから E2E・開発専用依存が除外される。
- `python manage.py check` と `python -m pytest -v` が安定して成功する。
- 起動時にマイグレーションファイル生成が行われない。
- ログインと Markdown プレビューで CSRF を維持したテストが存在する。

## 7. 直近の推奨アクション

次の Pull Request では、影響が小さく効果が大きい以下をまとめて実施することを推奨します。

1. `cookies.txt` と `login_response*.html` の削除。
2. `techblog_cms/templates/static/` の削除可否確認と、重複なら削除。
3. `techblog_cms/templates/components/{% url 'categories' %}` の削除。
4. `docker/entrypoint.sh` の `makemigrations` 削除と CI の `makemigrations --check --dry-run` 追加。
5. README の実構成更新。

これにより、アプリケーション動作への影響を抑えつつ、保守対象・情報漏えいリスク・起動時の不確実性を大きく減らせます。
