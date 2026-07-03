import uuid

from django.db import models


class UUIDPkModelMixin:
    id: "models.UUIDField[uuid.UUID, uuid.UUID]" = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
