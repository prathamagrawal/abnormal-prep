import hashlib
from io import BytesIO

from django.test import SimpleTestCase

from files.hash_utils import compute_sha256_hex


class HashUtilsTests(SimpleTestCase):
    def test_empty_file_produces_known_digest(self):
        stream = BytesIO(b"")
        expected = hashlib.sha256(b"").hexdigest()
        self.assertEqual(compute_sha256_hex(stream), expected)
        self.assertEqual(stream.tell(), 0)

    def test_rewinds_stream_for_subsequent_reads(self):
        stream = BytesIO(b"payload")
        compute_sha256_hex(stream)
        self.assertEqual(stream.read(), b"payload")

    def test_matches_hashlib_for_multichunk_content(self):
        content = b"a" * 20000
        stream = BytesIO(content)
        self.assertEqual(compute_sha256_hex(stream), hashlib.sha256(content).hexdigest())
