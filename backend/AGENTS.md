# LocalHub Backend Rules

## Project contract

- Treat `docs/02_3일차_팀프로젝트_개발 의뢰서_전공.pdf` as the product brief.
- Treat `data/raw/서울/SCHEMA.md` and `data/raw/서울/SOURCE.md` as the data contract and attribution record.
- Use the JSON files in `data/raw/서울/` as read-only source data. Never rewrite or normalize them in place.
- Display the required Korea Tourism Organization attribution wherever project documentation or the product presents the dataset source.
- Report specification/data discrepancies instead of silently inventing missing data. In particular, `SOURCE.md` lists a restaurant file and 8,150 total rows, while the supplied directory currently has seven JSON files and 6,518 rows.

## Technology

- Use FastAPI, SQLAlchemy 2.x ORM, SQLite, Pydantic v2, pytest, and httpx.
- Keep routers, services, models, and schemas separate unless the existing code establishes a smaller structure.
- Use typed functions and Pydantic request/response models.
- Use `httpx.AsyncClient` with explicit timeouts for asynchronous external calls.
- Keep configuration in environment variables and provide names only in `.env.example`.

Do not introduce PostgreSQL, MySQL, Redis, Docker, Alembic, JWT, registration, login, admin roles, WebSockets, or a vector database unless the user explicitly changes scope. Do not perform unrelated refactors.

## Required behavior

- Implement an anonymous post board with list, detail, create, update, and delete operations.
- Store each post's `edit_password` in plaintext only because the supplied educational brief explicitly requires it. Compare it for update/delete, but never return or log it.
- Return HTTP 403 for a wrong edit password and HTTP 404 for a missing resource.
- Base location and chatbot answers on imported SQLite data, not on live TourAPI calls.
- Preserve `contentid` as the source identifier. Convert `mapx` to longitude and `mapy` to latitude only at the application boundary or import step.
- Treat blank source strings as missing values where the schema permits it. Do not fabricate addresses, coordinates, images, or restaurant records.
- Send only relevant, minimized database context to an LLM. Never include edit passwords or secrets.

## Quality and scope

- Read nearby code and tests before editing.
- Implement only the requested feature and add tests proportional to its risk.
- Run focused tests first, then the full backend test suite.
- Do not report completion while required tests fail.
- Never commit `.env`, API keys, passwords, tokens, or generated secret values.
- Do not claim compliance with the brief's AI-tool policy. The supplied brief permits only VSCode Copilot and prohibits Codex, which conflicts with this Codex-based workflow; surface that conflict in release results for human resolution.
