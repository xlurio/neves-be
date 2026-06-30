from __future__ import annotations

from typing import TYPE_CHECKING
from typing import overload

from neves_be.language_model.models import Logogram
from neves_be.language_model.models import LogogramWordMap
from neves_be.language_model.models import Radical
from neves_be.language_model.models import RadicalLogogramMap
from neves_be.language_model.models import Sentence
from neves_be.language_model.models import Word
from neves_be.language_model.models import WordSentenceMap
from neves_be.language_model.services.audio_cmn import get_audio_path_from_pinyin
from neves_be.practice_assessments.models import RadicalSessionAssessment
from neves_be.practice_questions.models import RadicalSessionAssessmentQuestion
from neves_be.radical_sessions.models import RadicalSession
from neves_be.radical_sessions.models import RadicalSessionRadical

if TYPE_CHECKING:
    import sqlite3


@overload
def row_value(row: sqlite3.Row, key: str, default: str = "") -> str: ...


@overload
def row_value(row: sqlite3.Row, key: str, default: int) -> int: ...


def row_value(row: sqlite3.Row, key: str, default: object = "") -> object:
    try:
        value = row[key]
    except IndexError, KeyError:
        return default
    return value if value is not None else default


def reset_radical_learning_tables() -> None:
    RadicalSessionAssessmentQuestion.objects.all().delete()
    RadicalSessionAssessment.objects.all().delete()
    RadicalSessionRadical.objects.all().delete()
    RadicalSession.objects.all().delete()
    WordSentenceMap.objects.all().delete()
    LogogramWordMap.objects.all().delete()
    RadicalLogogramMap.objects.all().delete()
    Sentence.objects.all().delete()
    Word.objects.all().delete()
    Logogram.objects.all().delete()
    Radical.objects.all().delete()


def import_radicals(
    cursor: sqlite3.Cursor,
    batch_size: int,
) -> None:
    radicals_query = "SELECT * FROM MCC2LM_RADICAL"
    radicals_rows = cursor.execute(radicals_query).fetchall()

    Radical.objects.bulk_create(
        [
            Radical(
                id=str(row_value(row, "ID")),
                pinyin=str(row_value(row, "PINYIN")),
                meaning=str(row_value(row, "MEANING")),
                pronounce=get_audio_path_from_pinyin(str(row_value(row, "PINYIN"))),
            )
            for row in radicals_rows
        ],
        batch_size=batch_size,
    )
