# Abnormal File Vault — Requirements & Implementation Plan

> **Scope of this document:** Requirements formulation and phased implementation plan only. No implementation code.

---

## 1. Project Overview

**Abnormal File Vault** is a secure, efficient file-hosting API built on Django and Django REST Framework (DRF), backed by SQLite, and runnable via Docker. The exercise extends an existing starter project with three capabilities:

1. **File deduplication** — reduce redundant storage
2. **Search & filtering** — retrieve files by multiple attributes
3. **Call & storage limits** — protect API health and per-user disk usage

All new behavior must align with the **API Product Requirements (PRD)** contract: request/response shapes, HTTP status codes, headers, and error messages.

---

## 2. Business Context

| Goal | How the product supports it |
|------|-----------------------------|
| Lower storage cost | Deduplicate identical file content (SHA-256) so one physical copy serves many logical uploads |
| Faster investigations | Filter/search by name, type, size, and upload window |
| Scalable operations | Per-user rate limits and storage quotas prevent abuse and unbounded growth |

---

## 3. Technical Constraints (from PRD)

| Area | Requirement |
|------|-------------|
| Backend | Django + DRF |
| Database | SQLite |
| Deployment | Docker (existing `docker-compose` / `Dockerfile`) |
| User identity | HTTP header `UserId` (no JWT/session auth for this exercise) |
| Default rate limit | **2 calls per 1 second** per user (`x` calls per `n` seconds — configurable) |
| Default storage limit | **10 MB per user** (configurable) |
| Rate-limit error | HTTP **429**, body message **`"Call Limit Reached"`** |
| Storage-quota error | HTTP **429**, body message **`"Storage Quota Exceeded"`** |

---

## 4. Current Starter Baseline (gap analysis)

What exists today vs. what the PRD requires:

| Capability | Starter today | PRD target |
|------------|---------------|------------|
| CRUD endpoints | `GET/POST/GET{id}/DELETE` on `/api/files/` via `FileViewSet` | Same routes + two custom actions |
| `File` model fields | `id`, `file`, `original_filename`, `file_type`, `size`, `uploaded_at` | Add `user_id`, `file_hash`, `reference_count`, `is_reference`, `original_file` |
| User scoping | None — global queryset | All operations scoped to `UserId` header |
| Deduplication | Every upload stores a new physical file | SHA-256 hash; references for duplicates |
| Search/filter | None | Query params on list endpoint |
| Rate limiting | None | 2 req/s per `UserId` |
| Storage quota | None | 10 MB logical usage per `UserId` |
| Storage stats | None | `GET /api/files/storage_stats/` |
| File types list | None | `GET /api/files/file_types/` |

---

## 5. Functional Requirements

### 5.1 User identification & scoping

- Every API request **must** be attributable to a user via the **`UserId` HTTP header**.
- **List, retrieve, delete, upload, storage_stats, and file_types** must only consider files belonging to that user.
- Missing or invalid `UserId` handling should be defined during implementation (PRD assumes header is present for “authenticated” calls; recommend **400** if absent for consistency).

### 5.2 Feature 1 — File deduplication

**Objective:** Detect duplicate content at upload time and avoid storing multiple copies on disk.

| ID | Requirement |
|----|-------------|
| D1 | On upload, compute **SHA-256** hash of file content (`file_hash`). |
| D2 | If content with the same hash **already exists** for this user (or globally for physical blob — see design note below), create a **reference record** instead of writing a new file to storage. |
| D3 | Reference records set `is_reference: true` and point to the canonical record via `original_file` (UUID of the canonical `File`). |
| D4 | Canonical (non-reference) records set `is_reference: false`, `original_file: null`. |
| D5 | Multiple uploads of the same bytes share one **physical** `file` path on disk. |
| D6 | Maintain **`reference_count`** on the canonical file: number of logical records pointing at that blob (including self or excluding — implement consistently with API examples). |
| D7 | **Delete** must decrement reference counting; remove physical media only when **no references remain**. |
| D8 | Serializer responses for all file endpoints must expose dedup fields per API contract. |

**Design decision (locked):** Deduplication is **per-user**. The same bytes uploaded by two different `UserId` values produce separate physical storage. Within one user, matching `file_hash` reuses the canonical blob and creates reference rows.

**Storage accounting for dedup:**

- **`total_storage_used`**: sum of unique physical content sizes attributed to the user (after dedup).
- **`original_storage_used`**: sum of `size` of every file row owned by the user (as if no dedup).
- **`storage_savings`**: `original_storage_used - total_storage_used`
- **`savings_percentage`**: `(storage_savings / original_storage_used) * 100` when denominator > 0, else `0`.

### 5.3 Feature 2 — Search & filtering

**Objective:** Efficient retrieval on `GET /api/files/` using combinable query parameters.

| ID | Parameter | Behavior |
|----|-----------|----------|
| S1 | `search` | Case-insensitive **partial** match on `original_filename` |
| S2 | `file_type` | Exact match on MIME type (e.g. `application/pdf`) |
| S3 | `min_size` | File size ≥ value (bytes) |
| S4 | `max_size` | File size ≤ value (bytes) |
| S5 | `start_date` | `uploaded_at` ≥ value (ISO 8601 with timezone) |
| S6 | `end_date` | `uploaded_at` ≤ value (ISO 8601 with timezone) |
| S7 | — | **All supplied filters apply together** (AND logic) |
| S8 | — | Optimize for large datasets: DB indexes on filtered fields (`user_id`, `original_filename`, `file_type`, `size`, `uploaded_at`) |

**Response:** Paginated DRF format:

```json
{
  "count": <int>,
  "next": <url|null>,
  "previous": <url|null>,
  "results": [ /* File objects */ ]
}
```

### 5.4 Feature 3 — Call & storage limits

**Objective:** Protect service health via configurable per-user limits.

#### 5.4.1 API call rate limit

| ID | Requirement |
|----|-------------|
| R1 | Track request count per `UserId` in a sliding or fixed window of **`n` seconds**. |
| R2 | Default: **`x = 2`**, **`n = 1`** (2 calls per second). |
| R3 | `x` and `n` must be **easily configurable** (e.g. Django settings / env vars). |
| R4 | When exceeded → **429** with message **`"Call Limit Reached"`**. |
| R5 | Applies to API requests (define whether all `/api/files/*` routes or entire API — recommend **all file vault endpoints**). |

#### 5.4.2 Per-user storage quota

| ID | Requirement |
|----|-------------|
| Q1 | Track **total logical or deduplicated storage** per user (PRD: “size of all files stored by each user”; quota check on upload — use **deduplicated `total_storage_used`** increment for *new unique content*, and full `size` toward quota for new logical files per PRD intent). |
| Q2 | Default limit: **10 MB** per user. |
| Q3 | Limit value **easily configurable** (settings / env). |
| Q4 | **Reject upload** if adding the file would exceed quota → **429** with **`"Storage Quota Exceeded"`**. |
| Q5 | **References** to existing global content should not consume additional physical storage; quota impact should reflect **new bytes** introduced for that user (align with `total_storage_used` semantics). |
| Q6 | On delete, reduce tracked usage accordingly. |

**Configurable settings (recommended names):**

| Setting | Default | Purpose |
|---------|---------|---------|
| `RATE_LIMIT_CALLS` | `2` | `x` |
| `RATE_LIMIT_WINDOW_SECONDS` | `1` | `n` |
| `STORAGE_QUOTA_MB` | `10` | Per-user cap |

---

## 6. API Contract Summary

Base path: **`/api/files/`**  
Authentication: header **`UserId: <string>`**

### 6.1 Standard resource endpoints

| Method | Path | Purpose | Success |
|--------|------|---------|---------|
| `GET` | `/api/files/` | List files (filtered, paginated) | 200 |
| `POST` | `/api/files/` | Upload with dedup + quota | 201 |
| `GET` | `/api/files/{id}/` | File details | 200 |
| `DELETE` | `/api/files/{id}/` | Delete with ref-count cleanup | 204 |

### 6.2 Custom actions

| Method | Path | Purpose | Success body |
|--------|------|---------|--------------|
| `GET` | `/api/files/storage_stats/` | Deduplication-aware usage stats | See §6.4 |
| `GET` | `/api/files/file_types/` | Distinct MIME types for user | JSON array of strings |

### 6.3 File object schema (all file responses)

| Field | Type | Notes |
|-------|------|-------|
| `id` | UUID string | Primary key |
| `file` | string (URL/path) | Media path; shared when deduplicated |
| `original_filename` | string | Client original name |
| `file_type` | string | MIME type |
| `size` | integer | Bytes |
| `uploaded_at` | ISO 8601 datetime | UTC with fractional seconds |
| `user_id` | string | From `UserId` header |
| `file_hash` | string | SHA-256 hex |
| `reference_count` | integer | Canonical ref count |
| `is_reference` | boolean | |
| `original_file` | UUID string or null | Set when `is_reference` is true |

### 6.4 Storage stats response

```json
{
  "user_id": "<string>",
  "total_storage_used": <bytes>,
  "original_storage_used": <bytes>,
  "storage_savings": <bytes>,
  "savings_percentage": <float>
}
```

### 6.5 Error responses

| Condition | Status | Message |
|-----------|--------|---------|
| Rate limit exceeded | 429 | `Call Limit Reached` |
| Storage quota exceeded | 429 | `Storage Quota Exceeded` |

Other errors (implementation detail): 400 for missing file / bad input; 404 for wrong user or unknown id.

---

## 7. Data Model Requirements

Extend `File` (or companion models) to support:

| Field | Purpose |
|-------|---------|
| `user_id` | Owner; indexed |
| `file_hash` | SHA-256; indexed for dedup lookup |
| `is_reference` | Whether row points to another canonical file |
| `original_file` | FK (nullable) to canonical `File` |
| `reference_count` | On canonical rows only |

**Optional supporting model:** `UserStorageStats` or compute on the fly from queryset aggregates.

**Indexes:** `(user_id)`, `(user_id, file_hash)`, `(user_id, original_filename)`, `(user_id, file_type)`, `(user_id, size)`, `(user_id, uploaded_at)`.

---

## 8. Non-Functional Requirements

| ID | Requirement |
|----|-------------|
| NF1 | Docker build and `docker-compose up` remain working |
| NF2 | SQLite migrations versioned and reproducible |
| NF3 | Rate-limit state: in-memory acceptable for single-process dev; document limitation for multi-worker production |
| NF4 | Hashing large files: stream/chunk reads to avoid memory spikes |
| NF5 | Media files persist via existing volume mount pattern |

---

## 9. Implementation Plan (phased)

### Phase 0 — Foundation & configuration

- [ ] Add settings for rate limit (`x`, `n`) and storage quota (MB)
- [ ] Document env var overrides in README (optional, not code in plan)
- [ ] Define `UserId` extraction helper/middleware used by all views

**Exit criteria:** Settings load defaults; missing `UserId` behavior documented.

---

### Phase 1 — Data model & migrations

- [ ] Extend `File` model with PRD fields and self-FK for `original_file`
- [ ] Create and apply migrations
- [ ] Add DB indexes for filter and dedup fields

**Exit criteria:** Admin/shell can create records with new fields; starter data migrates cleanly.

---

### Phase 2 — User scoping & serializers

- [ ] Scope all querysets by `UserId`
- [ ] Update `FileSerializer` (and nested representation of `original_file`) to match API contract
- [ ] Ensure upload sets `user_id` from header

**Exit criteria:** User A cannot see or delete User B’s files.

---

### Phase 3 — File deduplication (upload + delete)

- [ ] Implement SHA-256 on upload (chunked)
- [ ] Canonical vs reference creation logic
- [ ] `reference_count` increment/decrement on create/delete
- [ ] Physical file deletion only when last reference removed

**Exit criteria:** Duplicate uploads return `is_reference: true`, share `file` URL; disk holds one copy.

---

### Phase 4 — Storage quota enforcement

- [ ] Compute per-user usage (deduplicated + logical totals for stats)
- [ ] Pre-upload quota check → 429 `Storage Quota Exceeded`
- [ ] Adjust usage on delete

**Exit criteria:** User cannot upload past 10 MB default; references handled correctly.

---

### Phase 5 — Rate limiting

- [ ] Middleware or DRF throttle keyed on `UserId`
- [ ] Configurable window and call count
- [ ] 429 `Call Limit Reached` with exact message

**Exit criteria:** Third request within 1 second fails; limit configurable via settings.

---

### Phase 6 — Search & filtering

- [ ] DRF `FilterBackend` or custom `get_queryset` for all query params
- [ ] ISO 8601 date parsing with timezone
- [ ] Combined AND filters; pagination unchanged

**Exit criteria:** Integration tests or manual matrix of filter combinations pass.

---

### Phase 7 — Custom endpoints

- [ ] `GET storage_stats/` — aggregate fields per §5.2 formulas
- [ ] `GET file_types/` — distinct `file_type` for user

**Exit criteria:** Response JSON matches PRD examples structurally.

---

### Phase 8 — Verification & submission prep

- [ ] Manual test script against all endpoints (dedup, filters, limits, stats)
- [ ] Run `python manage.py test` if tests added
- [ ] Docker smoke test
- [ ] Run `create_submission_zip.py` per README

**Exit criteria:** All PRD API behaviors demonstrable; zip builds successfully.

---

## 10. Acceptance Criteria (checklist)

### Deduplication
- [ ] Same file bytes uploaded twice → one physical file, two API records
- [ ] Second record has `is_reference: true` and correct `original_file`
- [ ] `reference_count` accurate on canonical file
- [ ] Delete reference only removes row; delete last reference removes disk file

### Search & filtering
- [ ] `search` is case-insensitive substring on filename
- [ ] `file_type`, size range, date range work alone and combined
- [ ] List returns paginated `count`, `next`, `previous`, `results`

### Limits
- [ ] >2 requests in 1 second per `UserId` → 429 `Call Limit Reached`
- [ ] Upload exceeding 10 MB per user → 429 `Storage Quota Exceeded`
- [ ] Limits configurable without code changes (settings/env)

### API contract
- [ ] All responses include required fields
- [ ] `storage_stats` and `file_types` endpoints work
- [ ] `UserId` required on all documented endpoints

---

## 11. Suggested Testing Matrix (manual)

| # | Scenario | Expected |
|---|----------|----------|
| 1 | Upload unique file | 201, `is_reference: false`, ref count 1 |
| 2 | Upload duplicate content | 201, `is_reference: true`, same `file` path |
| 3 | List with `search=doc` | Only matching filenames for user |
| 4 | List with `file_type` + `min_size` | AND filter applied |
| 5 | Burst 3 API calls in 1s | Third returns 429 call limit |
| 6 | Fill quota to 10MB, upload again | 429 storage quota |
| 7 | `storage_stats` after dedup | `storage_savings` > 0 when duplicates exist |
| 8 | `file_types` | Unique MIME list for user only |
| 9 | Delete reference then canonical | Disk cleanup only when appropriate |

---

## 12. Assumptions & Open Questions

| # | Topic | Assumption / question |
|---|--------|---------------------|
| 1 | Dedup scope | **Per-user** — canonical lookup on `(user_id, file_hash)` where `is_reference=False` |
| 2 | Quota on reference upload | New logical file counts toward `original_storage_used`; only new unique bytes toward quota enforcement (confirm during implementation) |
| 3 | Missing `UserId` | Return 400 Bad Request (PRD silent — pick one behavior and stay consistent) |
| 4 | Rate limit scope | All `/api/files/*` endpoints count toward limit |
| 5 | `reference_count` on reference rows | PRD shows `1` on reference in list example — clarify whether count is stored on canonical only (recommended) |
| 6 | Pagination | Use DRF default page size unless PRD specifies otherwise |

---

## 13. Deliverables (this exercise)

| Deliverable | Description |
|-------------|-------------|
| Backend implementation | Django app satisfying §5–§6 |
| `plan.md` | This document |
| Submission zip | Via `create_submission_zip.py` |
| Gen AI video | Process documentation (not app demo) per README |

---

## 14. Reference

- **Source PRD:** `Abnormal File Vault – API Product Requirements Backend.pdf`
- **Starter repo:** `dplat-file-vault-coding-challenge` (Django `files` app, Docker, SQLite)
