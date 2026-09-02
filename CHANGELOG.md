# Changelog

All notable changes to this project are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

### Added
- `README.md` — full project documentation: architecture diagrams, quickstart, API reference, configuration table, deployment guide, roadmap.
- `docs/ARCHITECTURE.md` — deep dive on the state machine, data flow, and design decisions.
- `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, `SECURITY.md` — community health files.
- `.env.example` — environment template with placeholder values.
- `LICENSE` — MIT.
- GitHub issue and pull request templates.

### Changed
- `.gitignore` expanded to cover `__pycache__`, tool caches, downloaded media scratch files, editor directories, and draw.io backups.

### Known issues
See the *Project status* table in the [README](README.md#-project-status). The pipeline has not yet been verified end-to-end against live Azure resources.

---

## [0.1.0] — 2026-09-03

First working skeleton of the compliance agent. Every major component exists; the end-to-end run is not yet verified.

### Added

**Agent orchestration**
- `VideoAudit` state schema as a `TypedDict`, with `operator.add` reducers so `compliance_result` and `error` accumulate across nodes instead of overwriting.
- `Video_indexer_node` — downloads the video, uploads it to Azure Video Indexer, polls for completion, and normalizes transcript, OCR text, and metadata into state.
- `audit_content_node` — builds a retrieval query from transcript plus OCR, pulls the top 3 policy chunks from Azure AI Search, and prompts the LLM for a grounded verdict. Strips markdown code fences from the completion before parsing and fails closed to `FAIL` when parsing breaks.
- `create_graph()` — compiles a `StateGraph` running the indexer node into the audit node.

**Services**
- `video_indexer` client: `DefaultAzureCredential` → ARM token → Video Indexer account token exchange (no stored VI secret), `yt-dlp` download to a scratch file, upload with `privacy: "Private"`, a 30-second polling loop, and a flattening step that turns raw insights into transcript lines and OCR text.

**Retrieval**
- `index_documents.py` — offline ETL: loads every PDF in `Backend/data/`, splits at 1000 characters with 200 of overlap, embeds with `text-embedding-3-small`, and upserts into Azure AI Search with a `source` metadata tag.
- Seed policy corpus: FTC influencer/endorsement guidance and YouTube ad specifications.

**API**
- FastAPI application with `POST /audit` and `GET /health`, Pydantic request and response models, per-request UUID4 session correlation, and auto-generated OpenAPI docs.

**Observability**
- Azure Monitor / OpenTelemetry bootstrap, configured before the graph is imported so downstream LangChain and HTTP calls are instrumented.
- LangSmith tracing via environment variables.

**Tooling**
- `uv` project with a committed `uv.lock`; Python pinned to 3.12.
- `main.py` CLI entrypoint.
- `nodes.drawio` editable architecture diagram.

[Unreleased]: https://github.com/ArChIt690/Video_Summarizer_for_ads_llmops/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/ArChIt690/Video_Summarizer_for_ads_llmops/releases/tag/v0.1.0
