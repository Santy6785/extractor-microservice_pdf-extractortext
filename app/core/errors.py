"""RFC 9457 Problem Details for HTTP API errors."""


def rfc9457_error(
    status_code: int,
    title: str,
    detail: str,
    instance: str = "/api/extract",
) -> dict:
    """Create an RFC 9457 Problem Details error response.

    Args:
        status_code: HTTP status code (e.g. 400, 422, 500).
        title: Short human-readable summary of the problem type.
        detail: Human-readable explanation specific to this occurrence.
        instance: URI identifying the specific occurrence of the problem.

    Returns:
        A dict conforming to RFC 9457 Problem Details for HTTP APIs.
    """
    return {
        "type": instance,
        "title": title,
        "status": status_code,
        "detail": detail,
    }
