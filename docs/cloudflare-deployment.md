# Cloudflare で blog.iohub.link を公開する

techblog_cms(Django + PostgreSQL + Redis + nginx の docker compose 構成)を、
Cloudflare のエッジ経由で `https://blog.iohub.link` として公開するための手順です。

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

1. **iohub.link が Cloudflare のゾーンとして追加済み**で、ネームサーバーが Cloudflare を向いていること
2. **Zero Trust の組織(チーム名)** を作成済みであること(ダッシュボードの Zero Trust を初回開くと作成されます)。
   Access のログイン方法は既定の「One-time PIN」で動きます
3. **Terraform 用 API トークン**(Cloudflare ダッシュボード → My Profile → API Tokens → Custom token)
   - Account: `Cloudflare Tunnel: Edit`, `Access: Apps and Policies: Edit`
   - Zone(iohub.link のみ): `DNS: Edit`, `Zone Settings: Edit`, `Zone WAF: Edit`, `Cache Rules: Edit`
   - 権限名はダッシュボードの表記に合わせて選択してください(要検証: 権限名は Cloudflare 側で改称されることがあります)
4. **Terraform state 用の R2 バケット**(例: `techblog-cms-tfstate`)と、その R2 API トークンの S3 互換アクセスキー。
   state には Tunnel トークンが入るため、公開されない場所に置きます
5. **オリジンホスト**: Docker Compose v2.24 以降が動く Linux マシン(VPS など)。受信ポートの開放は不要です

## 手順

### 1. Cloudflare 側のリソースを作る(Terraform)

```bash
cd infra/cloudflare
cp terraform.tfvars.example terraform.tfvars   # 値を埋める(コミットしない)
cp backend.hcl.example backend.hcl             # <ACCOUNT_ID> を埋める(コミットしない)

export CLOUDFLARE_API_TOKEN=...                # 手順 3 のトークン
export AWS_ACCESS_KEY_ID=...                   # R2 の S3 互換キー
export AWS_SECRET_ACCESS_KEY=...

terraform init -backend-config=backend.hcl
terraform plan      # 作成されるものを必ず確認する
terraform apply
```

GitHub Actions から実行する場合は `Cloudflare Infra` ワークフローを手動実行します(`plan` / `apply` を選択)。
事前に以下を設定してください。

- Environment `cloudflare-production` を作成し、Required reviewers を設定(apply の最終承認)
- Secrets: `CLOUDFLARE_API_TOKEN`, `CLOUDFLARE_ACCOUNT_ID`, `R2_ACCESS_KEY_ID`, `R2_SECRET_ACCESS_KEY`
- Variables: `CLOUDFLARE_ZONE_ID`, `CLOUDFLARE_ACCESS_TEAM_NAME`, `TFSTATE_R2_BUCKET`,
  `CLOUDFLARE_ACCESS_ALLOWED_EMAILS`(JSON 配列。例: `["you@example.com"]`)

### 2. オリジンホストで起動する

```bash
git clone https://github.com/dendencat/techblog_cms.git && cd techblog_cms
cp .env.example .env
# .env を編集:
#   SECRET_KEY / DATABASE_URL / POSTGRES_* / REDIS_* を本番用の強い値に
#   ALLOWED_HOSTS=blog.iohub.link
#   CSRF_TRUSTED_ORIGINS=https://blog.iohub.link
#   CLOUDFLARE_TUNNEL_TOKEN=$(terraform output -raw tunnel_token) の値
chmod 600 .env

docker compose -f docker-compose.yml -f docker-compose.cloudflare.yml up -d --build
docker compose -f docker-compose.yml -f docker-compose.cloudflare.yml exec django python manage.py createsuperuser
```

`docker-compose.cloudflare.yml` を重ねると、nginx・redis のホストポート公開が外れ、certbot は起動せず、
cloudflared が追加されます。ホストのファイアウォールは受信をすべて閉じて構いません(SSH は別途管理)。

### 3. 確認

```bash
curl -sI https://blog.iohub.link/            # 200、server: cloudflare
curl -sI http://blog.iohub.link/             # 301 → https
curl -sI https://blog.iohub.link/ready/      # 403(WAF で遮断)
curl -sI https://blog.iohub.link/dashboard/  # 302 → <team>.cloudflareaccess.com(Access のログイン)
```

ブラウザで `/login/` を開くと Access のメール認証 → Django のログインの順に求められます。

## 注意点

- **ゾーン全体への影響**: `security.tf` の SSL モード `strict`・HTTPS 強制・最小 TLS は iohub.link の全サブドメインに効きます。
  他サブドメインの都合で困る場合は `manage_zone_settings = false` にしてください
- **既存のルール**: WAF カスタムルール・レート制限・キャッシュルールは、ゾーンごとにフェーズ 1 つの ruleset で管理されます。
  ダッシュボードで既にルールを作っている場合、apply が衝突します。既存ルールを `terraform import` するか削除してから実行してください
- **Free プランの制限**: レート制限は 1 ルール・10 秒単位です。Cloudflare Managed Ruleset(マネージド WAF)は Pro 以上で、Free では自動の Free Managed Ruleset が有効です
- **メディアファイル**: アップロード画像は従来どおりオリジンの `media_volume` に保存されます。DB と合わせてバックアップしてください
- **秘密情報**: API トークン・Tunnel トークン・R2 キーはリポジトリにコミットしません(`.gitignore` で `*.tfvars`・`backend.hcl`・state を除外済み)

## ロールバック

- 一時的に公開を止める: オリジンで `docker compose -f docker-compose.yml -f docker-compose.cloudflare.yml stop cloudflared`
- Cloudflare 側を元に戻す: `terraform destroy`(DNS レコード・Tunnel・Access・ルールが削除されます)
