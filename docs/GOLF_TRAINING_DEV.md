# Local development with VS Code Remote-SSH

## Requirements and isolation

Run these commands from `/opt/data/golf-training` on `dev`.

- Python 3.12.3 and the existing `.venv`, installed from `uv.lock` with the `dev` group.
- Project-local nvm 0.40.8 in `.cache/nvm`, with Node 22.23.4 pinned in `.nvmrc`.
- Application frontend packages installed with `npm ci --include=dev` from
  `package-lock.json`, including `@wger-project/react-components` 26.10.4.
- Sass 1.106.1 installed separately in `.cache/golf-frontend-tools` to run the
  existing `build:css:sass` command without changing application dependencies.

`settings.golf_dev` imports upstream global settings directly. It does not import
`settings.main`, `settings.local_dev`, untracked settings overrides, or environment
files. Production `DJANGO_DB_*` and `PS_DATABASE_URI` variables do not select its
database. Commands below select the development settings explicitly.

| Resource | Development value |
| --- | --- |
| Database | SQLite: `db/golf-dev/database.sqlite3` |
| Media | `db/golf-dev/media/` |
| Collected static output, if needed | `db/golf-dev/static/` |
| Cache | Process-local memory |
| Browser URL | `http://localhost:8001` |
| Bind address | `127.0.0.1:8001` |
| Allowed hosts | `localhost`, `127.0.0.1` |
| CSRF/CORS origins | Localhost and 127.0.0.1 on port 8001 |
| Timezone | Europe/Berlin |
| Mail | Console backend; no SMTP service |

PostgreSQL, Redis, Celery, Nginx, Docker and PowerSync are not needed for this local
browser/API workflow. Background synchronization and automatic ingredient downloads
are disabled. PostgreSQL and PowerSync integration must be verified separately for
future deployment. The optional online nutrition dataset was not downloaded.

Development settings enable debug, plain static storage, registration, and local
HTTP cookies, with email verification and Axes disabled. Their signing value is
deliberately development-only. Session authentication is the verified browser flow;
JWT signing and OIDC providers are not configured. Do not use this settings module
for a deployment or bind the debug server to a public address.

## Start the application

In a VS Code Remote-SSH terminal:

```bash
cd /opt/data/golf-training
source .venv/bin/activate
python manage.py check --settings=settings.golf_dev
python manage.py runserver 127.0.0.1:8001 --settings=settings.golf_dev
```

Use `--noreload` if a single development process is preferred. Stop your foreground
server with Ctrl+C. If port 8001 is occupied by an earlier development instance,
reuse it or stop that instance before starting another; do not terminate unrelated
processes. Inspect only this port with `ss -ltnp 'sport = :8001'`.

In VS Code, select `.venv/bin/python` as the remote Python interpreter. In the
**Ports** view, forward remote port **8001**, keep forwarding private, and open
**http://localhost:8001** on your local computer. Keep the forwarded local port at
8001 to match the site URL and trusted origins. No SSH, firewall or Nginx edits are
needed. The development server itself listens only on the remote loopback address.

Use the existing wger registration/login screens to create your own development
account. The bundled bootstrap also creates wger's standard development account;
no production account or credentials are used. Most wger page URLs include a
language prefix. `/account/login/` is an unprefixed login entry point.

The golf API has no dedicated frontend form yet. After signing in, test it from
the browser developer console on the same origin:

```javascript
// Before the first write, GET returns 404; after creation it returns 200.
await fetch('/api/v2/golf/profile/').then(r => r.json());

// Visit the login form first if this browser has not yet received a CSRF cookie.
const csrf = document.cookie.split('; ').find(x => x.startsWith('csrftoken='))?.split('=')[1];
const response = await fetch('/api/v2/golf/profile/', {
  method: 'POST',
  headers: {'Content-Type': 'application/json', 'X-CSRFToken': csrf},
  body: JSON.stringify({handicap_index: '18.4', playing_hand: 'right'})
});
console.log(response.status, await response.json());
```

POST/PUT/PATCH create the current user's profile (201) or update it (200). GET
returns only that user's profile. Anonymous requests return 403, and session writes
without a CSRF token return 403. Invalid handicaps return 400.

## Database initialization and future migrations

The dedicated database has been initialized after explicit approval using the
upstream bootstrap workflow. All migrations, including `golf.0001_initial`, and
bundled starter fixtures were applied. Its Django Site points at localhost:8001.
It is independent of any existing database, with files under the already ignored
`db/` directory.

The following commands document the setup. **Do not repeat initialization or apply
new migrations without the approval required by `/opt/data/AGENTS.md`.** Bootstrap
can initialize schemas and load users/fixtures; it is not a read-only check.

```bash
mkdir -p db/golf-dev/media db/golf-dev/static
DJANGO_SETTINGS_MODULE=settings.golf_dev .venv/bin/wger bootstrap --no-process-static
.venv/bin/python manage.py set-site-url --settings=settings.golf_dev
```

Do not run `load-online-fixtures`, `create-or-reset-admin`, or generic `bootstrap`
as part of normal startup. There is no need to reset an account or download the
large nutrition dataset. A read-only pending-migration check is:

```bash
.venv/bin/python manage.py migrate --check --settings=settings.golf_dev
```

For future approved schema updates, stop the development server, back up this
dedicated database, inspect the migration plan and apply only with the explicit
`settings.golf_dev` argument. No production connection settings are needed.

## Load Node tools and rebuild assets

nvm was installed project-locally as requested, following its
[documented directory and profile options](https://github.com/nvm-sh/nvm#installing-and-updating).
It was not added to shell profiles and is therefore loaded explicitly per shell:

```bash
export NVM_DIR="$PWD/.cache/nvm"
source "$NVM_DIR/nvm.sh"
nvm use
export npm_config_cache="$PWD/.cache/npm"
export TMPDIR="$PWD/.cache/golf-tmp"
export NPM_CONFIG_USERCONFIG=/dev/null
export PATH="$PWD/.cache/golf-frontend-tools/node_modules/.bin:$PATH"
npm run build:css:sass
```

The build produces `wger/core/static/bootstrap-compiled.css` and its source map,
both ignored by Git. It currently prints upstream Bootstrap/Sass deprecation
warnings but completes successfully. Existing SCSS was not rewritten.

Dependency installation has already been completed. To reproduce it in a fresh
checkout, obtain approval first, load the nvm-managed Node version, then use:

```bash
npm ci --include=dev --no-audit --no-fund
npm install --prefix .cache/golf-frontend-tools --no-audit --no-fund --save-exact sass@1.106.1
```

The frontend is the existing Django shell plus prebuilt React components. There
is no new frontend framework or separate frontend dev server. Node is needed for
asset installation/building, not for each Django server start. With debug enabled,
Django's staticfiles finder serves installed packages and generated CSS directly;
`collectstatic` is not required for local development.

## Backend verification

`settings.golf_test` extends upstream CI settings, pins SQLite to memory, disables
migrations for test setup, and keeps test media under `.cache/test-media`. It never
selects the persistent development database.

```bash
TMPDIR="$PWD/.cache/golf-tmp" .venv/bin/python manage.py test \
  wger.golf.tests \
  wger.core.tests.test_user_profile_api \
  wger.core.tests.api.test_permission_api \
  --settings=settings.golf_test --noinput
.venv/bin/python manage.py makemigrations golf --check --dry-run --settings=settings.golf_test
.venv/bin/ruff check --no-cache settings/golf_dev.py settings/golf_test.py wger/golf
.venv/bin/ruff format --check settings/golf_dev.py settings/golf_test.py wger/golf
```

All 33 selected backend tests pass. Django checks report no issues after frontend
installation, and lint/format checks pass. The migration execution path was also
exercised during the approved initialization of the dedicated SQLite database.
The dependency manifests and lockfiles remain unchanged.

The environment verification also checks HTTP page/asset delivery and browser-session
authentication with CSRF against the loopback server. Full interactive React
rendering and visual/mobile behavior still need a browser review through VS Code
port forwarding. JWT/OIDC, PostgreSQL behavior and deployment are outside this setup.
The optional gettext `msgfmt` tool is not installed, so wger's Django message
catalogues were not compiled; use the default English UI for this verification.
The packaged React translations are available independently. No system package
installation is needed to run the verified English development workflow.
