"""Shared test utilities."""

import files.middleware as rate_limit_middleware
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from rest_framework.test import APITestCase


@override_settings(RATE_LIMIT_CALLS=1000, RATE_LIMIT_WINDOW_SECONDS=60)
class FileAPITestCase(APITestCase):
    """API tests with rate limiting relaxed to avoid cross-test interference."""

    def setUp(self):
        rate_limit_middleware._limiter = None

    def tearDown(self):
        rate_limit_middleware._limiter = None

    @staticmethod
    def reset_rate_limiter():
        rate_limit_middleware._limiter = None
        rate_limit_middleware.get_rate_limiter().reset()

    @staticmethod
    def make_upload(content: bytes, name: str = "test.txt", content_type: str = "text/plain"):
        return SimpleUploadedFile(name, content, content_type=content_type)

    def post_file(self, user_id: str, content: bytes, name: str = "test.txt", content_type: str = "text/plain"):
        return self.client.post(
            "/api/files/",
            {"file": self.make_upload(content, name, content_type)},
            HTTP_USERID=user_id,
            format="multipart",
        )

    def get_files(self, user_id: str, **query):
        return self.client.get("/api/files/", query, HTTP_USERID=user_id)
