import time

from django.test import override_settings

from files.models import File, UserStorageMetrics
from files.tests.base import FileAPITestCase


class AuthenticationTests(FileAPITestCase):
    def test_missing_user_id_returns_400(self):
        response = self.client.get("/api/files/")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["error"], "UserId header is required")

    def test_whitespace_only_user_id_returns_400(self):
        response = self.client.get("/api/files/", HTTP_USERID="   ")
        self.assertEqual(response.status_code, 400)

    def test_upload_without_file_returns_400(self):
        response = self.client.post("/api/files/", {}, HTTP_USERID="user1", format="multipart")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["error"], "No file provided")


class UploadAndDeduplicationTests(FileAPITestCase):
    def test_upload_creates_canonical_file(self):
        response = self.post_file("alice", b"hello world", "hello.txt")
        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertFalse(data["is_reference"])
        self.assertIsNone(data["original_file"])
        self.assertEqual(data["reference_count"], 1)
        self.assertEqual(data["user_id"], "alice")
        self.assertTrue(data["file_hash"])

    def test_duplicate_upload_same_user_creates_reference(self):
        content = b"duplicate-me"
        first = self.post_file("alice", content, "a.txt")
        second = self.post_file("alice", content, "b.txt")
        self.assertEqual(first.status_code, 201)
        self.assertEqual(second.status_code, 201)

        first_data = first.json()
        second_data = second.json()
        self.assertFalse(first_data["is_reference"])
        self.assertTrue(second_data["is_reference"])
        self.assertEqual(second_data["original_file"], first_data["id"])
        self.assertEqual(first_data["file"], second_data["file"])
        self.assertEqual(second_data["reference_count"], 2)

        canonical = File.objects.get(pk=first_data["id"])
        self.assertEqual(canonical.reference_count, 2)

    def test_same_bytes_different_users_not_deduplicated(self):
        content = b"shared-bytes"
        alice = self.post_file("alice", content, "alice.txt")
        bob = self.post_file("bob", content, "bob.txt")
        self.assertEqual(alice.status_code, 201)
        self.assertEqual(bob.status_code, 201)
        self.assertNotEqual(alice.json()["file"], bob.json()["file"])
        self.assertFalse(alice.json()["is_reference"])
        self.assertFalse(bob.json()["is_reference"])

    def test_storage_stats_reflect_deduplication_savings(self):
        content = b"x" * 1000
        self.post_file("alice", content, "one.txt")
        self.post_file("alice", content, "two.txt")

        response = self.client.get("/api/files/storage_stats/", HTTP_USERID="alice")
        self.assertEqual(response.status_code, 200)
        stats = response.json()
        self.assertEqual(stats["original_storage_used"], 2000)
        self.assertEqual(stats["total_storage_used"], 1000)
        self.assertEqual(stats["storage_savings"], 1000)
        self.assertEqual(stats["savings_percentage"], 50.0)


class DeleteTests(FileAPITestCase):
    def test_delete_reference_keeps_canonical_and_physical_row(self):
        content = b"keep-on-disk"
        canonical = self.post_file("alice", content, "orig.txt").json()
        reference = self.post_file("alice", content, "copy.txt").json()

        response = self.client.delete(
            f"/api/files/{reference['id']}/",
            HTTP_USERID="alice",
        )
        self.assertEqual(response.status_code, 204)
        self.assertFalse(File.objects.filter(pk=reference["id"]).exists())

        canonical_row = File.objects.get(pk=canonical["id"])
        self.assertEqual(canonical_row.reference_count, 1)
        self.assertTrue(canonical_row.file.name)

    def test_delete_last_canonical_removes_record(self):
        file_id = self.post_file("alice", b"solo", "solo.txt").json()["id"]
        response = self.client.delete(f"/api/files/{file_id}/", HTTP_USERID="alice")
        self.assertEqual(response.status_code, 204)
        self.assertFalse(File.objects.filter(pk=file_id).exists())

    def test_delete_canonical_with_reference_promotes_successor(self):
        content = b"family"
        canonical = self.post_file("alice", content, "c.txt").json()
        ref = self.post_file("alice", content, "r.txt").json()

        response = self.client.delete(
            f"/api/files/{canonical['id']}/",
            HTTP_USERID="alice",
        )
        self.assertEqual(response.status_code, 204)

        remaining = File.objects.filter(user_id="alice")
        self.assertEqual(remaining.count(), 1)
        survivor = remaining.get()
        self.assertFalse(survivor.is_reference)
        self.assertEqual(str(survivor.id), ref["id"])

    def test_cannot_delete_other_users_file(self):
        file_id = self.post_file("alice", b"private", "p.txt").json()["id"]
        response = self.client.delete(f"/api/files/{file_id}/", HTTP_USERID="bob")
        self.assertEqual(response.status_code, 404)


class UserIsolationTests(FileAPITestCase):
    def test_list_only_returns_own_files(self):
        self.post_file("alice", b"a", "a.txt")
        self.post_file("bob", b"b", "b.txt")

        alice_list = self.get_files("alice").json()
        bob_list = self.get_files("bob").json()
        self.assertEqual(alice_list["count"], 1)
        self.assertEqual(bob_list["count"], 1)
        self.assertEqual(alice_list["results"][0]["original_filename"], "a.txt")

    def test_cannot_retrieve_other_users_file(self):
        file_id = self.post_file("alice", b"x", "x.txt").json()["id"]
        response = self.client.get(f"/api/files/{file_id}/", HTTP_USERID="bob")
        self.assertEqual(response.status_code, 404)


@override_settings(STORAGE_QUOTA_MB=1)
class StorageQuotaTests(FileAPITestCase):
    def test_upload_over_quota_returns_429(self):
        big = b"x" * (600 * 1024)
        self.assertEqual(self.post_file("alice", big, "big1.bin").status_code, 201)
        response = self.post_file("alice", big, "big2.bin")
        self.assertEqual(response.status_code, 429)
        self.assertIn("Storage Quota Exceeded", response.content.decode())

    def test_duplicate_still_counts_toward_logical_quota(self):
        content = b"x" * (400 * 1024)
        self.post_file("alice", content, "one.bin")
        response = self.post_file("alice", content, "two.bin")
        self.assertEqual(response.status_code, 201)
        metrics = UserStorageMetrics.for_user("alice")
        self.assertEqual(metrics.original_storage_used, 800 * 1024)
        self.assertEqual(metrics.total_storage_used, 400 * 1024)


class StorageStatsAndFileTypesTests(FileAPITestCase):
    def test_storage_stats_empty_user(self):
        response = self.client.get("/api/files/storage_stats/", HTTP_USERID="newuser")
        self.assertEqual(response.status_code, 200)
        stats = response.json()
        self.assertEqual(stats["total_storage_used"], 0)
        self.assertEqual(stats["savings_percentage"], 0.0)

    def test_file_types_lists_distinct_mimes_for_user(self):
        self.post_file("alice", b"a", "a.txt", "text/plain")
        self.post_file("alice", b"b", "b.pdf", "application/pdf")
        self.post_file("bob", b"c", "c.png", "image/png")

        response = self.client.get("/api/files/file_types/", HTTP_USERID="alice")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), ["application/pdf", "text/plain"])


class ListFilterTests(FileAPITestCase):
    def setUp(self):
        super().setUp()
        self.post_file("alice", b"x" * 100, "notes.txt", "text/plain")
        self.post_file("alice", b"y" * 1000, "Report.PDF", "application/pdf")

    def test_search_is_case_insensitive(self):
        response = self.get_files("alice", search="report")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["count"], 1)
        self.assertIn("Report", response.json()["results"][0]["original_filename"])

    def test_file_type_filter(self):
        response = self.get_files("alice", file_type="text/plain")
        self.assertEqual(response.json()["count"], 1)

    def test_size_range_filter(self):
        response = self.get_files("alice", min_size=50, max_size=500)
        self.assertEqual(response.json()["count"], 1)
        self.assertEqual(response.json()["results"][0]["original_filename"], "notes.txt")

    def test_combined_filters_and_logic(self):
        response = self.get_files(
            "alice",
            search="report",
            file_type="application/pdf",
            min_size=100,
        )
        self.assertEqual(response.json()["count"], 1)

    def test_invalid_min_size_is_ignored_not_500(self):
        response = self.get_files("alice", min_size="not-a-number")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["count"], 2)

    def test_invalid_date_is_ignored(self):
        response = self.get_files("alice", start_date="not-a-date")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["count"], 2)


@override_settings(RATE_LIMIT_CALLS=2, RATE_LIMIT_WINDOW_SECONDS=1)
class RateLimitMiddlewareTests(FileAPITestCase):
    def setUp(self):
        super().setUp()
        self.reset_rate_limiter()

    def test_third_request_within_window_returns_429(self):
        self.reset_rate_limiter()
        for _ in range(2):
            self.assertEqual(self.get_files("ratelimit-user").status_code, 200)
        response = self.get_files("ratelimit-user")
        self.assertEqual(response.status_code, 429)
        self.assertEqual(response.content.decode(), "Call Limit Reached")

    def test_rate_limits_are_per_user(self):
        self.reset_rate_limiter()
        self.assertEqual(self.get_files("user-a").status_code, 200)
        self.assertEqual(self.get_files("user-a").status_code, 200)
        self.assertEqual(self.get_files("user-b").status_code, 200)

    def test_requests_without_user_id_not_rate_limited(self):
        self.reset_rate_limiter()
        for _ in range(5):
            response = self.client.get("/api/files/")
            self.assertEqual(response.status_code, 400)

    def test_window_resets_after_sleep(self):
        self.reset_rate_limiter()
        self.get_files("window-user")
        self.get_files("window-user")
        self.assertEqual(self.get_files("window-user").status_code, 429)
        time.sleep(1.1)
        self.assertEqual(self.get_files("window-user").status_code, 200)


class PaginationTests(FileAPITestCase):
    def test_list_returns_paginated_envelope(self):
        for i in range(3):
            self.post_file("alice", f"file-{i}".encode(), f"f{i}.txt")
        response = self.get_files("alice")
        data = response.json()
        self.assertEqual(data["count"], 3)
        self.assertIn("results", data)
        self.assertIn("next", data)
        self.assertIn("previous", data)
        self.assertEqual(len(data["results"]), 3)
