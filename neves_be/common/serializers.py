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
            fields[camel_case_name] = fields.pop(snake_case_name)
        return fields
