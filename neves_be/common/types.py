from typing import Any
from typing import TypedDict


class CeleryTaskOutputSchema(TypedDict):
    did_succeed: bool
    payload: dict[str, Any] | None
