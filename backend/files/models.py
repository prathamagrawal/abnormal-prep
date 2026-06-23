from django.conf import settings
from django.db import models
import uuid
import os


def file_upload_path(instance, filename):
    """Generate a unique storage path for a new physical upload."""
    ext = filename.split(".")[-1] if "." in filename else ""
    stored_name = f"{uuid.uuid4()}.{ext}" if ext else str(uuid.uuid4())
    return os.path.join("uploads", stored_name)


class File(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    file = models.FileField(upload_to=file_upload_path)
    original_filename = models.CharField(max_length=255)
    file_type = models.CharField(max_length=100)
    size = models.BigIntegerField()
    uploaded_at = models.DateTimeField(auto_now_add=True)

    user_id = models.CharField(max_length=255, db_index=True)
    file_hash = models.CharField(max_length=64, db_index=True)

    is_reference = models.BooleanField(default=False)
    original_file = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="references",
    )
    # Maintained on canonical rows only: logical rows sharing this physical blob
    reference_count = models.PositiveIntegerField(default=1)

    class Meta:
        ordering = ["-uploaded_at"]
        indexes = [
            models.Index(fields=["user_id", "file_hash"]),
            models.Index(fields=["user_id", "original_filename"]),
            models.Index(fields=["user_id", "file_type"]),
            models.Index(fields=["user_id", "size"]),
            models.Index(fields=["user_id", "uploaded_at"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["user_id", "file_hash"],
                condition=models.Q(is_reference=False),
                name="unique_canonical_per_user_hash",
            ),
        ]

    def __str__(self):
        return self.original_filename


class UserStorageMetrics(models.Model):
    """Per-user storage counters (deduplicated vs logical totals)."""

    user_id = models.CharField(max_length=255, primary_key=True)
    total_storage_used = models.BigIntegerField(
        default=0,
        help_text="Bytes after deduplication (unique physical content per user).",
    )
    original_storage_used = models.BigIntegerField(
        default=0,
        help_text="Sum of logical file sizes as if every upload were stored separately.",
    )

    class Meta:
        verbose_name_plural = "User storage metrics"

    @property
    def storage_savings(self) -> int:
        return max(0, self.original_storage_used - self.total_storage_used)

    @property
    def savings_percentage(self) -> float:
        if self.original_storage_used == 0:
            return 0.0
        return round(
            (self.storage_savings / self.original_storage_used) * 100.0,
            1,
        )

    @classmethod
    def for_user(cls, user_id: str, *, lock: bool = False) -> "UserStorageMetrics":
        if lock:
            metrics, _ = cls.objects.select_for_update().get_or_create(user_id=user_id)
            return metrics
        metrics, _ = cls.objects.get_or_create(user_id=user_id)
        return metrics

    @staticmethod
    def quota_bytes() -> int:
        return int(getattr(settings, "STORAGE_QUOTA_MB", 10)) * 1024 * 1024

    def would_exceed_quota(self, size: int) -> bool:
        return self.original_storage_used + size > self.quota_bytes()

    def record_upload(self, size: int, *, duplicate: bool) -> None:
        self.original_storage_used += size
        if not duplicate:
            self.total_storage_used += size
        self.save(update_fields=["original_storage_used", "total_storage_used"])

    def record_delete(self, size: int, *, duplicate: bool) -> None:
        self.original_storage_used -= size
        if not duplicate:
            self.total_storage_used -= size
        self.save(update_fields=["original_storage_used", "total_storage_used"])

    def as_stats(self) -> dict:
        return {
            "user_id": self.user_id,
            "total_storage_used": self.total_storage_used,
            "original_storage_used": self.original_storage_used,
            "storage_savings": self.storage_savings,
            "savings_percentage": self.savings_percentage,
        }
