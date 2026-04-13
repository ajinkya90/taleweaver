import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.db import _parse_emails, get_admin_emails


def test_parse_emails_basic():
    assert _parse_emails("a@b.com, c@d.com") == {"a@b.com", "c@d.com"}


def test_parse_emails_empty():
    assert _parse_emails("") == set()
    assert _parse_emails(None) == set()


def test_parse_emails_whitespace_and_case():
    assert _parse_emails("  A@B.COM , c@d.com  ") == {"a@b.com", "c@d.com"}


def testget_admin_emails():
    with patch("app.db.settings") as mock_settings:
        mock_settings.admin_emails = "admin@test.com, boss@test.com"
        result = get_admin_emails()
        assert result == {"admin@test.com", "boss@test.com"}
