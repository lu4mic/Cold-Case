# Cold Case

Cold Case is an AI-powered mystery game in which a player investigates a case,
interrogates suspects, discovers clues, and makes a final accusation.

The most important design rule is:

> The backend owns the truth. The language model can produce dialogue and
> structured case suggestions, but it never decides the actual game state or
> whether an accusation is correct.

This repository is currently in the planning and setup stage. No game features
have been implemented yet.

## Start here

1. Read [ARCHITECTURE.md](ARCHITECTURE.md) for the system design and scope.
2. Follow [DEVELOPMENT_GUIDE.md](DEVELOPMENT_GUIDE.md) one task at a time.
3. Do not begin the next task until the current task's acceptance criteria pass.

## Prerequisites

- Linux
- Python 3.12 or newer
- PostgreSQL (needed when database work begins)
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

The lint and type-check commands can run immediately. `pytest` will report that
no tests were collected until Task 1.1 adds the first tests; that exit status is
expected during setup.

## Configuration

Later tasks will introduce environment variables. The application will read
them directly with `os.environ`; it will not use a settings framework. You may
keep local values in a `.env` file, which Git ignores, and load that file when
running a command with `uv run --env-file .env ...`. Document safe placeholder
values in `.env.example`; never put real API keys or passwords in that file.

Likely settings include:

```text
DATABASE_URL=postgresql+psycopg://cold_case:password@localhost:5432/cold_case
OPENAI_API_KEY=...
```

Do not create or commit real credentials during project setup.

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

Runtime dependencies are intentionally limited to the MVP described in the
architecture. Advanced systems such as RAG, vector databases, LangGraph,
multi-agent orchestration, Redis, and cloud tooling are deliberately excluded.

When dependencies change, use `uv` so `pyproject.toml` and `uv.lock` remain in
sync:

```bash
uv add package-name
uv add --dev package-name
uv remove package-name
uv lock
```
