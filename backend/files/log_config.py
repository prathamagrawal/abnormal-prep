"""Shared logging helpers for the files app."""

import logging

LOGGER_PREFIX = "files"


def get_logger(component: str) -> logging.Logger:
    """Return a namespaced logger, e.g. files.views."""
    return logging.getLogger(f"{LOGGER_PREFIX}.{component}")
