from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings

from files.models import File, UserStorageMetrics
from files.services import StorageQuotaExceeded, delete_file, upload_file


class UploadServiceTests(TestCase):
    def _upload(self, user: str, content: bytes, name: str = "f.txt"):
        uploaded = SimpleUploadedFile(name, content, content_type="text/plain")
        return upload_file(
            user_id=user,
            uploaded_file=uploaded,
            original_filename=name,
            file_type="text/plain",
            size=len(content),
        )

    def test_delete_nonexistent_file_is_noop(self):
        delete_file(user_id="nobody", file_id="00000000-0000-0000-0000-000000000099")
        self.assertEqual(File.objects.count(), 0)


@override_settings(STORAGE_QUOTA_MB=1)
class QuotaServiceTests(TestCase):
    def test_raises_when_logical_quota_exceeded(self):
        content = b"x" * (1024 * 1024)
        uploaded = SimpleUploadedFile("big.bin", content, content_type="application/octet-stream")
        upload_file(
            user_id="u1",
            uploaded_file=uploaded,
            original_filename="big.bin",
            file_type="application/octet-stream",
            size=len(content),
        )

        second = SimpleUploadedFile("big2.bin", content, content_type="application/octet-stream")
        with self.assertRaises(StorageQuotaExceeded):
            upload_file(
                user_id="u1",
                uploaded_file=second,
                original_filename="big2.bin",
                file_type="application/octet-stream",
                size=len(content),
            )

    def test_metrics_updated_on_upload_and_delete(self):
        record = self._upload_simple("u1", b"abc")
        metrics = UserStorageMetrics.for_user("u1")
        self.assertEqual(metrics.total_storage_used, 3)
        self.assertEqual(metrics.original_storage_used, 3)

        delete_file(user_id="u1", file_id=record.id)
        metrics.refresh_from_db()
        self.assertEqual(metrics.total_storage_used, 0)
        self.assertEqual(metrics.original_storage_used, 0)

    def _upload_simple(self, user: str, content: bytes):
        uploaded = SimpleUploadedFile("f.txt", content, content_type="text/plain")
        return upload_file(
            user_id=user,
            uploaded_file=uploaded,
            original_filename="f.txt",
            file_type="text/plain",
            size=len(content),
        )
