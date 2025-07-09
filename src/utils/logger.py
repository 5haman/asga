from __future__ import annotations

import logging

from langfuse.logger import console_handler, langfuse_logger


def get_logger(name: str) -> logging.Logger:
    """Return module logger emitting to console and Langfuse."""

    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.addHandler(console_handler)
        for h in langfuse_logger.handlers:
            logger.addHandler(h)
    logger.setLevel(logging.DEBUG)
    return logger

