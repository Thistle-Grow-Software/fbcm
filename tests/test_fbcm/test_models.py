"""Tests for fbcm.models — BaseModel and ColorScheme dataclass serialization."""

from fbcm.models import ColorScheme


class TestBaseModelToDict:
    def test_simple_dataclass_to_dict(self):
        scheme = ColorScheme(primary="#FF0000", secondary="#00FF00", light="#CCCCCC")
        result = scheme.to_dict()
        assert result["primary"] == "#FF0000"
        assert result["secondary"] == "#00FF00"

    def test_to_dict_includes_none_fields(self):
        scheme = ColorScheme(primary="#FF0000", secondary="#00FF00", light="#CCCCCC")
        result = scheme.to_dict()
        assert "dark" in result
        assert result["dark"] is None


class TestBaseModelFromDict:
    def test_simple_from_dict(self):
        data = {"primary": "#FF0000", "secondary": "#00FF00", "light": "#CCCCCC"}
        scheme = ColorScheme.from_dict(data)
        assert scheme.primary == "#FF0000"
        assert scheme.secondary == "#00FF00"

    def test_from_dict_with_none_value(self):
        data = {
            "primary": "#FF0000",
            "secondary": "#00FF00",
            "light": "#CCCCCC",
            "dark": None,
        }
        scheme = ColorScheme.from_dict(data)
        assert scheme.dark is None

    def test_from_dict_ignores_unknown_keys(self):
        data = {
            "primary": "#FF0000",
            "secondary": "#00FF00",
            "light": "#CCCCCC",
            "unknown_field": "should be ignored",
        }
        scheme = ColorScheme.from_dict(data)
        assert scheme.primary == "#FF0000"
        assert not hasattr(scheme, "unknown_field")

    def test_from_dict_returns_none_for_none_input(self):
        result = ColorScheme.from_dict(None)
        assert result is None


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
