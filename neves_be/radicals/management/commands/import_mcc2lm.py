from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any

from django.conf import settings
from django.core.management.base import BaseCommand
from django.core.management.base import CommandError
from django.core.management.base import CommandParser
from django.db import transaction

from neves_be.radicals.models import Logogram
from neves_be.radicals.models import Radical
from neves_be.radicals.models import Sentence
from neves_be.radicals.models import Word
from neves_be.radicals.services.mcc2lm_helpers import build_radical_models
from neves_be.radicals.services.mcc2lm_helpers import reset_radical_learning_tables
from neves_be.radicals.services.mcc2lm_imports import create_default_session
from neves_be.radicals.services.mcc2lm_imports import import_logogram_word_maps
from neves_be.radicals.services.mcc2lm_imports import import_logograms
from neves_be.radicals.services.mcc2lm_imports import import_radical_logogram_maps
from neves_be.radicals.services.mcc2lm_imports import import_sentences
from neves_be.radicals.services.mcc2lm_imports import import_word_sentence_maps
from neves_be.radicals.services.mcc2lm_imports import import_words


class Command(BaseCommand):
    help = "Import radicals and LCMC linguistic data from MCC2LM SQLite into Django DB"

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument("sqlite_path", type=str, help="Path to MCC2LM SQLite file")
        parser.add_argument("--batch-size", type=int, default=2000)

    def handle(self, *_args: object, **options: Any) -> None:
        sqlite_path = Path(options["sqlite_path"]).expanduser().resolve()
        batch_size = int(options["batch_size"])

        if not sqlite_path.exists():
            msg = f"SQLite file not found: {sqlite_path}"
            raise CommandError(msg)

        audio_dir = Path(settings.BASE_DIR) / "audio-cmn" / "18k-abr" / "syllabs"
        if not audio_dir.exists():
            self.stdout.write(
                self.style.WARNING(f"Audio directory not found: {audio_dir}"),
            )

        with sqlite3.connect(sqlite_path) as source_db:
            source_db.row_factory = sqlite3.Row
            cursor = source_db.cursor()

            with transaction.atomic():
                reset_radical_learning_tables()

                radicals_query = "SELECT * FROM MCC2LM_RADICAL"
                radicals_rows = cursor.execute(radicals_query).fetchall()
                radical_models, missing_audio_count = build_radical_models(
                    radicals_rows,
                    audio_dir,
                )
                Radical.objects.bulk_create(radical_models, batch_size=batch_size)
                import_logograms(cursor, batch_size)
                import_radical_logogram_maps(cursor, batch_size)
                import_words(cursor, batch_size)
                import_logogram_word_maps(cursor, batch_size)
                import_sentences(cursor, batch_size)
                import_word_sentence_maps(cursor, batch_size)
                create_default_session(len(radical_models), batch_size)

        self.stdout.write(self.style.SUCCESS("MCC2LM import finished successfully."))
        self.stdout.write(f"Radicals imported: {Radical.objects.count()}")
        self.stdout.write(f"Logograms imported: {Logogram.objects.count()}")
        self.stdout.write(f"Words imported: {Word.objects.count()}")
        self.stdout.write(f"Sentences imported: {Sentence.objects.count()}")
        self.stdout.write(f"Radicals without matching audio: {missing_audio_count}")
