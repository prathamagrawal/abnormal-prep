"""
SHA-256 content hashing for file deduplication.

Algorithm (streaming digest):
  1. Initialize SHA-256 hasher (hashlib.sha256).
  2. Read the upload in fixed-size chunks so large files never load fully into memory.
  3. Feed each chunk into the hasher via update().
  4. After EOF, finalize to a 64-character lowercase hex digest.
  5. Reset the file pointer to 0 so Django can persist the same upload object.

Dedup scope: hashes are compared per user_id (see file_service), not globally.
"""

from __future__ import annotations

import hashlib
from typing import BinaryIO

# 8 KiB — balance between syscall overhead and memory per read
DEFAULT_CHUNK_SIZE = 8192


def compute_sha256_hex(
    file_obj: BinaryIO,
    *,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
) -> str:
    """
    Compute SHA-256 hex digest of *file_obj* using chunked reads.

    Args:
        file_obj: Readable binary stream (e.g. Django UploadedFile).
        chunk_size: Bytes per read iteration.

    Returns:
        Lowercase hex string (64 chars) suitable for file_hash storage.
    """
    digest = _digest_file_stream(file_obj, chunk_size=chunk_size)
    _rewind(file_obj)
    return digest


def _digest_file_stream(file_obj: BinaryIO, *, chunk_size: int) -> str:
    """Internal: consume stream and return hex digest without rewinding."""
    hasher = hashlib.sha256()
    while True:
        chunk = file_obj.read(chunk_size)
        if not chunk:
            break
        hasher.update(chunk)
    return hasher.hexdigest()


def _rewind(file_obj: BinaryIO) -> None:
    """Reset stream position when the underlying object supports seek."""
    if hasattr(file_obj, "seek"):
        file_obj.seek(0)
