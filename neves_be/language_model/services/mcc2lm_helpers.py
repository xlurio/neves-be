from __future__ import annotations

import re
from typing import TYPE_CHECKING
from typing import overload

from neves_be.language_model.models import Logogram
from neves_be.language_model.models import LogogramWordMap
from neves_be.language_model.models import Radical
from neves_be.language_model.models import RadicalLogogramMap
from neves_be.language_model.models import Sentence
from neves_be.language_model.models import Word
from neves_be.language_model.models import WordSentenceMap
from neves_be.practice_assessments.models import RadicalSessionAssessment
from neves_be.practice_questions.models import RadicalSessionAssessmentQuestion
from neves_be.radical_sessions.models import RadicalSession
from neves_be.radical_sessions.models import RadicalSessionRadical

if TYPE_CHECKING:
    import sqlite3
    from pathlib import Path

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
def row_value(row: sqlite3.Row, key: str, default: str = "") -> str: ...


@overload
def row_value(row: sqlite3.Row, key: str, default: int) -> int: ...


def row_value(row: sqlite3.Row, key: str, default: object = "") -> object:
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


def build_radical_models(
    radicals_rows: list[sqlite3.Row],
    audio_dir: Path,
) -> tuple[list[Radical], int]:
    radical_models: list[Radical] = []
    missing_audio_count = 0
    for row in radicals_rows:
        radical_id = str(row_value(row, "ID"))
        pinyin = str(row_value(row, "PINYIN"))
        normalized = normalize_pinyin_for_filename(pinyin)
        pronounce = ""
        if normalized and audio_dir.exists():
            matches = sorted(audio_dir.glob(f"cmn-{normalized}[0-9].mp3"))
            if matches:
                pronounce = f"/audio-cmn/18k-abr/syllabs/{matches[0].name}"
        if not pronounce:
            missing_audio_count += 1
        radical_models.append(
            Radical(
                id=radical_id,
                pinyin=pinyin,
                meaning=str(row_value(row, "MEANING")),
                pronounce=pronounce,
            ),
        )
    return radical_models, missing_audio_count
