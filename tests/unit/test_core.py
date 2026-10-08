"""Unit tests for core module - Task 1."""


def test_core_config_importable():
    """Test that core.config.Settings is importable."""
    from app.core.config import Settings

    s = Settings()
    assert s is not None


def test_core_errors_rfc9457_importable():
    """Test that core.errors.rfc9457_error is importable and returns Problem Details."""
    from app.core.errors import rfc9457_error

    result = rfc9457_error(400, "Bad Request", "Invalid input", "/api/extract")
    assert result is not None
    assert result["type"] == "/api/extract"
    assert result["title"] == "Bad Request"
    assert result["detail"] == "Invalid input"
    assert result["status"] == 400


def test_rfc9457_structure():
    """Test RFC 9457 Problem Details required fields."""
    from app.core.errors import rfc9457_error

    error = rfc9457_error(
        422, "Unprocessable Entity", "Validation failed", "/api/v1/extract"
    )
    # RFC 9457 required fields: type, title, status, detail
    assert "type" in error
    assert "title" in error
    assert "status" in error
    assert "detail" in error
