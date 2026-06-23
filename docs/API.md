# Abnormal File Vault — API Documentation

Base URL (local): `http://localhost:8000`

All file API routes live under **`/api/files/`**.

---

## Authentication

Every endpoint requires the **`UserId`** HTTP header. There is no JWT or session auth in this project.

```http
UserId: your-user-id
```

Requests without `UserId` receive **400** with:

```json
{"error": "UserId header is required"}
```

---

## Rate limiting

- **Default:** 2 requests per 1 second per `UserId` (sliding window, middleware-level).
- **Exceeded:** HTTP **429** with plain text body: `Call Limit Reached`
- **Configure:** `RATE_LIMIT_CALLS`, `RATE_LIMIT_WINDOW_SECONDS` environment variables.

When testing, wait **≥ 1 second** between bursts of more than 2 calls, or use different `UserId` values.

---

## Storage quota

- **Default:** 10 MB per user (logical / `original_storage_used`).
- **Exceeded on upload:** HTTP **429** with plain text: `Storage Quota Exceeded`
- **Configure:** `STORAGE_QUOTA_MB` environment variable.

---

## File object schema

Returned by upload, list, and detail endpoints:

| Field | Type | Description |
|-------|------|-------------|
| `id` | UUID | Primary key |
| `file` | string | Media URL path |
| `original_filename` | string | Name from upload |
| `file_type` | string | MIME type |
| `size` | integer | Size in bytes |
| `uploaded_at` | datetime | ISO 8601 UTC |
| `user_id` | string | Owner (`UserId` header value) |
| `file_hash` | string | SHA-256 hex digest of content |
| `reference_count` | integer | Logical copies sharing this blob (on canonical) |
| `is_reference` | boolean | `true` if this row points to another file |
| `original_file` | UUID or null | Canonical file id when `is_reference` is true |

**Deduplication is per-user:** identical bytes uploaded twice by the same user create a reference row and reuse one physical file. Different users never share storage.

---

## Endpoints

### 1. List files

`GET /api/files/`

Paginated list scoped to the requesting user. Filters combine with **AND** logic.

**Query parameters**

| Parameter | Description |
|-----------|-------------|
| `search` | Case-insensitive substring match on `original_filename` |
| `file_type` | Exact MIME type (e.g. `image/jpeg`) |
| `min_size` | Minimum size in bytes |
| `max_size` | Maximum size in bytes |
| `start_date` | Upload time ≥ value (ISO 8601, e.g. `2024-01-15T00:00:00Z`) |
| `end_date` | Upload time ≤ value (ISO 8601) |
| `page` | Page number (default pagination page size: 100) |

**Response:** `200 OK`

```json
{
  "count": 1,
  "next": null,
  "previous": null,
  "results": [ { /* file object */ } ]
}
```

**Example**

```bash
curl -s -H "UserId: user123" "http://localhost:8000/api/files/"
```

```bash
curl -s -H "UserId: user123" \
  "http://localhost:8000/api/files/?search=resume&file_type=application/pdf&min_size=1000"
```

---

### 2. Upload file

`POST /api/files/`

Multipart upload with automatic **per-user SHA-256 deduplication**.

**Body:** `multipart/form-data` with field **`file`**

**Response:** `201 Created` — file object (canonical or reference)

**Example — JPEG image**

```bash
curl -s -X POST -H "UserId: user123" \
  -F "file=@/Users/fearsomejockey/Desktop/wallpaper.jpg" \
  http://localhost:8000/api/files/
```

**Example — PDF resume**

```bash
curl -s -X POST -H "UserId: user123" \
  -F "file=@/Users/fearsomejockey/Desktop/PrathamAgrawal-Resume.pdf" \
  http://localhost:8000/api/files/
```

**Test deduplication** (upload same file again; second response should have `"is_reference": true`):

```bash
curl -s -X POST -H "UserId: user123" \
  -F "file=@/Users/fearsomejockey/Desktop/wallpaper.jpg" \
  http://localhost:8000/api/files/
```

---

### 3. Get file details

`GET /api/files/{id}/`

**Response:** `200 OK` — single file object

**Example** (replace `FILE_UUID` from a list or upload response):

```bash
curl -s -H "UserId: user123" \
  http://localhost:8000/api/files/FILE_UUID/
```

---

### 4. Delete file

`DELETE /api/files/{id}/`

Deletes the logical row and updates reference counts. Physical media is removed only when no references remain.

**Response:** `204 No Content`

**Example**

```bash
curl -s -X DELETE -H "UserId: user123" \
  http://localhost:8000/api/files/FILE_UUID/
```

---

### 5. Storage statistics

`GET /api/files/storage_stats/`

Deduplication-aware usage for the current user.

**Response:** `200 OK`

```json
{
  "user_id": "user123",
  "total_storage_used": 5120,
  "original_storage_used": 10240,
  "storage_savings": 5120,
  "savings_percentage": 50.0
}
```

| Field | Meaning |
|-------|---------|
| `total_storage_used` | Unique physical bytes stored for this user |
| `original_storage_used` | Sum of all logical upload sizes |
| `storage_savings` | `original - total` |
| `savings_percentage` | Percent saved via dedup |

**Example**

```bash
curl -s -H "UserId: user123" \
  http://localhost:8000/api/files/storage_stats/
```

---

### 6. List file types

`GET /api/files/file_types/`

Distinct MIME types among the user’s files.

**Response:** `200 OK` — JSON array of strings

```json
["application/pdf", "image/jpeg"]
```

**Example**

```bash
curl -s -H "UserId: user123" \
  http://localhost:8000/api/files/file_types/
```

---

## Error responses

| Status | Body | When |
|--------|------|------|
| 400 | `{"error": "UserId header is required"}` | Missing `UserId` |
| 400 | `{"error": "No file provided"}` | POST without `file` field |
| 404 | DRF not found | File id not found for this user |
| 429 | `Call Limit Reached` | Rate limit (plain text) |
| 429 | `Storage Quota Exceeded` | Upload over quota (plain text) |

---

## Suggested end-to-end test script

Run the server first (`python3 manage.py runserver` from `backend/`, or Docker).

```bash
export API=http://localhost:8000
export UID=user123

# 1. Upload image (canonical)
curl -s -X POST -H "UserId: $UID" \
  -F "file=@/Users/fearsomejockey/Desktop/wallpaper.jpg" \
  "$API/api/files/" | jq .

sleep 1

# 2. Upload PDF
curl -s -X POST -H "UserId: $UID" \
  -F "file=@/Users/fearsomejockey/Desktop/PrathamAgrawal-Resume.pdf" \
  "$API/api/files/" | jq .

sleep 1

# 3. Upload image again (should be reference / dedup)
curl -s -X POST -H "UserId: $UID" \
  -F "file=@/Users/fearsomejockey/Desktop/wallpaper.jpg" \
  "$API/api/files/" | jq .

sleep 1

# 4. List + filter
curl -s -H "UserId: $UID" \
  "$API/api/files/?file_type=image/jpeg" | jq .

sleep 1

# 5. Storage stats
curl -s -H "UserId: $UID" "$API/api/files/storage_stats/" | jq .

sleep 1

# 6. File types
curl -s -H "UserId: $UID" "$API/api/files/file_types/" | jq .
```

Save a file id from step 1, then:

```bash
export FILE_ID=<uuid-from-upload>

sleep 1
curl -s -H "UserId: $UID" "$API/api/files/$FILE_ID/" | jq .

sleep 1
curl -s -X DELETE -H "UserId: $UID" "$API/api/files/$FILE_ID/"
```

**Rate limit check** (third call within 1 second should 429):

```bash
curl -s -H "UserId: ratetest" "$API/api/files/"
curl -s -H "UserId: ratetest" "$API/api/files/"
curl -s -w "\nHTTP %{http_code}\n" -H "UserId: ratetest" "$API/api/files/"
```

---

## Logging

Structured logs use the `files.*` logger namespace. Example log lines:

```
INFO [files.request] request_started method=POST path=/api/files/ user_id=user123 query=-
INFO [files.views] upload_request user_id=user123 filename=wallpaper.jpg size=12345 type=image/jpeg
INFO [files.services] upload_canonical user_id=user123 file_id=... filename=wallpaper.jpg ...
INFO [files.request] request_completed method=POST path=/api/files/ user_id=user123 status=201 duration_ms=42.10
WARNING [files.middleware] rate_limit_exceeded user_id=ratetest method=GET path=/api/files/
```

**Verbose logging:** start server with `LOG_LEVEL=DEBUG`.

```bash
cd backend
LOG_LEVEL=DEBUG python3 manage.py runserver
```

---

## Configuration reference

| Variable | Default | Purpose |
|----------|---------|---------|
| `STORAGE_QUOTA_MB` | `10` | Per-user logical storage cap |
| `RATE_LIMIT_CALLS` | `2` | Max requests per window |
| `RATE_LIMIT_WINDOW_SECONDS` | `1` | Sliding window length (seconds) |
| `LOG_LEVEL` | `INFO` | `files.*` log verbosity |

---

## Implementation map

| Concern | Module |
|---------|--------|
| HTTP / routing | `files/views.py`, `files/urls.py` |
| Upload / delete + dedup | `files/services.py` |
| SHA-256 hashing | `files/hash_utils.py` |
| Search / filter | `files/filters.py` |
| Per-user metrics | `files/models.py` → `UserStorageMetrics` |
| Rate limit | `files/middleware.py`, `files/rate_limit.py` |
| Request tracing | `files/middleware.py` → `RequestLoggingMiddleware` |

---

## Automated tests

```bash
cd backend
pip install -r requirements.txt
python3 manage.py test files.tests -v 2
```

PRD coverage and edge-case notes: [EDGE_CASES.md](EDGE_CASES.md)
