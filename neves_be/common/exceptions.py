from typing import Any

from rest_framework import status
from rest_framework.exceptions import APIException

from neves_be.common.api import ErrorCode


class NevesBackEndError(APIException):
    status_code = status.HTTP_400_BAD_REQUEST

    def __init__(
        self,
        code: ErrorCode,
        title: str,
        details: str,
        *,
        http_status: int = status.HTTP_400_BAD_REQUEST,
        payload: dict[str, Any] | None = None,
    ):
        super().__init__(title, code)

        self.__code = code
        self.__title = title
        self.__details = details
        self.__http_status = http_status
        self.__payload = payload

    @property
    def code(self) -> ErrorCode:
        return self.__code

    @property
    def title(self) -> str:
        return self.__title

    @property
    def details(self) -> str:
        return self.__details

    @property
    def http_status(self) -> int:
        return self.__http_status

    @property
    def payload(self) -> dict[str, Any] | None:
        return self.__payload
