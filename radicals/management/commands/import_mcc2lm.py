from __future__ import annotations

import re
import sqlite3
from pathlib import Path
from typing import overload

from django.conf import settings
from django.core.management.base import BaseCommand
from django.core.management.base import CommandError
from django.db import transaction

from radicals.models import Logogram
from radicals.models import LogogramWordMap
from radicals.models import Radical
from radicals.models import RadicalLogogramMap
from radicals.models import RadicalSession
from radicals.models import RadicalSessionRadical
from radicals.models import RadicalSessionTest
from radicals.models import RadicalSessionTestQuestion
from radicals.models import Sentence
from radicals.models import Word
from radicals.models import WordSentenceMap

ACCENTED_PINYIN_REPLACEMENTS = {
    "ā": "a",
    "á": "a",
    "ǎ": "a",
    "à": "a",
    "ē": "e",
    "é": "e",
    "ě": "e",
    "è": "e",
    "ī": "i",
    "í": "i",
    "ǐ": "i",
    "ì": "i",
    "ō": "o",
    "ó": "o",
    "ǒ": "o",
    "ò": "o",
    "ū": "u",
    "ú": "u",
    "ǔ": "u",
    "ù": "u",
    "ǖ": "v",
    "ǘ": "v",
    "ǚ": "v",
    "ǜ": "v",
    "ü": "v",
}

PINYIN_TOKEN_RE = re.compile(r"[a-zA-ZüÜǖǘǚǜāáǎàēéěèīíǐìōóǒòūúǔùv:]+")


@overload
def _row_value(row: sqlite3.Row, key: str, default: str = "") -> str: ...


@overload
def _row_value(row: sqlite3.Row, key: str, default: int) -> int: ...


def _row_value(row: sqlite3.Row, key: str, default: object = "") -> object:
    try:
        value = row[key]
    except IndexError, KeyError:
        return default

    return value if value is not None else default


def normalize_pinyin_for_filename(pinyin: str) -> str:
    token_match = PINYIN_TOKEN_RE.search((pinyin or "").strip())
    if token_match is None:
        return ""

    token = token_match.group(0).lower().replace("u:", "v")
    normalized = "".join(ACCENTED_PINYIN_REPLACEMENTS.get(char, char) for char in token)
    return re.sub(r"[^a-zv]", "", normalized)


class Command(BaseCommand):
    help = "Import radicals and LCMC linguistic data from MCC2LM SQLite into Django DB"

    def add_arguments(self, parser):
        parser.add_argument("sqlite_path", type=str, help="Path to MCC2LM SQLite file")
        parser.add_argument("--batch-size", type=int, default=2000)

    def handle(self, *args, **options):
        sqlite_path = Path(options["sqlite_path"]).expanduser().resolve()
        batch_size = int(options["batch_size"])

        if not sqlite_path.exists():
            raise CommandError(f"SQLite file not found: {sqlite_path}")

        audio_dir = Path(settings.BASE_DIR) / "audio-cmn" / "18k-abr" / "syllabs"
        if not audio_dir.exists():
            self.stdout.write(
                self.style.WARNING(f"Audio directory not found: {audio_dir}"),
            )

        with sqlite3.connect(sqlite_path) as source_db:
            source_db.row_factory = sqlite3.Row
            cursor = source_db.cursor()

            with transaction.atomic():
                RadicalSessionTestQuestion.objects.all().delete()
                RadicalSessionTest.objects.all().delete()
                RadicalSessionRadical.objects.all().delete()
                RadicalSession.objects.all().delete()
                WordSentenceMap.objects.all().delete()
                LogogramWordMap.objects.all().delete()
                RadicalLogogramMap.objects.all().delete()
                Sentence.objects.all().delete()
                Word.objects.all().delete()
                Logogram.objects.all().delete()
                Radical.objects.all().delete()

                radicals_rows = cursor.execute(
                    "SELECT * FROM MCC2LM_RADICAL",
                ).fetchall()
                radical_models: list[Radical] = []
                missing_audio_count = 0

                for row in radicals_rows:
                    radical_id = str(_row_value(row, "ID"))
                    pinyin = str(_row_value(row, "PINYIN"))
                    normalized = normalize_pinyin_for_filename(pinyin)
                    pronounce = ""

                    if normalized and audio_dir.exists():
                        matches = sorted(audio_dir.glob(f"{normalized}[0-9].mp3"))
                        if matches:
                            pronounce = f"/audio-cmn/18k-abr/syllabs/{matches[0].name}"

                    if not pronounce:
                        missing_audio_count += 1

                    radical_models.append(
                        Radical(
                            id=radical_id,
                            pinyin=pinyin,
                            meaning=str(_row_value(row, "MEANING")),
                            main_representation=ord(radical_id[0])
                            if radical_id
                            else None,
                            other_vars=[],
                            pronounce=pronounce,
                        ),
                    )

                Radical.objects.bulk_create(radical_models, batch_size=batch_size)

                logogram_rows = cursor.execute(
                    "SELECT * FROM MCC2LM_LOGOGRAM",
                ).fetchall()
                Logogram.objects.bulk_create(
                    [
                        Logogram(
                            id=str(_row_value(row, "ID")),
                            occurrences=int(_row_value(row, "OCCURRENCIES", 0) or 0),
                            pinyin=str(_row_value(row, "PINYIN")),
                            meaning=str(_row_value(row, "MEANING")),
                        )
                        for row in logogram_rows
                    ],
                    batch_size=batch_size,
                )

                map_rows = cursor.execute(
                    "SELECT LOGOGRAM_ID, RADICAL_ID FROM MCC2LM_RADICAL_LOGOGRAM_MAP",
                ).fetchall()
                RadicalLogogramMap.objects.bulk_create(
                    [
                        RadicalLogogramMap(
                            logogram_id=str(_row_value(row, "LOGOGRAM_ID")),
                            radical_id=str(_row_value(row, "RADICAL_ID")),
                        )
                        for row in map_rows
                    ],
                    batch_size=batch_size,
                    ignore_conflicts=True,
                )

                word_rows = cursor.execute("SELECT * FROM MCC2LM_WORD").fetchall()
                Word.objects.bulk_create(
                    [
                        Word(
                            id=int(_row_value(row, "ID", 0) or 0),
                            value=str(_row_value(row, "VALUE")),
                            pos_tag=str(_row_value(row, "POS_TAG")),
                            occurrences=int(_row_value(row, "OCCURRENCIES", 0) or 0),
                        )
                        for row in word_rows
                    ],
                    batch_size=batch_size,
                )

                logogram_word_rows = cursor.execute(
                    "SELECT WORD_ID, LOGOGRAM_ID FROM MCC2LM_LOGOGRAM_WORD_MAP",
                ).fetchall()
                LogogramWordMap.objects.bulk_create(
                    [
                        LogogramWordMap(
                            word_id=int(_row_value(row, "WORD_ID", 0) or 0),
                            logogram_id=str(_row_value(row, "LOGOGRAM_ID")),
                        )
                        for row in logogram_word_rows
                    ],
                    batch_size=batch_size,
                    ignore_conflicts=True,
                )

                sentence_rows = cursor.execute(
                    "SELECT * FROM MCC2LM_SENTENCE",
                ).fetchall()
                Sentence.objects.bulk_create(
                    [
                        Sentence(
                            id=int(_row_value(row, "ID", 0) or 0),
                            value=str(_row_value(row, "VALUE")),
                        )
                        for row in sentence_rows
                    ],
                    batch_size=batch_size,
                )

                word_sentence_rows = cursor.execute(
                    "SELECT SENTENCE_ID, WORD_ID FROM MCC2LM_WORD_SENTENCE_MAP",
                ).fetchall()
                WordSentenceMap.objects.bulk_create(
                    [
                        WordSentenceMap(
                            sentence_id=int(_row_value(row, "SENTENCE_ID", 0) or 0),
                            word_id=int(_row_value(row, "WORD_ID", 0) or 0),
                        )
                        for row in word_sentence_rows
                    ],
                    batch_size=batch_size,
                    ignore_conflicts=True,
                )

                default_session = RadicalSession.objects.create(
                    num_of_radicals=min(20, len(radical_models)),
                )
                RadicalSessionRadical.objects.bulk_create(
                    [
                        RadicalSessionRadical(
                            session=default_session,
                            radical=radical,
                            position=position,
                        )
                        for position, radical in enumerate(
                            Radical.objects.order_by("id")[
                                : default_session.num_of_radicals
                            ],
                            start=1,
                        )
                    ],
                    batch_size=batch_size,
                )

        self.stdout.write(self.style.SUCCESS("MCC2LM import finished successfully."))
        self.stdout.write(f"Radicals imported: {Radical.objects.count()}")
        self.stdout.write(f"Logograms imported: {Logogram.objects.count()}")
        self.stdout.write(f"Words imported: {Word.objects.count()}")
        self.stdout.write(f"Sentences imported: {Sentence.objects.count()}")
        self.stdout.write(f"Radicals without matching audio: {missing_audio_count}")
