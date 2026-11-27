# kconvertor-server — Runbook

Flask REST API for Haetae Daegu. It does three things: EUR⇄KRW currency conversion, a historical rate graph, and accommodation listings with user accounts.
Production runs on a **DigitalOcean droplet**. Images are stored in **DigitalOcean Spaces**.

See [../../README.md](../../README.md) for the full system overview and the upgrade plan.

---

## 1. Code layout

```
kconvertor-server/
├── app.py                  # entry point: create_app() → Flask app
├── app/
│   ├── __init__.py         # create_app(): config, CORS, JWT, Swagger, blueprints
│   ├── config.py           # Development / Production config (picked by FLASK_ENV)
│   ├── error.py            # APIError(code, message)
│   ├── api/                # HTTP layer (Flask blueprints)
│   │   ├── auth.py         #   /auth/register, /login, /refresh, /me, /logout
│   │   ├── user.py         #   /users/...
│   │   ├── accommodations.py #   /accommodations/...
│   │   ├── currency.py     #   POST /currency/
│   │   └── graph.py        #   GET  /graph/
│   ├── services/           # business logic
│   │   ├── accommodation_service.py  # CRUD + Google geocoding of the address
│   │   ├── user_service.py / auth_service.py
│   │   ├── s3_service.py   # upload to DO Spaces (boto3, S3-compatible)
│   │   ├── storage_factory.py / storage_interface.py
│   │   └── alert_service.py  # Discord webhook notifications
│   ├── models/             # SQLAlchemy models: User, Accommodation
│   ├── schemas/            # Pydantic validation (create/update payloads)
│   ├── data_sources/       # ExchangeRate-API client + parser for the historical file
│   ├── data_script/        # historical_currency.txt (static data, ends 11/02/2025) + scraper
│   ├── security/           # bcrypt, JWTManager, @role_required
│   └── static/swagger.json # API docs served at /apidocs (only when not in production)
├── migrations/             # Alembic: env.py + versions/ (0001_baseline = initial schema). See §5 "Database migrations"
├── tests/                  # pytest (SQLite temp DB)
├── Dockerfile / entrypoint.sh / docker-compose.yml
└── scripts/                # build.sh, run.sh, clean.sh (podman-compose), migrate.sh, deploy.sh (old AWS)
```

Request flow: **blueprint (api/)** → **Pydantic schema** → **service** → **SQLAlchemy model** → PostgreSQL.
Side effects: Google Geocoding (on create/update of a listing), DO Spaces (image upload), and a Discord webhook (on almost every request, including errors).

## 2. API endpoints

| Method | Path | Auth | Notes |
|---|---|---|---|
| GET | `/` | – | Lists all routes. Handy health check. |
| POST | `/currency/` | – | `{from_currency, to_currency, amount}` → calls ExchangeRate-API |
| GET | `/graph/` | – | Reads `data_script/historical_currency.txt` |
| POST | `/auth/register` | – | `{email, username, password}` (bcrypt hashed) |
| POST | `/auth/login` | – | Returns `access_token` and `refresh_token` |
| POST | `/auth/refresh` | JWT | ⚠ see the known bugs below |
| GET | `/auth/me` | JWT | Current user |
| GET | `/users/` | admin | |
| GET | `/users/<id>` | – | Public: the frontend shows host contact info |
| POST | `/users/` | – | ⚠ stores the password **in plain text** |
| PUT/DELETE | `/users/<id>` | JWT (self or admin) | |
| GET | `/accommodations/` | – | Active listings, newest first |
| GET | `/accommodations/user` | JWT | Listings of the current user |
| GET | `/accommodations/<id>` | – | |
| POST | `/accommodations/` | JWT | multipart: `data` (JSON string) + `images[]` (at least 1) |
| PUT | `/accommodations/<id>` | JWT (owner) | multipart or JSON |
| PUT | `/accommodations/<id>/status` | JWT (owner/admin) | `{status: active\|hidden\|booked}` |
| DELETE | `/accommodations/<id>` | JWT (owner) | |

Swagger UI is at `http://localhost:5000/apidocs` whenever `FLASK_ENV` is not `production`.

## 3. Environment variables (`.env` at the repo root)

```env
# Flask
FLASK_ENV=development            # set to "production" on the droplet (hides Swagger, asserts secrets)
SECRET_KEY=change-me             # also used to sign JWTs. Keep the same value or every user is logged out

# Database. Two forms are used, so set both
DATABASE_URL=postgresql://kconv:kconv@db:5432/kconvertor   # used by SQLAlchemy
DB_HOST=db                       # used by entrypoint.sh (psql checks). Alembic uses DATABASE_URL
DB_PORT=5432
DB_USER=kconv
DB_PASSWORD=kconv
DB_NAME=kconvertor

# External services
EXCHANGE_RATE_API_KEY=...        # https://www.exchangerate-api.com
GOOGLE_MAPS_API_KEY=...          # Geocoding API. Creating or updating a listing FAILS without it
SPACE_ENDPOINT=https://lon1.digitaloceanspaces.com
SPACE_REGION=lon1
SPACE_NAME=accommodations
SPACE_ACCESS_KEY=...
SPACE_SECRET_KEY=...
DISCORD_WEBHOOK_URL=...          # optional. Alerts are skipped if empty
CLIENT_URL=https://haetaedaegu.vercel.app   # used in Discord messages
```

> Inside docker-compose, the DB host is the service name `db`. When running Flask directly on your machine, use `localhost`.

## 4. Run locally

### Option A: Docker Compose (closest to production)

```bash
cd kconvertor-server
nano .env                   # create it from section 3 (it is gitignored, and no .env.example exists yet)
docker compose up --build   # or: ./scripts/build.sh (podman-compose up -d --build)
# API → http://localhost:5000   Swagger → http://localhost:5000/apidocs
docker compose logs -f app
docker compose down         # add -v to wipe the Postgres volume
```

What `entrypoint.sh` does at every container start:
1. Waits for Postgres with `psql`.
2. Refuses to start if tables exist but the DB was never stamped by Alembic (see §5 "Database migrations", one-time switch).
3. Runs `alembic upgrade head`: applies pending migrations, or does nothing if the DB is up to date. On an empty DB it creates all tables.
4. Runs `flask run --host=0.0.0.0` (the Flask dev server).

### Option B: bare Python (fast iteration)

```bash
cd kconvertor-server
python3.10 -m venv .venv && source .venv/bin/activate   # the code targets 3.10
pip install -r requirements.txt
docker compose up -d db                                  # just Postgres
# in .env: DATABASE_URL=postgresql://kconv:kconv@localhost:5432/kconvertor
alembic upgrade head                                     # creates the tables
flask --app app.py run --debug
```

### Tests and lint (the same checks CI runs in `.github/workflows/python-app.yml`)

The DB tests (`tests/`) need a **dedicated** Postgres database (the models use `ARRAY`, which SQLite lacks). Every table in it is dropped after each test, so never point `TEST_DATABASE_URL` at a real database. CI provides one through a `postgres:14` service.

```bash
pip install black==26.10.1 pytest
docker compose exec db createdb -U $DB_USER kconvertor_test     # once
export TEST_DATABASE_URL=postgresql://$DB_USER:$DB_PASSWORD@localhost:5432/kconvertor_test
black . --check
pytest
```

Geocoding and S3 are mocked in the tests. No external API is called.

## 5. Production (DigitalOcean droplet)

> `scripts/deploy.sh` targets an **old AWS EC2 instance** and is obsolete. The droplet setup is not in the repo. Check the following on the droplet and write the answers in this section.

Discovery commands to run once on the droplet:

```bash
ssh root@<droplet-ip>
docker ps -a                       # or: podman ps -a  → running containers
ls ~ /opt /srv | grep -i kconv     # where the repo is cloned
cat <repo>/.env | cut -d= -f1      # which env vars are set (names only)
systemctl list-units | grep -Ei 'nginx|caddy|docker|podman'
ls /etc/nginx/sites-enabled/ 2>/dev/null; cat /etc/caddy/Caddyfile 2>/dev/null
sudo certbot certificates 2>/dev/null   # TLS cert (Vercel → API must be HTTPS)
crontab -l                         # backups or renewals, if any
```

Vercel serves the frontend over HTTPS, and browsers block calls from an HTTPS page to a plain-HTTP API. So there must be a reverse proxy with TLS (nginx, Caddy or similar) in front of port 5000. Find out which one it is.

Likely deploy procedure, based on the repo:

```bash
ssh root@<droplet-ip>
cd <repo>
git pull
docker compose up -d --build app     # rebuilds the image (the .env is baked in. See upgrades)
docker compose logs -f --tail=100 app
curl -s localhost:5000/ | head       # smoke test
```

Database backup and restore (do this before any risky change):

```bash
docker compose exec db pg_dump -U $DB_USER $DB_NAME > backup_$(date +%F).sql
cat backup.sql | docker compose exec -T db psql -U $DB_USER $DB_NAME
```

### Database migrations (Alembic)

The schema is versioned in `migrations/versions/`. The DB URL comes from `DATABASE_URL` (`migrations/env.py` also loads the repo-root `.env` when you run `alembic` from your machine). `alembic.ini` is committed and holds no secrets.

**Workflow to change the schema:**

```bash
# 1. local DB up to date
alembic upgrade head
# 2. edit a model in app/models/, then generate the revision
alembic revision --autogenerate -m "add google_id to users"   # or: ./scripts/migrate.sh "add google_id to users"
# 3. REVIEW the generated file in migrations/versions/. Autogenerate misses or gets wrong:
#    renames (seen as drop + add, so data is lost), server defaults, data migrations,
#    and NOT NULL columns on tables that already have rows (add a server_default).
alembic upgrade head          # apply locally and test
alembic downgrade -1 && alembic upgrade head   # check the downgrade works
# 4. commit the model change and the revision file in the same PR
# 5. deploy: the container runs "alembic upgrade head" on start
```

Back up the DB (see above) before deploying a migration that drops or alters columns.

**One-time switch on an existing database (prod).** The old entrypoint built the schema with `create_all()` and left an empty `alembic_version` table. `0001_baseline` describes exactly that schema, so the DB must be marked as already at the baseline instead of running it:

```bash
docker compose exec db pg_dump -U $DB_USER $DB_NAME > backup_$(date +%F).sql   # 1. backup
[ -f alembic.ini ] && mv alembic.ini alembic.ini.old   # the hand-made untracked copy would block git pull
git pull                                                                         # 2. get this change
docker compose build app
docker compose run --rm --entrypoint alembic app stamp 0001_baseline             # 3. once, writes the version only
docker compose run --rm --entrypoint alembic app check                           # 4. must print "No new upgrade operations detected."
docker compose up -d app
```

If step 4 reports differences, prod has drifted from the models (e.g. a column added by hand). Fix it with a new revision before deploying. Until step 3 is done, the container refuses to start with an explicit error, and it never recreates tables.

Create an admin user (no endpoint exists for this):

```bash
docker compose exec db psql -U $DB_USER $DB_NAME -c "UPDATE users SET role='admin' WHERE email='you@example.com';"
```

## 6. Known bugs found while documenting

| # | Where | Problem |
|---|---|---|
| 1 | `api/user.py` `POST /users/` and `PUT /users/<id>` with `password` | Password saved **in plain text**. `auth.py` login also falls back to a plain-text compare. |
| 2 | `api/auth.py` `/auth/refresh` | Uses `verify_jwt_in_request()` without `refresh=True` and reads the header, while the frontend sends the refresh token in the body. Returns no `refresh_token`. In practice refresh fails and users get logged out. |
| 3 | `api/user.py` `remove_user` | Compares `current_user_id` (str) with `user_id` (int), so non-admins can never delete themselves. The frontend calls `DELETE /users/me`, which matches no route. |
| 4 | frontend `changePassword` | Calls `POST /users/change-password`, which does not exist. |
| 5 | `api/accommodations.py` `remove_accommodation` | `if not current_user and current_user.role...` is a logic bug. Admins cannot delete other users' listings. |
| 6 | `api/currency.py` | `return APIError(...)` without `.to_response()`. A missing field gives a 500 (KeyError). |
| 7 | `services/s3_service.py` | Uploaded key and returned URL may differ (`{folder}/{s3_path}` when `folder == SPACE_NAME`). Filenames are not made unique, so two `photo.jpg` uploads overwrite each other. Check this. |
| 8 | `accommodation_service.set_coordinates` | Address is not URL-encoded. No timeout on `requests.get`. |
| 9 | `security/security.py` `role_required` | `APIError("User not found", 404)` has its arguments reversed. |
| 10 | `Dockerfile` | `COPY .env` bakes secrets into the image. `COPY . .` and `COPY app/ .` duplicate the code. |
