"""Dependency to handle browser cache requests."""

import re
from typing import List

from fastapi import Depends, Request
from safir.dependencies.logger import logger_dependency
from structlog.stdlib import BoundLogger

_ETAG_REGEX = re.compile(r'(?:W/)?"([^\"\s]+)"$')
"""Regex matching ETag values in ``If-None-Match`` header."""

__all__ = ["etag_validation_dependency"]


async def etag_validation_dependency(
    request: Request, logger: BoundLogger = Depends(logger_dependency)
) -> List[str]:
    """Parse browser cache ETag validation headers.

    Browsers with a cached file that has expired will attempt to revalidate it
    using the ``If-None-Match`` request header.  This dependency parses that
    header and returns a list of the ETag values that the browser has cached.
    The hander is responsible for comparing this list to the ETag of the
    resource and returning a 304 Not Modified response without the content if
    the file has not been modified.
    """
    etags_str = request.headers.get("If-None-Match")
    if not etags_str:
        return []
    etags = []
    for element in re.split(r"\s*,\s+", etags_str):
        match = _ETAG_REGEX.match(element)
        if match:
            etags.append(match.group(1))
        else:
            logger.warning(
                "Ignoring invalid ETag in If-None-Match header",
                header=etags_str,
                etag=element,
            )
    return etags
