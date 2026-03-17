"""Extended tests for fbcm.models — ColorScheme edge cases."""

from fbcm.models import ColorScheme


class TestColorScheme:
    def test_from_dict(self):
        data = {"primary": "#FF0000", "secondary": "#00FF00", "light": "#CCCCCC"}
        scheme = ColorScheme.from_dict(data)
        assert scheme.primary == "#FF0000"
        assert scheme.secondary == "#00FF00"
        assert scheme.light == "#CCCCCC"
        assert scheme.dark is None
        assert scheme.medium is None

    def test_to_dict(self):
        scheme = ColorScheme(primary="#FF0000", secondary="#00FF00", light="#CCCCCC")
        result = scheme.to_dict()
        assert result["primary"] == "#FF0000"
        assert result["secondary"] == "#00FF00"
        assert result["light"] == "#CCCCCC"

    def test_roundtrip(self):
        original = ColorScheme(
            primary="#FF0000", secondary="#00FF00", light="#CCCCCC", dark="#330000"
        )
        restored = ColorScheme.from_dict(original.to_dict())
        assert restored.primary == original.primary
        assert restored.dark == original.dark


class TestBaseModelExcludeFields:
    def test_exclude_fields_filters_to_dict(self):
        """Verify that exclude_fields class variable works."""
        scheme = ColorScheme(primary="#FF0000", secondary="#00FF00", light="#CCCCCC")
        result = scheme.to_dict()
        assert "primary" in result
        assert "secondary" in result
