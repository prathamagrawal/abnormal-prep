from django.test import SimpleTestCase

from files.rate_limit import SlidingWindowRateLimiter


class SlidingWindowRateLimiterTests(SimpleTestCase):
    def test_allows_up_to_max_calls_in_window(self):
        limiter = SlidingWindowRateLimiter(max_calls=2, window_seconds=1)
        self.assertTrue(limiter.is_allowed("user-a"))
        self.assertTrue(limiter.is_allowed("user-a"))
        self.assertFalse(limiter.is_allowed("user-a"))

    def test_limits_are_per_user(self):
        limiter = SlidingWindowRateLimiter(max_calls=1, window_seconds=1)
        self.assertTrue(limiter.is_allowed("user-a"))
        self.assertFalse(limiter.is_allowed("user-a"))
        self.assertTrue(limiter.is_allowed("user-b"))
