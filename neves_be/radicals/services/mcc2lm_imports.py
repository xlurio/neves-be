from __future__ import annotations

from typing import TYPE_CHECKING

from neves_be.radical_sessions.models import RadicalSession
from neves_be.radical_sessions.models import RadicalSessionRadical
from neves_be.radicals.models import Logogram
from neves_be.radicals.models import LogogramWordMap
from neves_be.radicals.models import Radical
from neves_be.radicals.models import RadicalLogogramMap
from neves_be.radicals.models import Sentence
from neves_be.radicals.models import Word
from neves_be.radicals.models import WordSentenceMap
from neves_be.radicals.services.mcc2lm_helpers import row_value

if TYPE_CHECKING:
    import sqlite3


def import_logograms(cursor: sqlite3.Cursor, batch_size: int) -> None:
    logogram_rows = cursor.execute("SELECT * FROM MCC2LM_LOGOGRAM").fetchall()
    Logogram.objects.bulk_create(
        [
            Logogram(
                id=str(row_value(row, "ID")),
                occurrences=int(row_value(row, "OCCURRENCIES", 0) or 0),
                pinyin=str(row_value(row, "PINYIN")),
                meaning=str(row_value(row, "MEANING")),
            )
            for row in logogram_rows
        ],
        batch_size=batch_size,
    )


def import_radical_logogram_maps(cursor: sqlite3.Cursor, batch_size: int) -> None:
    map_rows = cursor.execute(
        "SELECT LOGOGRAM_ID, RADICAL_ID FROM MCC2LM_RADICAL_LOGOGRAM_MAP",
    ).fetchall()
    RadicalLogogramMap.objects.bulk_create(
        [
            RadicalLogogramMap(
                logogram_id=str(row_value(row, "LOGOGRAM_ID")),
                radical_id=str(row_value(row, "RADICAL_ID")),
            )
            for row in map_rows
        ],
        batch_size=batch_size,
        ignore_conflicts=True,
    )


def import_words(cursor: sqlite3.Cursor, batch_size: int) -> None:
    word_rows = cursor.execute("SELECT * FROM MCC2LM_WORD").fetchall()
    Word.objects.bulk_create(
        [
            Word(
                id=int(row_value(row, "ID", 0) or 0),
                value=str(row_value(row, "VALUE")),
                pos_tag=str(row_value(row, "POS_TAG")),
                occurrences=int(row_value(row, "OCCURRENCIES", 0) or 0),
            )
            for row in word_rows
        ],
        batch_size=batch_size,
    )


def import_logogram_word_maps(cursor: sqlite3.Cursor, batch_size: int) -> None:
    logogram_word_rows = cursor.execute(
        "SELECT WORD_ID, LOGOGRAM_ID FROM MCC2LM_LOGOGRAM_WORD_MAP",
    ).fetchall()
    LogogramWordMap.objects.bulk_create(
        [
            LogogramWordMap(
                word_id=int(row_value(row, "WORD_ID", 0) or 0),
                logogram_id=str(row_value(row, "LOGOGRAM_ID")),
            )
            for row in logogram_word_rows
        ],
        batch_size=batch_size,
        ignore_conflicts=True,
    )


def import_sentences(cursor: sqlite3.Cursor, batch_size: int) -> None:
    sentence_rows = cursor.execute("SELECT * FROM MCC2LM_SENTENCE").fetchall()
    Sentence.objects.bulk_create(
        [
            Sentence(
                id=int(row_value(row, "ID", 0) or 0),
                value=str(row_value(row, "VALUE")),
            )
            for row in sentence_rows
        ],
        batch_size=batch_size,
    )


def import_word_sentence_maps(cursor: sqlite3.Cursor, batch_size: int) -> None:
    word_sentence_rows = cursor.execute(
        "SELECT SENTENCE_ID, WORD_ID FROM MCC2LM_WORD_SENTENCE_MAP",
    ).fetchall()
    WordSentenceMap.objects.bulk_create(
        [
            WordSentenceMap(
                sentence_id=int(row_value(row, "SENTENCE_ID", 0) or 0),
                word_id=int(row_value(row, "WORD_ID", 0) or 0),
            )
            for row in word_sentence_rows
        ],
        batch_size=batch_size,
        ignore_conflicts=True,
    )


def create_default_session(radical_count: int, batch_size: int) -> None:
    default_session = RadicalSession.objects.create(
        num_of_radicals=min(20, radical_count),
    )
    RadicalSessionRadical.objects.bulk_create(
        [
            RadicalSessionRadical(
                session=default_session,
                radical=radical,
                position=position,
            )
            for position, radical in enumerate(
                Radical.objects.order_by("id")[: default_session.num_of_radicals],
                start=1,
            )
        ],
        batch_size=batch_size,
    )
