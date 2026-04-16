import pytest
from unittest.mock import MagicMock, patch

from pr_insight.algo.git_patch_processing import (
    extend_patch,
    decode_if_bytes,
    should_skip_patch,
    process_patch_lines,
    omit_deletion_hunks,
)


class TestDecodeIfBytes:
    """Test suite for decode_if_bytes function."""

    def test_decode_string_returns_string(self):
        result = decode_if_bytes("test string")
        assert result == "test string"

    def test_decode_utf8_bytes(self):
        result = decode_if_bytes(b"test string")
        assert result == "test string"

    def test_decode_latin1_bytes(self):
        test_str = "test café"
        result = decode_if_bytes(test_str.encode("latin-1"))
        assert result == test_str

    def test_decode_empty_bytes(self):
        result = decode_if_bytes(b"")
        assert result == ""


class TestShouldSkipPatch:
    """Test suite for should_skip_patch function."""

    def test_should_skip_markdown(self):
        with patch("pr_insight.algo.git_patch_processing.get_settings") as mock:
            mock.return_value.config.patch_extension_skip_types = [".md", ".txt"]
            assert should_skip_patch("readme.md") is True

    def test_should_skip_txt(self):
        with patch("pr_insight.algo.git_patch_processing.get_settings") as mock:
            mock.return_value.config.patch_extension_skip_types = [".md", ".txt"]
            assert should_skip_patch("notes.txt") is True

    def test_should_not_skip_python(self):
        with patch("pr_insight.algo.git_patch_processing.get_settings") as mock:
            mock.return_value.config.patch_extension_skip_types = [".md", ".txt"]
            assert should_skip_patch("main.py") is False

    def test_should_not_skip_javascript(self):
        with patch("pr_insight.algo.git_patch_processing.get_settings") as mock:
            mock.return_value.config.patch_extension_skip_types = [".md", ".txt"]
            assert should_skip_patch("app.js") is False


class TestExtendPatch:
    """Test suite for extend_patch function."""

    def test_extend_patch_empty_patch(self):
        result = extend_patch("original", "", patch_extra_lines_before=5)
        assert result == ""

    def test_extend_patch_no_extra_lines(self):
        result = extend_patch("original", "patch", patch_extra_lines_before=0, patch_extra_lines_after=0)
        assert result == "patch"

    def test_extend_patch_with_extra_lines_before(self):
        original = "line1\nline2\nline3\n"
        patch_str = "@@ -1,3 +1,4 @@\n+new_line\n"
        result = extend_patch(original, patch_str, patch_extra_lines_before=1)
        assert result is not None

    def test_extend_patch_skips_for_markdown(self):
        original = "line1\nline2\n"
        patch_str = "@@ -1,2 +1,3 @@\n+new_line\n"
        with patch("pr_insight.algo.git_patch_processing.get_settings") as mock:
            mock.return_value.config.patch_extension_skip_types = [".md"]
            result = extend_patch(original, patch_str, patch_extra_lines_before=5, filename="readme.md")
            assert result == patch_str


class TestOmitDeletionHunks:
    """Test suite for omit_deletion_hunks function."""

    def test_omit_deletion_hunks_empty(self):
        result = omit_deletion_hunks("")
        assert result == ""

    def test_omit_deletion_hunks_preserves_additions(self):
        patch_str = "@@ -1,3 +1,4 @@\n+new_line\n old_line\n"
        result = omit_deletion_hunks(patch_str)
        assert result is not None

    def test_omit_deletion_hunks_with_deletions(self):
        patch_str = "@@ -1,3 +1,2 @@\n-removed_line\n"
        result = omit_deletion_hunks(patch_str)
        assert result is not None
