# Django向けセキュリティ対策チェックリスト（実装例つき）

> 目的: Djangoプロジェクトを本番運用する際に最低限押さえるべきセキュリティ設定・実装の要点を、設定例とあわせて短くまとめます。

---

## 0) 事前チェック

* 本番では `DEBUG = False`、`ALLOWED_HOSTS` を厳格に設定。
* 秘密情報（`SECRET_KEY` など）は環境変数や秘密管理ツールで管理（例: `django-environ`, cloud secret manager）。
* デプロイ前に `python manage.py check --deploy` を実行し警告を解消。

```python
# settings.py
DEBUG = False
ALLOWED_HOSTS = ["example.com"]
```

---

## 1) HTTPS 強制とHSTS

* すべての通信をHTTPSへリダイレクト。
* HSTSを有効化（サブドメイン含む）。CDN/リバプロ運用時は `SECURE_PROXY_SSL_HEADER` を正しく設定。

```python
# settings.py
SECURE_SSL_REDIRECT = True
SECURE_HSTS_SECONDS = 31536000  # 1年
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")  # リバプロ配下で必要な場合
```

---

## 2) クッキーとセッション

* セキュア属性/HttpOnly/SameSite を設定。
* セッション固定化対策としてログイン時のセッションIDローテーション（Djangoは`login()`時にローテーション）。

```python
# settings.py
SESSION_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"  # CSRF対策観点でLax/Strictを検討
CSRF_COOKIE_SECURE = True
CSRF_COOKIE_HTTPONLY = False  # トークン送信用のため既定でFalse
CSRF_COOKIE_SAMESITE = "Lax"
```

---

## 3) CSRF対策

* 既定の `CsrfViewMiddleware` を有効のままにする。
* テンプレートのPOSTフォームに `{% csrf_token %}` を必ず挿入。
* 跨ドメインPOSTが必要なら `CSRF_TRUSTED_ORIGINS` を利用し、Origin/Referer要件を満たす。

```python
# settings.py
MIDDLEWARE = [
    # ...
    "django.middleware.csrf.CsrfViewMiddleware",
    # ...
]
CSRF_TRUSTED_ORIGINS = ["https://api.example.com"]
```

---

## 4) XSS対策 + CSP

* Djangoテンプレートの自動エスケープを前提に、`safe`/`mark_safe` の多用を避ける。
* 動的に埋め込むJSには `json_script` を活用。
* 追加対策としてCSP(Content Security Policy)を導入（`django-csp` など）。

```python
# settings.py（CSP例: django-csp使用時）
INSTALLED_APPS += ["csp"]
MIDDLEWARE += ["csp.middleware.CSPMiddleware"]
CSP_DEFAULT_SRC = ("'self'",)
CSP_SCRIPT_SRC = ("'self'", "'unsafe-inline'",)  # 可能な限り'unsafe-inline'は排除
CSP_OBJECT_SRC = ("'none'",)
CSP_BASE_URI = ("'self'",)
CSP_FRAME_ANCESTORS = ("'none'",)  # クリックジャッキング防御強化
```

---

## 5) クリックジャッキング対策

* `XFrameOptionsMiddleware` を有効化（既定: `DENY`）。必要な画面のみ個別に緩和。

```python
# settings.py
MIDDLEWARE += ["django.middleware.clickjacking.XFrameOptionsMiddleware"]
X_FRAME_OPTIONS = "DENY"  # 例: "SAMEORIGIN" に変更可能
```

個別緩和例:

```python
from django.views.decorators.clickjacking import xframe_options_exempt

@xframe_options_exempt
def embeddable_view(request):
    ...
```

---

## 6) 各種セキュリティヘッダ

* MIMEスニッフィング防止やReferrer-Policyなどを有効に。

```python
# settings.py
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "same-origin"  # 例: "strict-origin-when-cross-origin"
```

（必要に応じてWebサーバ/Nginx/CDN側で `X-Content-Type-Options: nosniff`, `Referrer-Policy` を付与。）

---

## 7) 認証・パスワード

* 強力なパスワードハッシュ（Argon2推奨）とバリデータを有効化。
* 管理サイト`/admin` は多要素認証（`django-otp` 等）やIP制限、CSRF有効のまま運用。

```python
# settings.py
INSTALLED_APPS += ["django.contrib.auth", "django.contrib.contenttypes"]
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.Argon2PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher",
    "django.contrib.auth.hashers.BCryptSHA256PasswordHasher",
]
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator", "OPTIONS": {"min_length": 12}},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]
```

---

## 8) SQLインジェクション対策

* Django ORMのパラメータバインドを使用し、文字列連結によるクエリ生成を禁止。
* `raw()`, `extra()` 等の使用は最小限にし、必ずパラメータ化する。

```python
# 悪い例（文字列連結）
User.objects.raw(f"SELECT * FROM auth_user WHERE username = '{username}'")

# 良い例（ORMフィルタ）
User.objects.filter(username=username)
```

---

## 9) 入力検証・アップロード

* `forms`/`serializers` のバリデーションを活用し、不正値・境界値を検査。
* ファイルアップロードは拡張子/Content-Type/サイズを検証し、保管先はアプリ直下の公開ディレクトリ外。画像処理はサーバ側で再エンコード。

---

## 10) CORS と API

* ブラウザ連携が必要なら `django-cors-headers` でオリジンを限定。
* DRF使用時は CSRF / 認可（Token/Auth）設計、`SAFE_METHODS` に応じた権限制御、ページネーション/スロットリングを適用。

```python
# settings.py（例）
INSTALLED_APPS += ["corsheaders"]
MIDDLEWARE = ["corsheaders.middleware.CorsMiddleware", *MIDDLEWARE]
CORS_ALLOWED_ORIGINS = ["https://app.example.com"]
```

---

## 11) ロギングと監査

* セキュリティ関連ロガー（`django.security.*`）をINFO/WARN以上で出力。
* 認証/権限エラー、重要操作（管理画面、支払い等）を監査ログに記録し改ざん防止保管。

```python
# settings.py（例）
LOGGING = {
  "version": 1,
  "handlers": {"console": {"class": "logging.StreamHandler"}},
  "loggers": {
    "django.security": {"handlers": ["console"], "level": "WARNING"},
  }
}
```

---

## 12) 管理運用の実務ポイント

* 管理ユーザは最小権限・個別アカウント、2FA必須。
* 依存パッケージ・Django本体はLTSへ追随し、セキュリティリリースを迅速適用。
* バックアップ/災害復旧手順の定期演習。脆弱性診断（ZAP/Burp等）をCIや定期運用に組み込み。

---

## 参考コマンド

```bash
python manage.py check --deploy
python -m django --version
pip list --outdated | grep django
```

---

### 付録: NginxなどのWebサーバ側ヘッダ例

```nginx
add_header X-Content-Type-Options "nosniff" always;
add_header Referrer-Policy "strict-origin-when-cross-origin" always;
add_header X-Frame-Options "DENY" always;  # Django側で管理するなら重複に注意
```
