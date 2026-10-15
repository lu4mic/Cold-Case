# Cold Case

Cold Case is an AI-powered mystery game in which a player investigates a case,
interrogates suspects, discovers clues, and makes a final accusation.

The most important design rule is:

> The backend owns the truth. The language model can produce dialogue and
> structured case suggestions, but it never decides the actual game state or
> whether an accusation is correct.

The repository already contains typed internal/public models, PostgreSQL storage
and an Alembic migration, public read routes, clue discovery, and final accusation
logic. Case generation and suspect interrogation are not implemented yet. There
is a static-check CI workflow; database and gameplay verification are not yet
automated. Existing behavior still needs the verification tracked below.

## Start here

Follow the [MVP execution roadmap](https://github.com/lu4mic/Cold-Case/issues/8).
It links each task's scope, prerequisites, security requirements and acceptance
criteria. Start with [offline checks and PostgreSQL CI](https://github.com/lu4mic/Cold-Case/issues/2),
then validated case creation and gameplay hardening, interrogation, a minimal
playable interface, and local packaging. Check prerequisites before starting work.

## Prerequisites

- Linux
- Python 3.12 or newer
- PostgreSQL for API startup, migrations and database-backed route tests
- `uv` for Python versions, virtual environments, and dependencies

## Install uv on Linux

Use the official standalone installer:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Restart the terminal, or load the usual local binary directory for the current
shell:

```bash
export PATH="$HOME/.local/bin:$PATH"
```

Confirm the installation:

```bash
uv --version
```

If `curl` is unavailable, install `uv` with `pipx` instead:

```bash
python3 -m pip install --user pipx
python3 -m pipx ensurepath
pipx install uv
```

Restart the terminal and run `uv --version` again.

## Set up the project

From the repository root:

```bash
uv python install 3.12
uv sync --all-groups
```

`uv sync` creates a local `.venv` and installs the application and development
dependencies declared in `pyproject.toml`.

Run project tools without manually activating the virtual environment:

```bash
uv run pytest
uv run ruff check .
uv run mypy cold_case
```

The repository has model, application-lifetime and API scenario tests. The API
scenario is skipped unless `TEST_DATABASE_URL` points to a disposable PostgreSQL
test database. A passing run with that test skipped does not verify persistence
or route behavior. Do not point tests at a database containing application data:
the scenario creates tables and writes/deletes its own case records.

[Static checks](.github/workflows/static-checks.yml) run Ruff and strict mypy on
pull requests and pushes to `main`, using Python 3.12 and locked dependencies.
The workflow does not start the API, connect to PostgreSQL or call a model.
Passing static checks does not verify gameplay or migrations; automated test and
PostgreSQL coverage remain in [issue #2](https://github.com/lu4mic/Cold-Case/issues/2).

## Configuration

The application reads environment variables directly with `os.environ`. You may
keep local values in a `.env` file, which Git ignores, and load that file when
running a command with `uv run --env-file .env ...`. Never commit real credentials.

Current settings:

```text
DATABASE_URL=postgresql+psycopg://cold_case:password@localhost:5432/cold_case
```

The database URL above is an example for a local development database. Startup
requires only `DATABASE_URL`; no AI provider key is needed. No model integration
exists yet, so do not supply a real provider key.

After configuring a local PostgreSQL database and applying the migration, start
the API bound to loopback:

```bash
uv run --env-file .env uvicorn cold_case.main:app --host 127.0.0.1
```

Use `/docs` to inspect the current routes. This is a local development API without
player authentication; do not expose it publicly. UUIDs alone do not authorize
access to a case. Session isolation and gameplay concurrency are tracked in
[issue #4](https://github.com/lu4mic/Cold-Case/issues/4).

## Cost and security boundary

Development and tests must not call paid APIs, paid models or billable trial
endpoints. No model provider has been selected for execution. Existing SDK
dependencies do not authorize API calls. Use offline fixtures for validation;
any actual AI option must be verified free/local, opt-in and bounded, with no
paid fallback. Track that separately from deterministic gameplay so the project
does not claim AI features that are not implemented.

The backend retains the solution and hidden information. Clients receive only
public response models and discovered clues. Model output must be treated as
untrusted suggestions and must not determine game state or accusation outcomes.

## Database migrations

After setting `DATABASE_URL`, create or update the PostgreSQL schema:

```bash
uv run --env-file .env alembic upgrade head
```

Roll back the latest migration:

```bash
uv run --env-file .env alembic downgrade -1
```

Check the current database revision:

```bash
uv run --env-file .env alembic current
```

Application code should use `create_case()` and `get_case()` from
`cold_case.database.queries`. These functions flush changes but do not commit;
the caller keeps explicit control of the transaction.

## Dependency policy

Runtime dependencies are intentionally limited to the MVP in the linked roadmap.
Advanced systems such as RAG, vector databases, LangGraph,
multi-agent orchestration, Redis, and cloud tooling are deliberately excluded.

When dependencies change, use `uv` so `pyproject.toml` and `uv.lock` remain in
sync:

```bash
uv add package-name
uv add --dev package-name
uv remove package-name
uv lock
```
