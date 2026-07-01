from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from neves_be.language_model.models import Logogram
from neves_be.language_model.models import LogogramWordMap
from neves_be.language_model.models import RadicalLogogramMap
from neves_be.language_model.models import Sentence
from neves_be.language_model.models import Word
from neves_be.language_model.models import WordSentenceMap
from neves_be.language_model.services.audio_cmn import get_audio_path_from_chinese
from neves_be.language_model.services.audio_cmn import get_audio_path_from_pinyin
from neves_be.language_model.services.mcc2lm_helpers import row_value

if TYPE_CHECKING:
    import sqlite3


def import_logograms(cursor: sqlite3.Cursor, batch_size: int) -> None:
    _logger = logging.getLogger(import_logograms.__name__)

    logogram_rows = cursor.execute("SELECT * FROM MCC2LM_LOGOGRAM").fetchall()

    logogram_models: list[Logogram] = []
    for row in logogram_rows:
        logogram = str(row_value(row, "ID"))
        pinyin = str(row_value(row, "PINYIN"))

        try:
            try:
                pronounce = get_audio_path_from_chinese(logogram)
            except ValueError:
                pronounce = get_audio_path_from_pinyin(pinyin)
        except ValueError:
            _logger.warning("Failed to process logogram %s", logogram)
            pronounce = ""

        logogram_models.append(
            Logogram(
                id=logogram,
                occurrences=int(row_value(row, "OCCURRENCIES", 0) or 0),
                pinyin=pinyin,
                meaning=str(row_value(row, "MEANING")),
                pronounce=pronounce,
            ),
        )

    Logogram.objects.bulk_create(logogram_models, batch_size=batch_size)


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


def import_words(cursor: sqlite3.Cursor, batch_size: int) -> int:
    word_rows = cursor.execute("SELECT * FROM MCC2LM_WORD").fetchall()

    Word.objects.bulk_create(
        [
            Word(
                id=int(row_value(row, "ID", 0) or 0),
                value=str(row_value(row, "VALUE")),
                pos_tag=str(row_value(row, "POS_TAG")),
                occurrences=int(row_value(row, "OCCURRENCIES", 0) or 0),
                pronounce="",
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
