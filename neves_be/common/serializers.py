from __future__ import annotations

from typing import TYPE_CHECKING
from typing import Any
from typing import ClassVar

if TYPE_CHECKING:
    from collections.abc import MutableMapping


class CamelCaseAliasSerializerMixin:
    camel_case_aliases: ClassVar[dict[str, str]] = {}

    def _rename_camel_case_fields(
        self,
        fields: MutableMapping[str, Any],
    ) -> MutableMapping[str, Any]:
        for snake_case_name, camel_case_name in self.camel_case_aliases.items():
            if snake_case_name not in fields:
                continue

            field = fields.pop(snake_case_name)
            if getattr(field, "source", None) in {None, "", snake_case_name}:
                field.source = snake_case_name
            fields[camel_case_name] = field
        return fields
