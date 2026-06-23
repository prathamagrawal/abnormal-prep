"""Upload/delete with per-user deduplication."""

from django.db import transaction

from files.hash_utils import compute_sha256_hex
from files.log_config import get_logger
from files.models import File, UserStorageMetrics

logger = get_logger("services")


class StorageQuotaExceeded(Exception):
    pass


@transaction.atomic
def upload_file(
    *,
    user_id: str,
    uploaded_file,
    original_filename: str,
    file_type: str,
    size: int,
) -> File:
    metrics = UserStorageMetrics.for_user(user_id, lock=True)
    if metrics.would_exceed_quota(size):
        raise StorageQuotaExceeded()

    file_hash = compute_sha256_hex(uploaded_file)
    canonical = (
        File.objects.select_for_update()
        .filter(user_id=user_id, file_hash=file_hash, is_reference=False)
        .first()
    )

    if canonical is None:
        record = File.objects.create(
            file=uploaded_file,
            original_filename=original_filename,
            file_type=file_type,
            size=size,
            user_id=user_id,
            file_hash=file_hash,
            is_reference=False,
            reference_count=1,
        )
        metrics.record_upload(size, duplicate=False)
        return record

    canonical.reference_count += 1
    canonical.save(update_fields=["reference_count"])
    metrics.record_upload(size, duplicate=True)

    return File.objects.create(
        file=canonical.file,
        original_filename=original_filename,
        file_type=file_type,
        size=size,
        user_id=user_id,
        file_hash=file_hash,
        is_reference=True,
        original_file=canonical,
        reference_count=canonical.reference_count,
    )


@transaction.atomic
def delete_file(*, user_id: str, file_id) -> None:
    record = (
        File.objects.select_for_update()
        .filter(id=file_id, user_id=user_id)
        .first()
    )
    if record is None:
        return

    metrics = UserStorageMetrics.for_user(user_id)

    if record.is_reference:
        canonical = File.objects.select_for_update().get(pk=record.original_file_id)
        canonical.reference_count -= 1
        canonical.save(update_fields=["reference_count"])
        metrics.record_delete(record.size, duplicate=True)
        record.delete()
        return

    if record.reference_count <= 1:
        physical = record.file
        size = record.size
        record.delete()
        physical.delete(save=False)
        metrics.record_delete(size, duplicate=False)
        return

    _reassign_canonical(record, metrics)


def _reassign_canonical(record: File, metrics: UserStorageMetrics) -> None:
    references = list(record.references.select_for_update().order_by("uploaded_at"))
    successor = references[0]

    successor.original_file = None
    successor.save(update_fields=["original_file"])

    if len(references) > 1:
        File.objects.filter(original_file=record).exclude(pk=successor.pk).update(
            original_file=successor
        )

    metrics.record_delete(record.size, duplicate=True)
    record.delete()

    successor.is_reference = False
    successor.reference_count = record.reference_count - 1
    successor.save(update_fields=["is_reference", "reference_count"])
