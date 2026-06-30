from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import TypedDict
from typing import Unpack

from django.core.management.base import BaseCommand
from django.core.management.base import CommandError
from django.core.management.base import CommandParser
from django.db import transaction

from neves_be.language_model.models import Logogram
from neves_be.language_model.models import Radical
from neves_be.language_model.models import Sentence
from neves_be.language_model.models import Word
from neves_be.language_model.services.mcc2lm_helpers import import_radicals
from neves_be.language_model.services.mcc2lm_helpers import (
    reset_radical_learning_tables,
)
from neves_be.language_model.services.mcc2lm_imports import import_logogram_word_maps
from neves_be.language_model.services.mcc2lm_imports import import_logograms
from neves_be.language_model.services.mcc2lm_imports import import_radical_logogram_maps
from neves_be.language_model.services.mcc2lm_imports import import_sentences
from neves_be.language_model.services.mcc2lm_imports import import_word_sentence_maps
from neves_be.language_model.services.mcc2lm_imports import import_words


class _Options(TypedDict):
    sqlite_path: str
    batch_size: int


class Command(BaseCommand):
    help = "Import radicals and LCMC linguistic data from MCC2LM SQLite into Django DB"

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument("sqlite_path", type=str, help="Path to MCC2LM SQLite file")
        parser.add_argument("--batch-size", type=int, default=2000)

    def handle(self, *_args: object, **options: Unpack[_Options]) -> None:
        del _args

        sqlite_path = Path(options["sqlite_path"]).expanduser().resolve()
        batch_size = int(options["batch_size"])

        if not sqlite_path.exists():
            msg = f"SQLite file not found: {sqlite_path}"
            raise CommandError(msg)

        with sqlite3.connect(sqlite_path) as source_db:
            source_db.row_factory = sqlite3.Row
            cursor = source_db.cursor()

            with transaction.atomic():
                reset_radical_learning_tables()

                import_radicals(cursor, batch_size)
                import_logograms(cursor, batch_size)
                import_radical_logogram_maps(cursor, batch_size)
                import_words(cursor, batch_size)
                import_logogram_word_maps(cursor, batch_size)
                import_sentences(cursor, batch_size)
                import_word_sentence_maps(cursor, batch_size)

        self.__stdout_result()

    def __stdout_result(self) -> None:
        self.stdout.write(self.style.SUCCESS("MCC2LM import finished successfully."))
        self.stdout.write(f"Radicals imported: {Radical.objects.count()}")
        self.stdout.write(f"Logograms imported: {Logogram.objects.count()}")
        self.stdout.write(f"Words imported: {Word.objects.count()}")
        self.stdout.write(f"Sentences imported: {Sentence.objects.count()}")
