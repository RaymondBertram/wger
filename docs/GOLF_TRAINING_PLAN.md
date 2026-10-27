# Golf Training: architecture and MVP plan

## 1. Project overview and analysis boundary

Golf Training will extend wger into a self-hosted training platform for individual
golfers, with coaching and teams added later. Reuse upstream functionality and
keep golf rules in a separate Django app rather than replacing the fitness system.

This is a planning document, not an implementation specification frozen against
future discoveries. Analysis date: 2026-10-25 (Europe/Berlin). Inspected checkout:
`dev`, commit `c7ecb8a77`; origin `RaymondBertram/wger`, upstream
`wger-project/wger`. The working tree was clean before this task. No nested
`AGENTS.md` was found in the project.

Evidence comes from local source and the upstream documentation linked below.
No dependencies were installed, application or database started, migrations run,
containers changed, or Git history changed. Runtime behavior, installed versions,
database contents, and production readiness have not been verified. Remote branch
freshness was not checked with a fetch. Online `latest` documentation can differ
from this checkout; local code takes precedence for this plan.

## 2. Existing wger architecture

### Backend and application boundaries

This is a Django monolith with Django REST Framework (DRF), server-rendered pages,
and embedded React screens. `pyproject.toml` declares Python >=3.12, Django
`~=6.0.7`, and DRF `~=3.18.2`; `uv.lock` records dependency resolution. These are
repository declarations, not evidence of what is installed on the development host.

| Component | Current responsibility and relevant source |
| --- | --- |
| `wger.core` | User profile, language/license records, units, authentication integration, shared templates and React page host |
| `wger.exercises` | Exercise catalogue, translated descriptions, aliases, categories, muscles, equipment, licensed images/videos, history and remote synchronization |
| `wger.manager` | Routines, ordered days, slots, exercise prescriptions, progression configuration, training sessions and workout logs |
| `wger.measurements` | User-owned measurement categories and dated numeric measurements, units and chart configuration |
| `wger.weight` | Weight-facing functionality; the profile also uses measurements for body weight |
| `wger.gym` / `wger.config` | Gym membership, trainer/member configuration, contracts and management features |
| Other apps | Nutrition, progress gallery, trophies, mailer and software pages; preserve their functionality |
| `wger.utils` | Shared permissions, owner checks, pagination, authentication adapters, caching and other helpers |

`settings/settings_global.py` registers apps and framework defaults;
`settings/main.py` supplies deployment configuration. `settings/local_dev.py`
supports local development and an optional untracked settings override, described
in `settings/README.md`. `wger/urls.py` combines page routes, authentication routes,
and the DRF router.

### Exercise and training models

| Existing model | Meaning | Golf reuse and limits |
| --- | --- | --- |
| `exercises.Exercise` | Stable UUID, one required category, optional muscle/equipment relations and variation group | Reuse the exercise identity; add golf taxonomy through related metadata |
| `exercises.Translation` | Name, description and source per exercise/language, UUID, license and history | Reuse instructions, translations and attribution |
| `ExerciseImage`, `ExerciseVideo`, `Alias`, `ExerciseComment` | Media, alternate names and notes | Reuse for drill guidance; check licensing for each item |
| `manager.Routine` | User-owned dated plan, templates/public templates, weekly fitting | Reuse as the individual training plan; current maximum-duration constant is 120 days |
| `manager.Day` | Ordered training/rest day, type, description and advancement settings | Use custom days for golf; reuse the date sequence rather than adding a second scheduler |
| `manager.Slot` / `SlotEntry` | Ordered drill grouping and exercise reference, comments, units and configuration | Reuse for planned drills; attach golf targets to entries |
| Sets/repetitions/weight/rest/RiR configuration models | Prescription and progression rules | Reuse for golf fitness; automatic strength progression is unsuitable for most skill drills |
| `manager.WorkoutSession` | UUID, user, optional routine/day, start/end, notes and impression | Reuse as the actual training session, including unplanned practice |
| `manager.WorkoutLog` | Exercise result with optional routine/slot, session, repetitions, weight, rest, RiR and targets | Reuse for fitness; golf outcomes need their own representation |

The current plan hierarchy is `Routine -> Day -> Slot -> SlotEntry -> Exercise`.
There is no separate current `Workout` model in the manager model package; some
labels and API paths retain workout terminology. Sessions are distinct from
exercise-level logs. Routine statistics calculate fitness measures such as volume,
intensity and sets; they are not generic golf analytics.

The catalogue is shared, with public reads and contribution permissions, rather
than a collection of private exercises per user. Creation/submission and trusted
contributor rules live in `wger/exercises/api/permissions.py` and the profile trust
logic. Do not bypass those rules or store private player notes in descriptions.

### Authentication and user management

The project uses Django's built-in `User` directly in many existing models and
`core.UserProfile` as a one-to-one extension. The profile already stores preferences,
language, timezone, gym association, fitness details and verification/trust helpers.
Replacing the user model would create unnecessary migration and compatibility work.

Django-allauth supplies account pages, email and password management, social-login
integration, MFA/passkeys and headless authentication. Social providers require
configuration; installed capabilities do not mean they are enabled. Settings also
include Axes and rate limits, registration/guest flags, and an OIDC provider that
requires configuration. Reuse the existing account flows, including password reset,
rather than implementing golf-specific credentials.

The DRF stack accepts session authentication, tokens, headless JWT, OIDC tokens and
SimpleJWT through the configured adapters. For same-origin web pages, retain
session authentication and CSRF protection. Do not add another token system.

### API, authorization and frontend

`/api/v2/` exposes exercises, routines, days, slots, entries, configuration records,
sessions, workout logs, profiles, measurements and other resources. Serializers,
filtersets and viewsets are grouped inside each app. drf-spectacular supplies the
OpenAPI schema. Account routes include `/account/` and `/allauth/`.

`WgerPermission`, `WgerOwnerObjectModelViewSet` and `check_fk_ownership` demonstrate
existing object ownership conventions. Private viewsets also filter querysets and
force the owner on creation. Public routine templates have separate access rules;
their personal logs/statistics remain owner-only. Golf endpoints must explicitly
check authentication, list filtering, object access and submitted foreign keys.
Object permissions alone do not filter list responses or validate all relationships.

The frontend is hybrid: Django templates provide the shell and Bootstrap styling;
`ReactView` mounts interactive screens. See `wger/core/views/react.py`,
`wger/core/templates/react/react-page.html`, `wger/core/templates/template.html`,
and `wger/manager/urls.py`. `package.json` consumes
`@wger-project/react-components` version `26.10.4`. Its editable source is in the
separate [wger-project/react repository](https://github.com/wger-project/react),
as confirmed by the [frontend documentation](https://wger.readthedocs.io/en/latest/development/frontend.html).
Editing generated assets or `node_modules` would not be a maintainable UI change.

### Development and Docker setup

The [backend guide](https://wger.readthedocs.io/en/latest/development/backend.html)
describes native setup and Django's test runner. The local CI workflow uses
`settings.ci`, Python 3.12/3.13/3.14 and `manage.py test --parallel auto`; its SQLite
test configuration skips migrations. Ruff configuration is in `pyproject.toml`.
The current main CI workflow targets `master`, so pushes to `dev` do not receive
that workflow's push checks automatically.

Local Dockerfiles are under `extras/docker/{base,development,production,demo}`.
They build Python and frontend assets; production runs Gunicorn when configured.
The deployment Compose stack is maintained separately in
[wger-project/docker](https://github.com/wger-project/docker). The
[Docker documentation](https://wger.readthedocs.io/en/latest/installation/docker.html)
describes PostgreSQL, Redis, Nginx and persistent database/static/media volumes.

Important local behavior: `wger bootstrap` can initialize a database, load fixtures,
create an administrator, and install/build assets. The production entrypoint calls
bootstrap, may collect static files, runs migrations by default, and can synchronize
catalogue content. Even disabling the entrypoint's explicit migration step is not
sufficient to assume bootstrap cannot initialize an empty database. None of these
commands is an appropriate read-only inspection step.

## 3. Proposed modular architecture

### App boundary and integration

Create `wger.golf` with its own models, migrations, API, forms/views, templates,
services, tests and management commands. Use related extension models rather than
adding golf columns throughout upstream apps. Keep only the necessary integration
edits in app registration, URL inclusion and navigation. Preserve existing APIs and
fitness screens.

Proposed page prefix: `/golf/`; proposed API prefix: `/api/v2/golf/`. These are new
routes, not existing functionality. Use an owner-scoped service layer for plan
creation, session completion and result validation, with transactions around related
writes. Reuse existing cache invalidation helpers when updating routine structure.

Start golf screens with Django templates/forms and existing Bootstrap conventions.
This keeps the initial MVP in this repository. Preserve embedded React for existing
routine screens and add targeted enhancements only when the interaction needs them.
A golf-specific planning/logging form can operate on the same underlying routines
without requiring the fitness-oriented React editor to understand golf metrics.

If golf features are integrated into the React routine editor or charts, fork
`wger-project/react`, add routes/forms/API types there, and publish or package a
versioned build consumed by this backend. Do not assume the upstream package will
recognize new golf endpoints. A dedicated frontend repository is therefore optional
for the initial template-based MVP, and required for changes to those React screens.

### Data model overview (proposed, not created)

| Model | Relationships and minimum fields | Purpose |
| --- | --- | --- |
| `PlayerProfile` | One-to-one `settings.AUTH_USER_MODEL`; optional handicap index, handedness, home club, preferred distance unit | Golf identity without duplicating account or timezone data |
| `PlayerGoal` | Player FK; description, optional category, target date, status | Individual goals; numeric targets can follow the first MVP |
| `GolfCategory` | Unique stable slug and display label | Seed driving, long game, iron play, approach shots, chipping, pitching, bunker play, putting, golf fitness and mental training |
| `GolfExercise` | One-to-one `Exercise`; many-to-many golf categories; difficulty, setup guidance, archive flag, result protocol/version | Adds golf meaning while preserving translations, media and exercise identity |
| `GolfPlan` | One-to-one `Routine`; optional goal FK | Marks golf plans and provides a home for golf metadata; routine remains the owner/date source |
| `GolfPrescription` | One-to-one `SlotEntry`; planned attempts, duration, practice distance/unit, optional success target | Typed golf targets attached to existing planned exercises |
| `GolfSession` | One-to-one `WorkoutSession`; completion state and optional location | Marks golf practice without duplicating session ownership, timestamps or notes |
| `GolfDrillResult` | Golf session FK; golf exercise FK; optional slot entry FK; occurrence order, attempts, successes, optional duration/distance, protocol version and context snapshot | Actual drill outcomes, including repetitions of a drill and unplanned practice |

Use real typed columns for MVP quantities and explicit units. A small validated
context snapshot may preserve target size, distance, drill/protocol name and version
at logging time; do not start with an unrestricted JSON metric engine. Handicap is
an optional manually recorded value, not an automatic official handicap calculation.
Confirm handicap display/range conventions before implementing its validators.

Initially support an attempts/successes protocol for scored putting, chipping or
accuracy drills, and a duration-only protocol for mental practice and timed work.
Every category can contain instructions even when its advanced KPIs are deferred.
Fitness prescriptions/logs continue using wger's existing fields. Launch-monitor
metrics, per-shot records, arbitrary scoring formulas and generalized metric
definitions belong to later iterations.

### Plan and session behavior

1. Create a user-owned routine with custom days and existing slots/entries, plus
   golf extensions for targets. Use existing date-sequence/weekly fitting behavior.
   Start with a fixed repeating week and no automatic skill progression.
2. Open a workout session with the selected routine/day, or no plan for ad hoc
   practice. Create its golf extension through the golf service.
3. Save one result per drill occurrence. A putting example records 30 attempts,
   21 successes, 2 metres practice distance, and the protocol/target context.
   Fitness sets can remain normal `WorkoutLog` records in the same session.
4. Complete the session explicitly and close its timestamps. Count only completed
   golf sessions in golf progress summaries. Avoid creating placeholder fitness
   logs simply to make a golf session appear populated.

Routine advancement currently checks sessions, so verify the distinction between
an open session and a completed session before enabling `need_logs_to_advance` for
golf. Keep it disabled for the first fixed-week MVP. Existing log/statistics screens
will not automatically display golf results; provide golf history and charts.

### Integrity, permissions and history

Enforce positive attempt counts, `0 <= successes <= attempts`, nonnegative durations,
valid units and the required fields for each protocol. Validate that a supplied
slot belongs to the session's selected routine/day and references the result's
exercise. Cross-user routine/day/goal/session references must fail on create and
update. Derive owners from the authenticated user and linked objects.

Preserve historical meaning when a drill or prescription changes by storing the
protocol/context snapshot. Archive used golf drills rather than deleting them;
use protective relationships for referenced golf definitions and nullable plan-entry
links where plan removal must preserve results. Explicitly test deletion through
upstream APIs as well as golf APIs, since existing exercise deletion cascades to
fitness logs. Do not promise retention until those paths are covered. Account
deletion should have a deliberate policy consistent with existing user deletion.

Saving/completing a session should be atomic and retries should not create duplicate
drill occurrences; use a client-supplied result identifier or equivalent uniqueness
contract. Define whether completed results can be corrected and test recalculation.

### Progress representation

Compute basic statistics from persisted results instead of storing duplicate totals:
completed sessions per local week, completed practice minutes, attempts by category,
and success-rate trends for comparable drill protocols/distances/targets. Aggregate
successes divided by attempts, not the average of session percentages. Missing
results are not zeros. Avoid double-counting an exercise tagged with multiple
categories in overall totals; document category totals as overlapping if applicable.

Use the owner's existing `UserProfile.zone_info` for local dates and week boundaries.
Keep durations derived from session timestamps distinct from drill practice duration.
Do not mix drill versions or distances in a trend without an explicit filter.
Reuse chart styling and aggregation patterns from measurements, but keep session
outcomes in golf results: a generic measurement does not capture drill, denominator,
session, plan or protocol context. Standalone fitness/body measurements remain in
`wger.measurements`.

### Future coaching and teams

Study gym trainer workflows and UI patterns, but do not equate a gym membership
with a golf coaching authorization. Current profiles point to one gym, and gym
configuration models have one-to-one user links; they are not a general multi-team
membership system.

Later add `Team`, `TeamMembership` (user/team/role), and explicit coaching
relationships with invitation, acceptance, scope and revocation. Keep each player
as the owner of their plans/results. Assignments should reference a versioned
template and create player-owned plan instances with provenance. Group sessions
need participant-specific results. Add centralized access policies and audit records
before enabling coach reads/writes; deny access after revocation. Team comparisons
require opt-in visibility and comparable result protocols. MVP owner-only APIs do
not grant coaches access automatically.

## 4. MVP scope and prioritized milestones

The first release supports an individual golfer using an authenticated responsive
web interface. Coaches, teams, official handicap calculation, tournament scoring,
mobile app extensions, sensor integrations, advanced progression and private custom
exercise sharing are outside this release.

Each milestone should be separately reviewable and tested before the next begins.
Schema migration execution and dependency changes still require approval.

| Priority / milestone | Deliverable | Acceptance and focused tests |
| --- | --- | --- |
| 1. Foundation and player profile | Register `wger.golf`; profile model, owner-only GET/PATCH API and responsive profile form using existing login | Existing account flows still work; anonymous/cross-user access fails; optional fields validate; existing users work without a pre-created golf profile |
| 2. Curated golf library | Category taxonomy, exercise extensions, small representative drill dataset with translations, attribution and protocols; searchable/filterable list/detail | Every category supported; stable identifiers and repeatable import; public/private content policy explicit; edits limited to authorized curators; existing exercise API unchanged |
| 3. Individual plans | Golf routine creation/editing, ordered days/drills and typed targets; weekly view and goals | Ownership and foreign-key mismatch tests; weekly schedule correct; invalid targets rejected; regular fitness plans unaffected |
| 4. Practice logging | Planned/ad hoc sessions, attempts/successes and duration protocols, completion, corrections and history | Invalid counts/units rejected; cross-owner and wrong-plan references rejected; duplicate retries safe; history survives plan edits/removal; session end/start validated |
| 5. Basic progress | Frequency, minutes and filtered success-rate trend with empty states | Weighted rates correct; incomplete sessions excluded; local week/year/DST boundaries correct; no double counts or cross-player disclosure |
| 6. Release validation and self-hosting guide | End-to-end golfer workflow, backup/restore procedure, pinned deployment design and documented upgrades | Mobile viewport and keyboard checks; relevant upstream regressions; migrations tested in disposable PostgreSQL only after approval; restore rehearsal before deployment |

Keep milestone 2's dataset small: a useful drill for each category, with scored
putting/chipping examples and a timed mental drill. The MVP is complete when a new
user can sign in, create a player profile, choose drills, create a weekly plan,
record a session and see progress without using a shell or database editor.

### Recommended first implementation task

Implement milestone 1 only: a minimal `wger.golf` app and optional player profile
extension with owner-only API/form, existing authentication integration, and tests
for creation, validation, anonymous access and user isolation. Use an explicit
get-or-create service rather than requiring a backfill or changing upstream user
creation signals. Keep only handicap, handedness, home club and distance preference
in the first profile; use existing user fields for name and email.

Add the migration file for review, but request approval before applying it. Confirm
an isolated test database/settings before running model tests; do not run migrations
against the development database as an incidental test setup. No new dependencies
or frontend repository are needed for this first task.

## 5. Technical risks and dependencies

| Risk / dependency | Recommended response |
| --- | --- |
| Upstream changes to routines, sessions, auth and React payloads | Keep golf changes additive; pin the inspected baseline; run focused contract/regression tests when integrating upstream changes |
| Exercise synchronization overwrites remote identities and translated content | Give curated local drills stable local UUIDs; do not edit synchronized upstream descriptions as the source of golf metadata; test sync and remote deletion handling before enabling jobs |
| Required existing exercise category and shared catalogue semantics | Keep golf tags separate; choose an explicit local base-category strategy and test fixture/sync identifier conflicts; do not repurpose upstream muscle-category IDs |
| Generic routine copy/export/cache operations omit extension rows | Add a golf-aware transactional copy/export path when exposed; test golf targets and goals are copied appropriately, without copying personal results |
| Fitness statistics/UI ignore golf results | Provide dedicated golf summaries; retain fitness statistics for their original purpose |
| Cascading deletion, plan edits and protocol changes | Protect referenced definitions, retain context snapshots, archive drills, and test all deletion paths |
| CI skips migrations and workflow is scoped to `master` | Add `dev` checks in a later approved implementation change and a separate disposable PostgreSQL migration check; SQLite tests alone are insufficient |
| Separate React and deployment repositories drift | Pin backend/frontend/container versions together; document a compatibility matrix before release |
| Production Docker build does not use `uv.lock` for its wheel resolution and uses mutable base tags | Review reproducibility and image pinning before deployment; do not assume the lockfile fixes the container's dependency set |
| Content licensing and attribution | Retain LICENSE/AUTHORS and per-item attribution; follow repository-declared AGPL-3.0-or-later code, CC-BY-SA documentation, and individual content licenses; include source availability in release planning |

No additional Python/JS dependency is proposed for the initial MVP. Additional
repositories only become necessary when changing packaged React components or
deployment orchestration. Flutter/mobile and PowerSync integration are future work;
new golf data will not appear in those clients automatically.

## 6. Self-hosting considerations

Use a custom Golf Training application image, PostgreSQL, Redis where required,
and an Nginx HTTPS reverse proxy in a future isolated deployment. Persist and back
up PostgreSQL and uploaded media; static assets should be reproducible from a
versioned image. Add Celery worker/beat services only for enabled background jobs.
Do not enable large nutrition or exercise synchronization jobs just to support the
golf MVP.

Maintain deployment overrides separately from upstream Compose files, ideally in
a dedicated deployment repository. Pin releases and review environment-variable
changes against that release. Configure hostname/site URL, timezone, allowed hosts,
CSRF origins, HTTPS cookies, proxy handling, mail delivery and registration policy
before exposure. Provision credentials and signing keys outside source control;
retain upstream attribution and offer the corresponding modified source as required
by the project's license.

Review the bootstrap and entrypoint behavior before the first container start.
Define an explicit approval-controlled initialization/migration step, database
backup, migration test and restore-based rollback procedure. A container restart
must not become an unreviewed schema upgrade. Coordinate web and worker versions
and verify application/database readiness after upgrades.

Document backups and restore checks for both database and media, upload limits,
resource usage, log retention, mail setup, health checks and source/version records.
Coaching data export/deletion and privacy controls should precede multi-player
access. All container, schema and deployment work remains a future task requiring
the approvals specified in `/opt/data/AGENTS.md`.

## 7. Evidence and validation references

Primary local references: `README.md`, `pyproject.toml`, `package.json`,
`settings/{README.md,settings_global.py,main.py,local_dev.py,ci.py}`,
`wger/urls.py`, `wger/core/models/profile.py`, `wger/core/views/react.py`,
`wger/core/templates/template.html`, `wger/exercises/{models,api,sync.py}`,
`wger/manager/{models,api,managers.py,helpers.py}`, `wger/measurements/models`,
`wger/gym/models`, `wger/utils/{permissions.py,viewsets.py}`,
`wger/tasks.py`, `.github/workflows/ci.yml`, and `extras/docker` documentation,
Dockerfiles and production entrypoint.

External primary documentation reviewed on 2026-10-25:

- [Backend development](https://wger.readthedocs.io/en/latest/development/backend.html)
- [Frontend development and separate React source](https://wger.readthedocs.io/en/latest/development/frontend.html)
- [Docker installation](https://wger.readthedocs.io/en/latest/installation/docker.html)
- [Deployment stack repository](https://github.com/wger-project/docker)

This documentation-only task is validated by reviewing source references, checking
required section coverage and local paths, and inspecting Git status/diff. Application
tests are not run because application functionality is unchanged. No runtime,
migration, browser or deployment success is claimed.

## 8. Milestone 1 implementation progress (2026-10-25)

The initial backend foundation is implemented in `wger.golf`. Registration in
`settings/settings_global.py` and the namespaced API include in `wger/urls.py`
are the only existing application integration points changed. No frontend, drill,
plan, coaching or analytics features are included in this milestone.

### Implemented model

`GolfPlayerProfile` links one-to-one to `settings.AUTH_USER_MODEL`, using the
reverse relation `user.golf_profile`. It is optional for existing users and created
only on a valid authenticated write, without changing upstream user signals.
The requested milestone fields supersede the earlier illustrative profile fields:
home club and preferred distance unit remain deferred.

- `handicap_index`: nullable decimal with one decimal place; accepted application
  range is -10.0 to 54.0 inclusive. Negative values represent plus handicaps.
  The lower bound is an application policy, not an official handicap rule.
- `playing_hand`: `right` or `left`, default `right`.
- `training_goals`: optional text, at most 2,000 characters, default empty string.
- `created_at` and `updated_at`: server-managed timestamps.
- `user`: unique owner; deleting the user cascades to the golf profile.

Field validators cover API and model validation. Database check constraints also
enforce the handicap range and permitted playing hands, and the one-to-one relation
enforces uniqueness. The initial migration is prepared in
`wger/golf/migrations/0001_initial.py`; it was initially left unapplied. See the
environment milestone below for its separately approved local application.

### Implemented API contract

The single endpoint is `/api/v2/golf/profile/` (URL name `golf:profile`).

| Method | Behavior |
| --- | --- |
| `GET` | Return the authenticated user's profile (200), or 404 if absent; never create a profile on a read |
| `POST` | Create or partially update the current user's profile |
| `PUT` | Create or update the current user's profile; optional omitted fields follow DRF model serializer defaults on creation and retain existing values on update |
| `PATCH` | Create or partially update the current user's profile |

Writes return 201 when creating and 200 when updating. An empty write is valid
and creates a profile with defaults. To clear optional values, send
`{"handicap_index": null}` or `{"training_goals": ""}`. Invalid input returns 400
without creating a profile. Upserts validate input before calling the transactional
`update_or_create`, with ownership fixed to `request.user`.

Responses contain `id`, `user`, `handicap_index`, `playing_hand`, `training_goals`,
`created_at` and `updated_at`. IDs, owner and timestamps are read-only; supplied
values for these fields are ignored under standard DRF serializer behavior.
Neither URL IDs nor query parameters select a different player's profile. There
are no list, detail-by-ID or delete endpoints. Authentication uses the existing
DRF configuration, including CSRF protection for browser session writes.
Unauthenticated requests are rejected (403 with the current session-first setup).

Example JSON write body:

```json
{
  "handicap_index": "18.4",
  "playing_hand": "left",
  "training_goals": "Improve putting consistency"
}
```

### Validation status and next steps

Added 20 model/API tests in `wger/golf/tests/test_profile.py`, using existing wger
test fixtures. Coverage includes creation, retrieval, each upsert method, partial
updates, timestamps, boundary and invalid handicaps, optional fields, hand/goal
validation, database constraints, anonymous access, owner spoofing, user isolation,
malformed payloads, session CSRF protection and unsupported routes/methods.

After explicit approval, a project-local environment was created from `uv.lock`
using `uv sync --locked --group dev --python /usr/bin/python3.12`. Python 3.12.3,
Django 6.0.8 and DRF 3.18.2 were used for verification. uv 0.13.5 is installed under
`.cache/golf-tools/`; its package cache and temporary build files are also inside
the project. `.venv/` and `.cache/` are already ignored by Git. Neither dependency
manifest nor lockfile changed, and no system Python packages were installed.

The first runtime run exposed that `TextField(max_length=2000)` alone does not
enforce length during model validation. An explicit `MaxLengthValidator(2000)`
was added to `training_goals` and the unapplied migration. The final run passed
all 33 tests: 20 golf tests plus 13 existing core profile/permission tests.
The database was SQLite in memory, with migrations disabled for test table setup;
no existing database was used.

Ruff lint and formatting checks passed for all 11 golf Python files. Django system
checks reported no errors and one warning: `staticfiles.W004`, because the frontend
`node_modules` directory is absent. No frontend dependencies were installed.
`makemigrations golf --check --dry-run` reported no changes, confirming the migration
matches the model; that command did not write or apply migrations. Git diff checks,
syntax, whitespace and static field/constraint checks also passed.

Activate the environment with `source .venv/bin/activate`. To reproduce the isolated
checks from the project root without selecting an existing database:

```bash
TMPDIR="$PWD/.cache/golf-tmp" .venv/bin/python -B - <<'PY'
import os
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings.ci'

import django
from django.conf import settings

settings.DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
        'TEST': {'NAME': ':memory:', 'MIGRATE': False},
    }
}
settings.MEDIA_ROOT = os.path.join(os.getcwd(), '.cache', 'test-media')
django.setup()

from django.core.management import call_command
from django.test.utils import get_runner

call_command('check')
call_command('makemigrations', 'golf', check=True, dry_run=True)
runner = get_runner(settings)(verbosity=1, interactive=False)
raise SystemExit(bool(runner.run_tests([
    'wger.golf.tests',
    'wger.core.tests.test_user_profile_api',
    'wger.core.tests.api.test_permission_api',
])))
PY
.venv/bin/ruff check --no-cache wger/golf
.venv/bin/ruff format --check wger/golf
```

At completion of Milestone 1 the initial migration was unapplied; its execution
was subsequently verified on the separately approved development SQLite database
in the environment milestone below. PostgreSQL behavior remains unverified.
Existing databases and deployments still require separate approval for migrations.

## 9. Milestone 2: local development environment (2026-10-25)

This user-requested environment milestone prepares the existing application for
manual testing before additional golf features; the golf library feature roadmap
in section 4 remains unchanged.

- Added `settings.golf_dev`: standalone development settings based on upstream
  globals, with a fixed project-local SQLite database, local media/static paths,
  in-memory cache, console email, local HTTP/CSRF/CORS configuration and disabled
  background sync. No production or untracked settings are imported.
- Reused the locked Python `.venv`. Installed nvm 0.40.8 under `.cache/nvm` at the
  user's request, without shell-profile changes; `.nvmrc` pins Node 22.23.4.
- Installed the existing frontend from `package-lock.json` and used isolated Sass
  1.106.1 tooling to build upstream Bootstrap CSS. The React package is 26.10.4.
  Generated CSS and source maps are now ignored. No framework or dependency
  manifest/lockfile changes were required.
- After explicit approval, initialized only
  `db/golf-dev/database.sqlite3` using upstream bootstrap with static processing
  disabled. All migrations, including golf, and bundled fixtures completed. The
  site URL is localhost:8001. No optional online nutrition download was performed.
- Added `settings.golf_test` for reproducible in-memory backend tests, independent
  of the persistent development database.

PostgreSQL, Redis, Celery, Docker, Nginx and PowerSync are not required for this
local workflow. No system packages, containers, production services, SSH settings
or firewall rules were changed. All local tool caches stay under the project.

Start from a VS Code Remote-SSH terminal:

```bash
cd /opt/data/golf-training
source .venv/bin/activate
python manage.py runserver 127.0.0.1:8001 --settings=settings.golf_dev
```

Forward remote port 8001 privately in VS Code and open `http://localhost:8001`.
The verification instance was started with `--noreload` and bound only to
`127.0.0.1:8001`; reuse it or stop that instance before starting another.
Full setup, account/API examples, frontend rebuild, database approval boundaries,
and test commands are documented in [GOLF_TRAINING_DEV.md](GOLF_TRAINING_DEV.md).

Verification results:

- All 33 backend tests passed with in-memory SQLite (20 golf and 13 existing
  profile/permission tests). Ruff lint and formatting checks passed for the golf
  code and new settings. Django checks report no issues; the development database
  has no pending migrations and the golf migration matches the current model.
- HTTP checks passed for the landing, login and registration pages; Bootstrap CSS
  and JS, HTMX, packaged React JS/CSS, English React translations and icon CSS.
- Real form login established a session. Anonymous access and CSRF-less writes
  were rejected; golf profile creation/retrieval/update and invalid-handicap
  rejection passed over HTTP. Only a temporary smoke-test account was created
  for these checks and it was removed afterward.
- The frontend build succeeds with upstream Sass deprecation warnings. Full
  interactive React rendering and visual behavior need a manual browser check.
  JWT/OIDC signing, translated Django message compilation and PostgreSQL-specific
  behavior have not been verified. Browser sessions work without these additions.

There is no known blocker for local browser/session API testing. Further schema
changes, dependency installs and deployments retain the workspace approval rules.
