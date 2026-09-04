"""
Structured logging configuration for Glyph.
Supports standard stream output, configurable levels, and systemd journal integration.
"""

import logging
import os
import sys
from typing import Optional


def is_systemd_environment() -> bool:
    """Detects if running under a systemd unit (checks JOURNAL_STREAM)."""
    return bool(os.environ.get("JOURNAL_STREAM"))


def setup_logging(debug: bool = False, verbose: bool = False, force_journal: bool = False) -> logging.Logger:
    """
    Configures structured logging for Glyph.
    
    Levels:
    - Debug: DEBUG level with timestamps and logger names.
    - Verbose: INFO level with logger names.
    - Default: INFO level with concise messages.
    """
    root_logger = logging.getLogger()
    for handler in list(root_logger.handlers):
        root_logger.removeHandler(handler)

    level = logging.DEBUG if debug else logging.INFO
    root_logger.setLevel(level)

    journal_attached = False
    if force_journal or is_systemd_environment():
        try:
            from systemd.journal import JournalHandler  # type: ignore
            journal_handler = JournalHandler()
            journal_handler.setFormatter(logging.Formatter("[%(name)s] %(message)s"))
            root_logger.addHandler(journal_handler)
            journal_attached = True
        except ImportError:
            pass

    if not journal_attached or sys.stderr.isatty():
        stream_handler = logging.StreamHandler(sys.stderr)
        if debug:
            formatter = logging.Formatter("%(asctime)s [%(levelname)s] [%(name)s] %(message)s", datefmt="%H:%M:%S")
        elif verbose:
            formatter = logging.Formatter("[%(levelname)s] [%(name)s] %(message)s")
        else:
            formatter = logging.Formatter("[%(levelname)s] %(message)s")
        stream_handler.setFormatter(formatter)
        root_logger.addHandler(stream_handler)

    return logging.getLogger("glyph")

