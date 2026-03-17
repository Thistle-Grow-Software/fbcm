from dataclasses import asdict, dataclass, fields
from typing import Any, ClassVar, Union, get_args, get_origin

from docx.shared import RGBColor


@dataclass
class BaseModel:
    exclude_fields: ClassVar[list[str]] = []

    def to_dict(self) -> dict[str, Any]:
        return {
            key: value
            for key, value in asdict(self).items()
            if key not in self.exclude_fields
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> BaseModel:
        """Create an instance from a dictionary, handling nested dataclasses."""
        if data is None:
            return None

        field_info = {f.name: f.type for f in fields(cls)}
        kwargs: dict[str, Any] = {}

        for key, value in data.items():
            if key not in field_info:
                continue

            if value is None:
                kwargs[key] = None
                continue

            field_type = field_info[key]
            kwargs[key] = cls._convert_value(value, field_type)

        return cls(**kwargs)

    @classmethod
    def _convert_value(cls, value: Any, field_type: Any) -> Any:
        """Convert a value to the appropriate type, handling unions and nested types."""
        origin = get_origin(field_type)

        # Handle Union types (e.g., SomeType | None)
        if origin is Union:
            args = get_args(field_type)
            # Find the non-None type in the union
            for arg in args:
                if arg is type(None):
                    continue
                return cls._convert_value(value, arg)

        # Handle List types
        if origin is list:
            item_type = get_args(field_type)[0]
            return [cls._convert_value(item, item_type) for item in value]

        # Handle nested dataclasses that have from_dict
        if isinstance(value, dict) and hasattr(field_type, "from_dict"):
            return field_type.from_dict(value)

        return value


@dataclass
class ColorScheme(BaseModel):
    primary: str
    secondary: str
    light: str

    dark: str | None = None
    medium: str | None = None
    primary_rgb: RGBColor | None = None
    light_rgb: RGBColor | None = None
