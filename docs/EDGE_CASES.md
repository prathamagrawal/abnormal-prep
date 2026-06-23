# Edge Cases & PRD Coverage

This document maps PRD requirements to tests and records known gaps.

## PRD coverage matrix

| Requirement | Test location | Status |
|-------------|---------------|--------|
| `UserId` header required | `test_api.AuthenticationTests` | Covered |
| Per-user file scoping | `UserIsolationTests` | Covered |
| SHA-256 dedup (per-user) | `UploadAndDeduplicationTests` | Covered |
| Reference rows + `reference_count` | `test_duplicate_upload_same_user_creates_reference` | Covered |
| Delete reference / canonical / promote | `DeleteTests` | Covered |
| Storage stats & savings % | `test_storage_stats_reflect_deduplication_savings` | Covered |
| `file_types` endpoint | `StorageStatsAndFileTypesTests` | Covered |
| List filters (search, type, size, dates) | `ListFilterTests` | Covered |
| Combined AND filters | `test_combined_filters_and_logic` | Covered |
| Storage quota 429 + message | `StorageQuotaTests` | Covered |
| Rate limit 429 + message | `RateLimitMiddlewareTests` | Covered |
| Configurable limits (settings) | `override_settings` in tests | Covered |

## Edge cases tested

1. **Whitespace-only `UserId`** → 400 (fixed in `views._require_user_id`).
2. **Same bytes, different users** → separate physical files (per-user dedup).
3. **Duplicate upload** → logical quota increases, physical does not.
4. **Delete canonical with references** → successor promoted.
5. **Invalid `min_size` / date query params** → ignored (no 500); see `test_invalid_*`.
6. **Rate limit** → per-user, sliding window reset after sleep.
7. **No `UserId`** → not counted toward rate limit (returns 400 from view).
8. **Empty user storage stats** → zeros and 0% savings.

## Known gaps / intentional behaviors

| Item | Severity | Notes |
|------|----------|-------|
| Rate limiter in-memory only | Medium (prod) | Each Gunicorn worker has its own window; use Redis for multi-worker. |
| `delete_file()` silent no-op | Low | Wrong `file_id` via service alone does nothing; API uses `get_object()` → 404. |
| Invalid negative `min_size` | Low | Ignored (treated as invalid); not rejected with 400. |
| Empty file upload | Low | Allowed; SHA-256 of empty content is valid. |
| No max filename length enforcement | Low | Model `max_length=255`; longer names may error at DB layer. |
| Rate limit applies to all `/api/*` | Info | Includes `storage_stats` and `file_types`. |
| `reference_count` on reference rows in DB | Info | Serializer overwrites with canonical count in API response. |
| Concurrent duplicate uploads | Medium | `select_for_update` helps; unique canonical per `(user_id, file_hash)` constraint exists. |
| Canonical delete with references | Fixed | Was: `CASCADE` on `original_file` + promote order caused `IntegrityError`. Now `SET_NULL` + reassign-before-delete in `_reassign_canonical`. |
| Media path in tests | Low | Physical file existence checks use DB row retention as primary assertion. |

## Possible future improvements

- Return **400** for malformed numeric/date query params instead of ignoring.
- Reset rate limiter via management command for ops.
- Integration test with real files from `image.jpeg` / resume PDF (optional; CI may not have paths).
- Test `HTTP_USERID` header alias used by Django test client matches production `UserId` header.

## Running tests

```bash
cd backend
python3 manage.py test files.tests -v 2
```

For a single module:

```bash
python3 manage.py test files.tests.test_api -v 2
```
