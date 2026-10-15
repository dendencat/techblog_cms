# Cloudflare でブログを公開する

techblog_cms(Django + PostgreSQL + Redis + nginx の docker compose 構成)を、
Cloudflare のエッジ経由で `https://<BLOG_HOSTNAME>`(例: `blog.example.com`)として公開するための手順です。
公開ホスト名は `.env` の `BLOG_HOSTNAME` と `terraform.tfvars` の `hostname` の 2 か所で指定します。

> **ドメインの条件**: ホスト名は **ネームサーバーを Cloudflare に向けた(フルセットアップの)ゾーン配下** に置く必要があります。
> DNS を Route 53 など他社で運用しているドメインのサブドメインだけを Cloudflare に載せる方法(CNAME セットアップ)は
> Business プラン以上、サブドメイン単位の委任は Enterprise 限定で、Free では使えません。
> また Tunnel の `cfargotunnel.com` は同じ Cloudflare アカウント内の DNS レコードしか中継しないため、
> 他社 DNS から CNAME を向けても動きません。

## 構成

```text
閲覧者 ──HTTPS──▶ Cloudflare エッジ ──Tunnel(外向き接続)──▶ cloudflared ─▶ nginx ─▶ Django(Gunicorn)
                  │  ・TLS 終端 / Always Use HTTPS / TLS1.2+          (オリジンホスト上の docker compose。
                  │  ・WAF カスタムルール / ログインのレート制限        ホストのポートは一切公開しない)
                  │  ・静的ファイルとメディアのエッジキャッシュ                      │
                  │  ・Access: /login /logout /dashboard /api /admin           ├─ PostgreSQL
                  │    は許可したメールアドレスのみ                              └─ Redis
```

| 目的 | 使う Cloudflare の機能 | 定義場所 |
|---|---|---|
| オリジンを外部に晒さない | Cloudflare Tunnel(cloudflared) | `infra/cloudflare/tunnel.tf`, `docker-compose.cloudflare.yml` |
| 公開 DNS | プロキシ有効の CNAME → `<tunnel-id>.cfargotunnel.com` | `infra/cloudflare/tunnel.tf` |
| 管理画面の保護 | Zero Trust Access(メールの OTP)+ cloudflared 側での JWT 検証 | `infra/cloudflare/access.tf`, `tunnel.tf` |
| TLS | エッジで終端、最小 TLS1.2、TLS1.3、HTTPS 強制 | `infra/cloudflare/security.tf` |
| 攻撃対策 | WAF カスタムルール、ログイン POST のレート制限 | `infra/cloudflare/security.tf` |
| 配信性能 | `/static/`・`/media/` のキャッシュルール | `infra/cloudflare/security.tf` |

Django は Workers 上では動かせない(psycopg2 やファイルアップロードを含むフル Django のため)ので、
アプリ本体は従来どおり docker compose でオリジンホスト上に置き、入口だけを Cloudflare に寄せています。
Let's Encrypt/certbot はエッジで TLS を終端するため不要になります。

## 用意するもの(人が行う作業)

1. **ブログ用ドメインが Cloudflare のゾーンとして追加済み**で、ネームサーバーが Cloudflare を向いていること(上の「ドメインの条件」参照)
2. **Zero Trust の組織(チーム名)** を作成済みであること(ダッシュボードの Zero Trust を初回開くと作成されます)。
   Access のログイン方法は既定の「One-time PIN」で動きます
3. **Terraform 用 API トークン**(Cloudflare ダッシュボード → My Profile → API Tokens → Custom token)
   - Account: `Cloudflare Tunnel: Edit`, `Access: Apps and Policies: Edit`
   - Zone(ブログ用ゾーンのみ): `DNS: Edit`, `Zone Settings: Edit`, `Zone WAF: Edit`, `Cache Rules: Edit`
   - 権限名はダッシュボードの表記に合わせて選択してください(要検証: 権限名は Cloudflare 側で改称されることがあります)
4. **オリジンホスト**: Docker Compose v2.24 以降が動く Linux マシン。受信ポートの開放も固定 IP も不要です(下の「費用」参照)

## 手順

### 1. Cloudflare 側のリソースを作る(Terraform、手元の PC で実行)

```bash
cd infra/cloudflare
cp terraform.tfvars.example terraform.tfvars   # 値を埋める(コミットしない)
export CLOUDFLARE_API_TOKEN=...                # 手順 3 のトークン

terraform init
terraform plan      # 作成されるものを必ず確認する
terraform apply
terraform output -raw tunnel_token             # オリジンの .env に設定する値
```

state(`terraform.tfstate`)は手元に保存されます。Tunnel トークンを含むのでコミットせず、
PC のバックアップ対象に入れてください。複数の PC から操作したくなった場合だけ、
`backend_r2.tf.example` を使って R2(無料枠内)に移せます。
GitHub Actions では構文チェック(fmt/validate)のみ行い、API トークンは GitHub に預けません。

### 2. オリジンホストで起動する

```bash
git clone https://github.com/dendencat/techblog_cms.git && cd techblog_cms
cp .env.example .env
# .env を編集:
#   SECRET_KEY は python3 -c "import secrets; print(secrets.token_urlsafe(64))" で生成
#   DATABASE_URL / POSTGRES_* / REDIS_* を本番用の強い値に
#   BLOG_HOSTNAME=blog.example.com(terraform.tfvars の hostname と同じ値。ALLOWED_HOSTS と CSRF_TRUSTED_ORIGINS はここから自動設定)
#   CLOUDFLARE_TUNNEL_TOKEN=$(terraform output -raw tunnel_token) の値
chmod 600 .env

docker compose -f docker-compose.yml -f docker-compose.cloudflare.yml up -d --build   # 以降の更新は ./deploy.sh
docker compose -f docker-compose.yml -f docker-compose.cloudflare.yml exec django python manage.py createsuperuser
```

`docker-compose.cloudflare.yml` を重ねると、nginx・redis のホストポート公開が外れ、certbot は起動せず、
cloudflared が追加されます。ホストのファイアウォールは受信をすべて閉じて構いません(SSH は別途管理)。

### 3. 確認

```bash
curl -sI https://$BLOG_HOSTNAME/            # 200、server: cloudflare
curl -sI http://$BLOG_HOSTNAME/             # 301 → https
curl -sI https://$BLOG_HOSTNAME/ready/      # 403(WAF で遮断)
curl -sI https://$BLOG_HOSTNAME/dashboard/  # 302 → <team>.cloudflareaccess.com(Access のログイン)
```

ブラウザで `/login/` を開くと Access のメール認証 → Django のログインの順に求められます。

## 注意点

- **ゾーン全体への影響**: `security.tf` の SSL モード `strict`・HTTPS 強制・最小 TLS はゾーンの全サブドメインに効きます。
  他サブドメインの都合で困る場合は `manage_zone_settings = false` にしてください
- **既存のルール**: WAF カスタムルール・レート制限・キャッシュルールは、ゾーンごとにフェーズ 1 つの ruleset で管理されます。
  ダッシュボードで既にルールを作っている場合、apply が衝突します。既存ルールを `terraform import` するか削除してから実行してください
- **Free プランの制限**: レート制限は 1 ルール・10 秒単位です。Cloudflare Managed Ruleset(マネージド WAF)は Pro 以上で、Free では自動の Free Managed Ruleset が有効です
- **メディアファイル**: アップロード画像は従来どおりオリジンの `media_volume` に保存されます。DB と合わせてバックアップしてください
- **秘密情報**: API トークン・Tunnel トークン・R2 キーはリポジトリにコミットしません(`.gitignore` で `*.tfvars`・`backend_r2.tf`・state を除外済み)

## 自宅マシンで運用する

オリジンは自宅のマシンで動かす前提です(2026-10-07 決定)。Tunnel は外向き接続だけなので、
ルーターのポート開放・固定 IP・DDNS はいずれも不要です。

**マシンの目安**: 64bit Linux(Ubuntu Server / Debian / Raspberry Pi OS 64bit)、メモリ 2GB 以上、
ストレージは SSD 推奨。Raspberry Pi 5(4GB 以上)でも動きます。使うイメージはすべて arm64 に対応しています。

**最初に一度だけやること**
1. OS の自動セキュリティ更新を有効にする(Ubuntu/Debian: `sudo apt install unattended-upgrades`)
2. Docker を起動時に自動起動する(`sudo systemctl enable docker`)。各コンテナは `restart: always` なので、
   停電や再起動の後も自動で戻ります
3. ルーターのポート開放はしない。マシンの SSH も家庭内 LAN からだけにする(インターネットに公開しない)
4. バックアップを cron に登録する(下記)

**バックアップ**: `scripts/backup.sh` が DB(pg_dump)とアップロード画像を日付付きで保存し、14 日より
古いものを消します。マシンが壊れても戻せるよう、`BACKUP_DIR` は USB ディスクなど別の媒体にしてください。

```bash
# 毎日 3:30 に実行(crontab -e で追記)
30 3 * * * BACKUP_DIR=/mnt/usb/techblog /path/to/techblog_cms/scripts/backup.sh >> $HOME/techblog-backup.log 2>&1
```

復元するとき:

```bash
gunzip -c db_YYYYMMDD_HHMMSS.sql.gz | docker compose -f docker-compose.yml -f docker-compose.cloudflare.yml exec -T db sh -c 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB"'
docker compose -f docker-compose.yml -f docker-compose.cloudflare.yml run --rm -T --no-deps --entrypoint tar django -C /app/media -xzf - < media_YYYYMMDD_HHMMSS.tar.gz
```

**止まっている間**: マシンや回線が落ちている間はブログが表示されません(Cloudflare のエラーページになります)。
復旧すれば cloudflared が自動で再接続します。

## 費用

Cloudflare 側はすべて **Free プランの範囲**で動く構成です。有料の機能(Pro 以上の Managed WAF、
Argo、Load Balancing、Workers Paid、Containers など)は使っていません。

| 項目 | 使っている機能 | 費用 |
|---|---|---|
| DNS・CDN・TLS 証明書 | Free プラン | 0 円 |
| オリジンの公開 | Cloudflare Tunnel | 0 円 |
| 管理画面の保護 | Zero Trust Access(Free は 50 ユーザーまで) | 0 円 |
| WAF カスタムルール | Free は 5 ルールまで(使用 2) | 0 円 |
| レート制限 | Free は 1 ルールまで(使用 1) | 0 円 |
| キャッシュルール | Free は 10 ルールまで(使用 1) | 0 円 |
| Terraform state | 手元のローカルファイル | 0 円 |
| CI(GitHub Actions)・Dependabot | 公開リポジトリは無料 | 0 円 |
| ブログ用ドメイン | 未定(Cloudflare Registrar で新規取得する場合は年額の原価のみ) | 要検証: TLD ごとの価格 |

費用が発生しうるのは **オリジンホスト** だけです。Tunnel は外向き接続だけで動くため、固定 IP や
ポート開放は不要で、自宅のマシンでも安全に公開できます。

| 選択肢 | 月額の目安 | 備考 |
|---|---|---|
| **自宅の PC / Raspberry Pi 5(4GB 以上)(採用)** | 電気代のみ(数百円程度)| 停電・回線断の間は閲覧不可 |
| Oracle Cloud Always Free(Arm VM)| 0 円 | 無料だが登録にクレジットカードが必要。アイドル状態の VM は回収されることがある |
| 低価格 VPS(1〜2GB メモリ)| 500〜1,000 円程度 | 最も安定。要検証: 料金は各社の最新価格を確認 |

全コンテナのメモリ上限の合計は約 1.5GB ですが、小規模ブログの実使用量はその半分程度の見込みです(要検証)。

## アプリとコンテナのセキュリティ対策

| 対策 | 内容 |
|---|---|
| フレームワーク | Django 5.2 LTS(4.2 LTS はサポート終了で未修正の脆弱性あり) |
| 記事本文の XSS | Markdown 変換後の HTML を nh3 の許可リストでサニタイズ(`<script>`・イベント属性・`javascript:` 等を除去) |
| SECRET_KEY | 本番(DEBUG=False)では未設定・既定値・50 文字未満なら起動を拒否 |
| ログアウト | POST + CSRF のみ受け付け(リンクや画像によるログアウト強制を防ぐ) |
| 外部 CSS | バージョン固定 + Subresource Integrity |
| アプリイメージ | コンパイラ・sudo・ブラウザ用ライブラリ・pip を含めない。UID 10001 の非 root、コードは読み取り専用 |
| 本番コンテナ | django はソースをマウントせず read-only ルート FS、`cap_drop: ALL`、`no-new-privileges` |
| 依存関係の監視 | CI で pip-audit と Trivy(django / nginx イメージ、HIGH 以上で失敗)、Dependabot で週次更新 |

既知で受け入れている残リスク(2026-10-07 時点、Trivy で確認):

- `postgres:16-alpine` の gosu に含まれる Go 標準ライブラリの脆弱性。compose で `user: postgres` を指定しており gosu は実行されず、DB は内部ネットワークのみ
- `cloudflare/cloudflared` のベースイメージの libssl。上流の更新を Dependabot で取り込む
- テンプレートにインラインの style/script が多く、厳格な Content-Security-Policy は未導入(今後の改善候補)

既存の環境から移行する場合: アプリの UID が 10001 に変わったため、以前のボリュームを使い回すなら
`docker run --rm -v techblog_cms_static_volume:/s -v techblog_cms_media_volume:/m -v techblog_cms_logs:/l alpine chown -R 10001:10001 /s /m /l`
で所有者を合わせてください。

## ロールバック

- 一時的に公開を止める: オリジンで `docker compose -f docker-compose.yml -f docker-compose.cloudflare.yml stop cloudflared`
- Cloudflare 側を元に戻す: `terraform destroy`(DNS レコード・Tunnel・Access・ルールが削除されます)
