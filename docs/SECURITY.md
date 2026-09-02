# Security Model

How credentials, media, and telemetry are handled, and what has to be tightened before this runs anywhere exposed. Internal reference — see the [README](../README.md) for setup.

---

## Credential handling

| Credential | Storage | Notes |
|------------|---------|-------|
| Azure Video Indexer | **None** | Obtained at call time: `DefaultAzureCredential` → ARM token → short-lived account token |
| Azure AI Search key | Environment | `.env`, gitignored; move to Key Vault when deployed |
| Azure AI Foundry key | Environment | Same |
| App Insights connection string | Environment | Same |
| LangSmith key | Environment | Same |

`.env` is gitignored and must stay that way. `.env.example` holds placeholders only and is the file that gets committed.

The Video Indexer path is the one worth preserving as the pattern for everything else: no VI secret exists anywhere on disk, because access is derived from an identity at call time. `DefaultAzureCredential` resolves that identity from environment variables, workload identity, managed identity, or an `az login` session, in that order — so the same code works locally and in a deployed container without a code change.

When deploying, prefer a **managed identity** for every service that supports it, and put the remaining keys in **Azure Key Vault** rather than an `--env-file`.

---

## Data handling

**Downloaded media** is written to a local scratch file and deleted after upload to Video Indexer. Cleanup currently runs only on the success path, so a crash between download and upload leaves the `.mp4` on disk. Treat the working directory as sensitive until that is fixed with a `finally` block.

**Uploaded videos** are created with `privacy: "Private"` in Video Indexer, but are never deleted after processing. Storage grows without bound — prune the VI account periodically until automatic cleanup lands.

**Transcripts and OCR text** are sent to the configured LLM endpoint. If you audit unreleased or confidential creative, confirm the data-handling terms of your Azure AI deployment cover it.

**Telemetry** exports traces to Application Insights and, when enabled, full prompts and completions to LangSmith. Prompts contain the entire transcript. Set `LANGCHAIN_TRACING_V2=false` when handling anything confidential.

---

## Before exposing the API

`POST /audit` currently has **no authentication and no rate limiting**, and it accepts an arbitrary URL that the server then fetches. Both matter:

- **Unauthenticated access** means anyone who can reach the port can spend your Azure quota — Video Indexer minutes and LLM tokens are the expensive part.
- **Server-side fetch of a user-supplied URL** is SSRF-adjacent. The node does check for a YouTube host before downloading, but that check is a string containment test, not a parsed-host allowlist.

Minimum hardening before this listens on anything public:

- [ ] Authenticated gateway in front of the service
- [ ] Rate limiting per caller
- [ ] Parse the URL and allowlist the host properly, rather than substring matching
- [ ] Restrict container egress to the domains actually needed
- [ ] Run as a non-root user with a read-only root filesystem apart from the scratch directory
- [ ] Cap concurrency to your Video Indexer quota so the service cannot DoS itself
- [ ] Secrets from Key Vault, not environment files

---

## Known security-relevant gaps

Documented rather than fixed; tracked on the roadmap.

| Gap | Risk | Interim mitigation |
|-----|------|--------------------|
| No auth on the API | Quota exhaustion by anyone who can reach it | Keep it bound to localhost or behind a gateway |
| Substring host check | Weak validation on a server-side fetch | Restrict egress; parse the host before v0.3 |
| Temp file not removed on failure | Media persists on disk | Ephemeral containers; clean the workdir |
| VI assets never deleted | Unbounded retention of uploaded media | Scheduled pruning |
| No wait cap on the polling loop | A stalled job pins a worker indefinitely | External request timeout |
| Prompts sent to LangSmith | Transcript leaves your tenancy | Disable tracing for confidential work |
