from __future__ import annotations

from typing import ClassVar


class CamelCaseAliasSerializerMixin:
    camel_case_aliases: ClassVar[dict[str, str]] = {}

    def _rename_camel_case_fields(self, fields):
        for snake_case_name, camel_case_name in self.camel_case_aliases.items():
            fields[camel_case_name] = fields.pop(snake_case_name)
        return fields
